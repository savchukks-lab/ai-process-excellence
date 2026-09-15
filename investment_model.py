from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite
from typing import Any

import pandas as pd


INVESTMENT_YEARS = [f"Y{year}" for year in range(1, 11)]
PERCENT_ROWS = {"Gross Margin %", "EBITDA Margin %", "EBIT Margin %"}


def investment_demo_cases() -> list[dict[str, Any]]:
    return [
        {
            "Case ID": "INV-2001",
            "Investment Case Name": "Regional Capacity Expansion",
            "Investment Type": "Capacity",
            "Business Unit / Market": "Consumer Health / Region A",
            "Owner": "Daniel Ortiz",
            "Status": "Model in Progress",
            "Last Updated": "2026-09-12",
            "Profile": "growth",
        },
        {
            "Case ID": "INV-2002",
            "Investment Case Name": "Distribution Automation Program",
            "Investment Type": "Efficiency",
            "Business Unit / Market": "Supply Operations / Region B",
            "Owner": "Daniel Ortiz",
            "Status": "Draft",
            "Last Updated": "2026-09-10",
            "Profile": "saving",
        },
    ]


def _series(start: float, growth: float = 0.0) -> dict[str, float]:
    return {year: start * ((1 + growth) ** index) for index, year in enumerate(INVESTMENT_YEARS)}


def default_investment_inputs(case: dict[str, Any]) -> dict[str, Any]:
    profile = str(case.get("Profile", "growth"))
    growth_case = profile == "growth"
    inputs: dict[str, Any] = {
        "settings": {
            "Case Name": str(case.get("Investment Case Name", "New Investment Case")),
            "Investment Type": str(case.get("Investment Type", "Growth")),
            "Benefit Type": "Revenue Growth" if growth_case else "Cost Saving",
            "Currency": "USD",
            "Base Year": 2026,
            "Forecast Horizon": 10,
            "Investment Start Date": date(2026, 10, 1),
            "Operational Start Date": date(2027, 7, 1) if growth_case else date(2027, 4, 1),
            "Tax Rate": 0.24,
            "Inflation Rate": 0.025,
            "Model Basis": "Nominal",
            "Model Version": "1.0",
            "As Of Date": date(2026, 9, 15),
        },
        "capital": {
            "Risk-Free Rate": 0.042,
            "Beta": 0.95 if growth_case else 0.85,
            "Equity Risk Premium": 0.055,
            "Country Risk Premium": 0.01,
            "Pre-tax Cost of Debt": 0.062,
            "Target Debt %": 0.35,
            "Target Equity %": 0.65,
            "Corporate Hurdle Rate": 0.10,
            "Existing Business ROIC": 0.145,
            "Marginal Reinvestment Return": 0.118 if growth_case else 0.105,
            "Treasury / Cash Yield": 0.04,
            "Source": "FY27 corporate planning assumptions",
            "Effective Date": "2026-07-01",
            "Rationale": "Management reference rates for capital allocation screening.",
        },
        "investment": {
            "Initial Investment": 38_000_000.0 if growth_case else 29_000_000.0,
            "Useful Life": 10,
            "Sustaining CAPEX": _series(350_000.0 if growth_case else 220_000.0, 0.02),
            "DSO": 52.0 if growth_case else 46.0,
            "DIO": 64.0 if growth_case else 42.0,
            "DPO": 48.0 if growth_case else 45.0,
        },
    }

    baseline_volume = _series(720_000.0 if growth_case else 500_000.0, 0.025 if growth_case else 0.01)
    baseline_price = _series(64.0 if growth_case else 120.0, 0.02)
    utilization = {year: value for year, value in zip(INVESTMENT_YEARS, [0.20, 0.42, 0.62, 0.76, 0.84, 0.88, 0.90, 0.90, 0.90, 0.90])}
    if not growth_case:
        utilization = {year: 0.0 for year in INVESTMENT_YEARS}
    inputs["revenue"] = {
        "Baseline Volume": baseline_volume,
        "Incremental Capacity": {year: 360_000.0 if growth_case else 0.0 for year in INVESTMENT_YEARS},
        "Capacity Utilization %": utilization,
        "Baseline Price": baseline_price,
        "Price Growth %": {year: 0.02 for year in INVESTMENT_YEARS},
    }
    inputs["savings"] = {
        "Baseline Cost": _series(15_000_000.0 if growth_case else 22_000_000.0, 0.025),
        "Cost Saving %": {year: (0.01 if growth_case else rate) for year, rate in zip(INVESTMENT_YEARS, [0.04, 0.08, 0.12, 0.15, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16])},
        "Productivity Gain %": {year: (0.0 if growth_case else 0.03) for year in INVESTMENT_YEARS},
        "Avoided / Reduced FTE": {year: (0.0 if growth_case else min(18.0, 4.0 + index * 2.0)) for index, year in enumerate(INVESTMENT_YEARS)},
        "Cost per FTE": _series(95_000.0, 0.025),
        "Other Savings": _series(100_000.0 if growth_case else 450_000.0, 0.02),
        "Realization %": {year: (0.75 if index == 0 else 0.90 if index == 1 else 0.95) for index, year in enumerate(INVESTMENT_YEARS)},
    }
    inputs["opex"] = {
        "Variable Cost per Unit": _series(29.0 if growth_case else 52.0, 0.02),
        "Fixed Operating Cost": _series(2_900_000.0 if growth_case else 2_400_000.0, 0.025),
        "Personnel Cost": _series(4_400_000.0 if growth_case else 6_200_000.0, 0.025),
        "Maintenance": _series(850_000.0 if growth_case else 1_050_000.0, 0.025),
        "Utilities / Facilities": _series(620_000.0 if growth_case else 780_000.0, 0.025),
        "IT / Licenses": _series(380_000.0 if growth_case else 900_000.0, 0.025),
        "Other OPEX": _series(500_000.0 if growth_case else 650_000.0, 0.025),
    }
    return inputs


