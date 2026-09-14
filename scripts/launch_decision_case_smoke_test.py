import os
import sys
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

CORE_SECTIONS = [
    "Executive Summary",
    "Patient & Market Opportunity",
    "Key Launch Elements",
    "Financial Case",
    "Sensitivity Analysis",
    "Launch Readiness & Key Risks",
    "Key Takeaways / Decision Required",
]

APPENDICES = [
    "Marketing Appendix",
    "Sales Appendix",
    "Medical Appendix",
    "Market Access Appendix",
    "Regulatory Appendix",
    "Supply / Operations Appendix",
    "Finance Appendix",
]


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def button_by_key(app: AppTest, key: str):
    return next(button for button in app.button if button.key == key)


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = ROLES[0]
    app.session_state[f"launch_case_section_{case_id}"] = "Decision Case"
    app.run()
    assert_clean(app, f"{case_id} Decision Case")

    page_text = "\n".join(str(item.value) for item in app.markdown)
    for heading in [*CORE_SECTIONS, "Functional Appendix", *APPENDICES]:
        assert heading in page_text, f"{case_id}: missing {heading}"
    assert page_text.index("Functional Appendix") > page_text.index("Key Takeaways / Decision Required")
    assert "Decision Required" in page_text
    assert "Generate / Refresh Decision Case" in [button.label for button in app.button]
    assert not list(app.number_input), f"{case_id}: Decision Case exposed numerical inputs"
    assert not list(app.date_input), f"{case_id}: Decision Case exposed date inputs"
    assert not list(app.text_input), f"{case_id}: Decision Case exposed text inputs"

    refresh_key = f"launch_decision_case_last_refreshed_{case_id}"
    button_by_key(app, f"launch_decision_case_refresh_{case_id}").click().run()
    assert_clean(app, f"{case_id} refresh")
    assert app.session_state[refresh_key]

    for role in ROLES[1:]:
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role} Decision Case")
        role_text = "\n".join(str(item.value) for item in app.markdown)
        for heading in CORE_SECTIONS:
            assert heading in role_text, f"{case_id} {role}: missing {heading}"
        assert app.session_state[refresh_key]

print("launch decision case smoke test complete")
