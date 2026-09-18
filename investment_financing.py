from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite
from typing import Any

import pandas as pd


FINANCING_SCHEMA_VERSION = 1
FINANCING_PERIODS = [f"Y{i}" for i in range(11)]
FUNDING_SCENARIOS = [
    ("internal", "Internal Cash / Equity", 1.0, 0.0, "Straight-line", 0.0, 8),
    ("mixed", "Mixed Funding", 0.4, 0.6, "Straight-line", 0.072, 8),
    ("high_debt", "Debt-Heavy Funding", 0.2, 0.8, "Bullet", 0.085, 4),
]


def _number(value: Any) -> float:
    try:
        result = float(value)
        return result if isfinite(result) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if abs(denominator) > 1e-12 else None


def _npv(rate: float, cash_flows: list[float]) -> float:
    return sum(value / (1 + rate) ** index for index, value in enumerate(cash_flows))


def _irr(cash_flows: list[float]) -> float | None:
    if not cash_flows or min(cash_flows) >= 0 or max(cash_flows) <= 0:
        return None
    low, high = -0.99, 10.0
    low_value, high_value = _npv(low, cash_flows), _npv(high, cash_flows)
    if low_value * high_value > 0:
        return None
    for _ in range(200):
        midpoint = (low + high) / 2
        midpoint_value = _npv(midpoint, cash_flows)
        if abs(midpoint_value) < 0.01:
            return midpoint
        if low_value * midpoint_value <= 0:
            high, high_value = midpoint, midpoint_value
        else:
            low, low_value = midpoint, midpoint_value
    return (low + high) / 2


def _payback(cash_flows: list[float]) -> float | None:
    cumulative = cash_flows[0] if cash_flows else 0.0
    if cumulative >= 0:
        return 0.0
    for index, value in enumerate(cash_flows[1:], start=1):
        previous = cumulative
        cumulative += value
        if cumulative >= 0 and value > 0:
            return (index - 1) + abs(previous) / value
    return None


def _default_covenants() -> list[dict[str, Any]]:
    return [
        {"Applicable": True, "Covenant": "Net Debt / EBITDA", "Limit": 3.0, "Calculation Basis": "Relevant Business Scope", "Direction": "Maximum"},
        {"Applicable": True, "Covenant": "Interest Coverage", "Limit": 3.0, "Calculation Basis": "Relevant Business Scope", "Direction": "Minimum"},
        {"Applicable": True, "Covenant": "DSCR", "Limit": 1.2, "Calculation Basis": "Relevant Business Scope", "Direction": "Minimum"},
        {"Applicable": False, "Covenant": "Minimum Cash", "Limit": 2_000_000.0, "Calculation Basis": "Borrower / Company", "Direction": "Minimum"},
    ]


def _default_scenario(
    scenario_id: str,
    name: str,
    internal: float,
    debt: float,
    repayment_type: str,
    fixed_rate: float,
    maturity: int,
) -> dict[str, Any]:
    return {
        "Scenario ID": scenario_id,
        "Scenario Name": name,
        "Funding Mix": {"Internal Cash / Equity %": internal, "Debt %": debt, "Alternative Funding %": 0.0},
        "Additional Uses": {"Initial Working Capital": 0.0, "Contingency": 0.0, "Other Uses": 0.0},
        "Alternative Funding": [{
            "Applicable": False,
            "Type": "Grant / Subsidy",
            "Amount": 0.0,
            "Timing": "Y0",
            "Cost / Rate": 0.0,
            "Repayment Required": "No",
            "Source / Basis": "",
            "Comment": "",
        }],
        "Debt Terms": {
            "Interest Rate Type": "Fixed",
            "Fixed Interest Rate": fixed_rate,
            "Reference / Base Rate": 0.045,
            "Credit Spread": 0.027,
            "Facility Start / Availability Date": date(2026, 10, 1),
            "Maturity Year": maturity,
            "Grace Period Years": 2 if scenario_id == "mixed" else 1,
            "Repayment Type": repayment_type,
            "Arrangement Fee": 0.0125 if debt else 0.0,
            "Commitment Fee": 0.003 if debt else 0.0,
            "Commitment Fee Applicable": bool(debt),
            "Prepayment Allowed": True,
            "Interest Tax Shield Availability": "Project taxable income only",
        },
        "Custom Debt Schedule": [{"Period": period, "Drawdown": 0.0, "Principal Repayment": 0.0} for period in FINANCING_PERIODS],
        "Covenants": _default_covenants(),
        "Equity Discount Rate Override": {"Enabled": False, "Rate": 0.0, "Rationale": ""},
    }


