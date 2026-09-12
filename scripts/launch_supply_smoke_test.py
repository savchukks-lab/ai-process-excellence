import os
import sys
from datetime import date
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


required = {
    "Expected Stock Available Date",
    "Supply Plan / Rationale",
    "Manufacturing / Supply Constraint Status",
    "Constraint / Risk",
    "Constraint Potential Impact",
    "Plan / Management Response",
    "Supply Capacity May Constrain Launch Demand",
    "Maximum Available Units",
}
removed = {
    "Earliest Supply Available Date",
    "Launch Stock Available?",
    "Can Projected Demand Be Supplied?",
    "Major Supply Risk",
    "Supply Mitigation",
    "Incremental Supply Investment / Project",
}


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=45)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Supply / Operations"
    app.session_state[f"launch_case_section_{case_id}"] = "Workstreams"
    app.run()
    assert_clean(app, f"{case_id} Supply / Operations")

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    names = {str(row.get("Assumption Name", "")) for row in records}
    assert required.issubset(names), f"{case_id}: missing Supply assumptions {required - names}"
    assert not removed.intersection(names), f"{case_id}: legacy Supply assumptions remain {removed.intersection(names)}"

    cogs = next(row for row in records if row.get("Assumption Name") == "COGS per Unit")
    assert "Supply / Operations" not in str(cogs.get("Validators", ""))
    assert "Average Cost per FTE" not in names

    incoming = [
        row
        for row in records
        if row.get("Owner") != "Supply / Operations"
        and "Supply / Operations" in [part.strip() for part in str(row.get("Validators", "")).split(",")]
        and row.get("Assumption Name") == "Expected Regulatory Approval Date"
    ]
    assert len(incoming) == 1

    share_buttons = [button for button in app.button if button.label == "Share Supply Input for Alignment"]
    assert len(share_buttons) == 1

    new_stock_date = date(2027, 3, 12) if case_id == "LAUNCH-1001" else date(2027, 1, 20)
    widget_by_key(app.date_input, f"launch_supply_stock_date_{case_id}").set_value(new_stock_date).run()
    assert_clean(app, f"{case_id} stock date edit")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    by_name = {row.get("Assumption Name"): row for row in records}
    assert by_name["Expected Stock Available Date"]["Value"] == new_stock_date.isoformat()

    if case_id == "LAUNCH-1001":
        assert widget_by_key(app.checkbox, f"launch_supply_capacity_enabled_{case_id}").value
        widget_by_key(app.number_input, f"launch_supply_max_units_{case_id}_Y1").set_value(500).run()
        assert_clean(app, f"{case_id} maximum units edit")
        records = app.session_state[f"launch_case_assumptions_{case_id}"]
        maximum = next(row for row in records if row.get("Assumption Name") == "Maximum Available Units")
        assert float(maximum["Y1"]) == 500
        rendered_tables = "\n".join(str(markdown.value) for markdown in app.markdown)
        assert "Maximum Available Units" in rendered_tables
        assert "Sellable Units" in rendered_tables

        widget_by_key(app.date_input, f"launch_supply_stock_date_{case_id}").set_value(date(2026, 12, 1)).run()
        assert_clean(app, f"{case_id} timing consistency warning")
        assert any("Stock availability cannot precede" in warning.value for warning in app.warning)
    else:
        assert not any(widget.key == f"launch_supply_capacity_enabled_{case_id}" for widget in app.checkbox)
        records = app.session_state[f"launch_case_assumptions_{case_id}"]
        constraint = next(row for row in records if row.get("Assumption Name") == "Manufacturing / Supply Constraint Status")
        assert constraint["Value"] == "No known constraint"
        rendered_tables = "\n".join(str(markdown.value) for markdown in app.markdown)
        assert "Integrated model demand" in rendered_tables

    assert not any(widget.key == f"launch_supply_warehouse_status_{case_id}" for widget in app.selectbox)

    next(button for button in app.button if button.label == "Share Supply Input for Alignment").click().run()
    assert_clean(app, f"{case_id} Supply package share")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    owned = [
        row
        for row in records
        if row.get("Owner") == "Supply / Operations" and str(row.get("Validators", "")).strip()
    ]
    assert owned and all(row.get("Validation Status") == "Shared for Alignment" for row in owned)

    for role in ("Marketing · Launch Coordinator", "Sales", "Regulatory", "Supply / Operations"):
        app.session_state["launch_current_role"] = role
        app.run()
        assert_clean(app, f"{case_id} {role}")

print("launch supply smoke test complete")
