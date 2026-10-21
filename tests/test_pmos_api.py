import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pmos.api import create_router

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    app.include_router(create_router(ROOT, "12labs", str(tmp_path)))
    c = TestClient(app)
    c.state_dir = tmp_path
    return c


def items_by_id(client):
    return {i["id"]: i for i in client.get("/api/pmos/backlog").json()["items"]}


def test_sources_reports_counts_and_filters(client):
    data = client.get("/api/pmos/sources").json()
    assert data["counts"] == {"voc": 51, "support": 42, "crm": 32, "fireflies": 10, "commitment": 6}
    only_crm = client.get("/api/pmos/sources", params={"source": "crm"}).json()["records"]
    assert len(only_crm) == 32 and {r["source"] for r in only_crm} == {"crm"}
    hits = client.get("/api/pmos/sources", params={"q": "Gulf dialect"}).json()["records"]
    assert hits and all("gulf dialect" in r["text"].lower() for r in hits)


def test_backlog_is_scored_and_sorted_best_first(client):
    body = client.get("/api/pmos/backlog").json()
    scores = [i["rice"]["score"] for i in body["items"]]
    assert len(scores) == 29 and scores == sorted(scores, reverse=True)
    first = body["items"][0]
    assert first["rice"]["reach"]["breakdown"] and first["evidence"] and "effective" in first


def test_patch_item_overrides_scores_and_logs_a_user_event(client):
    before = items_by_id(client)["pronunciation-dictionary"]["rice"]["score"]
    r = client.patch("/api/pmos/items/pronunciation-dictionary", json={"fields": {"effort_pw": 12}})
    assert r.status_code == 200
    after = items_by_id(client)["pronunciation-dictionary"]
    assert after["effective"]["effort_pw"] == 12 and after["overridden"] == ["effort_pw"]
    assert after["rice"]["score"] == pytest.approx(before / 2, abs=0.01)
    ev = client.get("/api/pmos/events").json()["events"][-1]
    assert ev["type"] == "item.updated" and ev["actor"] == "user" and ev["ts"].endswith("Z")


def test_patch_rejects_bad_values_and_unknown_items(client):
    assert client.patch("/api/pmos/items/sso-soc2", json={"fields": {"confidence": 0.9}}).status_code == 422
    assert client.patch("/api/pmos/items/nope", json={"fields": {"impact": 1}}).status_code == 404


def test_drop_removes_an_item_but_commitments_are_pinned(client):
    assert client.delete("/api/pmos/items/salesforce-connector").status_code == 200
    body = client.get("/api/pmos/backlog").json()
    assert "salesforce-connector" not in {i["id"] for i in body["items"]}
    assert "salesforce-connector" in body["dropped"]
    assert client.delete("/api/pmos/items/sso-soc2").status_code == 409
    assert client.delete("/api/pmos/items/nope").status_code == 404


def test_merge_unions_evidence_into_target_and_protects_commitments(client):
    before = items_by_id(client)
    n_into, n_from = len(before["hindi-voices"]["evidence"]), len(before["swahili-voices"]["evidence"])
    r = client.post("/api/pmos/items/merge", json={"into": "hindi-voices", "from": ["swahili-voices"]})
    assert r.status_code == 200
    after = items_by_id(client)
    assert "swahili-voices" not in after and len(after["hindi-voices"]["evidence"]) == n_into + n_from
    assert client.post("/api/pmos/items/merge", json={"into": "hindi-voices", "from": ["sso-soc2"]}).status_code == 409
    assert client.post("/api/pmos/items/merge", json={"into": "nope", "from": ["salesforce-connector"]}).status_code == 404


def test_roadmap_places_every_commitment_on_or_before_its_due_month(client):
    plan = client.get("/api/pmos/roadmap").json()
    assert [m["month"] for m in plan["months"]] == ["2027-01", "2027-02", "2027-03"]
    due = {c["commitment_id"]: c["due_date"] for m in plan["months"] for c in m["items"] if c["committed"]}
    assert len(due) == 6
    for m in plan["months"]:
        for i in m["items"]:
            if i["committed"]:
                assert i["end_month"] <= i["due_date"][:7], i["id"]
    assert plan["at_risk"] == []
    assert plan["below_the_line"]


def test_roadmap_reacts_to_overrides(client):
    def placement():
        plan = client.get("/api/pmos/roadmap").json()
        ids = {i["id"] for m in plan["months"] for i in m["items"]}
        return ids, {b["id"] for b in plan["below_the_line"]}
    placed, below = placement()
    assert "pronunciation-dictionary" in placed
    client.patch("/api/pmos/items/pronunciation-dictionary", json={"fields": {"effort_pw": 15}})
    client.patch("/api/pmos/items/usage-analytics-dashboard", json={"fields": {"impact": 3}})
    placed2, below2 = placement()
    assert (placed, below) != (placed2, below2)


def test_build_logs_event_and_writes_snapshot(client):
    r = client.post("/api/pmos/roadmap/build")
    assert r.status_code == 200 and r.json()["months"]
    types = [e["type"] for e in client.get("/api/pmos/events").json()["events"]]
    assert types[-1] == "roadmap.built"
    snap = json.loads((client.state_dir / "snapshot.json").read_text())
    assert snap["event_count"] >= 1 and snap["generated_at"].endswith("Z")


def test_month_theme_can_be_edited_and_is_logged(client):
    assert client.put("/api/pmos/months/2027-02/theme", json={"theme": "Trust & scale"}).status_code == 200
    plan = client.get("/api/pmos/roadmap").json()
    assert plan["months"][1]["theme"] == "Trust & scale"
    assert client.put("/api/pmos/months/2027-09/theme", json={"theme": "x"}).status_code == 404


def test_router_is_mounted_in_the_real_app_without_breaking_chat():
    from app.main import app
    c = TestClient(app)
    assert c.get("/api/pmos/sources").status_code == 200
    assert c.post("/chat", json={"question": "  "}).status_code == 400
