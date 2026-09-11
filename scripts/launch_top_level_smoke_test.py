import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
CASE_ID = "LAUNCH-1001"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


app = AppTest.from_file(str(APP_PATH), default_timeout=90)
app.session_state["current_module"] = "launch"
app.session_state["launch_page"] = "Launch Case"
app.session_state["selected_launch_case_id"] = CASE_ID
app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
app.run()
assert_clean(app, "coordinator top-level render")

tab_labels = [tab.label for tab in app.tabs]
for label in ["Overview", "Workstreams", "Sensitivity", "Readiness", "Decision Case"]:
    assert label in tab_labels, f"Missing top-level tab: {label}"
assert "Assumptions" not in tab_labels
assert f"launch_case_assumptions_{CASE_ID}" in app.session_state
assert len(app.session_state[f"launch_case_assumptions_{CASE_ID}"]) > 0

markdown_text = "\n".join(str(item.value) for item in app.markdown)
for heading in [
    "Management Snapshot",
    "Integrated Launch Journey",
    "Cross-functional Status",
    "Key Milestones",
    "Sensitivity Drivers",
    "Scenario Results",
    "Launch Readiness",
    "Decision Case",
]:
    assert heading in markdown_text, f"Missing section: {heading}"

market_share_key = f"launch_sensitivity_downside_{CASE_ID}_market_share"
cogs_key = f"launch_sensitivity_downside_{CASE_ID}_cogs"
assert not widget_by_key(app.number_input, market_share_key).disabled
assert not widget_by_key(app.number_input, cogs_key).disabled
widget_by_key(app.number_input, market_share_key).set_value(-8.0).run()
assert_clean(app, "sensitivity autosave")
assert app.session_state[f"launch_sensitivity_{CASE_ID}"]["Market Share"]["Downside"] == -8.0

app.session_state["launch_current_role"] = "Finance"
app.run()
assert_clean(app, "finance sensitivity ownership")
assert widget_by_key(app.number_input, market_share_key).disabled
assert not widget_by_key(app.number_input, cogs_key).disabled

print("launch top-level smoke test complete")
