"""Load a company's mock sources from data/companies/<company>/ into typed models."""
import glob
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Iterator, List

from pmos.schema import (
    CompanyConfig, Commitment, CRMRecord, FirefliesMeeting, Interview, NPSRecord,
)


@dataclass
class Company:
    name: str
    path: str
    config: CompanyConfig
    interviews: List[Interview] = field(default_factory=list)
    crm: List[CRMRecord] = field(default_factory=list)
    fireflies: List[FirefliesMeeting] = field(default_factory=list)
    support: List[NPSRecord] = field(default_factory=list)
    commitments: List[Commitment] = field(default_factory=list)


def _read(path: str):
    with open(path) as f:
        return json.load(f)


def _list_files(folder: str) -> List[str]:
    return sorted(glob.glob(os.path.join(folder, "*.json")))


def load_company(root: str, name: str) -> Company:
    base = os.path.join(root, "data", "companies", name)
    company = Company(
        name=name, path=base, config=CompanyConfig(**_read(os.path.join(base, "company.json")))
    )
    company.interviews = [Interview(**_read(p)) for p in _list_files(os.path.join(base, "voc"))]
    for p in _list_files(os.path.join(base, "crm")):
        company.crm += [CRMRecord(**r) for r in _read(p)]
    company.fireflies = [FirefliesMeeting(**_read(p)) for p in _list_files(os.path.join(base, "fireflies"))]
    for p in _list_files(os.path.join(base, "support")):
        company.support += [NPSRecord(**r) for r in _read(p)]
    commitments_path = os.path.join(base, "commitments.json")
    if os.path.exists(commitments_path):
        company.commitments = [Commitment(**r) for r in _read(commitments_path)]
    return company


def source_records(company: Company) -> Iterator[Dict[str, str]]:
    """Flatten every record to {source, record_id, account, date, text}.

    `text` is the full searchable text of the record; evidence quotes must be a
    verbatim substring of it."""
    for i in company.interviews:
        yield dict(source="voc", record_id=i.id, account=i.company, date=i.date,
                   text="\n".join(t.text for t in i.turns))
    for s in company.support:
        yield dict(source="support", record_id=s.id, account=s.account, date=s.date, text=s.text)
    for c in company.crm:
        yield dict(source="crm", record_id=c.id, account=c.account, date=c.date,
                   text=f"{c.request}\n{c.notes}")
    for m in company.fireflies:
        body = "\n".join(s.text for s in m.sentences)
        yield dict(source="fireflies", record_id=m.id, account=m.account, date=m.date,
                   text=f"{body}\n{m.summary}\n" + "\n".join(m.action_items))
    for c in company.commitments:
        yield dict(source="commitment", record_id=c.id, account=c.account, date=c.due_date,
                   text=c.commitment)
