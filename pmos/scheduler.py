"""Capacity-aware quarter scheduler.

1. Commitments (contract deal-breakers) go first, earliest deadline first, ASAP.
2. Everything else is placed by RICE score, highest first, in the earliest month
   whose squad capacity fits and whose dependencies finished in an earlier month.
3. Dependencies not yet scheduled are pulled forward ahead of their dependent.
4. Regular items never split across months; items bigger than one squad-month
   (oversized) span consecutive months (an uncommitted one needs half a month of
   room to start). Items that don't fit go below the line.
5. A month column lists every item active in it, flagged "starts" or "continues".
"""
from datetime import datetime
from typing import Dict, List, Optional

from pmos.schema import CompanyConfig, Commitment


def _label(month: str) -> str:
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def schedule(
    items: List[Dict],
    commitments: List[Commitment],
    config: CompanyConfig,
    month_themes: Optional[Dict[str, str]] = None,
) -> Dict:
    months = list(config.quarter.months)
    cap = {s.id: s.capacity_pw_per_month for s in config.squads}
    remaining = {(s, m): c for s, c in cap.items() for m in months}
    by_id = {i["id"]: i for i in items}
    due_of = {c.id: c for c in commitments}
    placed: Dict[str, Dict] = {}
    failed: Dict[str, str] = {}
    at_risk: List[Dict] = []
    warnings: List[str] = []
    in_progress = set()

    def due_idx(item: Dict) -> Optional[int]:
        c = due_of.get(item.get("commitment_id") or "")
        if not c:
            return None
        due_month = c.due_date[:7]
        if due_month < months[0]:
            return -1
        return max((i for i, m in enumerate(months) if m <= due_month), default=-1)

    def allocate(item: Dict, earliest: int) -> Optional[Dict[str, float]]:
        squad, effort = item["squad"], item["effective"]["effort_pw"]
        oversized = effort > cap[squad]
        for s in range(earliest, len(months)):
            if not oversized:
                if remaining[(squad, months[s])] >= effort:
                    return {months[s]: effort}
                continue
            committed = bool(item.get("commitment_id") in due_of)
            if not committed and remaining[(squad, months[s])] < cap[squad] / 2:
                continue  # don't start a long uncommitted item in a sliver of capacity
            alloc, left = {}, effort
            for m in months[s:]:
                take = min(remaining[(squad, m)], left)
                if take <= 0:
                    break
                alloc[m], left = take, left - take
                if left <= 0:
                    return alloc
        return None

    def place(item: Dict, pulled_by: Optional[str] = None) -> bool:
        iid = item["id"]
        if iid in placed:
            return True
        if iid in failed:
            return False
        if iid in in_progress:
            failed[iid] = "dependency cycle"
            return False
        if item["squad"] not in cap:
            failed[iid] = f"unknown squad {item['squad']!r}"
            return False
        in_progress.add(iid)
        earliest = 0
        for dep_id in item["depends_on"]:
            dep = by_id.get(dep_id)
            if dep is None:
                warnings.append(f"{iid}: unknown dependency {dep_id}")
                continue
            if not place(dep, pulled_by=iid):
                failed[iid] = f"blocked by {dep_id}"
                in_progress.discard(iid)
                return False
            earliest = max(earliest, months.index(placed[dep_id]["end_month"]) + 1)
        in_progress.discard(iid)
        alloc = allocate(item, earliest)
        if alloc is None:
            failed[iid] = f"no {item['squad']} capacity left this quarter"
            return False
        for m, pw in alloc.items():
            remaining[(item["squad"], m)] -= pw
        keys = list(alloc)
        c = due_of.get(item.get("commitment_id") or "")
        placed[iid] = {
            "id": iid, "title": item.get("title", iid), "squad": item["squad"],
            "theme": item.get("theme") or item["squad"],
            "committed": c is not None, "commitment_id": item.get("commitment_id"),
            "due_date": c.due_date if c else None,
            "effort_pw": item["effective"]["effort_pw"],
            "start_month": keys[0], "end_month": keys[-1], "allocation": alloc,
            "oversized": item["effective"]["effort_pw"] > cap[item["squad"]],
            "rice_score": item["rice"]["score"], "pulled_by": pulled_by,
        }
        d = due_idx(item)
        if d is not None and months.index(keys[-1]) > d:
            at_risk.append({
                "id": iid, "due_date": c.due_date,
                "reason": f"ships {keys[-1]}, after due month {c.due_date[:7]}",
            })
        return True

    committed = sorted(
        (i for i in items if i.get("commitment_id") in due_of),
        key=lambda i: (due_of[i["commitment_id"]].due_date, -due_of[i["commitment_id"]].arr_at_risk_usd, i["id"]),
    )
    for item in committed:
        if not place(item):
            c = due_of[item["commitment_id"]]
            at_risk.append({"id": item["id"], "due_date": c.due_date, "reason": failed[item["id"]]})
    have_item = {i.get("commitment_id") for i in items}
    for c in commitments:
        if c.id not in have_item:
            at_risk.append({"id": c.id, "due_date": c.due_date, "reason": "no backlog item for this commitment"})
    others = sorted(
        (i for i in items if i.get("commitment_id") not in due_of),
        key=lambda i: (-i["rice"]["score"], i["id"]),
    )
    for item in others:
        place(item)

    below = [
        {"id": i["id"], "title": i.get("title", i["id"]), "squad": i["squad"],
         "effort_pw": i["effective"]["effort_pw"], "rice_score": i["rice"]["score"],
         "reason": failed[i["id"]]}
        for i in others if i["id"] in failed and i["id"] not in placed
    ]
    below.sort(key=lambda r: (-r["rice_score"], r["id"]))

    out_months = []
    for m in months:
        active = sorted(
            (p for p in placed.values() if m in p["allocation"]),
            key=lambda p: (not p["committed"], -p["rice_score"], p["id"]),
        )
        in_col = [
            {**p, "phase": "starts" if p["start_month"] == m else "continues", "month_pw": p["allocation"][m]}
            for p in active
        ]
        weights: Dict[str, float] = {}
        for p in active:
            weights[p["theme"]] = weights.get(p["theme"], 0) + p["allocation"][m]
        themes = [{"theme": t, "pw": w} for t, w in sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))]
        theme = (month_themes or {}).get(m) or (themes[0]["theme"] if themes else "")
        out_months.append({
            "month": m, "label": _label(m), "theme": theme, "themes": themes, "items": in_col,
            "capacity": {s: {"used": cap[s] - remaining[(s, m)], "total": cap[s]} for s in cap},
        })
    return {
        "months": out_months,
        "below_the_line": below,
        "at_risk": sorted(at_risk, key=lambda r: r["id"]),
        "oversized": sorted(p["id"] for p in placed.values() if p["oversized"]),
        "warnings": warnings,
    }
