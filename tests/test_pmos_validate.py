import json
import os

import pytest

from pmos.validate import main, validate_backlog
from pmos.loaders import load_company
from pmos.schema import Backlog

CONFIG = {
    "name": "Acme", "product": "p",
    "quarter": {"label": "Q1", "months": ["2027-01", "2027-02", "2027-03"]},
    "squads": [{"id": "s1", "name": "S1", "engineers": 1, "capacity_pw_per_month": 8}],
    "reach": {"arr_weight_min": 1, "arr_weight_max": 3},
}


def make_company(tmp_path, items):
    base = tmp_path / "data" / "companies" / "acme"
    for d in ("voc", "crm", "fireflies", "support", "derived"):
        (base / d).mkdir(parents=True)
    (base / "company.json").write_text(json.dumps(CONFIG))
    (base / "crm" / "o.json").write_text(json.dumps([{
        "id": "crm_001", "account": "Acme Co", "segment": "smb", "arr_usd": 5, "stage": "Won",
        "rep": "R", "date": "2026-05-02", "request": "We need SAML SSO.", "notes": "Blocker for renewal.",
    }]))
    (base / "commitments.json").write_text(json.dumps([{
        "id": "com_001", "account": "Acme Co", "commitment": "Ship SSO.", "due_date": "2027-01-31",
        "arr_at_risk_usd": 5, "contract_ref": "X", "linked_theme": "sso",
    }]))
    (base / "derived" / "backlog.json").write_text(json.dumps({
        "company": "acme", "derived_at": "2026-10-21T10:00:00Z", "items": items}))
    return str(tmp_path)


def item(**over):
    base = {
        "id": "sso", "title": "SSO", "problem": "p", "squad": "s1", "theme": "Enterprise",
        "evidence": [{"source": "crm", "record_id": "crm_001", "account": "Acme Co", "quote": "We need SAML SSO."}],
        "suggested": {"impact": 2, "confidence": 0.8, "effort_pw": 4, "rationale": "r"},
        "depends_on": [], "commitment_id": "com_001",
    }
    base.update(over)
    return base


def errors(tmp_path, items):
    root = make_company(tmp_path, items)
    company = load_company(root, "acme")
    backlog = Backlog(**json.load(open(os.path.join(company.path, "derived", "backlog.json"))))
    return validate_backlog(company, backlog)


def test_valid_backlog_has_no_errors(tmp_path):
    assert errors(tmp_path, [item()]) == []


def test_fabricated_quote_is_reported(tmp_path):
    bad = item(evidence=[{"source": "crm", "record_id": "crm_001", "account": "Acme Co", "quote": "We need FIDO keys."}])
    errs = errors(tmp_path, [bad])
    assert any("crm_001" in e and "not found verbatim" in e for e in errs)


def test_quote_attributed_to_the_wrong_account_is_reported(tmp_path):
    bad = item(evidence=[{"source": "crm", "record_id": "crm_001", "account": "Other", "quote": "We need SAML SSO."}])
    assert any("account" in e for e in errors(tmp_path, [bad]))


def test_unknown_record_is_reported(tmp_path):
    bad = item(evidence=[{"source": "crm", "record_id": "crm_999", "account": "Acme Co", "quote": "x"}])
    assert any("crm_999" in e for e in errors(tmp_path, [bad]))


def test_every_commitment_must_have_an_item(tmp_path):
    errs = errors(tmp_path, [item(commitment_id=None)])
    assert any("com_001" in e and "no backlog item" in e for e in errs)


def test_unknown_squad_unknown_dependency_and_duplicate_ids(tmp_path):
    errs = errors(tmp_path, [item(squad="nope", depends_on=["ghost"]), item()])
    joined = " | ".join(errs)
    assert "unknown squad" in joined and "unknown dependency" in joined and "duplicate id" in joined


def test_dependency_cycle_is_reported(tmp_path):
    a = item(id="a", commitment_id="com_001", depends_on=["b"])
    b = item(id="b", commitment_id=None, depends_on=["a"])
    assert any("cycle" in e for e in errors(tmp_path, [a, b]))


