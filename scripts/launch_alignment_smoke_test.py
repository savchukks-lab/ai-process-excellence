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


def record(app: AppTest, assumption_name: str) -> dict:
    records = app.session_state[f"launch_case_assumptions_{CASE_ID}"]
    return next(row for row in records if row.get("Assumption Name") == assumption_name)


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


app = AppTest.from_file(str(APP_PATH), default_timeout=60)
app.session_state["current_module"] = "launch"
app.session_state["launch_page"] = "Launch Case"
app.session_state["selected_launch_case_id"] = CASE_ID
app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
app.run()
assert_clean(app, "coordinator all-workspace render")

package_labels = {
    "Share Marketing Input for Alignment",
    "Share Sales Input for Alignment",
    "Share Medical Input for Alignment",
    "Share Market Access Input for Alignment",
    "Share Regulatory Input for Alignment",
    "Share Supply Input for Alignment",
    "Share Finance Input for Alignment",
}
rendered_labels = [button.label for button in app.button]
for label in package_labels:
    assert rendered_labels.count(label) == 1, f"Expected one package action: {label}"
assert "Share for Alignment" not in rendered_labels
assert "Save & Share for Alignment" not in rendered_labels

for role in (
    "Marketing · Launch Coordinator",
    "Sales",
    "Medical",
    "Market Access",
    "Regulatory",
    "Supply / Operations",
    "Finance",
):
    app.session_state["launch_current_role"] = role
    app.run()
    assert_clean(app, f"{role} workspace")

app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
app.run()
expander_labels = {expander.label for expander in app.expander}
assert any(label.startswith("Medical Target Patient Package") for label in expander_labels)
assert any(label.startswith("Sales Coverage & Execution Package") for label in expander_labels)
assert any(label.startswith("Market Access Plan Package") for label in expander_labels)

package_key = "marketing_medical_target_patient_package"
confirm_key = f"launch_package_confirm_{CASE_ID}_{package_key}"
request_key = f"launch_package_change_{CASE_ID}_{package_key}"
comment_key = f"launch_package_add_comment_{CASE_ID}_{package_key}"
text_key = f"launch_package_comment_{CASE_ID}_{package_key}"
assert widget_by_key(app.button, confirm_key).disabled
assert widget_by_key(app.button, request_key).disabled
assert widget_by_key(app.button, comment_key).disabled

# Package sharing enables the partner actions.
app.session_state["launch_current_role"] = "Medical"
app.run()
next(button for button in app.button if button.label == "Share Medical Input for Alignment").click().run()
assert_clean(app, "Medical package share")
assert record(app, "Disease / Indication")["Validation Status"] == "Shared for Alignment"

app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
app.run()
assert not widget_by_key(app.button, confirm_key).disabled
assert not widget_by_key(app.button, request_key).disabled

# A comment preserves status and appears in the assumption history.
widget_by_key(app.text_area, text_key).set_value("Marketing alignment discussion note.").run()
widget_by_key(app.button, comment_key).click().run()
assert_clean(app, "add alignment comment")
prevalence = record(app, "Prevalence")
assert prevalence["Validation Status"] == "Shared for Alignment"
assert any(event.get("Action") == "Added Comment" for event in prevalence["Validation History"])

# Request Change requires and preserves a comment, then owner re-share re-enables alignment.
widget_by_key(app.text_area, text_key).set_value("Please reconcile the prevalence source with the latest evidence.").run()
widget_by_key(app.button, request_key).click().run()
assert_clean(app, "request alignment change")
disease = record(app, "Disease / Indication")
assert disease["Validation Status"] == "Alignment Required"
assert any(event.get("Action") == "Requested Change" and event.get("Comment") for event in disease["Validation History"])

app.session_state["launch_current_role"] = "Medical"
app.run()
next(button for button in app.button if button.label == "Share Medical Input for Alignment").click().run()
assert_clean(app, "Medical package re-share")
assert record(app, "Disease / Indication")["Validation Status"] == "Shared for Alignment"

app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
app.run()
widget_by_key(app.button, confirm_key).click().run()
assert_clean(app, "confirm alignment")
disease = record(app, "Disease / Indication")
assert disease["Validation Status"] == "Shared for Alignment"
assert any(event.get("Action") == "Confirmed Alignment" for event in disease["Validation History"])

app.session_state["launch_current_role"] = "Regulatory"
app.run()
regulatory_target_key = "regulatory_medical_target_patient_package"
regulatory_confirm = f"launch_package_confirm_{CASE_ID}_{regulatory_target_key}"
widget_by_key(app.button, regulatory_confirm).click().run()
assert_clean(app, "final multi-partner confirmation")
assert record(app, "Disease / Indication")["Validation Status"] == "Aligned"

evidence_key = "regulatory_key_clinical_evidence_gap_risk"
widget_by_key(app.button, f"launch_package_confirm_{CASE_ID}_{evidence_key}").click().run()
assert_clean(app, "clinical evidence gap confirmation")
assert record(app, "Key Clinical Evidence Gap / Risk")["Validation Status"] == "Aligned"

print("launch alignment smoke test complete")
