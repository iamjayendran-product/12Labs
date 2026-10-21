from pmos.scheduler import schedule
from pmos.schema import CompanyConfig, Commitment

MONTHS = ["2027-01", "2027-02", "2027-03"]


def cfg(cap=16, squads=("s1", "s2")):
    return CompanyConfig(
        name="T", product="p",
        quarter={"label": "Q1 2027", "months": MONTHS},
        squads=[{"id": s, "name": s.upper(), "engineers": 4, "capacity_pw_per_month": cap} for s in squads],
        reach={"arr_weight_min": 1, "arr_weight_max": 3},
    )


def it(id_, effort, score, squad="s1", depends=None, commitment=None, theme="Theme A"):
    return {
        "id": id_, "title": id_.upper(), "squad": squad, "theme": theme,
        "depends_on": depends or [], "commitment_id": commitment,
        "effective": {"impact": 1, "confidence": 1.0, "effort_pw": effort},
        "rice": {"score": score, "reach": {"score": 1}},
    }


def com(id_, due, arr=1000):
    return Commitment(id=id_, account="A", commitment="c", due_date=due, arr_at_risk_usd=arr,
                      contract_ref="x", linked_theme="t")


def placed(plan):
    return {i["id"]: i for m in plan["months"] for i in m["items"]}


def test_commitment_takes_capacity_before_a_higher_scoring_item():
    items = [it("hot", 12, 9.0), it("promise", 12, 0.1, commitment="c1")]
    plan = schedule(items, [com("c1", "2027-01-31")], cfg(squads=("s1",)))
    p = placed(plan)
    assert p["promise"]["start_month"] == "2027-01" and p["promise"]["committed"] is True
    assert p["hot"]["start_month"] == "2027-02"


def test_capacity_is_never_exceeded_in_any_squad_month():
    items = [it(f"i{n}", 5 + n % 4, 10 - n, squad="s1" if n % 2 else "s2") for n in range(14)]
    plan = schedule(items, [], cfg())
    for m in plan["months"]:
        for squad, cap in m["capacity"].items():
            assert cap["used"] <= cap["total"], (m["month"], squad)


def test_commitments_are_scheduled_earliest_deadline_first_and_meet_due_month():
    items = [it("late", 10, 1, commitment="c2"), it("early", 10, 1, commitment="c1")]
    plan = schedule(items, [com("c2", "2027-03-31"), com("c1", "2027-01-31")], cfg(squads=("s1",)))
    p = placed(plan)
    assert p["early"]["start_month"] == "2027-01"
    assert p["late"]["end_month"] <= "2027-03" and plan["at_risk"] == []


def test_commitment_that_cannot_meet_its_due_month_is_flagged_at_risk_but_still_placed():
    items = [it("a", 16, 1, commitment="c1"), it("b", 16, 1, commitment="c2")]
    plan = schedule(items, [com("c1", "2027-01-31"), com("c2", "2027-01-31")], cfg(squads=("s1",)))
    assert [r["id"] for r in plan["at_risk"]] == ["b"]
    assert "after due" in plan["at_risk"][0]["reason"]
    assert "b" in placed(plan)


def test_commitment_with_no_room_in_the_quarter_is_at_risk_and_unplaced():
    items = [it("huge", 60, 1, commitment="c1")]
    plan = schedule(items, [com("c1", "2027-03-31")], cfg(squads=("s1",)))
    assert [r["id"] for r in plan["at_risk"]] == ["huge"]
    assert "huge" not in placed(plan)


def test_dependent_item_starts_in_a_month_after_its_dependency_finishes():
    items = [it("base", 6, 1), it("on-top", 6, 9, depends=["base"])]
    p = placed(schedule(items, [], cfg(squads=("s1",))))
    assert p["on-top"]["start_month"] > p["base"]["end_month"]


def test_commitment_pulls_forward_an_unscheduled_dependency():
    items = [it("needs", 8, 9, commitment="c1", depends=["prereq"]), it("prereq", 4, 0.01)]
    p = placed(schedule(items, [com("c1", "2027-03-31")], cfg(squads=("s1",))))
    assert p["prereq"]["end_month"] < p["needs"]["start_month"]
    assert p["prereq"]["pulled_by"] == "needs"


