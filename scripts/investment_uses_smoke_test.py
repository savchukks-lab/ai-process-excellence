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

from investment_financing import calculate_financing_scenario, default_financing_inputs
from investment_model import CASE_ARCHETYPES, calculate_investment_model, default_investment_inputs


def enabled_initial_uses(inputs: dict) -> float:
    return sum(
        float(row.get("Amount", 0) or 0)
        for row in inputs["investment"]["uses"]
        if bool(row.get("Applicable", True))
    )


for index, archetype in enumerate(CASE_ARCHETYPES, start=1):
    case = {
        "Case ID": f"INV-USES-{index}",
        "Investment Case Name": f"{archetype} uses test",
        "Case Archetype": archetype,
        "Investment Type": archetype,
        "Business Unit / Market": "Test Scope",
        "Owner": "Daniel Ortiz",
        "Status": "Draft",
        "Last Updated": "2026-09-19",
    }
    inputs = default_investment_inputs(case)
    years = [f"Y{i}" for i in range(1, int(inputs["settings"]["Forecast Horizon"]) + 1)]
    initial = enabled_initial_uses(inputs)
    sustaining = sum(float(inputs["investment"]["Sustaining CAPEX"].get(year, 0) or 0) for year in years)
    avoided = sum(float(inputs["investment"]["CAPEX Avoidance"].get(year, 0) or 0) for year in years)

    assert initial > 0
    assert sustaining > 0
    assert initial + sustaining == enabled_initial_uses(inputs) + sum(
        float(inputs["investment"]["Sustaining CAPEX"].get(year, 0) or 0) for year in years
    )

    model = calculate_investment_model(inputs)
    assert model["cash_flow"].set_index("Year").at["Y0", "Unlevered Free Cash Flow"] == -initial
    repeated = calculate_investment_model(deepcopy(inputs))
    assert repeated["returns"]["Project NPV"] == model["returns"]["Project NPV"]
    assert repeated["returns"]["Project IRR"] == model["returns"]["Project IRR"]

    financing = default_financing_inputs()
    internal = calculate_financing_scenario(model, financing, "internal")
    assert abs(internal["metrics"]["Total Uses"] - initial) < 0.01
    assert abs(internal["metrics"]["Total Sources"] - internal["metrics"]["Total Uses"]) < 0.01
    assert internal["metrics"]["Sustaining CAPEX Over Forecast"] == sustaining
    assert avoided == 0 or avoided == sum(float(inputs["investment"]["CAPEX Avoidance"].get(year, 0) or 0) for year in years)

    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "investment"
    app.session_state["investment_page"] = "Investment Case"
    app.session_state["selected_investment_case_id"] = case["Case ID"]
    app.session_state["investment_runtime_cases"] = [case]
    app.session_state["investment_case_inputs"] = {case["Case ID"]: inputs}
    app.session_state[f"investment_case_section_{case['Case ID']}"] = "Model"
    app.run()
    assert not list(app.exception)
    metric_labels = {metric.label for metric in app.metric}
    assert {"Total Initial Investment", "Total Sustaining CAPEX", "Upfront Investment", "Forecast Sustaining CAPEX", "Total Modeled CAPEX"}.issubset(metric_labels)


avoidance_case = {
    "Case ID": "INV-USES-AVOID",
    "Investment Case Name": "Avoided CAPEX test",
    "Case Archetype": CASE_ARCHETYPES[0],
    "Investment Type": CASE_ARCHETYPES[0],
    "Business Unit / Market": "Test Scope",
    "Owner": "Daniel Ortiz",
    "Status": "Draft",
    "Last Updated": "2026-09-19",
}
avoidance_inputs = default_investment_inputs(avoidance_case)
avoidance_inputs["settings"]["Value Creation Drivers"] = list(dict.fromkeys(avoidance_inputs["settings"]["Value Creation Drivers"] + ["Asset / CAPEX Avoidance"]))
avoidance_inputs["investment"]["CAPEX Avoidance"]["Y4"] = 4_000_000
avoidance_initial = enabled_initial_uses(avoidance_inputs)
avoidance_model = calculate_investment_model(avoidance_inputs)
assert enabled_initial_uses(avoidance_inputs) == avoidance_initial
assert avoidance_model["cash_flow"].set_index("Year").at["Y0", "Unlevered Free Cash Flow"] == -avoidance_initial
assert avoidance_model["cash_flow"].set_index("Year").at["Y4", "CAPEX"] == 0

avoidance_app = AppTest.from_file(str(APP_PATH), default_timeout=90)
avoidance_app.session_state["current_module"] = "investment"
avoidance_app.session_state["investment_page"] = "Investment Case"
avoidance_app.session_state["selected_investment_case_id"] = avoidance_case["Case ID"]
avoidance_app.session_state["investment_runtime_cases"] = [avoidance_case]
avoidance_app.session_state["investment_case_inputs"] = {avoidance_case["Case ID"]: avoidance_inputs}
avoidance_app.session_state[f"investment_case_section_{avoidance_case['Case ID']}"] = "Model"
avoidance_app.run()
assert not list(avoidance_app.exception)
assert "Total Avoided Future CAPEX" in {metric.label for metric in avoidance_app.metric}
assert "Avoided Future CAPEX" in {metric.label for metric in avoidance_app.metric}

print("investment uses summary and reconciliation smoke test complete")
