import pytest

from pmos.rice import account_arr, median_arr, reach, rice_score, score_items
from pmos.schema import ReachConfig

CFG = ReachConfig(arr_weight_min=1, arr_weight_max=3)


def ev(account, record_id="r1", quote="q"):
    return {"source": "crm", "record_id": record_id, "account": account, "quote": quote}


def test_median_arr_of_distinct_accounts():
    assert median_arr({"a": 100, "b": 300, "c": 200}) == 200
    assert median_arr({"a": 100, "b": 300}) == 200


def test_reach_weights_accounts_by_arr_clamped_between_min_and_max():
    arr = {"big": 1000, "mid": 150, "tiny": 10}
    r = reach([ev("big"), ev("mid"), ev("tiny")], arr, median=100, cfg=CFG)
    weights = {b["account"]: b["weight"] for b in r["breakdown"]}
    assert weights == {"big": 3, "mid": 1.5, "tiny": 1}
    assert r["score"] == 5.5 and r["accounts"] == 3 and r["total_arr"] == 1160


def test_reach_counts_each_account_once_however_many_quotes():
    r = reach([ev("a", "r1"), ev("a", "r2"), ev("a", "r3")], {"a": 200}, median=100, cfg=CFG)
    assert r["accounts"] == 1 and r["score"] == 2


def test_account_without_crm_arr_gets_minimum_weight():
    r = reach([ev("voc-only")], {"a": 500}, median=100, cfg=CFG)
    assert r["score"] == 1 and r["total_arr"] == 0
    assert r["breakdown"][0]["arr"] is None


def test_rice_formula():
    assert rice_score(4, 2, 0.8, 4) == 1.6


def test_rice_rejects_non_positive_effort():
    with pytest.raises(ValueError):
        rice_score(4, 2, 0.8, 0)


def test_score_items_uses_effective_values_and_sorts_best_first():
    items = [
        {"id": "slow", "evidence": [ev("a")], "effective": {"impact": 1, "confidence": 1.0, "effort_pw": 10}},
        {"id": "fast", "evidence": [ev("a")], "effective": {"impact": 1, "confidence": 1.0, "effort_pw": 2}},
        {"id": "also-fast", "evidence": [ev("a")], "effective": {"impact": 1, "confidence": 1.0, "effort_pw": 2}},
    ]
    scored = score_items(items, {"a": 100}, CFG)
    assert [i["id"] for i in scored] == ["also-fast", "fast", "slow"]  # tie broken by id
    assert scored[0]["rice"]["score"] == 0.5 and scored[0]["rice"]["reach"]["score"] == 1


def test_account_arr_reads_crm_and_commitments(tmp_path):
    from pmos.loaders import load_company
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arr = account_arr(load_company(root, "12labs"))
    assert arr["Vantage Enterprise Systems"] == 480000
    assert arr["Alpine Trail Guides"] == 18000
