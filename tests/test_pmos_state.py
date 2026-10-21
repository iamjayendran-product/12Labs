import json

import pytest

from pmos.state import EventLog, build_snapshot, write_snapshot


def item(id_, impact=1, conf=0.8, effort=4, depends=None, evidence=None, commitment=None):
    return {
        "id": id_, "title": id_.title(), "problem": "p", "squad": "platform-sdk",
        "evidence": evidence or [{"source": "crm", "record_id": "crm_001", "account": "A", "quote": "q1"}],
        "suggested": {"impact": impact, "confidence": conf, "effort_pw": effort, "rationale": "r"},
        "depends_on": depends or [], "commitment_id": commitment,
    }


def fixed_clock():
    ticks = iter(["2026-10-21T10:00:00Z", "2026-10-21T10:00:05Z", "2026-10-21T10:00:09Z", "2026-10-21T10:01:00Z"])
    return lambda: next(ticks)


def test_append_stamps_iso_utc_timestamp_and_actor(tmp_path):
    log = EventLog(str(tmp_path), clock=fixed_clock())
    e = log.append("sources.loaded", "claude", {"records": 5})
    assert e["ts"] == "2026-10-21T10:00:00Z" and e["actor"] == "claude" and e["type"] == "sources.loaded"
    assert json.loads((tmp_path / "events.jsonl").read_text().splitlines()[0]) == e


def test_log_is_append_only_and_read_returns_chronological_order(tmp_path):
    log = EventLog(str(tmp_path), clock=fixed_clock())
    log.append("sources.loaded", "claude", {})
    log.append("backlog.derived", "claude", {"items": 3})
    assert [e["type"] for e in log.read()] == ["sources.loaded", "backlog.derived"]
    assert len((tmp_path / "events.jsonl").read_text().splitlines()) == 2


def test_unknown_event_type_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        EventLog(str(tmp_path)).append("item.exploded", "user", {})


def test_item_update_rejects_out_of_scale_values(tmp_path):
    log = EventLog(str(tmp_path))
    with pytest.raises(ValueError):
        log.append("item.updated", "user", {"item_id": "a", "fields": {"confidence": 0.9}})
    with pytest.raises(ValueError):
        log.append("item.updated", "user", {"item_id": "a", "fields": {"impact": 5}})
    with pytest.raises(ValueError):
        log.append("item.updated", "user", {"item_id": "a", "fields": {"effort_pw": 0}})


def test_override_wins_over_suggestion_and_is_flagged(tmp_path):
    log = EventLog(str(tmp_path))
    log.append("item.updated", "user", {"item_id": "a", "fields": {"effort_pw": 9}})
    snap = build_snapshot([item("a", effort=4)], log.read())
    a = snap["items"][0]
    assert a["effective"] == {"impact": 1, "confidence": 0.8, "effort_pw": 9}
    assert a["overridden"] == ["effort_pw"]


def test_dropped_items_leave_the_snapshot(tmp_path):
    log = EventLog(str(tmp_path))
    log.append("item.dropped", "user", {"item_id": "b"})
    snap = build_snapshot([item("a"), item("b")], log.read())
    assert [i["id"] for i in snap["items"]] == ["a"]
    assert snap["dropped"] == ["b"]


def test_merge_unions_evidence_and_repoints_dependencies(tmp_path):
    log = EventLog(str(tmp_path))
    log.append("item.merged", "user", {"into": "a", "from": ["b"]})
    ev_b = [{"source": "voc", "record_id": "call_001", "account": "B", "quote": "q2"}]
    items = [item("a"), item("b", evidence=ev_b), item("c", depends=["b"])]
    snap = build_snapshot(items, log.read())
    by_id = {i["id"]: i for i in snap["items"]}
    assert set(by_id) == {"a", "c"}
    assert {e["record_id"] for e in by_id["a"]["evidence"]} == {"crm_001", "call_001"}
    assert by_id["c"]["depends_on"] == ["a"]
    assert by_id["a"]["merged_from"] == ["b"]


def test_overrides_survive_a_rederive_and_orphans_are_reported(tmp_path):
    log = EventLog(str(tmp_path))
    log.append("item.updated", "user", {"item_id": "a", "fields": {"impact": 3}})
    log.append("item.updated", "user", {"item_id": "gone", "fields": {"impact": 2}})
    first = build_snapshot([item("a", impact=1)], log.read())
    rederived = build_snapshot([item("a", impact=0.5, effort=7)], log.read())
    assert first["items"][0]["effective"]["impact"] == 3
    assert rederived["items"][0]["effective"] == {"impact": 3, "confidence": 0.8, "effort_pw": 7}
    assert rederived["orphaned_overrides"] == ["gone"]


def test_write_snapshot_records_generation_time_and_event_count(tmp_path):
    log = EventLog(str(tmp_path), clock=fixed_clock())
    log.append("sources.loaded", "claude", {})
    path = write_snapshot(str(tmp_path), [item("a")], log.read(), now="2026-10-21T11:00:00Z")
    data = json.loads(open(path).read())
    assert data["generated_at"] == "2026-10-21T11:00:00Z" and data["event_count"] == 1


# --- review fix pass: replay must never remove a commitment; tolerate a torn log ---
def test_replay_ignores_drop_and_merge_away_of_committed_items_and_reports_them(tmp_path):
    log = EventLog(str(tmp_path))
    log.append("item.dropped", "user", {"item_id": "promise"})
    log.append("item.merged", "user", {"into": "a", "from": ["promise"]})
    snap = build_snapshot([item("a"), item("promise", commitment="com_001")], log.read())
    assert {i["id"] for i in snap["items"]} == {"a", "promise"}
    assert [e["type"] for e in snap["ignored_events"]] == ["item.dropped", "item.merged"]
    assert snap["dropped"] == []


@pytest.mark.parametrize("fields", [
    {"effort_pw": "5"}, {"effort_pw": None}, {"effort_pw": True}, {"effort_pw": float("inf")},
    {"effort_pw": float("nan")}, {"impact": True}, {"confidence": True}, {"impact": None},
    {"title": None}, {"title": ""}, {"title": {"a": 1}}, {"squad": 7}, {"squad": ""},
])
def test_item_update_rejects_wrong_types(tmp_path, fields):
    with pytest.raises(ValueError):
        EventLog(str(tmp_path)).append("item.updated", "user", {"item_id": "a", "fields": fields})
    assert EventLog(str(tmp_path)).read() == []


def test_read_skips_corrupt_lines_and_append_still_works_after_a_torn_write(tmp_path):
    log = EventLog(str(tmp_path), clock=lambda: "2026-10-21T10:00:00Z")
    log.append("sources.loaded", "claude", {})
    with open(log.path, "a") as f:
        f.write('{"ts": "2026-10-21T00:00:0')  # torn write, no newline
    assert [e["type"] for e in log.read()] == ["sources.loaded"] and log.corrupt_lines() == 1
    log.append("backlog.derived", "claude", {"items": 1})
    assert [e["type"] for e in log.read()] == ["sources.loaded", "backlog.derived"]


def test_read_skips_lines_missing_required_keys(tmp_path):
    log = EventLog(str(tmp_path))
    (tmp_path / "events.jsonl").write_text('{"type": "x"}\n[]\n"str"\n')
    assert log.read() == [] and log.corrupt_lines() == 3
