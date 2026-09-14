import os
import sys
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))

ROLES = [
    "Marketing · Launch Coordinator",
    "Sales",
    "Medical",
    "Market Access",
    "Regulatory",
    "Supply / Operations",
    "Finance",
]


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    for role in ROLES:
        app = AppTest.from_file(str(APP_PATH), default_timeout=90)
        app.session_state["current_module"] = "launch"
        app.session_state["launch_page"] = "Launch Case"
        app.session_state["selected_launch_case_id"] = case_id
        app.session_state["launch_current_role"] = role
        app.session_state[f"launch_case_section_{case_id}"] = "Readiness"
        app.run()
        assert_clean(app, f"{case_id} {role} Readiness")

        labels = {metric.label for metric in app.metric}
        required = {"Overall Status", "Data Readiness %", "Process Readiness %", "Days Remaining"}
        assert required.issubset(labels), f"{case_id} {role}: missing KPIs {required - labels}"
        content = "\n".join(str(item.value) for item in app.markdown)
        for heading in (
            "Functional Readiness",
            "Workstream Input Status",
            "Alignment Status",
            "Sensitivity Completion",
            "Top Open Actions",
            "Timeline Readiness",
        ):
            assert heading in content, f"{case_id} {role}: missing {heading}"

        sensitivity = app.session_state[f"launch_sensitivity_{case_id}"]
        completed = set(sensitivity.get("Completed Drivers", []))
        if case_id == "LAUNCH-1001":
            assert "Sales Coverage" not in completed
            assert "Regulatory Timing" not in completed
            assert "Market Share" in completed
        else:
            assert len(completed) == 8

    coordinator = AppTest.from_file(str(APP_PATH), default_timeout=90)
    coordinator.session_state["current_module"] = "launch"
    coordinator.session_state["launch_page"] = "Launch Case"
    coordinator.session_state["selected_launch_case_id"] = case_id
    coordinator.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
    coordinator.session_state[f"launch_case_section_{case_id}"] = "Workstreams"
    coordinator.session_state[f"launch_workstream_section_{case_id}"] = "Marketing"
    coordinator.run()
    assert_clean(coordinator, f"{case_id} coordinator deadline")
    deadline_key = f"launch_case_decision_deck_deadline_{case_id}"
    deadline_widget = by_key(coordinator.date_input, f"launch_decision_deck_deadline_widget_{case_id}")
    assert not deadline_widget.disabled
    deadline_widget.set_value(date(2026, 12, 31)).run()
    assert_clean(coordinator, f"{case_id} coordinator deadline edit")
    assert coordinator.session_state[deadline_key] == date(2026, 12, 31)
    coordinator.session_state["launch_current_role"] = "Finance"
    coordinator.session_state[f"launch_case_section_{case_id}"] = "Readiness"
    coordinator.run()
    assert_clean(coordinator, f"{case_id} deadline after role and tab switch")
    switched_text = "\n".join(str(item.value) for item in coordinator.markdown)
    assert "31 Dec 2026" in switched_text

    viewer = AppTest.from_file(str(APP_PATH), default_timeout=90)
    viewer.session_state["current_module"] = "launch"
    viewer.session_state["launch_page"] = "Launch Case"
    viewer.session_state["selected_launch_case_id"] = case_id
    viewer.session_state["launch_current_role"] = "Finance"
    viewer.session_state[f"launch_case_section_{case_id}"] = "Readiness"
    viewer.run()
    assert_clean(viewer, f"{case_id} Finance deadline view")
    deadline_text = "\n".join(str(item.value) for item in viewer.markdown)
    assert "Decision / Deck Deadline" in deadline_text

print("launch readiness smoke test complete")
