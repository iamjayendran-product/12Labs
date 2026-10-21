from pmos.pipeline import top_quotes


def ev(source, rid, account, quote="q"):
    return {"source": source, "record_id": rid, "account": account, "quote": quote + rid}


def test_picks_distinct_accounts_biggest_arr_first():
    item = {"evidence": [ev("crm", "crm_1", "small"), ev("voc", "call_1", "big"), ev("crm", "crm_2", "big"), ev("crm", "crm_3", "mid")]}
    picked = top_quotes(item, {"small": 10, "big": 900, "mid": 100}, n=3)
    assert [p["account"] for p in picked] == ["big", "mid", "small"]


def test_prefers_customer_voice_over_the_commitment_register_line():
    item = {"evidence": [ev("commitment", "com_001", "A"), ev("crm", "crm_001", "A"), ev("support", "sup_001", "B")]}
    picked = top_quotes(item, {"A": 500, "B": 100})
    assert [p["source"] for p in picked] == ["crm", "support"]


def test_falls_back_to_the_commitment_line_when_it_is_the_only_evidence():
    item = {"evidence": [ev("commitment", "com_001", "A")]}
    assert [p["record_id"] for p in top_quotes(item, {"A": 1})] == ["com_001"]


def test_mixes_source_types_when_one_account_has_several_records():
    item = {"evidence": [ev("crm", "crm_1", "A"), ev("crm", "crm_2", "B"), ev("fireflies", "ff_1", "B")]}
    picked = top_quotes(item, {"A": 100, "B": 100}, n=2)
    assert len({p["account"] for p in picked}) == 2
