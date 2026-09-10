import os
import sys
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


required = {
    "Regulatory Dossier Submission Date",
    "Expected Regulatory Approval Date",
    "Approval Timing Rationale / Key Drivers",
    "Regulatory Timing Benchmark",
    "Expected Label / Indication",
    "Risk Level",
    "Risk / Issue",
    "Potential Impact",
    "Response / Management Consideration",
}
removed = {"Key Regulatory Dependency", "Regulatory Confidence", "Regulatory Mitigation", "Material Regulatory Risk"}
incoming_allowed = {
    "Disease / Indication",
    "Line of Therapy",
    "Biomarker / Prior Treatment / Clinical Restriction",
    "Key Clinical Evidence Gap / Risk",
}


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=45)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Regulatory"
    app.run()
    assert_clean(app, f"{case_id} Regulatory")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    names = {str(row.get("Assumption Name", "")) for row in records}
    assert required.issubset(names), f"{case_id}: missing Regulatory assumptions {required - names}"
    assert not removed.intersection(names), f"{case_id}: legacy Regulatory assumptions remain {removed.intersection(names)}"
    benchmark = next(row for row in records if row.get("Assumption Name") == "Regulatory Timing Benchmark")
    assert benchmark["Assumption Type"] == "MASTER DATA"
    assert benchmark["Owner"] == "Central Reference Data"

    incoming = [
        row
        for row in records
        if row.get("Owner") != "Regulatory"
        and "Regulatory" in [part.strip() for part in str(row.get("Validators", "")).split(",")]
        and row.get("Assumption Name") in incoming_allowed
    ]
    assert len(incoming) <= 4

    share_buttons = [button for button in app.button if button.label == "Share Regulatory Input for Alignment"]
    assert len(share_buttons) == 1

    new_approval_date = date(2027, 5, 15) if case_id == "LAUNCH-1001" else date(2027, 1, 15)
    widget_by_key(app.date_input, f"launch_regulatory_approval_{case_id}").set_value(new_approval_date).run()
    assert_clean(app, f"{case_id} approval date edit")
    widget_by_key(app.text_area, f"launch_regulatory_label_{case_id}").set_value(
        "Expected approved indication with a defined eligible population."
    ).run()
    assert_clean(app, f"{case_id} expected label edit")
    widget_by_key(app.selectbox, f"launch_regulatory_risk_level_{case_id}").set_value("High").run()
    assert_clean(app, f"{case_id} risk edit")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    by_name = {row.get("Assumption Name"): row for row in records}
    assert by_name["Expected Regulatory Approval Date"]["Value"] == new_approval_date.isoformat()
    assert by_name["Expected Label / Indication"]["Value"] == "Expected approved indication with a defined eligible population."
    assert by_name["Risk Level"]["Value"] == "High"

    next(button for button in app.button if button.label == "Share Regulatory Input for Alignment").click().run()
    assert_clean(app, f"{case_id} Regulatory package share")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    owned = [
        row
        for row in records
        if row.get("Owner") == "Regulatory" and str(row.get("Validators", "")).strip()
    ]
    assert owned and all(row.get("Validation Status") == "Shared for Alignment" for row in owned)

    for role in ("Marketing · Launch Coordinator", "Medical", "Market Access", "Regulatory"):
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role}")

print("launch regulatory smoke test complete")
