"""Glue: sources + derived backlog + event log -> snapshot -> RICE -> schedule.

Everything is recomputed from files on each call, so edits to data/ or the event
log show up immediately and there is no cache to invalidate."""
import json
import os
from typing import Dict, List, Optional

from pmos.loaders import Company, load_company, source_records
from pmos.rice import account_arr, score_items
from pmos.scheduler import schedule
from pmos.schema import Backlog
from pmos.state import EventLog, build_snapshot, write_snapshot


def top_quotes(item: Dict, arr: Dict[str, int], n: int = 3) -> List[Dict]:
    """Pick up to n quotes: distinct accounts first, biggest ARR first, mixed source types."""
    ranked = sorted(item["evidence"], key=lambda e: (-(arr.get(e["account"]) or 0), e["record_id"]))
    picked, accounts, sources = [], set(), set()
    for prefer_new_source in (True, False):
        for e in ranked:
            if len(picked) >= n or e in picked or e["account"] in accounts:
                continue
            if prefer_new_source and e["source"] in sources:
                continue
            picked.append(e)
            accounts.add(e["account"])
            sources.add(e["source"])
    return picked


class Pipeline:
    def __init__(self, root: str, company: str, state_dir: Optional[str] = None):
        self.root, self.name = root, company
        self.state_dir = state_dir or os.path.join(root, "state")
        self.log = EventLog(self.state_dir)

    def company(self) -> Company:
        return load_company(self.root, self.name)

    def derived(self) -> Backlog:
        path = os.path.join(self.company().path, "derived", "backlog.json")
        with open(path) as f:
            return Backlog(**json.load(f))

    def snapshot(self) -> Dict:
        items = [i.model_dump() for i in self.derived().items]
        return build_snapshot(items, self.log.read())

    def scored(self) -> List[Dict]:
        c = self.company()
        return score_items(self.snapshot()["items"], account_arr(c), c.config.reach)

    def plan(self) -> Dict:
        c = self.company()
        snap = self.snapshot()
        arr = account_arr(c)
        scored = score_items(snap["items"], arr, c.config.reach)
        plan = schedule(scored, c.commitments, c.config, snap["month_themes"])
        by_id = {i["id"]: i for i in scored}

        def enrich(card: Dict) -> Dict:
            item = by_id[card["id"]]
            return {**card, "problem": item["problem"], "rice": item["rice"],
                    "effective": item["effective"], "overridden": item["overridden"],
                    "depends_on": item["depends_on"], "quotes": top_quotes(item, arr),
                    "evidence_count": len(item["evidence"])}

        for m in plan["months"]:
            m["items"] = [enrich(i) for i in m["items"]]
        plan["below_the_line"] = [{**b, "problem": by_id[b["id"]]["problem"],
                                   "rice": by_id[b["id"]]["rice"]} for b in plan["below_the_line"]]
        plan["company"] = c.config.name
        plan["quarter"] = c.config.quarter.label
        plan["commitments"] = [c_.model_dump() for c_ in c.commitments]
        return plan

    def build(self, actor: str = "user") -> Dict:
        plan = self.plan()
        self.log.append("roadmap.built", actor, {
            "placed": len({i["id"] for m in plan["months"] for i in m["items"]}),
            "below_the_line": len(plan["below_the_line"]), "at_risk": len(plan["at_risk"]),
        })
        items = [i.model_dump() for i in self.derived().items]
        write_snapshot(self.state_dir, items, self.log.read())
        return plan

    def sources(self, source: Optional[str] = None, q: Optional[str] = None,
                account: Optional[str] = None, limit: int = 500) -> Dict:
        records = list(source_records(self.company()))
        counts: Dict[str, int] = {}
        for r in records:
            counts[r["source"]] = counts.get(r["source"], 0) + 1
        if source:
            records = [r for r in records if r["source"] == source]
        if account:
            records = [r for r in records if r["account"] == account]
        if q:
            low = q.lower()
            records = [r for r in records if low in r["text"].lower() or low in r["account"].lower()]
        return {"counts": counts, "total": len(records), "records": records[:limit]}