def test_oversized_item_spans_consecutive_months_and_is_flagged():
    plan = schedule([it("vpc", 20, 5)], [], cfg(squads=("s1",)))
    vpc = placed(plan)["vpc"]
    assert vpc["oversized"] is True and sum(vpc["allocation"].values()) == 20
    assert (vpc["start_month"], vpc["end_month"]) == ("2027-01", "2027-02")
    assert plan["oversized"] == ["vpc"]


def test_regular_item_is_never_split_across_months():
    items = [it("a", 10, 9), it("b", 10, 8)]
    p = placed(schedule(items, [], cfg(squads=("s1",))))
    assert p["a"]["start_month"] == p["a"]["end_month"] == "2027-01"
    assert p["b"]["start_month"] == p["b"]["end_month"] == "2027-02"


def test_items_that_do_not_fit_go_below_the_line_and_smaller_ones_still_fill_gaps():
    items = [it("a", 16, 9), it("b", 16, 8), it("c", 16, 7), it("big", 16, 6), it("tiny", 1, 0.5)]
    plan = schedule(items, [], cfg(squads=("s1",)))
    assert [r["id"] for r in plan["below_the_line"]] == ["big", "tiny"]  # months full


def test_smaller_item_fills_a_gap_left_by_one_that_did_not_fit():
    items = [it("a", 12, 9), it("b", 12, 8), it("c", 12, 7), it("d", 12, 6), it("tiny", 4, 0.5)]
    plan = schedule(items, [], cfg(squads=("s1",)))
    assert [r["id"] for r in plan["below_the_line"]] == ["d"]
    assert "tiny" in placed(plan)


def test_month_theme_is_effort_weighted_and_an_override_wins():
    items = [it("a", 4, 1, theme="Voice"), it("b", 10, 1, theme="Enterprise")]
    plan = schedule(items, [], cfg(squads=("s1",)))
    assert plan["months"][0]["theme"] == "Enterprise"
    plan = schedule(items, [], cfg(squads=("s1",)), month_themes={"2027-01": "Custom"})
    assert plan["months"][0]["theme"] == "Custom"


def test_scheduling_is_deterministic():
    items = [it(f"i{n}", 3 + n % 5, 5.0) for n in range(12)]
    assert schedule(items, [], cfg()) == schedule(list(reversed(items)), [], cfg())


def test_continuing_oversized_item_is_listed_in_each_active_month_with_its_phase():
    plan = schedule([it("vpc", 20, 5)], [], cfg(squads=("s1",)))
    jan, feb, mar = plan["months"]
    assert [(i["id"], i["phase"], i["month_pw"]) for i in jan["items"]] == [("vpc", "starts", 16)]
    assert [(i["id"], i["phase"], i["month_pw"]) for i in feb["items"]] == [("vpc", "continues", 4)]
    assert mar["items"] == []


def test_uncommitted_oversized_item_does_not_start_in_a_sliver_of_capacity():
    items = [it("filler", 14, 9), it("long", 20, 5)]  # Jan has only 2pw left after filler
    long_ = placed(schedule(items, [], cfg(squads=("s1",))))["long"]
    assert long_["start_month"] == "2027-02"


def test_committed_oversized_item_still_starts_as_early_as_possible():
    items = [it("filler", 14, 1, commitment="c0"), it("long", 20, 5, commitment="c1")]
    plan = schedule(items, [com("c0", "2027-01-31"), com("c1", "2027-03-31")], cfg(squads=("s1",)))
    assert placed(plan)["long"]["start_month"] == "2027-01"


def test_commitment_without_any_backlog_item_is_reported_at_risk():
    plan = schedule([it("a", 4, 1)], [com("c9", "2027-02-28")], cfg(squads=("s1",)))
    assert [(r["id"], r["reason"]) for r in plan["at_risk"]] == [("c9", "no backlog item for this commitment")]


def test_item_with_unknown_squad_goes_below_the_line_instead_of_crashing():
    plan = schedule([it("a", 4, 1, squad="nope"), it("b", 4, 0.5)], [], cfg(squads=("s1",)))
    assert [(r["id"], r["reason"]) for r in plan["below_the_line"]] == [("a", "unknown squad 'nope'")]
    assert "b" in placed(plan)
