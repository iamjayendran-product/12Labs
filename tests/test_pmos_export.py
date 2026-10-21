import json
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pmos.api import create_router
from pmos.export import main, render_markdown
from pmos.pipeline import Pipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def plan(tmp_path):
    return Pipeline(ROOT, "12labs", str(tmp_path)).plan()


def section(md, heading):
    start = md.index(heading)
    nxt = md.find("\n## ", start + 1)
    return md[start: nxt if nxt != -1 else len(md)]


def test_has_a_heading_with_theme_for_each_month(plan):
    md = render_markdown(plan)
    for m in plan["months"]:
        assert f"## {m['label']} — {m['theme']}" in md


def test_every_commitment_is_listed_under_committed_in_its_start_month(plan):
    md = render_markdown(plan)
    for m in plan["months"]:
        body = section(md, f"## {m['label']}")
        for card in m["items"]:
            if card["committed"] and card["phase"] == "starts":
                committed_part = body.split("### Prioritised by RICE")[0]
                assert card["title"] in committed_part and card["due_date"] in committed_part


def test_committed_block_comes_before_rice_ranked_block(plan):
    body = section(render_markdown(plan), "## January 2027")
    assert body.index("### Committed") < body.index("### Prioritised by RICE")


def test_cards_carry_rice_effort_and_a_verbatim_quote(plan):
    md = render_markdown(plan)
    card = plan["months"][0]["items"][0]
    assert f"RICE {card['rice']['score']:.2f}" in md
    assert f"> “{card['quotes'][0]['quote']}”" in md


def test_continuing_items_are_one_liners_not_repeated_cards(plan):
    md = render_markdown(plan)
    feb = section(md, "## February 2027")
    assert "continues from 2027-01" in feb
    assert feb.count("**VPC / private-cloud deployment**") == 1  # the continuation line only
    assert md.count("> “Legal wants a VPC deployment with a BAA.”") <= 1


def test_below_the_line_and_commitment_register_are_present(plan):
    md = render_markdown(plan)
    assert "## Below the line" in md and "Hindi voices" in section(md, "## Below the line")
    register = section(md, "## Commitment register")
    assert register.count("com_00") == 6 and "$480k" in register
    assert "None" not in md


def test_http_download_has_no_side_effects_and_export_writes_file_and_logs(tmp_path):
    out = tmp_path / "ROADMAP.md"
    app = FastAPI()
    app.include_router(create_router(ROOT, "12labs", str(tmp_path / "state"), export_path=str(out)))
    c = TestClient(app)
    r = c.get("/api/pmos/roadmap.md")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/markdown")
    assert "attachment" in r.headers["content-disposition"]
    assert not out.exists() and c.get("/api/pmos/events").json()["events"] == []
    assert c.post("/api/pmos/roadmap/export").status_code == 200
    assert out.read_text().startswith("# 12Labs")
    assert c.get("/api/pmos/events").json()["events"][-1]["type"] == "roadmap.exported"


def test_cli_writes_the_file_and_logs_as_claude(tmp_path):
    out = tmp_path / "R.md"
    assert main(["--company", "12labs", "--root", ROOT, "--out", str(out), "--state-dir", str(tmp_path / "s")]) == 0
    assert "## March 2027" in out.read_text()
    last = [json.loads(l) for l in open(tmp_path / "s" / "events.jsonl")][-1]
    assert last["type"] == "roadmap.exported" and last["actor"] == "claude"
