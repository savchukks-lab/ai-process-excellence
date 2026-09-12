import os
import sys
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
CASES = ("LAUNCH-1001", "LAUNCH-1002")
ROLES = (
    "Marketing · Launch Coordinator",
    "Sales",
    "Medical",
    "Market Access",
    "Regulatory",
    "Supply / Operations",
    "Finance",
)
SECTIONS = ("Overview", "Workstreams", "Sensitivity", "Readiness", "Decision Case")
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def launch_app(case_id: str) -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = ROLES[0]
    app.session_state[f"launch_case_section_{case_id}"] = "Overview"
    app.run()
    assert_clean(app, f"{case_id} initial render")
    return app


for case_id in CASES:
    app = launch_app(case_id)
    assumption_key = f"launch_case_assumptions_{case_id}"
    assert assumption_key in app.session_state
    persisted_inputs = deepcopy(app.session_state[assumption_key])

    for cycle in range(3):
        for role_index, role in enumerate(ROLES):
            app.session_state["launch_current_role"] = role
            section = SECTIONS[(cycle + role_index) % len(SECTIONS)]
            app.session_state[f"launch_case_section_{case_id}"] = section
            app.run()
            assert_clean(app, f"{case_id} cycle {cycle + 1} {role} {section}")

    for role, sequence in (
        ("Sales", ("Workstreams", "Sensitivity", "Overview")),
        ("Finance", ("Readiness", "Decision Case")),
    ):
        app.session_state["launch_current_role"] = role
        for section in sequence:
            app.session_state[f"launch_case_section_{case_id}"] = section
            app.run()
            assert_clean(app, f"{case_id} {role} {section}")

    assert app.session_state[assumption_key] == persisted_inputs

print("launch top-level role and navigation stability smoke test complete")