def _value(series: dict[str, Any], year: str) -> float:
    try:
        value = float(series.get(year, 0.0))
        return value if isfinite(value) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if abs(denominator) > 1e-12 else 0.0


def _payback(cash_flows: list[float]) -> float | None:
    cumulative = cash_flows[0]
    if cumulative >= 0:
        return 0.0
    for year_index, cash_flow in enumerate(cash_flows[1:], start=1):
        previous = cumulative
        cumulative += cash_flow
        if cumulative >= 0 and cash_flow > 0:
            return (year_index - 1) + abs(previous) / cash_flow
    return None


def _npv(rate: float, cash_flows: list[float]) -> float:
    return sum(value / ((1 + rate) ** index) for index, value in enumerate(cash_flows))


def _irr(cash_flows: list[float]) -> float | None:
    if not cash_flows or min(cash_flows) >= 0 or max(cash_flows) <= 0:
        return None
    low, high = -0.99, 10.0
    low_value, high_value = _npv(low, cash_flows), _npv(high, cash_flows)
    if low_value * high_value > 0:
        return None
    for _ in range(200):
        midpoint = (low + high) / 2
        value = _npv(midpoint, cash_flows)
        if abs(value) < 0.01:
            return midpoint
        if low_value * value <= 0:
            high = midpoint
            high_value = value
        else:
            low = midpoint
            low_value = value
    return (low + high) / 2


def _pnl_frame(rows: dict[str, dict[str, float]], years: list[str]) -> pd.DataFrame:
    order = [
        "Revenue", "COGS", "Gross Profit", "Gross Margin %", "Personnel",
        "Other Operating Expenses", "EBITDA", "EBITDA Margin %",
        "Depreciation & Amortization", "EBIT", "EBIT Margin %",
    ]
    return pd.DataFrame([{"Metric": metric, **{year: rows[metric][year] for year in years}} for metric in order])


