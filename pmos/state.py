"""Timestamped, append-only app state: an event log plus a snapshot rebuilt by replay.

Overrides are keyed by item id, so they survive a re-derive of backlog.json as long
as /derive-backlog keeps item ids stable."""
import copy
import json
import math
import os
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

EVENT_TYPES = {
    "sources.loaded", "backlog.derived", "item.updated", "item.merged",
    "item.dropped", "month.theme_set", "roadmap.built", "roadmap.exported",
}
IMPACT_SCALE = (0.25, 0.5, 1, 2, 3)
CONFIDENCE_SCALE = (0.5, 0.8, 1.0)
EDITABLE_FIELDS = {"impact", "confidence", "effort_pw", "title", "squad"}
RICE_FIELDS = ("impact", "confidence", "effort_pw")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _validate_fields(fields: Dict) -> None:
    if not isinstance(fields, dict) or not fields:
        raise ValueError("fields must be a non-empty object")
    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"cannot edit fields: {sorted(unknown)}")
    if "impact" in fields and not (_is_number(fields["impact"]) and fields["impact"] in IMPACT_SCALE):
        raise ValueError(f"impact must be one of {IMPACT_SCALE}")
    if "confidence" in fields and not (_is_number(fields["confidence"]) and fields["confidence"] in CONFIDENCE_SCALE):
        raise ValueError(f"confidence must be one of {CONFIDENCE_SCALE}")
    if "effort_pw" in fields and not (_is_number(fields["effort_pw"]) and fields["effort_pw"] > 0):
        raise ValueError("effort_pw must be a finite number > 0")
    for k in ("title", "squad"):
        if k in fields and not (isinstance(fields[k], str) and fields[k].strip()):
            raise ValueError(f"{k} must be a non-empty string")


class EventLog:
    def __init__(self, state_dir: str, clock: Optional[Callable[[], str]] = None):
        self.dir = state_dir
        self.path = os.path.join(state_dir, "events.jsonl")
        self._clock = clock or utc_now

    def append(self, type_: str, actor: str, payload: Dict) -> Dict:
        if type_ not in EVENT_TYPES:
            raise ValueError(f"unknown event type: {type_}")
        if type_ == "item.updated":
            _validate_fields(payload.get("fields", {}))
        event = {"ts": self._clock(), "actor": actor, "type": type_, "payload": payload}
        os.makedirs(self.dir, exist_ok=True)
        prefix = ""
        if os.path.exists(self.path) and os.path.getsize(self.path):
            with open(self.path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    prefix = "\n"  # terminate a torn line so this event starts on its own line
        with open(self.path, "a") as f:
            f.write(prefix + json.dumps(event) + "\n")
        return event

    def _scan(self):
        events, corrupt = [], 0
        if not os.path.exists(self.path):
            return events, corrupt
        with open(self.path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    corrupt += 1
                    continue
                if (isinstance(e, dict) and isinstance(e.get("ts"), str) and e.get("type") in EVENT_TYPES
                        and isinstance(e.get("payload"), dict)):
                    events.append(e)
                else:
                    corrupt += 1
        return events, corrupt

    def read(self) -> List[Dict]:
        """Valid events in chronological order; unreadable lines are skipped (see corrupt_lines)."""
        return sorted(self._scan()[0], key=lambda e: e["ts"])  # stable: ties keep file order

    def corrupt_lines(self) -> int:
        return self._scan()[1]


def _evidence_key(e: Dict):
    return (e["source"], e["record_id"], e["quote"])


def build_snapshot(items: List[Dict], events: List[Dict]) -> Dict:
    """Replay events over the derived backlog; return the current effective state."""
    by_id = {i["id"]: copy.deepcopy(i) for i in items}
    overrides: Dict[str, Dict] = {}
    dropped: List[str] = []
    merges = []
    month_themes: Dict[str, str] = {}
    ignored: List[Dict] = []
    pinned = {i["id"] for i in items if i.get("commitment_id")}  # a stale or hand-edited log must never remove a commitment
    for e in events:
        p = e["payload"]
        try:
            if e["type"] == "item.updated":
                overrides.setdefault(p["item_id"], {}).update(p["fields"])
            elif e["type"] == "item.dropped":
                if p["item_id"] in pinned:
                    ignored.append(e)
                else:
                    dropped.append(p["item_id"])
            elif e["type"] == "item.merged":
                away = [x for x in p["from"] if x not in pinned]
                if len(away) != len(p["from"]):
                    ignored.append(e)
                merges.append((p["into"], away))
            elif e["type"] == "month.theme_set":
                month_themes[p["month"]] = p["theme"]
        except (KeyError, TypeError):
            ignored.append(e)

    for into, sources in merges:
        if into not in by_id:
            continue
        target = by_id[into]
        for src in sources:
            if src not in by_id or src == into:
                continue
            seen = {_evidence_key(x) for x in target["evidence"]}
            target["evidence"] += [x for x in by_id[src]["evidence"] if _evidence_key(x) not in seen]
            target.setdefault("merged_from", []).append(src)
            del by_id[src]
            for other in by_id.values():
                other["depends_on"] = [into if d == src else d for d in other["depends_on"]]
                other["depends_on"] = [d for d in other["depends_on"] if d != other["id"]]
    for d in dropped:
        by_id.pop(d, None)

    merged_away = {s for _, srcs in merges for s in srcs}
    out = []
    for item in by_id.values():
        ov = overrides.get(item["id"], {})
        eff = {k: item["suggested"][k] for k in RICE_FIELDS}
        eff.update({k: ov[k] for k in RICE_FIELDS if k in ov})
        for k in ("title", "squad"):
            if k in ov:
                item[k] = ov[k]
        item["effective"] = eff
        item["overridden"] = sorted(ov)
        out.append(item)
    orphaned = sorted(k for k in overrides if k not in by_id and k not in dropped and k not in merged_away)
    return {
        "items": out,
        "dropped": sorted(set(dropped)),
        "orphaned_overrides": orphaned,
        "month_themes": month_themes,
        "ignored_events": ignored,
    }


def write_snapshot(state_dir: str, items: List[Dict], events: List[Dict], now: Optional[str] = None) -> str:
    snap = build_snapshot(items, events)
    snap["generated_at"] = now or utc_now()
    snap["event_count"] = len(events)
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, "snapshot.json")
    with open(path, "w") as f:
        json.dump(snap, f, indent=2)
    return path
