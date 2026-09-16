from __future__ import annotations

import os
import sys
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "streamlit_app.py"
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from investment_model import CASE_ARCHETYPES, VALUE_CREATION_DRIVERS, archetype_default_drivers, calculate_investment_model, default_investment_inputs, investment_demo_cases


def assert_clean(app: AppTest, label: str) -> None:
    if list(app.exception):
        raise AssertionError(f"{label}: {app.exception[0].message}")


cases = investment_demo_cases()
assert len(cases) >= 2
for case in cases:
    inputs = default_investment_inputs(case)
    ten_year = calculate_investment_model(inputs)
    assert len(ten_year["years"]) == 10
    assert ten_year["returns"]["Project IRR"] is not None
    assert not ten_year["baseline_pnl"].empty
    assert not ten_year["scenario_pnl"].empty
    assert not ten_year["cash_flow"].empty

    five_year_inputs = deepcopy(inputs)
    five_year_inputs["settings"]["Forecast Horizon"] = 5
    five_year = calculate_investment_model(five_year_inputs)
    assert len(five_year["years"]) == 5
    assert len(five_year["cash_flow"]) == 6

    for drivers in (["Revenue Growth"], ["Cost Reduction"], VALUE_CREATION_DRIVERS):
        variant = deepcopy(inputs)
        variant["settings"]["Value Creation Drivers"] = list(drivers)
        result = calculate_investment_model(variant)
        assert result["years"]
        assert "Project NPV" in result["returns"]

for index, archetype in enumerate(CASE_ARCHETYPES, start=1):
    case = {"Case ID": f"INV-T{index}", "Investment Case Name": archetype, "Case Archetype": archetype, "Investment Type": archetype, "Business Unit / Market": "Test Scope", "Owner": "Daniel Ortiz", "Status": "Draft", "Last Updated": "2026-09-15"}
    inputs = default_investment_inputs(case)
    for method in ("CAPM – Own Beta", "CAPM – Peer / Proxy Beta", "Corporate Provided Cost of Equity", "Manual / Other"):
        inputs["capital"]["Cost of Equity Method"] = method
        result = calculate_investment_model(inputs)
        assert result["returns"]["WACC"] > 0
    if archetype == CASE_ARCHETYPES[0]:
        for mode in ("Unit-based", "Revenue-based"):
            inputs["settings"]["Revenue Modeling Mode"] = mode
            assert calculate_investment_model(inputs)["years"]

    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "investment"
    app.session_state["investment_page"] = "Investment Case"
    app.session_state["selected_investment_case_id"] = case["Case ID"]
    app.session_state["investment_runtime_cases"] = [case]
    app.session_state["investment_case_inputs"] = {case["Case ID"]: inputs}
    app.session_state[f"investment_case_section_{case['Case ID']}"] = "Model"
    app.run()
    assert_clean(app, f"{archetype} Model")

# Model editors must persist Streamlit's latest delta before recalculation.
case = cases[0]
case_id = case["Case ID"]
inputs = default_investment_inputs(case)
app = AppTest.from_file(str(APP_PATH), default_timeout=90)
app.session_state["current_module"] = "investment"
app.session_state["investment_page"] = "Investment Case"
app.session_state["selected_investment_case_id"] = case_id
app.session_state["investment_runtime_cases"] = [case]
app.session_state["investment_case_inputs"] = {case_id: inputs}
app.session_state[f"investment_case_section_{case_id}"] = "Model"
app.run()
assert_clean(app, "Model first-edit setup")