def default_financing_inputs() -> dict[str, Any]:
    return {
        "schema_version": FINANCING_SCHEMA_VERSION,
        "selected_scenario_id": "mixed",
        "scenarios": {
            scenario_id: _default_scenario(scenario_id, name, internal, debt, repayment, rate, maturity)
            for scenario_id, name, internal, debt, repayment, rate, maturity in FUNDING_SCENARIOS
        },
    }


def ensure_financing_inputs(value: Any) -> dict[str, Any]:
    defaults = default_financing_inputs()
    if not isinstance(value, dict) or value.get("schema_version") != FINANCING_SCHEMA_VERSION:
        return defaults
    result = deepcopy(value)
    result.setdefault("selected_scenario_id", "mixed")
    result.setdefault("scenarios", {})
    for scenario_id, default_scenario in defaults["scenarios"].items():
        existing = result["scenarios"].get(scenario_id)
        if not isinstance(existing, dict):
            result["scenarios"][scenario_id] = default_scenario
            continue
        for key, default_value in default_scenario.items():
            existing.setdefault(key, deepcopy(default_value))
        if scenario_id == "high_debt" and existing.get("Scenario Name") == "High Debt":
            existing["Scenario Name"] = "Debt-Heavy Funding"
        existing.setdefault("Debt Terms", {})
        for key, default_value in default_scenario["Debt Terms"].items():
            existing["Debt Terms"].setdefault(key, deepcopy(default_value))
    if result["selected_scenario_id"] not in result["scenarios"]:
        result["selected_scenario_id"] = "mixed"
    return result


def _investment_uses(model_inputs: dict[str, Any]) -> dict[str, float]:
    implementation_tokens = ("implementation", "integration", "consulting", "data migration", "training")
    transaction_tokens = ("transaction fee", "transaction cost")
    working_capital_tokens = ("working capital",)
    other_tokens = ("contingency", "other use")
    result = {
        "Initial Investment / CAPEX": 0.0,
        "Implementation Costs": 0.0,
        "Transaction Costs": 0.0,
        "Initial Working Capital": 0.0,
        "Contingency / Other Uses": 0.0,
    }
    for line in model_inputs.get("investment", {}).get("uses", []):
        if not bool(line.get("Applicable", True)):
            continue
        name = str(line.get("Investment Component", "")).lower()
        amount = _number(line.get("Amount"))
        if any(token in name for token in transaction_tokens):
            result["Transaction Costs"] += amount
        elif any(token in name for token in working_capital_tokens):
            result["Initial Working Capital"] += amount
        elif any(token in name for token in other_tokens):
            result["Contingency / Other Uses"] += amount
        elif any(token in name for token in implementation_tokens):
            result["Implementation Costs"] += amount
        else:
            result["Initial Investment / CAPEX"] += amount
    return result


def _alternative_totals(lines: list[dict[str, Any]]) -> tuple[float, float, float]:
    non_repayable = 0.0
    for line in lines:
        if not bool(line.get("Applicable", True)):
            continue
        non_repayable += _number(line.get("Amount"))
    return non_repayable, 0.0, 0.0


