import os
import sys
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))

from investment_model import CASE_ARCHETYPES, default_investment_inputs


for index, archetype in enumerate(CASE_ARCHETYPES):
    case_id = f"DECISION-{index}"
    case = {
        "Case ID": case_id,
        "Investment Case Name": archetype,
        "Case Archetype": archetype,
        "Investment Type": archetype,
        "Business Unit / Market": "Test Scope",
        "Owner": "Daniel Ortiz",
        "Status": "Draft",
        "Last Updated": "2026-09-19",
    }
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "investment"
    app.session_state["investment_page"] = "Investment Case"
    app.session_state["selected_investment_case_id"] = case_id
    app.session_state["investment_runtime_cases"] = [case]
    source_inputs = default_investment_inputs(case)
    app.session_state["investment_case_inputs"] = {case_id: deepcopy(source_inputs)}
    app.session_state[f"investment_case_section_{case_id}"] = "Decision Case"
    app.run()

    assert not list(app.exception), app.exception[0].message if list(app.exception) else ""
    assert len(app.metric) >= 19
    assert len(app.expander) >= 9
    page_text = "\n".join(str(item.value) for item in app.markdown)
    assert "Total Sources:" in page_text
    assert "Total Uses:" in page_text
    assert app.session_state["investment_case_inputs"][case_id] == source_inputs

    for section in ("Overview", "Sensitivity"):
        app.session_state[f"investment_case_section_{case_id}"] = section
        app.run()
        assert not list(app.exception), app.exception[0].message if list(app.exception) else ""
        assert app.session_state["investment_case_inputs"][case_id] == source_inputs
        section_text = "\n".join(str(item.value) for item in app.markdown)
        if section == "Overview":
            assert "Management Takeaway" in section_text
        else:
            assert "One-at-a-Time" in section_text

print("Investment Decision Case rendered cleanly for all three archetypes")
