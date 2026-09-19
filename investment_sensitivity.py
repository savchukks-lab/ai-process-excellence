from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd

from investment_model import CASE_ARCHETYPES, calculate_investment_model


def _number(value: Any) -> float:
    try:
        result = float(value)
        return result if pd.notna(result) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _scale_series(values: dict[str, Any], factor: float) -> None:
    for year in list(values):
        values[year] = _number(values[year]) * factor


def _scale_cost_group(inputs: dict[str, Any], group: str, factor: float) -> None:
    for row in inputs.get("operating_costs", {}).get(group, []):
        row["Scenario Y1"] = _number(row.get("Scenario Y1")) * factor
        if group == "variable":
            row["Scenario Unit Cost"] = _number(row.get("Scenario Unit Cost")) * factor
    for value_type in ("Scenario Cost",):
        _scale_series(inputs.get("operating_cost_schedules", {}).get(group, {}).get(value_type, {}), factor)


def _pnl_value(model: dict[str, Any], metric: str, year: str) -> float:
    table = model.get("scenario_pnl", pd.DataFrame())
    if not isinstance(table, pd.DataFrame) or table.empty:
        return 0.0
    indexed = table.set_index("Metric")
    return _number(indexed.at[metric, year]) if metric in indexed.index and year in indexed.columns else 0.0


def _driver(
    driver_id: str,
    label: str,
    base_value: float,
    base_display: str,
    unit: str,
    method: str,
    downside: float,
    upside: float,
    basis: str,
    confidence: str = "Medium",
) -> dict[str, Any]:
    return {
        "Driver ID": driver_id,
        "Applicable": True,
        "Driver": label,
        "Base Value": base_value,
        "Base": base_display,
        "Downside": downside,
        "Upside": upside,
        "Unit": unit,
        "Input Method": method,
        "Range Basis": basis,
        "Range Confidence": confidence,
    }


