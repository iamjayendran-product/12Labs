"""Render the scheduled plan as ROADMAP.md.

Run: python -m pmos.export --company 12labs [--out ROADMAP.md]"""
import argparse
import os
import sys
from typing import Dict, List, Optional

from pmos.pipeline import Pipeline
from pmos.state import utc_now

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_LABEL = {"voc": "Voice of customer", "crm": "CRM", "fireflies": "Fireflies",
                "support": "NPS / support", "commitment": "Commitment"}


def _usd(n: float) -> str:
    return f"${round(n / 1000)}k"


def _n(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _card(card: Dict, squads: Dict[str, str]) -> List[str]:
    r = card["rice"]["reach"]
    tags = [squads.get(card["squad"], card["squad"]), f"{card['effort_pw']:g} pw"]
    if card["committed"]:
        tags.append(f"**Committed — due {card['due_date']}**")
    if card["end_month"] != card["start_month"]:
        tags.append(f"ships {card['end_month']}")
    if card.get("pulled_by"):
        tags.append(f"pulled forward for {card['pulled_by']}")
    if card["overridden"]:
        tags.append("edited by PM")
    lines = [f"- **{card['title']}** — RICE {card['rice']['score']:.2f} · " + " · ".join(tags),
             f"  {card['problem']}",
             f"  _{_n(r['accounts'], 'account')} · {_usd(r['total_arr'])} ARR · {_n(card['evidence_count'], 'quote')}_"]
    for q in card["quotes"]:
        lines.append(f"  > “{q['quote']}” — {q['account']} ({SOURCE_LABEL.get(q['source'], q['source'])})")
    return lines + [""]


def render_markdown(plan: Dict, generated_at: Optional[str] = None) -> str:
    squads = plan.get("squads", {})
    counts = plan.get("source_counts", {})
    out = [f"# {plan['company']} — {plan['quarter']} Product Roadmap", "",
           f"_Generated {generated_at or utc_now()} · derived from "
           + ", ".join(f"{counts[k]} {SOURCE_LABEL[k].lower()}" for k in ("voc", "crm", "fireflies", "support", "commitment") if k in counts)
           + "_", "",
           "**How this was built.** Contractual commitments are pinned first, earliest deadline first. Everything else is ranked by "
           "RICE (Reach × Impact × Confidence ÷ Effort) and fills the remaining squad capacity. Reach is computed from the "
           "ARR-weighted accounts that asked for the item.", ""]

    out += ["## At a glance", "", "| Month | Theme | Committed | RICE-ranked | Capacity used |", "|---|---|---|---|---|"]
    for m in plan["months"]:
        starts = [c for c in m["items"] if c["phase"] == "starts"]
        used = f"{sum(c['used'] for c in m['capacity'].values()):g}"
        total = f"{sum(c['total'] for c in m['capacity'].values()):g}"
        out.append(f"| {m['label']} | {m['theme']} | {sum(1 for c in starts if c['committed'])} | "
                   f"{sum(1 for c in starts if not c['committed'])} | {used}/{total} pw |")
    out.append("")

    for m in plan["months"]:
        out += [f"## {m['label']} — {m['theme']}", "",
                "Capacity: " + " · ".join(f"{squads.get(s, s)} {c['used']:g}/{c['total']:g} pw" for s, c in m["capacity"].items()), ""]
        starts = [c for c in m["items"] if c["phase"] == "starts"]
        committed = [c for c in starts if c["committed"]]
        ranked = [c for c in starts if not c["committed"]]
        if committed:
            out += ["### Committed (pinned)", ""]
            for c in committed:
                out += _card(c, squads)
        if ranked:
            out += ["### Prioritised by RICE", ""]
            for c in ranked:
                out += _card(c, squads)
        cont = [c for c in m["items"] if c["phase"] == "continues"]
        if cont:
            out += ["### Continuing from earlier months", ""]
            out += [f"- **{c['title']}** — continues from {c['start_month']} ({c['month_pw']:g} pw this month, ships {c['end_month']})" for c in cont]
            out.append("")
        if not m["items"]:
            out += ["_Nothing scheduled._", ""]

    out += ["## Below the line", "",
            "Ranked by RICE but no squad capacity left this quarter (or blocked by a dependency).", "",
            "| Item | Squad | Effort | RICE | Reach | Why not |", "|---|---|---|---|---|---|"]
    for b in plan["below_the_line"]:
        out.append(f"| {b['title']} | {squads.get(b['squad'], b['squad'])} | {b['effort_pw']:g} pw | {b['rice_score']:.2f} | "
                   f"{_n(b['rice']['reach']['accounts'], 'account')} · {_usd(b['rice']['reach']['total_arr'])} | {b['reason']} |")
    out.append("")

    if plan["at_risk"] or plan["oversized"]:
        out += ["## Risks and flags", ""]
        out += [f"- **At risk:** {r['id']} — {r['reason']}" for r in plan["at_risk"]]
        if plan["oversized"]:
            out.append("- **Larger than one squad-month** (spans months; consider splitting): " + ", ".join(plan["oversized"]))
        out.append("")

    placed = {c["commitment_id"]: c for m in plan["months"] for c in m["items"] if c["committed"] and c["phase"] == "starts"}
    out += ["## Commitment register", "", "| ID | Account | Commitment | Due | ARR at risk | Scheduled |", "|---|---|---|---|---|---|"]
    for com in sorted(plan["commitments"], key=lambda c: c["due_date"]):
        card = placed.get(com["id"])
        sched = f"{card['start_month']} → {card['end_month']}" if card else "**not scheduled**"
        out.append(f"| {com['id']} | {com['account']} | {com['commitment']} | {com['due_date']} | {_usd(com['arr_at_risk_usd'])} | {sched} |")
    out.append("")
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--out")
    p.add_argument("--state-dir")
    args = p.parse_args(argv)
    pipe = Pipeline(args.root, args.company, args.state_dir)
    path = pipe.export(args.out or os.path.join(args.root, "ROADMAP.md"), "claude")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
