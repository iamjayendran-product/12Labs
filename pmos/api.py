"""FastAPI router for the PM OS. `create_router` takes its paths so tests can use temp state."""
from typing import Dict, List, Optional

import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from pmos.export import render_markdown
from pmos.pipeline import Pipeline


class ItemPatch(BaseModel):
    fields: Dict


class MergeRequest(BaseModel):
    into: str
    from_: List[str] = []

    model_config = {"populate_by_name": True}

    def __init__(self, **data):  # JSON key is "from", a Python keyword
        if "from" in data:
            data["from_"] = data.pop("from")
        super().__init__(**data)


class ThemeBody(BaseModel):
    theme: str


def create_router(root: str, company: str, state_dir: Optional[str] = None,
                  export_path: Optional[str] = None) -> APIRouter:
    pipe = Pipeline(root, company, state_dir)
    router = APIRouter(prefix="/api/pmos")

    def current_items() -> Dict[str, Dict]:
        return {i["id"]: i for i in pipe.snapshot()["items"]}

    @router.get("/sources")
    def sources(source: Optional[str] = None, q: Optional[str] = None,
                account: Optional[str] = None, limit: int = Query(500, le=2000)):
        return pipe.sources(source, q, account, limit)

    @router.get("/backlog")
    def backlog():
        snap = pipe.snapshot()
        return {"company": pipe.name, "derived_at": pipe.derived().derived_at,
                "items": pipe.scored(), "dropped": snap["dropped"],
                "orphaned_overrides": snap["orphaned_overrides"]}

    @router.patch("/items/{item_id}")
    def patch_item(item_id: str, body: ItemPatch):
        if item_id not in current_items():
            raise HTTPException(404, f"unknown item {item_id}")
        valid_squads = [q.id for q in pipe.company().config.squads]
        if "squad" in body.fields and body.fields["squad"] not in valid_squads:
            raise HTTPException(422, f"squad must be one of {valid_squads}")
        try:
            event = pipe.log.append("item.updated", "user", {"item_id": item_id, "fields": body.fields})
        except ValueError as e:
            raise HTTPException(422, str(e))
        return {"event": event}

    @router.delete("/items/{item_id}")
    def drop_item(item_id: str):
        item = current_items().get(item_id)
        if item is None:
            raise HTTPException(404, f"unknown item {item_id}")
        if item.get("commitment_id"):
            raise HTTPException(409, "committed items are pinned and cannot be dropped")
        return {"event": pipe.log.append("item.dropped", "user", {"item_id": item_id})}

    @router.post("/items/merge")
    def merge_items(body: MergeRequest):
        items = current_items()
        if body.into not in items or not body.from_ or any(f not in items for f in body.from_):
            raise HTTPException(404, "unknown item in merge")
        if body.into in body.from_:
            raise HTTPException(400, "cannot merge an item into itself")
        if any(items[f].get("commitment_id") for f in body.from_):
            raise HTTPException(409, "committed items are pinned and cannot be merged away")
        return {"event": pipe.log.append("item.merged", "user", {"into": body.into, "from": body.from_})}

    @router.get("/roadmap")
    def roadmap():
        return pipe.plan()

    @router.get("/roadmap.md")
    def roadmap_md():
        return Response(render_markdown(pipe.plan()), media_type="text/markdown; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="ROADMAP.md"'})

    @router.post("/roadmap/export")
    def export_md():
        path = pipe.export(export_path or os.path.join(root, "ROADMAP.md"), "user")
        return {"path": os.path.basename(path), "event": pipe.log.read()[-1]}

    @router.post("/roadmap/build")
    def build():
        return pipe.build()

    @router.put("/months/{month}/theme")
    def set_theme(month: str, body: ThemeBody):
        if month not in pipe.company().config.quarter.months:
            raise HTTPException(404, f"{month} is not in the quarter")
        return {"event": pipe.log.append("month.theme_set", "user", {"month": month, "theme": body.theme})}

    @router.get("/events")
    def events(limit: int = Query(200, le=2000)):
        return {"events": pipe.log.read()[-limit:], "corrupt_lines": pipe.log.corrupt_lines()}

    return router