def investment_sensitivity_drivers(inputs: dict[str, Any], base_model: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return archetype-relevant sensitivity controls sourced from the Base model."""
    model = base_model or calculate_investment_model(inputs)
    years = list(model["years"])
    terminal = "Y5" if "Y5" in years else years[-1]
    settings = inputs.get("settings", {})
    archetype = str(settings.get("Case Archetype", CASE_ARCHETYPES[0]))
    enabled = set(settings.get("Value Creation Drivers", []))
    rows: list[dict[str, Any]] = []

    if archetype == CASE_ARCHETYPES[0] and str(settings.get("Revenue Modeling Mode", "Unit-based")) == "Unit-based":
        volume = _number(inputs.get("capacity", {}).get("Scenario Volume", {}).get(terminal))
        price = _number(inputs.get("capacity", {}).get("Baseline Net Revenue per Unit", {}).get(terminal))
        rows.extend([
            _driver("revenue_volume", "Revenue / Volume", volume, f"{volume:,.0f}", "% change", "Relative % change", -10.0, 10.0, "Demand and utilization range", "Medium"),
            _driver("net_price", "Net Price", price, f"${price:,.1f}", "% change", "Relative % change", -8.0, 5.0, "Commercial price range", "Medium"),
        ])
    else:
        revenue = _pnl_value(model, "Revenue", terminal)
        rows.append(_driver("revenue_volume", "Revenue / Volume", revenue, f"${revenue:,.0f}", "% change", "Relative % change", -10.0, 10.0, "Commercial forecast range", "Medium"))

    if archetype == CASE_ARCHETYPES[2]:
        margin = _number(inputs.get("acquisition", {}).get("Target Gross Margin %", {}).get(terminal))
        rows.append(_driver("target_margin", "Gross Margin", margin, f"{margin:.1%}", "percentage points", "Percentage-point change", -5.0, 3.0, "Target margin diligence range", "Medium"))
    else:
        variable_cost = _pnl_value(model, "COGS", terminal)
        rows.append(_driver("variable_cost", "Variable Cost", variable_cost, f"${variable_cost:,.0f}", "% change", "Relative % change", 10.0, -7.5, "Supplier and operating-cost range", "Medium"))

    personnel = _pnl_value(model, "Personnel", terminal)
    fixed_cost = _pnl_value(model, "Other Operating Expenses", terminal)
    initial = _number(model.get("total_initial_investment"))
    sustaining = sum(_number(inputs.get("investment", {}).get("Sustaining CAPEX", {}).get(year)) for year in years)
    rows.extend([
        _driver("personnel_cost", "Personnel Cost", personnel, f"${personnel:,.0f}", "% change", "Relative % change", 10.0, -5.0, "Workforce and labor-cost range", "Medium"),
        _driver("fixed_cost", "Fixed Operating Cost", fixed_cost, f"${fixed_cost:,.0f}", "% change", "Relative % change", 10.0, -5.0, "Operating-plan range", "Medium"),
        _driver("initial_investment", "Initial Investment / CAPEX", initial, f"${initial:,.0f}", "% change", "Relative % change", 15.0, -5.0, "Estimate and contingency range", "Medium"),
        _driver("sustaining_capex", "Sustaining CAPEX", sustaining, f"${sustaining:,.0f}", "% change", "Relative % change", 15.0, -10.0, "Long-range maintenance range", "Medium"),
    ])

    if "Working Capital Improvement" in enabled:
        working_capital = inputs.get("working_capital", {})
        rows.extend([
            _driver("dso", "Working Capital / DSO", _number(working_capital.get("Relevant DSO")), f"{_number(working_capital.get('Relevant DSO')):.0f}", "days", "Absolute value", _number(working_capital.get("Relevant DSO")) + 10, max(0.0, _number(working_capital.get("Relevant DSO")) - 10), "Collection-cycle range", "Medium"),
            _driver("dio", "Working Capital / DIO", _number(working_capital.get("Relevant DIO")), f"{_number(working_capital.get('Relevant DIO')):.0f}", "days", "Absolute value", _number(working_capital.get("Relevant DIO")) + 10, max(0.0, _number(working_capital.get("Relevant DIO")) - 10), "Inventory-cycle range", "Medium"),
            _driver("dpo", "Working Capital / DPO", _number(working_capital.get("Relevant DPO")), f"{_number(working_capital.get('Relevant DPO')):.0f}", "days", "Absolute value", max(0.0, _number(working_capital.get("Relevant DPO")) - 10), _number(working_capital.get("Relevant DPO")) + 10, "Supplier-payment range", "Medium"),
        ])

    if "Cost Reduction" in enabled:
        if archetype == CASE_ARCHETYPES[2]:
            terminal_ramp = _number(inputs.get("acquisition", {}).get("Synergy Ramp %", {}).get(terminal))
            base_display = f"{terminal_ramp:.1%}"
            base_value = terminal_ramp
        else:
            realizations = [_number(row.get("Realization %")) for row in inputs.get("savings_register", []) if row.get("Applicable", True)]
            base_value = sum(realizations) / len(realizations) if realizations else 0.0
            base_display = f"{base_value:.1%}"
        rows.append(_driver("savings_realization", "Savings / Synergy Realization", base_value, base_display, "% change", "Relative % change", -15.0, 10.0, "Benefit-delivery range", "Medium"))
    return rows


def normalize_sensitivity_settings(inputs: dict[str, Any], saved: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    defaults = investment_sensitivity_drivers(inputs)
    saved_by_id = {str(row.get("Driver ID")): row for row in (saved or [])}
    normalized = []
    for default in defaults:
        prior = saved_by_id.get(str(default["Driver ID"]), {})
        row = deepcopy(default)
        for field in ("Applicable", "Downside", "Upside", "Range Basis", "Range Confidence"):
            if field in prior:
                row[field] = prior[field]
        normalized.append(row)
    return normalized


def _relative_factor(value: Any) -> float:
    return max(0.0, 1.0 + _number(value) / 100.0)


def apply_sensitivity_driver(base_inputs: dict[str, Any], driver: dict[str, Any], scenario_value: Any) -> dict[str, Any]:
    """Apply one analytical overlay to a copy of Base inputs; model formulas remain authoritative."""
    inputs = deepcopy(base_inputs)
    driver_id = str(driver.get("Driver ID", ""))
    factor = _relative_factor(scenario_value)
    archetype = str(inputs.get("settings", {}).get("Case Archetype", CASE_ARCHETYPES[0]))

    if driver_id == "revenue_volume":
        if archetype == CASE_ARCHETYPES[0] and str(inputs["settings"].get("Revenue Modeling Mode", "Unit-based")) == "Unit-based":
            _scale_series(inputs["capacity"]["Scenario Volume"], factor)
        elif archetype == CASE_ARCHETYPES[2]:
            _scale_series(inputs["acquisition"]["Target Revenue"], factor)
            _scale_series(inputs["acquisition"]["Revenue Synergies"], factor)
        else:
            _scale_series(inputs["revenue_based"]["Incremental Revenue / Revenue Uplift"], factor)
    elif driver_id == "net_price":
        _scale_series(inputs["capacity"]["Baseline Net Revenue per Unit"], factor)
    elif driver_id == "variable_cost":
        _scale_cost_group(inputs, "variable", factor)
    elif driver_id == "target_margin":
        delta = _number(scenario_value) / 100.0
        for year in inputs["acquisition"]["Target Gross Margin %"]:
            inputs["acquisition"]["Target Gross Margin %"][year] = min(1.0, max(0.0, _number(inputs["acquisition"]["Target Gross Margin %"][year]) + delta))
    elif driver_id == "personnel_cost":
        _scale_cost_group(inputs, "personnel", factor)
    elif driver_id == "fixed_cost":
        _scale_cost_group(inputs, "fixed", factor)
    elif driver_id == "initial_investment":
        for row in inputs["investment"]["uses"]:
            if row.get("Applicable", True):
                row["Amount"] = _number(row.get("Amount")) * factor
    elif driver_id == "sustaining_capex":
        _scale_series(inputs["investment"]["Sustaining CAPEX"], factor)
    elif driver_id in {"dso", "dio", "dpo"}:
        field = {"dso": "Relevant DSO", "dio": "Relevant DIO", "dpo": "Relevant DPO"}[driver_id]
        inputs["working_capital"][field] = max(0.0, _number(scenario_value))
    elif driver_id == "savings_realization":
        if archetype == CASE_ARCHETYPES[2]:
            for year in inputs["acquisition"]["Synergy Ramp %"]:
                inputs["acquisition"]["Synergy Ramp %"][year] = min(1.0, max(0.0, _number(inputs["acquisition"]["Synergy Ramp %"][year]) * factor))
        else:
            for row in inputs.get("savings_register", []):
                if row.get("Applicable", True):
                    row["Realization %"] = min(1.0, max(0.0, _number(row.get("Realization %")) * factor))
    return inputs


def _scenario_output(model: dict[str, Any], scenario: str) -> dict[str, Any]:
    years = list(model["years"])
    terminal = "Y5" if "Y5" in years else years[-1]
    return {
        "Scenario": scenario,
        "NPV": _number(model["returns"].get("Project NPV")),
        "IRR": model["returns"].get("Project IRR"),
        "Payback": model["returns"].get("Payback Period"),
        "Cumulative FCF": _number(model["returns"].get("Cumulative Unlevered FCF")),
        "Y5 Revenue": _pnl_value(model, "Revenue", terminal),
        "Y5 EBITDA": _pnl_value(model, "EBITDA", terminal),
        "Y5 EBITDA Margin": _pnl_value(model, "EBITDA Margin %", terminal),
    }


def calculate_investment_sensitivity(base_inputs: dict[str, Any], settings: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate one-at-a-time and combined scenarios exclusively through the controlled Base model."""
    base_model = calculate_investment_model(base_inputs)
    active = [deepcopy(row) for row in settings if bool(row.get("Applicable", True))]
    tornado = []
    for row in active:
        downside_model = calculate_investment_model(apply_sensitivity_driver(base_inputs, row, row.get("Downside")))
        upside_model = calculate_investment_model(apply_sensitivity_driver(base_inputs, row, row.get("Upside")))
        base_npv = _number(base_model["returns"].get("Project NPV"))
        downside_npv = _number(downside_model["returns"].get("Project NPV"))
        upside_npv = _number(upside_model["returns"].get("Project NPV"))
        tornado.append({
            "Driver": row["Driver"],
            "Downside NPV": downside_npv,
            "Base NPV": base_npv,
            "Upside NPV": upside_npv,
            "Downside Impact": downside_npv - base_npv,
            "Upside Impact": upside_npv - base_npv,
            "NPV Range": abs(upside_npv - downside_npv),
        })

    downside_inputs = deepcopy(base_inputs)
    upside_inputs = deepcopy(base_inputs)
    for row in active:
        downside_inputs = apply_sensitivity_driver(downside_inputs, row, row.get("Downside"))
        upside_inputs = apply_sensitivity_driver(upside_inputs, row, row.get("Upside"))
    downside_model = calculate_investment_model(downside_inputs)
    upside_model = calculate_investment_model(upside_inputs)
    tornado.sort(key=lambda row: row["NPV Range"], reverse=True)
    return {
        "base_model": base_model,
        "downside_model": downside_model,
        "upside_model": upside_model,
        "tornado": pd.DataFrame(tornado),
        "scenarios": pd.DataFrame([
            _scenario_output(downside_model, "Downside"),
            _scenario_output(base_model, "Base"),
            _scenario_output(upside_model, "Upside"),
        ]),
    }


def calculate_standardized_sensitivity(base_inputs: dict[str, Any], settings: list[dict[str, Any]]) -> pd.DataFrame:
    base_model = calculate_investment_model(base_inputs)
    base_npv = _number(base_model["returns"].get("Project NPV"))
    rows = []
    for row in settings:
        if not bool(row.get("Applicable", True)) or str(row.get("Input Method")) != "Relative % change":
            continue
        downside = calculate_investment_model(apply_sensitivity_driver(base_inputs, row, -10.0))
        upside = calculate_investment_model(apply_sensitivity_driver(base_inputs, row, 10.0))
        rows.append({
            "Driver": row["Driver"],
            "-10% NPV": _number(downside["returns"].get("Project NPV")),
            "Base NPV": base_npv,
            "+10% NPV": _number(upside["returns"].get("Project NPV")),
        })
    return pd.DataFrame(rows)
