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
    "General Manager",
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
    for heading in [*CORE_SECTIONS, *APPENDICES]:
        assert heading in page_text, f"{case_id}: missing {heading}"
    assert "Functional Appendix (7 workstreams)" in [item.label for item in app.expander]
    assert "Decision Required" in page_text
    assert "Generate / Refresh Decision Case" not in [button.label for button in app.button]
    assert "Live view" in "\n".join(str(item.value) for item in app.caption)
    assert not list(app.number_input), f"{case_id}: Decision Case exposed numerical inputs"
    assert not list(app.date_input), f"{case_id}: Decision Case exposed date inputs"
    assert not list(app.text_input), f"{case_id}: Decision Case exposed text inputs"

    for role in ROLES[1:-1]:
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role} Decision Case")
        role_text = "\n".join(str(item.value) for item in app.markdown)
        for heading in CORE_SECTIONS:
            assert heading in role_text, f"{case_id} {role}: missing {heading}"

    app.session_state["launch_current_role"] = ROLES[0]
    app.run()
    button_by_key(app, f"launch_send_for_approval_{case_id}").click().run()
    assert_clean(app, f"{case_id} submit")
    assert app.session_state["launch_approval_records"][case_id]["Status"] == "Pending Approval"

    role_selector = next(item for item in app.selectbox if item.key == "launch_current_role")
    role_selector.set_value("General Manager").run()
    assert_clean(app, f"{case_id} GM inbox")
    assert app.session_state["launch_page"] == "Launch Sandbox Home"
    assert app.session_state["selected_launch_case_id"] is None
    next(item for item in app.checkbox if item.key == f"launch_case_selected_{case_id}").set_value(True).run()
    button_by_key(app, "launch_gm_view_details").click().run()
    assert app.session_state["launch_page"] == "Launch Case"
    app.run()
    assert_clean(app, f"{case_id} GM review")
    gm_text = "\n".join(str(item.value) for item in app.markdown)
    for heading in CORE_SECTIONS:
        assert heading in gm_text, f"{case_id} GM: missing {heading}"
    assert button_by_key(app, f"launch_gm_capture_decision_{case_id}")

    decision = next(item for item in app.radio if item.key == f"launch_gm_decision_{case_id}")
    if case_id == "LAUNCH-1001":
        decision.set_value("Return for Changes")
        comment = next(item for item in app.text_area if item.key == f"launch_gm_decision_comment_{case_id}")
        comment.set_value("Please resolve the open launch readiness actions.")
        button_by_key(app, f"launch_gm_capture_decision_{case_id}").click().run()
        assert app.session_state["launch_approval_records"][case_id]["Status"] == "Returned for Changes"
        app.session_state["launch_current_role"] = ROLES[0]
        app.run()
        button_by_key(app, f"launch_send_for_approval_{case_id}").click().run()
        assert app.session_state["launch_approval_records"][case_id]["Submitted Version"] == 2
        app.session_state["launch_current_role"] = "General Manager"
        app.run()
        next(item for item in app.radio if item.key == f"launch_gm_decision_{case_id}").set_value("Approve")
        button_by_key(app, f"launch_gm_capture_decision_{case_id}").click().run()
        assert app.session_state["launch_approval_records"][case_id]["Status"] == "Approved"
    else:
        decision.set_value("Reject")
        comment = next(item for item in app.text_area if item.key == f"launch_gm_decision_comment_{case_id}")
        comment.set_value("The current launch case does not meet the decision threshold.")
        button_by_key(app, f"launch_gm_capture_decision_{case_id}").click().run()
        assert app.session_state["launch_approval_records"][case_id]["Status"] == "Rejected"

    launch_events = [
        event for event in app.session_state["audit_events"]
        if event.get("Deal ID") == case_id and event.get("Entity") == "Launch Approval"
    ]
    assert launch_events, f"{case_id}: launch approval audit events missing"

print("launch decision case smoke test complete")
