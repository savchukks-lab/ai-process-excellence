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

from investment_financing import calculate_all_financing_scenarios, calculate_financing_scenario, default_financing_inputs
from investment_model import calculate_investment_model, default_investment_inputs, investment_demo_cases


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


case = investment_demo_cases()[0]
case_id = case["Case ID"]
model_inputs = default_investment_inputs(case)
operating_model = calculate_investment_model(model_inputs)
financing = default_financing_inputs()
results = calculate_all_financing_scenarios(operating_model, financing)

assert set(results) == {"internal", "mixed", "high_debt"}
project_economics = {(round(result["metrics"]["Project NPV"], 2), round(result["metrics"]["Project IRR"], 8)) for result in results.values()}
assert len(project_economics) == 1
assert results["internal"]["metrics"]["Peak Debt"] == 0
assert results["internal"]["metrics"]["Interest Cost"] == 0
assert results["internal"]["metrics"]["Minimum DSCR"] is None
assert results["mixed"]["metrics"]["Equity IRR"] > results["internal"]["metrics"]["Equity IRR"]
assert results["high_debt"]["metrics"]["Equity IRR"] > results["mixed"]["metrics"]["Equity IRR"]
assert results["high_debt"]["metrics"]["Covenant Breaches"] >= 1

for scenario_id in ("mixed", "high_debt"):
    schedule = results[scenario_id]["debt_schedule"]
    for _, row in schedule.iterrows():
        assert abs(row["Opening Debt"] + row["Debt Drawdown"] - row["Principal Repayment"] - row["Closing Debt"]) < 0.01

floating = deepcopy(financing)
floating_terms = floating["scenarios"]["mixed"]["Debt Terms"]
floating_terms["Interest Rate Type"] = "Floating"
floating_terms["Reference / Base Rate"] = 0.05
floating_terms["Credit Spread"] = 0.03
floating_result = calculate_financing_scenario(operating_model, floating, "mixed")
assert abs(floating_result["metrics"]["All-in Interest Rate"] - 0.08) < 1e-12

bullet = deepcopy(financing)
bullet_terms = bullet["scenarios"]["mixed"]["Debt Terms"]
bullet_terms["Repayment Type"] = "Bullet"
bullet_terms["Maturity Year"] = 5
bullet_result = calculate_financing_scenario(operating_model, bullet, "mixed")
bullet_repayments = bullet_result["debt_schedule"].set_index("Period")["Principal Repayment"]
assert bullet_repayments["Y5"] > 0 and bullet_repayments.drop("Y5").sum() == 0

custom = deepcopy(financing)
custom_scenario = custom["scenarios"]["mixed"]
custom_scenario["Debt Terms"]["Repayment Type"] = "Custom"
facility = results["mixed"]["metrics"]["Debt Funding"]
for row in custom_scenario["Custom Debt Schedule"]:
    row["Drawdown"] = facility if row["Period"] == "Y0" else 0.0
    row["Principal Repayment"] = facility if row["Period"] == "Y6" else 0.0
custom_result = calculate_financing_scenario(operating_model, custom, "mixed")
assert abs(custom_result["debt_schedule"].iloc[-1]["Closing Debt"]) < 0.01

alternative = deepcopy(financing)
alternative_scenario = alternative["scenarios"]["mixed"]
alternative_scenario["Funding Mix"] = {"Internal Cash / Equity %": 0.3, "Debt %": 0.6, "Alternative Funding %": 0.1}
target_result = calculate_financing_scenario(operating_model, alternative, "mixed")
alternative_scenario["Alternative Funding"] = [{
    "Applicable": True,
    "Type": "Grant / Subsidy",
    "Amount": target_result["metrics"]["Alternative Funding Target"],
    "Timing": "Y0",
    "Cost / Rate": 0.0,
    "Repayment Required": "No",
    "Source / Basis": "Regional development program",
    "Comment": "Illustrative committed grant",
}]
alternative_result = calculate_financing_scenario(operating_model, alternative, "mixed")
assert abs(alternative_result["metrics"]["Funding Gap / Excess Funding"]) < 1

covenants = results["mixed"]["covenants"]
for _, row in covenants[covenants["Metric Value"].notna()].iterrows():
    expected = row["Covenant Limit"] - row["Metric Value"] if row["Covenant"] == "Net Debt / EBITDA" else row["Metric Value"] - row["Covenant Limit"]
    assert abs(row["Headroom"] - expected) < 1e-9

app = AppTest.from_file(str(APP_PATH), default_timeout=90)
app.session_state["current_module"] = "investment"
app.session_state["investment_page"] = "Investment Case"
app.session_state["selected_investment_case_id"] = case_id
app.session_state["investment_runtime_cases"] = [case]
model_inputs["financing"] = financing
app.session_state["investment_case_inputs"] = {case_id: model_inputs}
app.session_state[f"investment_case_section_{case_id}"] = "Financing"
app.run()
assert not list(app.exception)

fixed_rate_key = f"investment_financing_{case_id}_mixed_fixed_rate"
before_interest = calculate_financing_scenario(
    calculate_investment_model(app.session_state["investment_case_inputs"][case_id]),
    app.session_state["investment_case_inputs"][case_id]["financing"],
    "mixed",
)["metrics"]["Interest Cost"]
widget_by_key(app.number_input, fixed_rate_key).set_value(8.2).run()
assert not list(app.exception)
saved = app.session_state["investment_case_inputs"][case_id]
assert abs(saved["financing"]["scenarios"]["mixed"]["Debt Terms"]["Fixed Interest Rate"] - 0.082) < 1e-12
after_interest = calculate_financing_scenario(calculate_investment_model(saved), saved["financing"], "mixed")["metrics"]["Interest Cost"]
assert after_interest != before_interest

repayment_key = f"investment_financing_{case_id}_mixed_repayment"
widget_by_key(app.selectbox, repayment_key).set_value("Bullet").run()
assert not list(app.exception)
assert app.session_state["investment_case_inputs"][case_id]["financing"]["scenarios"]["mixed"]["Debt Terms"]["Repayment Type"] == "Bullet"

rate_type_key = f"investment_financing_{case_id}_mixed_rate_type"
widget_by_key(app.selectbox, rate_type_key).set_value("Floating").run()
assert not list(app.exception)
assert any(widget.key == f"investment_financing_{case_id}_mixed_reference_rate" for widget in app.number_input)

widget_by_key(app.selectbox, repayment_key).set_value("Custom").run()
assert not list(app.exception)

print("investment financing calculation and interaction smoke test complete")
