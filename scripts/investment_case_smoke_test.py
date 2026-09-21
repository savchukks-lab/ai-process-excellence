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

        inputs = default_investment_inputs(case)
        inputs["capacity_input_methods"]["Baseline Volume"] = "Y1 + Growth"
        inputs["capacity"]["Baseline Volume"]["Y1"] = 720_000
        inputs["capacity_growth_rates"]["Baseline Volume"] = 0.10
        growth_result = calculate_investment_model(inputs)
        growth_bridge = growth_result["capacity_bridge"].set_index("Metric")
        assert round(growth_bridge.at["Baseline Volume", "Y2"]) == 792_000

        annual_inputs = deepcopy(inputs)
        annual_inputs["capacity_input_methods"]["Baseline Volume"] = "Annual Schedule"
        annual_inputs["capacity"]["Baseline Volume"]["Y2"] = 765_432
        annual_result = calculate_investment_model(annual_inputs)
        annual_bridge = annual_result["capacity_bridge"].set_index("Metric")
        assert annual_bridge.at["Baseline Volume", "Y2"] == 765_432
        assert annual_bridge.at["Baseline Idle Capacity", "Y2"] == annual_bridge.at["Baseline Capacity", "Y2"] - 765_432
        assert annual_bridge.at["Scenario Idle Capacity", "Y2"] == annual_bridge.at["Total Scenario Capacity", "Y2"] - annual_bridge.at["Scenario Volume", "Y2"]
        assert abs(annual_bridge.at["Baseline Utilization %", "Y2"] - annual_bridge.at["Baseline Volume", "Y2"] / annual_bridge.at["Baseline Capacity", "Y2"]) < 1e-9
        assert abs(annual_bridge.at["Scenario Utilization %", "Y2"] - annual_bridge.at["Scenario Volume", "Y2"] / annual_bridge.at["Total Scenario Capacity", "Y2"]) < 1e-9

        scenario_pnl = annual_result["scenario_pnl"].set_index("Metric")
        assert scenario_pnl.at["COGS", "Y1"] > 0
        assert 0 < scenario_pnl.at["Gross Margin %", "Y1"] < 1
        assert (annual_result["working_capital"]["Incremental Inventory"] > 0).all()
        assert (annual_result["working_capital"]["Incremental Accounts Payable"] > 0).all()

        revenue_inputs = deepcopy(inputs)
        revenue_inputs["settings"]["Revenue Modeling Mode"] = "Revenue-based"
        revenue_inputs["revenue_input_method"] = "Y1 + Growth"
        revenue_inputs["revenue_based"]["Baseline Revenue"]["Y1"] = 20_000_000
        revenue_inputs["revenue_growth_rate"] = 0.05
        revenue_growth_result = calculate_investment_model(revenue_inputs)
        assert round(revenue_growth_result["baseline_pnl"].set_index("Metric").at["Revenue", "Y2"]) == 21_000_000
        revenue_inputs["revenue_input_method"] = "Annual Schedule"
        revenue_inputs["revenue_based"]["Baseline Revenue"]["Y2"] = 22_222_222
        revenue_annual_result = calculate_investment_model(revenue_inputs)
        assert revenue_annual_result["baseline_pnl"].set_index("Metric").at["Revenue", "Y2"] == 22_222_222

        ramp_expectations = {
            "Immediate": (720_000, 720_000, 720_000),
            "1-year ramp": (360_000, 720_000, 720_000),
            "2-year ramp": (240_000, 480_000, 720_000),
            "Custom": (144_000, 432_000, 648_000),
        }
        for ramp_profile, expected in ramp_expectations.items():
            savings_inputs = default_investment_inputs(case)
            savings_inputs["settings"]["Value Creation Drivers"] = ["Cost Reduction"]
            savings_inputs["savings_register"] = [{
                "Initiative": "Ramp test",
                "Gross Run-rate Saving": 900_000,
                "Realization %": 0.80,
                "Ramp Profile": ramp_profile,
                "Custom Y1 Ramp %": 0.20,
                "Custom Y2 Ramp %": 0.60,
                "Custom Y3+ Ramp %": 0.90,
                "Source / Basis": "Test",
                "Comment": "",
            }]
            savings_result = calculate_investment_model(savings_inputs)
            realized = savings_result["drivers"]["Realized Savings"]
            assert tuple(round(realized[year]) for year in ("Y1", "Y2", "Y3")) == expected
    if archetype == CASE_ARCHETYPES[2]:
        acquisition_result = calculate_investment_model(inputs)
        acquisition_pnl = acquisition_result["scenario_pnl"].set_index("Metric")
        assert 0 < acquisition_pnl.at["COGS", "Y1"]
        assert 0 < acquisition_pnl.at["Gross Margin %", "Y1"] < 1
        assert "Target Working Capital" not in inputs["acquisition"]
        assert "Opening / Transaction Working Capital Reference" in inputs["acquisition"]

    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "investment"
    app.session_state["investment_page"] = "Investment Case"
    app.session_state["selected_investment_case_id"] = case["Case ID"]
    app.session_state["investment_runtime_cases"] = [case]
    app.session_state["investment_case_inputs"] = {case["Case ID"]: inputs}
    app.session_state[f"investment_case_section_{case['Case ID']}"] = "Model"
    app.run()
    assert_clean(app, f"{archetype} Model")
    sustaining_value = 300_000 + index * 10_000
    sustaining_key = f"investment_sustaining_{case['Case ID']}_10_0"
    app.session_state[sustaining_key] = {
        "edited_rows": {0: {"Amount": sustaining_value}},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()
    assert_clean(app, f"{archetype} Sustaining CAPEX edit")
    assert app.session_state["investment_case_inputs"][case["Case ID"]]["investment"]["Sustaining CAPEX"]["Y1"] == sustaining_value
    app.session_state[f"investment_case_section_{case['Case ID']}"] = "Financing"
    app.run()
    assert_clean(app, f"{archetype} Financing navigation")
    app.session_state[f"investment_case_section_{case['Case ID']}"] = "Model"
    app.run()
    assert_clean(app, f"{archetype} Model return")
    assert app.session_state["investment_case_inputs"][case["Case ID"]]["investment"]["Sustaining CAPEX"]["Y1"] == sustaining_value

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

sustaining_key = f"investment_sustaining_{case_id}_10_0"
app.session_state[sustaining_key] = {"edited_rows": {0: {"Amount": 360_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Sustaining CAPEX first edit")
assert app.session_state["investment_case_inputs"][case_id]["investment"]["Sustaining CAPEX"]["Y1"] == 360_000

capacity_key = f"investment_driver_{case_id}_capacity_schedule_count_10"
app.session_state[capacity_key] = {"edited_rows": {1: {"Y1": 810_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Capacity first edit")
assert app.session_state["investment_case_inputs"][case_id]["capacity"]["Scenario Volume"]["Y1"] == 810_000

custom_driver_key = f"investment_{case_id}_driver_cost_reduction"
next(widget for widget in app.checkbox if widget.key == custom_driver_key).set_value(True).run()
assert_clean(app, "Customized value drivers")
assert "Cost Reduction" in app.session_state["investment_case_inputs"][case_id]["settings"]["Value Creation Drivers"]
savings_key = f"investment_records_{case_id}_savings"
app.session_state[savings_key] = {"edited_rows": {0: {"Gross Run-rate Saving": 700_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Savings register first edit")
assert app.session_state["investment_case_inputs"][case_id]["savings_register"][0]["Gross Run-rate Saving"] == 700_000

for group, field, value in (
    ("non_manufacturing_personnel", "Scenario Y1", 5_000_000),
    ("manufacturing_cogs", "Scenario Input", 30.0),
    ("non_manufacturing_opex", "Scenario Y1", 1_700_000),
):
    schema_suffix = "_generic_input_v2" if group == "manufacturing_cogs" else ""
    editor_key = f"investment_records_{case_id}_cost_{group}{schema_suffix}"
    app.session_state[editor_key] = {"edited_rows": {0: {field: value}}, "added_rows": [], "deleted_rows": []}
    app.run()
    assert_clean(app, f"{group} cost first edit")
    assert app.session_state["investment_case_inputs"][case_id]["operating_costs"][group][0][field] == value

personnel_method_key = f"investment_{case_id}_cost_method_non_manufacturing_personnel"
next(widget for widget in app.radio if widget.key == personnel_method_key).set_value("Annual Schedule").run()
assert_clean(app, "Personnel annual schedule mode")
personnel_schedule_key = f"investment_driver_{case_id}_cost_schedule_non_manufacturing_personnel_monetary_value_10"
app.session_state[personnel_schedule_key] = {"edited_rows": {1: {"Y1": 5_250_000}}, "added_rows": [], "deleted_rows": []}
app.run()
assert_clean(app, "Personnel annual schedule first edit")
assert app.session_state["investment_case_inputs"][case_id]["operating_cost_schedules"]["non_manufacturing_personnel"]["Scenario Cost"]["Y1"] == 5_250_000

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
acquisition_app.session_state[acquisition_editor_key] = {"edited_rows": {4: {"Y1": 3_750_000}}, "added_rows": [], "deleted_rows": []}
acquisition_app.run()
assert_clean(acquisition_app, "Acquisition synergy first edit")
assert acquisition_app.session_state["investment_case_inputs"][acquisition_case["Case ID"]]["acquisition"]["Revenue Synergies"]["Y1"] == 3_750_000
assert not any(widget.key == f"investment_records_{acquisition_case['Case ID']}_savings" for widget in acquisition_app.dataframe)

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