def _build_debt_schedule(facility: float, terms: dict[str, Any], custom: list[dict[str, Any]]) -> pd.DataFrame:
    rate_type = str(terms.get("Interest Rate Type", "Fixed"))
    all_in_rate = _number(terms.get("Fixed Interest Rate")) if rate_type == "Fixed" else _number(terms.get("Reference / Base Rate")) + _number(terms.get("Credit Spread"))
    maturity = max(1, min(10, int(_number(terms.get("Maturity Year")) or 1)))
    grace = max(0, min(maturity - 1, int(_number(terms.get("Grace Period Years")))))
    repayment_type = str(terms.get("Repayment Type", "Straight-line"))
    custom_by_period = {str(row.get("Period")): row for row in custom}
    repayment_years = list(range(grace + 1, maturity + 1))
    straight_line_payment = facility / len(repayment_years) if repayment_years else facility
    opening = 0.0
    cumulative_drawdown = 0.0
    rows: list[dict[str, Any]] = []
    for index, period in enumerate(FINANCING_PERIODS):
        if repayment_type == "Custom":
            custom_row = custom_by_period.get(period, {})
            requested_drawdown = max(0.0, _number(custom_row.get("Drawdown")))
            requested_repayment = max(0.0, _number(custom_row.get("Principal Repayment")))
        else:
            requested_drawdown = facility if index == 0 else 0.0
            if repayment_type == "Bullet":
                requested_repayment = facility if index == maturity else 0.0
            else:
                requested_repayment = straight_line_payment if index in repayment_years else 0.0
        validation: list[str] = []
        if index > maturity and requested_drawdown > 0:
            validation.append("Drawdown after maturity ignored")
            requested_drawdown = 0.0
        if index > maturity and requested_repayment > 0:
            validation.append("Repayment after maturity ignored")
            requested_repayment = 0.0
        available_commitment = max(0.0, facility - cumulative_drawdown)
        drawdown = min(requested_drawdown, available_commitment)
        if requested_drawdown > available_commitment + 0.01:
            validation.append("Drawdown capped at remaining facility")
        cumulative_drawdown += drawdown
        principal_repayment = min(requested_repayment, opening + drawdown)
        if requested_repayment > opening + drawdown + 0.01:
            validation.append("Repayment capped at outstanding debt")
        closing = max(0.0, opening + drawdown - principal_repayment)
        if repayment_type == "Custom" and index == maturity and closing > 0.01:
            validation.append("Outstanding debt remains at maturity")
        average = 0.0 if index == 0 else (opening + closing) / 2
        interest = average * all_in_rate
        undrawn_commitment = max(0.0, facility - cumulative_drawdown)
        commitment_fee = undrawn_commitment * _number(terms.get("Commitment Fee")) if bool(terms.get("Commitment Fee Applicable")) and index > 0 else 0.0
        arrangement_fee = facility * _number(terms.get("Arrangement Fee")) if index == 0 else 0.0
        financing_fees = arrangement_fee + commitment_fee
        rows.append({
            "Period": period,
            "Opening Debt": opening,
            "Debt Drawdown": drawdown,
            "Principal Repayment": principal_repayment,
            "Closing Debt": closing,
            "Average Debt": average,
            "Cash Interest Expense": interest,
            "Financing Fees": financing_fees,
            "Total Debt Service": principal_repayment + interest,
            "Validation": "; ".join(validation),
        })
        opening = closing
    return pd.DataFrame(rows)


def _metric_source(model: dict[str, Any], metric: str) -> dict[str, float]:
    frame = model["scenario_pnl"].set_index("Metric")
    return {year: _number(frame.at[metric, year]) for year in model["years"]}


