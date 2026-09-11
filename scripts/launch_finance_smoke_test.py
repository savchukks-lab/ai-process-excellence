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


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


required_finance = {
    "COGS per Unit",
    "Product Manager Fully Loaded Cost per FTE",
    "Product Manager Annual Escalation %",
    "KAM / Sales FTE Fully Loaded Cost per FTE",
    "KAM / Sales FTE Annual Escalation %",
    "MSL / Medical FTE Fully Loaded Cost per FTE",
    "MSL / Medical FTE Annual Escalation %",
}
removed = {"Average Cost per FTE", "Launch Investment Classification"}


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Finance"
    app.run()
    assert_clean(app, f"{case_id} Finance")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    names = {str(row.get("Assumption Name", "")) for row in records}
    assert required_finance.issubset(names), f"{case_id}: missing Finance assumptions {required_finance - names}"
    assert not removed.intersection(names), f"{case_id}: obsolete Finance assumptions remain {removed.intersection(names)}"

    marketing_fte = next(row for row in records if row.get("Assumption Name") == "Marketing FTE")
    sales_fte = next(row for row in records if row.get("Assumption Name") == "Sales FTE")
    medical_fte = next(row for row in records if row.get("Assumption Name") == "Medical FTE")
    assert marketing_fte["Owner"] == "Marketing"
    assert sales_fte["Owner"] == "Sales"
    assert medical_fte["Owner"] == "Medical"

    cogs = next(row for row in records if row.get("Assumption Name") == "COGS per Unit")
    assert cogs["Owner"] == "Finance"
    assert "Supply / Operations" not in str(cogs.get("Validators", ""))
    assert all(cogs.get(year) is not None for year in ("Y1", "Y2", "Y3", "Y4", "Y5"))

    share_buttons = [button for button in app.button if button.label == "Share Finance Input for Alignment"]
    assert len(share_buttons) == 1

    widget_by_key(app.selectbox, f"launch_finance_cogs_mode_{case_id}").set_value("By Year").run()
    assert_clean(app, f"{case_id} COGS mode")
    widget_by_key(app.number_input, f"launch_finance_cogs_{case_id}_Y1").set_value(321.0).run()
    assert_clean(app, f"{case_id} COGS edit")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    cogs = next(row for row in records if row.get("Assumption Name") == "COGS per Unit")
    assert float(cogs["Y1"]) == 321.0
    assert cogs["Forecast Mode"] == "By Year"

    widget_by_key(app.number_input, f"launch_finance_fte_cost_{case_id}_sales").set_value(150000.0).run()
    widget_by_key(app.number_input, f"launch_finance_fte_escalation_{case_id}_sales").set_value(4.0).run()
    assert_clean(app, f"{case_id} personnel edit")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    by_name = {row.get("Assumption Name"): row for row in records}
    assert float(by_name["KAM / Sales FTE Fully Loaded Cost per FTE"]["Value"]) == 150000.0
    assert abs(float(by_name["KAM / Sales FTE Annual Escalation %"]["Value"]) - 0.04) < 1e-9
    for role_name in ("Product Manager", "KAM / Sales FTE", "MSL / Medical FTE"):
        assumption = by_name[f"{role_name} Fully Loaded Cost per FTE"]
        assert str(assumption.get("Source", "")).strip(), f"{case_id}: missing {role_name} cost source"
        assert str(assumption.get("Rationale / Comment", "")).strip(), f"{case_id}: missing {role_name} cost rationale"

    widget_by_key(app.text_input, f"launch_finance_fte_source_{case_id}_sales").set_value("Finance workforce benchmark").run()
    widget_by_key(app.text_area, f"launch_finance_fte_rationale_{case_id}_sales").set_value("Validated fully loaded KAM employment cost.").run()
    assert_clean(app, f"{case_id} personnel source")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    by_name = {row.get("Assumption Name"): row for row in records}
    assert by_name["KAM / Sales FTE Fully Loaded Cost per FTE"]["Source"] == "Finance workforce benchmark"
    assert by_name["KAM / Sales FTE Fully Loaded Cost per FTE"]["Rationale / Comment"] == "Validated fully loaded KAM employment cost."

    benchmark_key = f"launch_finance_benchmark_{case_id}"
    assert benchmark_key in app.session_state
    benchmark_before = dict(app.session_state[benchmark_key])
    widget_by_key(app.text_input, f"launch_finance_benchmark_version_{case_id}").set_value("LRF regression reference").run()
    assert_clean(app, f"{case_id} benchmark edit")
    assert app.session_state[benchmark_key]["Benchmark Version / Date"] == "LRF regression reference"
    records_after_benchmark = app.session_state[f"launch_case_assumptions_{case_id}"]
    assert records_after_benchmark == records
    assert benchmark_before["Revenue"]

    project_rows = app.session_state[f"launch_projects_{case_id}"]
    project_functions = {row.get("Function") for row in project_rows}
    assert {"Marketing", "Sales", "Medical"}.issubset(project_functions)
    expander_labels = {expander.label for expander in app.expander}
    assert "Functional project spend alignment" in expander_labels
    assert any(label.startswith("Market Access pricing") for label in expander_labels)
    assert not any(label.startswith("Market Access Channel Plan") for label in expander_labels)

    next(button for button in app.button if button.label == "Share Finance Input for Alignment").click().run()
    assert_clean(app, f"{case_id} Finance package share")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    owned = [row for row in records if row.get("Owner") == "Finance" and str(row.get("Validators", "")).strip()]
    assert owned and all(row.get("Validation Status") == "Shared for Alignment" for row in owned)

    for role in ("Marketing · Launch Coordinator", "Sales", "Medical", "Market Access", "Regulatory", "Supply / Operations", "Finance"):
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role}")

print("launch finance smoke test complete")