uses_key = f"investment_records_{case_id}_uses"
npv_before_edit = calculate_investment_model(app.session_state["investment_case_inputs"][case_id])["returns"]["Project NPV"]
app.session_state[uses_key] = {"edited_rows": {0: {"Amount": 23_000_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Investment Uses first edit")
assert app.session_state["investment_case_inputs"][case_id]["investment"]["uses"][0]["Amount"] == 23_000_000
assert calculate_investment_model(app.session_state["investment_case_inputs"][case_id])["returns"]["Project NPV"] != npv_before_edit

sustaining_key = f"investment_records_{case_id}_sustaining_10"
app.session_state[sustaining_key] = {"edited_rows": {0: {"Amount": 360_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Sustaining CAPEX first edit")
assert app.session_state["investment_case_inputs"][case_id]["investment"]["Sustaining CAPEX"]["Y1"] == 360_000

capacity_key = f"investment_driver_{case_id}_capacity_count_10"
app.session_state[capacity_key] = {"edited_rows": {3: {"Y1": 810_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Capacity first edit")
assert app.session_state["investment_case_inputs"][case_id]["capacity"]["Scenario Volume"]["Y1"] == 810_000

custom_driver_key = f"investment_{case_id}_driver_cost_reduction"
next(widget for widget in app.checkbox if widget.key == custom_driver_key).set_value(True).run()
assert_clean(app, "Customized value drivers")
assert "Cost Reduction" in app.session_state["investment_case_inputs"][case_id]["settings"]["Value Creation Drivers"]
savings_key = f"investment_records_{case_id}_savings"
app.session_state[savings_key] = {"edited_rows": {0: {"Gross Saving": 700_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Savings register first edit")
assert app.session_state["investment_case_inputs"][case_id]["savings_register"][0]["Gross Saving"] == 700_000

for group, field, value in (
    ("personnel", "Scenario Y1", 5_000_000),
    ("variable", "Scenario Unit Cost", 30.0),
    ("fixed", "Scenario Y1", 1_700_000),
):
    editor_key = f"investment_records_{case_id}_cost_{group}"
    app.session_state[editor_key] = {"edited_rows": {0: {field: value}}, "added_rows": [], "deleted_rows": []}
    app.run()
    assert_clean(app, f"{group} cost first edit")
    assert app.session_state["investment_case_inputs"][case_id]["operating_costs"][group][0][field] == value

capex_driver_key = f"investment_{case_id}_driver_asset_capex_avoidance"
next(widget for widget in app.checkbox if widget.key == capex_driver_key).set_value(True).run()
assert_clean(app, "CAPEX avoidance enabled")
capex_editor_key = f"investment_driver_{case_id}_capex_avoidance_monetary_value_10"
app.session_state[capex_editor_key] = {"edited_rows": {0: {"Y1": 250_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "CAPEX avoidance first edit")
assert app.session_state["investment_case_inputs"][case_id]["investment"]["CAPEX Avoidance"]["Y1"] == 250_000

next(widget for widget in app.checkbox if widget.key == custom_driver_key).set_value(False).run()
assert_clean(app, "Restored archetype defaults")
next(widget for widget in app.checkbox if widget.key == capex_driver_key).set_value(False).run()
assert_clean(app, "Restored archetype defaults after CAPEX")
assert set(app.session_state["investment_case_inputs"][case_id]["settings"]["Value Creation Drivers"]) == set(archetype_default_drivers(CASE_ARCHETYPES[0]))

acquisition_case = {"Case ID": "INV-ACQ-EDIT", "Investment Case Name": "Acquisition Edit Test", "Case Archetype": CASE_ARCHETYPES[2], "Investment Type": CASE_ARCHETYPES[2], "Business Unit / Market": "Test Scope", "Owner": "Daniel Ortiz", "Status": "Draft", "Last Updated": "2026-09-16"}
acquisition_inputs = default_investment_inputs(acquisition_case)
acquisition_app = AppTest.from_file(str(APP_PATH), default_timeout=90)
acquisition_app.session_state["current_module"] = "investment"
acquisition_app.session_state["investment_page"] = "Investment Case"
acquisition_app.session_state["selected_investment_case_id"] = acquisition_case["Case ID"]
acquisition_app.session_state["investment_runtime_cases"] = [acquisition_case]
acquisition_app.session_state["investment_case_inputs"] = {acquisition_case["Case ID"]: acquisition_inputs}
acquisition_app.session_state[f"investment_case_section_{acquisition_case['Case ID']}"] = "Model"
acquisition_app.run()
assert_clean(acquisition_app, "Acquisition first-edit setup")
acquisition_editor_key = f"investment_driver_{acquisition_case['Case ID']}_acquisition_monetary_value_10"
acquisition_app.session_state[acquisition_editor_key] = {"edited_rows": {5: {"Y1": 3_750_000}}, "added_rows": [], "deleted_rows": []}
acquisition_app.run()
assert_clean(acquisition_app, "Acquisition synergy first edit")
assert acquisition_app.session_state["investment_case_inputs"][acquisition_case["Case ID"]]["acquisition"]["Revenue Synergies"]["Y1"] == 3_750_000

for case in cases:
    case_id = case["Case ID"]
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "investment"
    app.session_state["investment_page"] = "Investment Case"
    app.session_state["selected_investment_case_id"] = case_id
    app.session_state[f"investment_case_section_{case_id}"] = "Overview"
    app.run()
    assert_clean(app, f"{case_id} Overview")
    for section in ("Model", "Financing", "Sensitivity", "Decision Case", "Overview"):
        app.session_state[f"investment_case_section_{case_id}"] = section
        app.run()
        assert_clean(app, f"{case_id} {section}")

print("investment case calculation and navigation smoke test complete")
