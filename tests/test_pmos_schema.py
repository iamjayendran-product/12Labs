import pytest
from pydantic import ValidationError

from pmos.schema import CRMRecord, Commitment, FirefliesMeeting, NPSRecord


def test_crm_record_requires_positive_arr():
    ok = dict(
        id="crm_001", account="Acme", segment="smb", arr_usd=1000, stage="Negotiation",
        rep="Dana", date="2026-05-01", request="Needs X", notes="Said Y",
    )
    assert CRMRecord(**ok).competitor is None
    with pytest.raises(ValidationError):
        CRMRecord(**{**ok, "arr_usd": 0})


def test_crm_record_rejects_unknown_segment():
    with pytest.raises(ValidationError):
        CRMRecord(
            id="crm_001", account="Acme", segment="giant", arr_usd=10, stage="Won",
            rep="Dana", date="2026-05-01", request="r", notes="n",
        )


def test_fireflies_sentences_have_timestamps_in_order():
    base = dict(
        id="ff_001", title="Call", date="2026-06-01", account="Acme",
        attendees=["A"], summary="s", action_items=["x"],
    )
    ok = FirefliesMeeting(**base, sentences=[
        {"speaker": "A", "start_s": 0.0, "text": "hi"},
        {"speaker": "B", "start_s": 4.5, "text": "yo"},
    ])
    assert ok.sentences[1].start_s == 4.5
    with pytest.raises(ValidationError):
        FirefliesMeeting(**base, sentences=[
            {"speaker": "A", "start_s": 9.0, "text": "hi"},
            {"speaker": "B", "start_s": 4.5, "text": "yo"},
        ])


def test_nps_score_range():
    with pytest.raises(ValidationError):
        NPSRecord(id="n1", account="A", date="2026-06-01", channel="nps", score=11, text="t")


def test_commitment_due_date_must_be_iso_date():
    ok = dict(
        id="com_001", account="Acme", commitment="SSO", due_date="2027-01-31",
        arr_at_risk_usd=1, contract_ref="MSA-1", linked_theme="sso-soc2",
    )
    assert Commitment(**ok).due_date == "2027-01-31"
    with pytest.raises(ValidationError):
        Commitment(**{**ok, "due_date": "31/01/2027"})