def calculate_financing_scenario(
    model: dict[str, Any],
    financing: dict[str, Any],
    scenario_id: str,
) -> dict[str, Any]:
    controlled = ensure_financing_inputs(financing)
    scenario = deepcopy(controlled["scenarios"][scenario_id])
    mix = scenario["Funding Mix"]
    debt_pct = _number(mix.get("Debt %"))
    debt_pct = min(1.0, max(0.0, debt_pct))

    use_components = _investment_uses(model["inputs"])
    pre_fee_uses = sum(use_components.values())
    terms = scenario["Debt Terms"]
    arrangement_rate = _number(terms.get("Arrangement Fee")) if debt_pct > 0 else 0.0
    denominator = 1 - debt_pct * arrangement_rate
    total_uses = pre_fee_uses / denominator if denominator > 0 else pre_fee_uses
    debt_source = total_uses * debt_pct
    arrangement_fee = debt_source * arrangement_rate
    total_uses = pre_fee_uses + arrangement_fee
    non_repayable_alt, repayable_alt, alternative_annual_cost = _alternative_totals(scenario["Alternative Funding"])
    actual_alternative = non_repayable_alt + repayable_alt
    alternative_target = actual_alternative
    internal_source = max(0.0, total_uses - debt_source - actual_alternative)
    impossible_sources = debt_source + actual_alternative > total_uses + 0.01
    total_sources = internal_source + debt_source + actual_alternative
    funding_gap = total_sources - total_uses
    alternative_pct = _ratio(actual_alternative, total_uses) or 0.0
    internal_pct = _ratio(internal_source, total_uses) or 0.0
    mix_total = internal_pct + debt_pct + alternative_pct
    scenario["Funding Mix"] = {
        "Internal Cash / Equity %": internal_pct,
        "Debt %": debt_pct,
        "Alternative Funding %": alternative_pct,
    }

    uses = pd.DataFrame([
        {"Use": "Initial Investment / CAPEX", "Amount": use_components["Initial Investment / CAPEX"], "Type": "Model"},
        {"Use": "Implementation Costs", "Amount": use_components["Implementation Costs"], "Type": "Model"},
        {"Use": "Transaction Costs", "Amount": use_components["Transaction Costs"], "Type": "Model"},
        {"Use": "Initial Working Capital", "Amount": use_components["Initial Working Capital"], "Type": "Model"},
        {"Use": "Contingency / Other Uses", "Amount": use_components["Contingency / Other Uses"], "Type": "Model"},
        {"Use": "Upfront Debt Arrangement Fee", "Amount": arrangement_fee, "Type": "Financing"},
    ])
    source_rows = [
        {"Source": "Internal Cash / Equity", "Amount": internal_source, "Type": "Calculated from mix"},
        {"Source": "Debt", "Amount": debt_source, "Type": "Calculated from mix"},
    ]
    source_rows.extend(
        {"Source": str(line.get("Type", "Other Funding")), "Amount": _number(line.get("Amount")), "Type": "Input line"}
        for line in scenario["Alternative Funding"]
        if bool(line.get("Applicable", True)) and _number(line.get("Amount")) != 0
    )
    sources = pd.DataFrame(source_rows)

    debt_schedule = _build_debt_schedule(debt_source, terms, scenario["Custom Debt Schedule"])
    years = model["years"]
    periods = FINANCING_PERIODS
    scenario_ebit = _metric_source(model, "EBIT")
    scenario_ebitda = _metric_source(model, "EBITDA")
    incremental_ebitda_frame = model["incremental"].set_index("Metric")
    ufcf_by_period = {str(row["Year"]): _number(row["Unlevered Free Cash Flow"]) for _, row in model["cash_flow"].iterrows()}
    unlevered_tax_by_period = {str(row["Year"]): _number(row["Cash Taxes"]) for _, row in model["cash_flow"].iterrows()}
    tax_rate = _number(model["inputs"]["settings"].get("Applicable Tax Rate"))
    maturity = max(1, min(10, int(_number(terms.get("Maturity Year")) or 1)))

    levered_rows: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []
    equity_cash_flows: list[float] = []
    cumulative_equity = 0.0
    covenant_rows: list[dict[str, Any]] = []
    covenant_lookup = {str(row.get("Covenant")): row for row in scenario["Covenants"] if bool(row.get("Applicable", True))}
    repayable_alt_balance = repayable_alt

    for index, period in enumerate(periods):
        debt_row = debt_schedule.iloc[index]
        alt_interest = alternative_annual_cost if 0 < index <= maturity and repayable_alt_balance > 0 else 0.0
        alt_repayment = repayable_alt_balance if index == maturity else 0.0
        if alt_repayment:
            repayable_alt_balance = 0.0
        total_interest = _number(debt_row["Cash Interest Expense"]) + alt_interest
        ebit = scenario_ebit.get(period, 0.0)
        ebt = ebit - total_interest
        levered_tax = max(0.0, ebt * tax_rate)
        net_income = ebt - levered_tax
        if period in years:
            levered_rows.append({"Metric": "EBIT", "Period": period, "Amount": ebit})
            levered_rows.append({"Metric": "Interest Expense", "Period": period, "Amount": -total_interest})
            levered_rows.append({"Metric": "EBT", "Period": period, "Amount": ebt})
            levered_rows.append({"Metric": "Cash / Income Tax", "Period": period, "Amount": -levered_tax})
            levered_rows.append({"Metric": "Net Income", "Period": period, "Amount": net_income})

        ufcf = ufcf_by_period.get(period, 0.0)
        external_inflow = actual_alternative if index == 0 else 0.0
        shield_method = str(terms.get("Interest Tax Shield Availability", "Project taxable income only"))
        if index == 0:
            tax_shield = 0.0
        elif shield_method == "Immediate / Group taxable income available":
            tax_shield = total_interest * tax_rate
        else:
            tax_shield = max(0.0, unlevered_tax_by_period.get(period, 0.0) - levered_tax)
        extra_initial_uses = 0.0
        equity_cash_flow = (
            ufcf
            + _number(debt_row["Debt Drawdown"])
            + external_inflow
            - _number(debt_row["Principal Repayment"])
            - alt_repayment
            - total_interest
            + tax_shield
            - _number(debt_row["Financing Fees"])
            - extra_initial_uses
        )
        cumulative_equity += equity_cash_flow
        equity_cash_flows.append(equity_cash_flow)
        equity_rows.append({
            "Period": period,
            "Unlevered Free Cash Flow": ufcf,
            "Debt Drawdown": _number(debt_row["Debt Drawdown"]),
            "Alternative Funding Inflow": external_inflow,
            "Principal Repayment": _number(debt_row["Principal Repayment"]),
            "Alternative Funding Repayment": alt_repayment,
            "Cash Interest": total_interest,
            "Interest Tax Shield": tax_shield,
            "Financing Fees": _number(debt_row["Financing Fees"]),
            "Other Initial Uses": extra_initial_uses,
            "Equity Cash Flow": equity_cash_flow,
            "Cumulative Equity Cash Flow": cumulative_equity,
        })

        if index == 0:
            continue
        closing_debt = _number(debt_row["Closing Debt"]) + repayable_alt_balance
        debt_service = _number(debt_row["Total Debt Service"]) + alt_interest + alt_repayment
        relevant_ebitda = scenario_ebitda.get(period, 0.0)
        project_ebitda = _number(incremental_ebitda_frame.at["Incremental EBITDA", period]) if period in years else 0.0
        cfads = max(0.0, ufcf + total_interest - tax_shield)
        for covenant_name, covenant in covenant_lookup.items():
            basis = str(covenant.get("Calculation Basis", "Project"))
            available = basis != "Borrower / Company" and covenant_name != "Minimum Cash"
            metric_value: float | None
            if not available:
                metric_value = None
            elif covenant_name == "Net Debt / EBITDA":
                metric_value = _ratio(closing_debt, project_ebitda if basis == "Project" else relevant_ebitda)
            elif covenant_name == "Interest Coverage":
                metric_value = _ratio(project_ebitda if basis == "Project" else relevant_ebitda, total_interest)
            elif covenant_name == "DSCR":
                metric_value = _ratio(cfads, debt_service)
            else:
                metric_value = None
            limit = _number(covenant.get("Limit"))
            direction = str(covenant.get("Direction", "Minimum"))
            if debt_source <= 0 and repayable_alt <= 0 and covenant_name != "Minimum Cash":
                status, headroom = "N/A", None
            elif metric_value is None:
                status, headroom = "Not Available", None
            else:
                headroom = limit - metric_value if direction == "Maximum" else metric_value - limit
                status = "OK" if headroom >= 0 else "Breach"
            covenant_rows.append({"Period": period, "Covenant": covenant_name, "Calculation Basis": basis, "Metric Value": metric_value, "Covenant Limit": limit, "Headroom": headroom, "Status": status})

    equity_override = scenario["Equity Discount Rate Override"]
    valid_equity_override = bool(equity_override.get("Enabled")) and bool(str(equity_override.get("Rationale", "")).strip())
    equity_discount_rate = _number(equity_override.get("Rate")) if valid_equity_override else _number(model["returns"].get("Cost of Equity"))
    covenant_table = pd.DataFrame(covenant_rows)
    applicable_statuses = covenant_table["Status"].tolist() if not covenant_table.empty else []
    dscr_values = covenant_table.loc[(covenant_table["Covenant"] == "DSCR") & covenant_table["Metric Value"].notna(), "Metric Value"].tolist() if not covenant_table.empty else []
    leverage_values = covenant_table.loc[(covenant_table["Covenant"] == "Net Debt / EBITDA") & covenant_table["Metric Value"].notna(), "Metric Value"].tolist() if not covenant_table.empty else []
    coverage_values = covenant_table.loc[(covenant_table["Covenant"] == "Interest Coverage") & covenant_table["Metric Value"].notna(), "Metric Value"].tolist() if not covenant_table.empty else []
    positive_closing = debt_schedule.loc[debt_schedule["Closing Debt"] > 0.01, "Period"].tolist()
    fully_repaid = "Not within schedule" if positive_closing and positive_closing[-1] == "Y10" else (f"Y{int(positive_closing[-1][1:]) + 1}" if positive_closing else ("N/A" if debt_source <= 0 else "Y0"))

    initial_equity_contribution = max(0.0, -equity_cash_flows[0]) if equity_cash_flows else 0.0
    additional_equity_support = sum(max(0.0, -value) for value in equity_cash_flows[1:])
    total_equity_contributions = initial_equity_contribution + additional_equity_support
    sustaining_capex = sum(_number(model["inputs"].get("investment", {}).get("Sustaining CAPEX", {}).get(year)) for year in years)

    metrics = {
        "Project NPV": _number(model["returns"].get("Project NPV")),
        "Project IRR": model["returns"].get("Project IRR"),
        "Total Funding Requirement": total_uses,
        "Equity Required": total_equity_contributions,
        "Initial Equity Contribution": initial_equity_contribution,
        "Additional Equity Support": additional_equity_support,
        "Total Equity Contributions": total_equity_contributions,
        "Debt Funding": debt_source,
        "Alternative Funding Target": alternative_target,
        "Equity IRR": _irr(equity_cash_flows),
        "Equity NPV": _npv(equity_discount_rate, equity_cash_flows),
        "Equity Payback": _payback(equity_cash_flows),
        "Equity Discount Rate": equity_discount_rate,
        "Interest Cost": float(debt_schedule["Cash Interest Expense"].sum()) + alternative_annual_cost * maturity,
        "Peak Debt": float(debt_schedule["Closing Debt"].max()) + repayable_alt,
        "Minimum DSCR": min(dscr_values) if dscr_values else None,
        "Peak Net Debt / EBITDA": max(leverage_values) if leverage_values else None,
        "Minimum Interest Coverage": min(coverage_values) if coverage_values else None,
        "Covenant Breaches": sum(status == "Breach" for status in applicable_statuses),
        "Debt Fully Repaid Year": fully_repaid,
        "Cumulative Equity Cash Flow": cumulative_equity,
        "Funding Mix Total": mix_total,
        "Total Uses": total_uses,
        "Total Sources": total_sources,
        "Funding Gap / Excess Funding": funding_gap,
        "Funding Inputs Valid": not impossible_sources,
        "Sustaining CAPEX Over Forecast": sustaining_capex,
        "All-in Interest Rate": _number(terms.get("Fixed Interest Rate")) if str(terms.get("Interest Rate Type")) == "Fixed" else _number(terms.get("Reference / Base Rate")) + _number(terms.get("Credit Spread")),
    }
    return {
        "scenario": scenario,
        "uses": uses,
        "sources": sources,
        "debt_schedule": debt_schedule,
        "covenants": covenant_table,
        "levered_pnl": pd.DataFrame(levered_rows),
        "equity_cash_flow": pd.DataFrame(equity_rows),
        "metrics": metrics,
    }


def calculate_all_financing_scenarios(model: dict[str, Any], financing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controlled = ensure_financing_inputs(financing)
    return {
        scenario_id: calculate_financing_scenario(model, controlled, scenario_id)
        for scenario_id in controlled["scenarios"]
    }
