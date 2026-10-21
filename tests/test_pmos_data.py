import json
import os
from collections import defaultdict

import pytest

from pmos.loaders import load_company, source_records

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ground truth of planted themes (kept out of data/ so /derive-backlog never sees it).
THEME_KEYWORDS = {
    "android-sdk": ["android"],
    "streaming-latency": ["latency", "time to first byte", "ttfb"],
    "hindi-arabic-voices": ["hindi", "arabic"],
    "sso-soc2": ["saml", "soc 2", "sso"],
    "usage-pricing": ["usage-based", "pay-as-you-go", "per-minute", "overage"],
    "clone-consent": ["consent", "voice clone", "cloning"],
    "vpc-onprem": ["vpc", "on-prem", "private cloud"],
    "pronunciation-dictionary": ["pronunciation", "lexicon"],
    "usage-analytics": ["analytics", "usage dashboard", "usage report"],
    "webhook-reliability": ["webhook"],
    "unity-sdk": ["unity", "unreal"],
    "support-sla": ["sla", "response time", "p1"],
}


def test_loader_reads_each_source_type(tmp_path):
    base = tmp_path / "data" / "companies" / "acme"
    for d in ("voc", "crm", "fireflies", "support"):
        (base / d).mkdir(parents=True)
    (base / "company.json").write_text(json.dumps({
        "name": "Acme", "product": "p",
        "quarter": {"label": "Q1", "months": ["2027-01", "2027-02", "2027-03"]},
        "squads": [{"id": "s", "name": "S", "engineers": 1, "capacity_pw_per_month": 4}],
        "reach": {"arr_weight_min": 1, "arr_weight_max": 3},
    }))
    (base / "voc" / "call_001.json").write_text(json.dumps({
        "id": "call_001", "customer_name": "A", "company": "Acme Co", "date": "2026-05-01",
        "turns": [{"speaker": "agent", "text": "q"}, {"speaker": "customer", "text": "a"}],
    }))
    (base / "crm" / "opps.json").write_text(json.dumps([{
        "id": "crm_001", "account": "Acme Co", "segment": "smb", "arr_usd": 5, "stage": "Won",
        "rep": "R", "date": "2026-05-02", "request": "r", "notes": "n",
    }]))
    (base / "commitments.json").write_text("[]")
    c = load_company(str(tmp_path), "acme")
    assert (len(c.interviews), len(c.crm), len(c.fireflies), len(c.support)) == (1, 1, 0, 0)
    assert c.config.name == "Acme"
    kinds = {r["source"] for r in source_records(c)}
    assert kinds == {"voc", "crm"}


@pytest.fixture(scope="module")
def company():
    return load_company(ROOT, "12labs")


def test_mock_volume_matches_plan(company):
    assert len(company.interviews) >= 50
    assert len(company.crm) >= 28
    assert len(company.fireflies) >= 10
    assert len(company.support) >= 38
    assert len(company.commitments) == 6


def test_record_ids_are_unique(company):
    ids = [r["record_id"] for r in source_records(company)]
    assert len(ids) == len(set(ids))


def test_new_data_is_dated_apr_to_oct_2026(company):
    for rec in list(company.crm) + list(company.fireflies) + list(company.support):
        assert "2026-04-01" <= rec.date <= "2026-10-20", rec.id


def test_commitments_due_inside_q1_2027_and_backed_by_a_crm_account(company):
    crm_accounts = {r.account for r in company.crm}
    for c in company.commitments:
        assert "2027-01-01" <= c.due_date <= "2027-03-31", c.id
        assert c.account in crm_accounts, c.id


def test_every_planted_theme_appears_in_several_sources(company):
    hits = defaultdict(set)
    for rec in source_records(company):
        low = rec["text"].lower()
        for theme, kws in THEME_KEYWORDS.items():
            if any(k in low for k in kws):
                hits[theme].add(rec["source"])
    for theme in THEME_KEYWORDS:
        assert len(hits[theme]) >= 2, f"{theme} only in {hits[theme]}"


def test_arr_is_consistent_per_account(company):
    arr = defaultdict(set)
    for r in company.crm:
        arr[r.account].add(r.arr_usd)
    assert all(len(v) == 1 for v in arr.values())
