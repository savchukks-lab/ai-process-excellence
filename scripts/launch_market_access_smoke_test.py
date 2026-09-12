import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))

from streamlit_app import (  # noqa: E402
    LAUNCH_YEARS,
    default_market_access_plan,
    market_access_plan_entries,
    market_access_year_metrics,
)


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


product = {"List Price": 100.0, "Gross Price": 95.0}
plan = default_market_access_plan("LAUNCH-1001", product)
entries = market_access_plan_entries(plan)
assert {row["Access Path"] for row in entries} == {
    "Federal",
    "Regional",
    "Private Insurance",
    "Out of Pocket",
}
assert all(row["Net Price"]["Y1"] == plan["Government Reimbursement"]["Net Price"]["Y1"] for row in entries[:2])

overlap_plan = default_market_access_plan("LAUNCH-1001", product)
overlap_plan["Government Reimbursement"]["Subchannels"]["Federal"]["Reach"] = {
    year: 0.8 for year in LAUNCH_YEARS
}
overlap_plan["Private Insurance"]["Reach"] = {year: 0.6 for year in LAUNCH_YEARS}
overlap_plan["Out of Pocket"]["Reach"] = {year: 0.2 for year in LAUNCH_YEARS}
metrics = market_access_year_metrics(overlap_plan, 2027)
assert metrics["Y2"]["Raw Total Reach"] > 1.0
assert abs(metrics["Y2"]["Total Reach"] - 1.0) < 1e-9

bridge_plan = default_market_access_plan("LAUNCH-1002", product)
private = bridge_plan["Private Insurance"]
private["Show Price Bridge"] = True
private["List Price"] = {year: 100.0 for year in LAUNCH_YEARS}
private["Rebate / Discount"] = {year: 0.15 for year in LAUNCH_YEARS}
private["Other GTN"] = {year: 0.05 for year in LAUNCH_YEARS}
bridge_metrics = market_access_year_metrics(bridge_plan, 2027)
private_row = next(row for row in bridge_metrics["Y2"]["Rows"] if row["Channel"] == "Private Insurance")
assert abs(float(private_row["Net Price"]) - 80.0) < 1e-9


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=45)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Market Access"
    app.session_state[f"launch_case_section_{case_id}"] = "Workstreams"
    app.run()
    assert_clean(app, f"{case_id} Market Access")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    names = {str(row.get("Assumption Name", "")) for row in records}
    assert {
        "Access Archetype",
        "Access Strategy & Pathway",
        "Access Eligibility / Restrictions",
        "Market Access Channel Plan",
        "Total Market Access Rate",
        "Accessible Patients",
    }.issubset(names)
    assert not {
        "Market Access Rate",
        "Access Ramp",
        "Coverage / Reimbursement",
        "Geographic / Account Coverage",
        "Patient Co-pay / OOP",
        "Target / Launch Price",
        "Rebate / Discount",
        "Other GTN",
    }.intersection(names)
    share_buttons = [button for button in app.button if button.label == "Share Market Access Input for Alignment"]
    assert len(share_buttons) == 1

    channel = "private" if case_id == "LAUNCH-1001" else "oop"
    reach_key = f"launch_access_reach_{case_id}_{channel}_Y2"
    net_key = f"launch_access_net_{case_id}_{channel}_Y2"
    widget_by_key(app.number_input, reach_key).set_value(17.0).run()
    assert_clean(app, f"{case_id} reach edit")
    widget_by_key(app.number_input, net_key).set_value(77.0).run()
    assert_clean(app, f"{case_id} net price edit")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    saved_plan = next(row for row in records if row.get("Assumption Name") == "Market Access Channel Plan")["Value"]
    channel_name = "Private Insurance" if channel == "private" else "Out of Pocket"
    assert abs(float(saved_plan[channel_name]["Reach"]["Y2"]) - 0.17) < 1e-9
    assert abs(float(saved_plan[channel_name]["Net Price"]["Y2"]) - 77.0) < 1e-9

    next(button for button in app.button if button.label == "Share Market Access Input for Alignment").click().run()
    assert_clean(app, f"{case_id} Market Access package share")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    owned = [
        row
        for row in records
        if row.get("Workstream") == "Market Access" and str(row.get("Validators", "")).strip()
    ]
    assert owned and all(row.get("Validation Status") == "Shared for Alignment" for row in owned)

    for role in (
        "Marketing · Launch Coordinator",
        "Medical",
        "Market Access",
        "Finance",
        "Regulatory",
    ):
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role}")

print("launch market access smoke test complete")
