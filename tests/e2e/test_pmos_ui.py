import json
import re

from playwright.sync_api import Page, expect


def month_of_card(page: Page, item_id: str) -> str:
    """The first month column that lists this item."""
    for m in ("2027-01", "2027-02", "2027-03"):
        if page.locator(f'[data-testid="month-{m}"] [data-testid="card-{item_id}"]').count():
            return m
    return ""


def test_every_commitment_appears_in_or_before_its_due_month(page: Page, commitment_items):
    page.goto("/pmos/roadmap.html")
    expect(page.get_by_test_id("month-2027-03")).to_be_visible()
    expect(page.locator('[data-testid^="card-"]').first).to_be_visible()
    assert len(commitment_items) == 6
    for item_id, due in commitment_items:
        month = month_of_card(page, item_id)
        assert month and month <= due[:7], f"{item_id} placed in {month!r}, due {due}"
        card = page.locator(f'[data-testid="card-{item_id}"]').first
        expect(card.get_by_test_id("badge-committed")).to_contain_text(due)
    expect(page.get_by_test_id("at-risk")).to_have_count(0)


def test_editing_effort_rescores_replaces_the_item_and_logs_an_event(page: Page):
    page.goto("/pmos/roadmap.html")
    expect(page.locator('[data-testid="month-2027-02"] [data-testid="card-pronunciation-dictionary"]')).to_be_visible()

    page.goto("/pmos/backlog.html")
    score = page.get_by_test_id("score-pronunciation-dictionary")
    expect(score).to_have_text("2.40")
    effort = page.get_by_test_id("effort-input-pronunciation-dictionary")
    effort.fill("16")
    effort.press("Tab")
    expect(score).to_have_text("0.90")
    expect(page.get_by_test_id("row-pronunciation-dictionary")).to_have_class(re.compile("overridden"))

    page.goto("/pmos/roadmap.html")
    expect(page.get_by_test_id("below-pronunciation-dictionary")).to_be_visible()
    assert month_of_card(page, "pronunciation-dictionary") == ""

    page.goto("/pmos/sources.html")
    first = page.get_by_test_id("event").first
    expect(first).to_contain_text("item.updated")
    expect(first).to_contain_text("by user")
    expect(first).to_contain_text("UTC")


def test_merging_two_items_unions_their_evidence(page: Page):
    page.goto("/pmos/backlog.html")
    hindi = page.get_by_test_id("row-hindi-voices")
    expect(hindi).to_contain_text("9 quotes")
    page.get_by_test_id("select-hindi-voices").check()
    expect(page.get_by_test_id("merge-btn")).to_be_disabled()
    page.get_by_test_id("select-swahili-voices").check()
    expect(page.get_by_test_id("merge-btn")).to_be_enabled()
    page.locator("#merge-target").select_option("hindi-voices")
    page.get_by_test_id("merge-btn").click()
    expect(page.get_by_test_id("row-swahili-voices")).to_have_count(0)
    expect(page.get_by_test_id("row-hindi-voices")).to_contain_text("11 quotes")


def test_committed_items_cannot_be_dropped(page: Page):
    page.goto("/pmos/backlog.html")
    expect(page.get_by_test_id("row-sso-soc2")).to_be_visible()
    expect(page.get_by_test_id("drop-sso-soc2")).to_be_disabled()
    page.get_by_test_id("drop-salesforce-connector").click()
    expect(page.get_by_test_id("row-salesforce-connector")).to_have_count(0)


def test_export_downloads_markdown_with_all_three_months(page: Page, server):
    page.goto("/pmos/roadmap.html")
    expect(page.locator('[data-testid^="card-"]').first).to_be_visible()
    with page.expect_download() as dl:
        page.get_by_test_id("export-md").click()
    path = dl.value.path()
    text = open(path).read()
    assert dl.value.suggested_filename == "ROADMAP.md"
    for heading in ("## January 2027", "## February 2027", "## March 2027", "## Below the line"):
        assert heading in text
    page.wait_for_timeout(500)  # the click also logs roadmap.exported
    events = json.loads(page.request.get("/api/pmos/events").text())["events"]
    assert events and events[-1]["type"] == "roadmap.exported"
    assert server["export"].exists()


def test_sources_page_lists_all_source_types_and_filters(page: Page):
    page.goto("/pmos/sources.html")
    for source, n in (("voc", "51"), ("crm", "32"), ("fireflies", "10"), ("support", "42"), ("commitment", "6")):
        expect(page.get_by_test_id(f"count-{source}")).to_contain_text(n)
    page.locator("#source").select_option("fireflies")
    expect(page.locator('[data-testid^="record-ff_"]')).to_have_count(10)
    page.locator("#source").select_option("")
    page.locator("#q").fill("Gulf dialect")
    expect(page.locator('[data-testid^="record-"]').first).to_contain_text("Gulf dialect", ignore_case=True)
