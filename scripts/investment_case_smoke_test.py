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
app.session_state[uses_key] = {"edited_rows": {0: {"Amount": 23_000_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Investment Uses first edit")
assert app.session_state["investment_case_inputs"][case_id]["investment"]["uses"][0]["Amount"] == 23_000_000

capacity_key = f"investment_driver_{case_id}_capacity_count_10"
app.session_state[capacity_key] = {"edited_rows": {3: {"Y1": 810_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Capacity first edit")
assert app.session_state["investment_case_inputs"][case_id]["capacity"]["Scenario Volume"]["Y1"] == 810_000

custom_driver_key = f"investment_{case_id}_driver_cost_reduction"
next(widget for widget in app.checkbox if widget.key == custom_driver_key).set_value(True).run()
assert_clean(app, "Customized value drivers")
assert "Cost Reduction" in app.session_state["investment_case_inputs"][case_id]["settings"]["Value Creation Drivers"]
next(widget for widget in app.checkbox if widget.key == custom_driver_key).set_value(False).run()
assert_clean(app, "Restored archetype defaults")
assert set(app.session_state["investment_case_inputs"][case_id]["settings"]["Value Creation Drivers"]) == set(archetype_default_drivers(CASE_ARCHETYPES[0]))

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
