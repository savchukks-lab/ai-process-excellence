import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=30)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Medical"
    app.run()
    assert_clean(app, f"{case_id} Medical")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    names = {str(row.get("Assumption Name", "")) for row in records}
    required = {
        "Prevalence",
        "Diagnosis Rate",
        "Treatment Rate / Treatment Eligibility",
        "Disease / Indication",
        "Target Segment / Severity",
        "Line of Therapy",
        "Dose per Administration",
        "Administration Frequency",
        "Treatment Duration",
        "Compliance",
        "Persistence",
        "Theoretical Units per Patient",
        "Adjusted Units per Patient",
        "Clinical Evidence",
        "Key Clinical Evidence Gap / Risk",
    }
    assert required.issubset(names), f"{case_id}: missing Medical assumptions {required - names}"
    assert not {"Treatment Pathway", "Severity / Segment", "Clinical Evidence / Rationale"}.intersection(names)
    assert len([button for button in app.button if button.label == "Share for Alignment"]) == 3

    compliance = next(widget for widget in app.number_input if widget.label == "Compliance (%)")
    compliance.set_value(81.0).run()
    assert_clean(app, f"{case_id} Medical compliance edit")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    saved_compliance = next(row for row in records if row.get("Assumption Name") == "Compliance")
    assert abs(float(saved_compliance["Value"]) - 0.81) < 1e-9

    persistence = next(widget for widget in app.checkbox if widget.label == "Use Persistence Adjustment")
    persistence.set_value(False).run()
    assert_clean(app, f"{case_id} Medical persistence toggle")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    saved_persistence = next(row for row in records if row.get("Assumption Name") == "Persistence")
    assert saved_persistence["Enabled"] is False

    add_evidence = next(button for button in app.button if button.label == "+ Add Evidence")
    add_evidence.click().run()
    assert_clean(app, f"{case_id} Medical add evidence")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    evidence = next(row for row in records if row.get("Assumption Name") == "Clinical Evidence")
    assert isinstance(evidence["Value"], list) and len(evidence["Value"]) == 2

    for role in ("Marketing · Launch Coordinator", "Sales", "Medical"):
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role}")

print("launch medical smoke test complete")