def calculate_investment_model(raw_inputs: dict[str, Any]) -> dict[str, Any]:
    inputs = deepcopy(raw_inputs)
    settings = inputs["settings"]
    horizon = 5 if int(settings.get("Forecast Horizon", 10)) == 5 else 10
    years = INVESTMENT_YEARS[:horizon]
    tax_rate = min(1.0, max(0.0, float(settings.get("Tax Rate", 0.0))))
    benefit_type = str(settings.get("Benefit Type", "Mixed"))
    revenue_enabled = benefit_type in {"Revenue Growth", "Mixed"}
    savings_enabled = benefit_type in {"Cost Saving", "Mixed"}

    capital = inputs["capital"]
    cost_of_equity = (
        float(capital.get("Risk-Free Rate", 0.0))
        + float(capital.get("Beta", 0.0)) * float(capital.get("Equity Risk Premium", 0.0))
        + float(capital.get("Country Risk Premium", 0.0))
    )
    after_tax_debt = float(capital.get("Pre-tax Cost of Debt", 0.0)) * (1 - tax_rate)
    debt_weight = float(capital.get("Target Debt %", 0.0))
    equity_weight = float(capital.get("Target Equity %", 0.0))
    wacc = cost_of_equity * equity_weight + after_tax_debt * debt_weight

    revenue_inputs = inputs["revenue"]
    saving_inputs = inputs["savings"]
    opex_inputs = inputs["opex"]
    investment = inputs["investment"]
    initial_investment = float(investment.get("Initial Investment", 0.0))
    useful_life = max(1, int(investment.get("Useful Life", 10)))

    baseline_rows = {metric: {} for metric in ["Revenue", "COGS", "Gross Profit", "Gross Margin %", "Personnel", "Other Operating Expenses", "EBITDA", "EBITDA Margin %", "Depreciation & Amortization", "EBIT", "EBIT Margin %"]}
    scenario_rows = deepcopy(baseline_rows)
    driver_rows: dict[str, dict[str, float]] = {name: {} for name in [
        "Baseline Volume", "Incremental Capacity", "Capacity Utilization %", "Incremental Volume",
        "Baseline Price", "Price Growth %", "Scenario Price", "Baseline Revenue", "Incremental Revenue",
        "Total Scenario Revenue", "Baseline Cost", "Cost Saving %", "Productivity Gain %",
        "Avoided / Reduced FTE", "Cost per FTE", "Other Savings", "Realization %", "Gross Savings", "Net Savings",
    ]}
    baseline_nwc: dict[str, float] = {}
    scenario_nwc: dict[str, float] = {}

    for year in years:
        base_volume = _value(revenue_inputs["Baseline Volume"], year)
        capacity = _value(revenue_inputs["Incremental Capacity"], year) if revenue_enabled else 0.0
        utilization = min(1.0, max(0.0, _value(revenue_inputs["Capacity Utilization %"], year)))
        incremental_volume = capacity * utilization
        base_price = _value(revenue_inputs["Baseline Price"], year)
        price_growth = _value(revenue_inputs["Price Growth %"], year)
        scenario_price = base_price * (1 + price_growth)
        baseline_revenue = base_volume * base_price
        incremental_revenue = incremental_volume * scenario_price
        scenario_revenue = baseline_revenue + incremental_revenue

        baseline_cost = _value(saving_inputs["Baseline Cost"], year)
        cost_saving_rate = max(0.0, _value(saving_inputs["Cost Saving %"], year)) if savings_enabled else 0.0
        productivity = max(0.0, _value(saving_inputs["Productivity Gain %"], year)) if savings_enabled else 0.0
        avoided_fte = max(0.0, _value(saving_inputs["Avoided / Reduced FTE"], year)) if savings_enabled else 0.0
        cost_per_fte = _value(saving_inputs["Cost per FTE"], year)
        other_savings = _value(saving_inputs["Other Savings"], year) if savings_enabled else 0.0
        realization = min(1.0, max(0.0, _value(saving_inputs["Realization %"], year)))
        gross_savings = baseline_cost * (cost_saving_rate + productivity) + avoided_fte * cost_per_fte + other_savings
        net_savings = gross_savings * realization

        variable_cost = _value(opex_inputs["Variable Cost per Unit"], year)
        baseline_cogs = base_volume * variable_cost
        scenario_cogs = (base_volume + incremental_volume) * variable_cost
        personnel = _value(opex_inputs["Personnel Cost"], year)
        other_opex = sum(_value(opex_inputs[name], year) for name in ["Fixed Operating Cost", "Maintenance", "Utilities / Facilities", "IT / Licenses", "Other OPEX"])
        baseline_da = baseline_revenue * 0.025
        scenario_da = baseline_da + initial_investment / useful_life

        baseline_gp = baseline_revenue - baseline_cogs
        baseline_ebitda = baseline_gp - personnel - other_opex
        baseline_ebit = baseline_ebitda - baseline_da
        scenario_gp = scenario_revenue - scenario_cogs
        scenario_other_opex = other_opex - net_savings
        scenario_ebitda = scenario_gp - personnel - scenario_other_opex
        scenario_ebit = scenario_ebitda - scenario_da

        values = {
            "Revenue": (baseline_revenue, scenario_revenue), "COGS": (baseline_cogs, scenario_cogs),
            "Gross Profit": (baseline_gp, scenario_gp),
            "Gross Margin %": (_safe_ratio(baseline_gp, baseline_revenue), _safe_ratio(scenario_gp, scenario_revenue)),
            "Personnel": (personnel, personnel), "Other Operating Expenses": (other_opex, scenario_other_opex),
            "EBITDA": (baseline_ebitda, scenario_ebitda),
            "EBITDA Margin %": (_safe_ratio(baseline_ebitda, baseline_revenue), _safe_ratio(scenario_ebitda, scenario_revenue)),
            "Depreciation & Amortization": (baseline_da, scenario_da), "EBIT": (baseline_ebit, scenario_ebit),
            "EBIT Margin %": (_safe_ratio(baseline_ebit, baseline_revenue), _safe_ratio(scenario_ebit, scenario_revenue)),
        }
        for metric, (baseline_value, scenario_value) in values.items():
            baseline_rows[metric][year] = baseline_value
            scenario_rows[metric][year] = scenario_value
        for metric, value in {
            "Baseline Volume": base_volume, "Incremental Capacity": capacity, "Capacity Utilization %": utilization,
            "Incremental Volume": incremental_volume, "Baseline Price": base_price,
            "Price Growth %": price_growth, "Scenario Price": scenario_price,
            "Baseline Revenue": baseline_revenue, "Incremental Revenue": incremental_revenue,
            "Total Scenario Revenue": scenario_revenue, "Baseline Cost": baseline_cost,
            "Cost Saving %": cost_saving_rate, "Productivity Gain %": productivity,
            "Avoided / Reduced FTE": avoided_fte, "Cost per FTE": cost_per_fte,
            "Other Savings": other_savings, "Realization %": realization,
            "Gross Savings": gross_savings, "Net Savings": net_savings,
        }.items():
            driver_rows[metric][year] = value

        dso, dio, dpo = (float(investment.get(name, 0.0)) for name in ["DSO", "DIO", "DPO"])
        baseline_nwc[year] = baseline_revenue * dso / 365 + baseline_cogs * dio / 365 - baseline_cogs * dpo / 365
        scenario_nwc[year] = scenario_revenue * dso / 365 + scenario_cogs * dio / 365 - scenario_cogs * dpo / 365

    baseline_pnl = _pnl_frame(baseline_rows, years)
    scenario_pnl = _pnl_frame(scenario_rows, years)
    incremental_metrics = ["Revenue", "Gross Profit", "EBITDA", "EBIT"]
    incremental = pd.DataFrame([
        {"Metric": f"Incremental {metric}", **{year: scenario_rows[metric][year] - baseline_rows[metric][year] for year in years}}
        for metric in incremental_metrics
    ])

    working_rows = []
    previous_incremental_nwc = 0.0
    change_nwc: dict[str, float] = {}
    for year in years:
        revenue = scenario_rows["Revenue"][year]
        cogs = scenario_rows["COGS"][year]
        dso, dio, dpo = (float(investment.get(name, 0.0)) for name in ["DSO", "DIO", "DPO"])
        ar, inventory_value, ap = revenue * dso / 365, cogs * dio / 365, cogs * dpo / 365
        nwc = ar + inventory_value - ap
        incremental_nwc = scenario_nwc[year] - baseline_nwc[year]
        change_nwc[year] = incremental_nwc - previous_incremental_nwc
        previous_incremental_nwc = incremental_nwc
        working_rows.append({"Year": year, "Accounts Receivable": ar, "Inventory": inventory_value, "Accounts Payable": ap, "Net Working Capital": nwc, "Change in NWC": change_nwc[year]})
    working_capital = pd.DataFrame(working_rows)

    cash_flow_rows = []
    cash_flows = [-initial_investment]
    discounted_cash_flows = [-initial_investment]
    cumulative = -initial_investment
    cumulative_discounted = -initial_investment
    cash_flow_rows.append({"Year": "Y0", "Incremental EBIT": 0.0, "Cash Taxes": 0.0, "D&A": 0.0, "CAPEX": initial_investment, "Change in NWC": 0.0, "Unlevered Free Cash Flow": -initial_investment, "Discount Factor": 1.0, "Present Value of FCF": -initial_investment, "Cumulative FCF": cumulative, "Cumulative Discounted FCF": cumulative_discounted})
    sustaining = investment.get("Sustaining CAPEX", {})
    for index, year in enumerate(years, start=1):
        incremental_ebit = scenario_rows["EBIT"][year] - baseline_rows["EBIT"][year]
        taxes = max(0.0, incremental_ebit * tax_rate)
        incremental_da = scenario_rows["Depreciation & Amortization"][year] - baseline_rows["Depreciation & Amortization"][year]
        capex = _value(sustaining, year)
        ufcf = incremental_ebit - taxes + incremental_da - capex - change_nwc[year]
        discount_factor = 1 / ((1 + wacc) ** index)
        pv = ufcf * discount_factor
        cash_flows.append(ufcf)
        discounted_cash_flows.append(pv)
        cumulative += ufcf
        cumulative_discounted += pv
        cash_flow_rows.append({"Year": year, "Incremental EBIT": incremental_ebit, "Cash Taxes": taxes, "D&A": incremental_da, "CAPEX": capex, "Change in NWC": change_nwc[year], "Unlevered Free Cash Flow": ufcf, "Discount Factor": discount_factor, "Present Value of FCF": pv, "Cumulative FCF": cumulative, "Cumulative Discounted FCF": cumulative_discounted})
    cash_flow = pd.DataFrame(cash_flow_rows)
    project_npv = sum(discounted_cash_flows)
    project_irr = _irr(cash_flows)
    payback = _payback(cash_flows)
    discounted_payback = _payback(discounted_cash_flows)
    profitability_index = (project_npv + initial_investment) / initial_investment if initial_investment else 0.0
    returns = {
        "Project NPV": project_npv, "Project IRR": project_irr, "Payback Period": payback,
        "Discounted Payback": discounted_payback, "Profitability Index": profitability_index,
        "Cumulative Unlevered FCF": cumulative, "WACC": wacc, "Cost of Equity": cost_of_equity,
        "After-tax Cost of Debt": after_tax_debt,
    }
    return {
        "inputs": inputs, "years": years, "drivers": driver_rows, "baseline_pnl": baseline_pnl,
        "scenario_pnl": scenario_pnl, "incremental": incremental, "working_capital": working_capital,
        "cash_flow": cash_flow, "returns": returns,
        "capital_structure_valid": abs(debt_weight + equity_weight - 1.0) < 0.0001,
    }
