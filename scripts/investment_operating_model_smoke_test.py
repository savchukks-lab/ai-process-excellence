from __future__ import annotations

from copy import deepcopy
from math import isclose
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from investment_financing import calculate_financing_scenario, default_financing_inputs
from investment_model import CASE_ARCHETYPES, calculate_investment_model, default_investment_inputs
from investment_sensitivity import calculate_investment_sensitivity, normalize_sensitivity_settings


def close(left: float, right: float, tolerance: float = 0.01) -> bool:
    return isclose(float(left), float(right), abs_tol=tolerance)


for index, archetype in enumerate(CASE_ARCHETYPES, start=1):
    case = {"Case ID": f"INV-OPERATING-{index}", "Investment Case Name": archetype, "Case Archetype": archetype}
    inputs = default_investment_inputs(case)
    model = calculate_investment_model(inputs)
    years = model["years"]
    baseline = model["baseline_pnl"].set_index("Metric")
    scenario = model["scenario_pnl"].set_index("Metric")

    for pnl in (baseline, scenario):
        for year in years:
            assert close(pnl.at["Gross Profit", year], pnl.at["Revenue", year] - pnl.at["COGS", year])
            assert close(pnl.at["EBITDA", year], pnl.at["Gross Profit", year] - pnl.at["Non-Manufacturing Personnel", year] - pnl.at["Non-Manufacturing OPEX", year])
            assert close(pnl.at["EBIT", year], pnl.at["EBITDA", year] - pnl.at["Depreciation & Amortization", year])

    cogs = model["cogs_bridge"]
    for case_name, pnl in (("Baseline", baseline), ("Investment Scenario", scenario)):
        components = cogs[(cogs["Case"] == case_name) & (cogs["COGS Component"] != "Total Manufacturing COGS")]
        for year in years:
            assert close(components[year].sum(), pnl.at["COGS", year])

    depreciation = model["depreciation_bridge"].set_index("D&A Component")
    total_da = depreciation.loc["Total Scenario D&A"]
    for year in years:
        assert close(total_da[year], scenario.at["Depreciation & Amortization", year])

    cash_flow = model["cash_flow"].set_index("Year")
    for year in years:
        expected = (
            cash_flow.at[year, "Incremental EBIT"]
            - cash_flow.at[year, "Cash Taxes"]
            + cash_flow.at[year, "D&A"]
            - cash_flow.at[year, "CAPEX"]
            - cash_flow.at[year, "Change in NWC"]
            + cash_flow.at[year, "Avoided CAPEX"]
        )
        assert close(expected, cash_flow.at[year, "Unlevered Free Cash Flow"])
        assert close(cash_flow.at[year, "CAPEX"], inputs["investment"]["Sustaining CAPEX"][year])
    assert close(model["returns"]["Project NPV"], cash_flow["Present Value of FCF"].sum())

    sensitivity = calculate_investment_sensitivity(inputs, normalize_sensitivity_settings(inputs, None))
    base_row = sensitivity["scenarios"].set_index("Scenario").loc["Base"]
    assert close(base_row["NPV"], model["returns"]["Project NPV"])
    assert close(base_row["IRR"], model["returns"]["Project IRR"], 1e-12)

    financing = calculate_financing_scenario(model, default_financing_inputs(), "internal")
    assert close(financing["metrics"]["Project NPV"], model["returns"]["Project NPV"])
    assert close(financing["metrics"]["Total Uses"], model["total_initial_investment"])


capacity_inputs = default_investment_inputs({"Case Archetype": CASE_ARCHETYPES[0]})
capacity_model = calculate_investment_model(capacity_inputs)
capacity_pnl = capacity_model["baseline_pnl"].set_index("Metric")
assert close(capacity_pnl.at["COGS", "Y1"], 20_880_000)

tax_bridge = capacity_model["tax_bridge"].set_index("Year")
assert tax_bridge.at["Y1", "Incremental EBIT"] < 0
assert tax_bridge.at["Y1", "Closing Tax Loss Balance"] > 0
assert tax_bridge.at["Y2", "Tax Loss Used"] > 0
assert tax_bridge.at["Y2", "Cash Taxes"] == 0
assert tax_bridge.at["Y3", "Cash Taxes"] > 0

avoidance_inputs = deepcopy(capacity_inputs)
avoidance_inputs["settings"]["Value Creation Drivers"].append("Asset / CAPEX Avoidance")
avoidance_inputs["investment"]["CAPEX Avoidance"]["Y4"] = 4_000_000
avoidance_model = calculate_investment_model(avoidance_inputs)
avoidance_flow = avoidance_model["cash_flow"].set_index("Year")
assert close(avoidance_flow.at["Y4", "CAPEX"], avoidance_inputs["investment"]["Sustaining CAPEX"]["Y4"])
assert close(avoidance_flow.at["Y4", "Avoided CAPEX"], 4_000_000)

print("investment operating model reconciliation smoke test complete")
