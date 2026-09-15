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

from investment_model import calculate_investment_model, default_investment_inputs, investment_demo_cases


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

    for benefit_type in ("Revenue Growth", "Cost Saving", "Mixed"):
        variant = deepcopy(inputs)
        variant["settings"]["Benefit Type"] = benefit_type
        result = calculate_investment_model(variant)
        assert result["years"]
        assert "Project NPV" in result["returns"]

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