def test_item_without_evidence_or_with_bad_scale_fails_schema():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Backlog(company="a", derived_at="t", items=[item(evidence=[])])
    with pytest.raises(ValidationError):
        Backlog(company="a", derived_at="t", items=[item(suggested={"impact": 5, "confidence": 0.8, "effort_pw": 4, "rationale": "r"})])
    with pytest.raises(ValidationError):
        Backlog(company="a", derived_at="t", items=[item(id="Bad Id")])


def test_cli_exit_codes_and_derived_event(tmp_path):
    root = make_company(tmp_path, [item()])
    assert main(["--company", "acme", "--root", root, "--log-derived"]) == 0
    events = [json.loads(l) for l in open(os.path.join(root, "state", "events.jsonl"))]
    assert [e["type"] for e in events] == ["sources.loaded", "backlog.derived"]
    assert events[0]["payload"]["counts"] == {"crm": 1, "commitment": 1}
    assert events[-1]["payload"]["items"] == 1
    root2 = make_company(tmp_path / "two", [item(commitment_id=None)])
    assert main(["--company", "acme", "--root", root2]) == 1


def add_sources(root):
    base = os.path.join(root, "data", "companies", "acme")
    json.dump({"id": "call_001", "customer_name": "Cy", "company": "Acme Co", "date": "2026-05-01", "turns": [
        {"speaker": "agent", "text": "Would single sign-on matter to you at all?"},
        {"speaker": "customer", "text": "Absolutely, we need SAML SSO for every vendor."},
        {"speaker": "customer", "text": "And a SOC 2 report."}]}, open(os.path.join(base, "voc", "call_001.json"), "w"))
    json.dump({"id": "ff_001", "title": "t", "date": "2026-05-02", "account": "Acme Co",
               "attendees": ["Pat (Pat Corp)", "Dana (Acme)"],
               "sentences": [{"speaker": "Pat", "start_s": 0, "text": "Our security team demands SAML SSO."},
                             {"speaker": "Dana", "start_s": 5, "text": "We will look at an enterprise roadmap soon."}],
               "summary": "Acme wants a strongly governed identity layer.", "action_items": ["Dana to scope hardware tokens"]},
              open(os.path.join(base, "fireflies", "ff_001.json"), "w"))


def quote_errors(tmp_path, source, rid, quote):
    root = make_company(tmp_path, [item()])
    add_sources(root)
    bad = item(evidence=[{"source": source, "record_id": rid, "account": "Acme Co", "quote": quote}])
    return errors_from(root, [bad])


def errors_from(root, items):
    base = os.path.join(root, "data", "companies", "acme", "derived", "backlog.json")
    json.dump({"company": "acme", "derived_at": "t", "items": items}, open(base, "w"))
    company = load_company(root, "acme")
    return validate_backlog(company, Backlog(**json.load(open(base))))


@pytest.mark.parametrize("source,rid,quote,expected_error", [
    ("voc", "call_001", "Would single sign-on matter to you at all?", "not customer speech"),
    ("voc", "call_001", "for every vendor.\nAnd a SOC 2 report.", "spans"),
    ("fireflies", "ff_001", "strongly governed identity layer", "not customer speech"),
    ("fireflies", "ff_001", "hardware tokens", "not customer speech"),
    ("fireflies", "ff_001", "We will look at an enterprise roadmap soon.", "not customer speech"),
    ("crm", "crm_001", "SAML SSO", "too short"),
])
def test_validator_accepts_only_customer_speech_and_substantial_single_line_quotes(tmp_path, source, rid, quote, expected_error):
    assert any(expected_error in e for e in quote_errors(tmp_path, source, rid, quote))


def test_customer_turn_and_customer_sentence_quotes_are_still_accepted(tmp_path):
    assert quote_errors(tmp_path, "voc", "call_001", "Absolutely, we need SAML SSO for every vendor.") == []
    assert quote_errors(tmp_path / "ff", "fireflies", "ff_001", "Our security team demands SAML SSO.") == []
