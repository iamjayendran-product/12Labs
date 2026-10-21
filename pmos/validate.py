"""Validate derived/backlog.json against the source data.

Run: python -m pmos.validate --company 12labs [--log-derived]
Exit code 0 = valid, 1 = problems (printed one per line)."""
import argparse
import json
import os
import sys
from typing import List, Optional

from pydantic import ValidationError

from pmos.loaders import Company, load_company, source_records
from pmos.schema import Backlog
from pmos.state import EventLog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def validate_backlog(company: Company, backlog: Backlog) -> List[str]:
    errors: List[str] = []
    records = {(r["source"], r["record_id"]): r for r in source_records(company)}
    squads = {s.id for s in company.config.squads}
    ids = [i.id for i in backlog.items]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate id: {dup}")

    for item in backlog.items:
        if item.squad not in squads:
            errors.append(f"{item.id}: unknown squad {item.squad!r}")
        for dep in item.depends_on:
            if dep not in ids:
                errors.append(f"{item.id}: unknown dependency {dep!r}")
        for ev in item.evidence:
            rec = records.get((ev.source, ev.record_id))
            if rec is None:
                errors.append(f"{item.id}: evidence record {ev.source}/{ev.record_id} does not exist")
                continue
            if ev.account != rec["account"]:
                errors.append(
                    f"{item.id}: evidence {ev.record_id} account {ev.account!r} != record account {rec['account']!r}"
                )
            if ev.quote not in rec["text"]:
                errors.append(f"{item.id}: quote not found verbatim in {ev.record_id}: {ev.quote[:60]!r}")

    covered = {i.commitment_id for i in backlog.items if i.commitment_id}
    for c in company.commitments:
        if c.id not in covered:
            errors.append(f"commitment {c.id} ({c.account}) has no backlog item")
    for item in backlog.items:
        if item.commitment_id and item.commitment_id not in {c.id for c in company.commitments}:
            errors.append(f"{item.id}: unknown commitment {item.commitment_id}")

    graph = {i.id: [d for d in i.depends_on if d in ids] for i in backlog.items}
    state = {}

    def visit(n: str) -> bool:
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        if any(visit(d) for d in graph[n]):
            return True
        state[n] = 2
        return False

    if any(visit(n) for n in sorted(graph)):
        errors.append("dependency cycle detected")
    return errors


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--root", default=ROOT)
    p.add_argument("--log-derived", action="store_true", help="append a backlog.derived event if valid")
    args = p.parse_args(argv)
    company = load_company(args.root, args.company)
    path = os.path.join(company.path, "derived", "backlog.json")
    try:
        backlog = Backlog(**json.load(open(path)))
    except (OSError, ValidationError, ValueError) as e:
        print(f"INVALID: cannot load {path}: {e}")
        return 1
    errors = validate_backlog(company, backlog)
    if errors:
        print(f"INVALID: {len(errors)} problem(s)")
        for e in errors:
            print(" -", e)
        return 1
    print(f"OK: {len(backlog.items)} items, {len(company.commitments)} commitments covered")
    if args.log_derived:
        EventLog(os.path.join(args.root, "state")).append(
            "backlog.derived", "claude",
            {"company": args.company, "items": len(backlog.items), "derived_at": backlog.derived_at},
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
