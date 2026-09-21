from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite
from typing import Any

import pandas as pd

SCHEMA_VERSION = 2
INVESTMENT_YEARS = [f"Y{i}" for i in range(1, 11)]
PERCENT_ROWS = {"Gross Margin %", "EBITDA Margin %", "EBIT Margin %"}
CASE_ARCHETYPES = ["Capacity Expansion / New Production Line", "Digital / AI / Software Investment", "Business Acquisition"]
VALUE_CREATION_DRIVERS = ["Revenue Growth", "Cost Reduction", "Working Capital Improvement", "Asset / CAPEX Avoidance"]


def investment_demo_cases() -> list[dict[str, Any]]:
    return [
        {"Case ID": "INV-2001", "Investment Case Name": "Regional Capacity Expansion", "Case Archetype": CASE_ARCHETYPES[0], "Investment Type": "Capacity Expansion", "Business Unit / Market": "Consumer Health / Region A", "Owner": "Daniel Ortiz", "Status": "Model in Progress", "Last Updated": "2026-09-12", "Profile": "capacity"},
        {"Case ID": "INV-2002", "Investment Case Name": "Distribution Automation Program", "Case Archetype": CASE_ARCHETYPES[1], "Investment Type": "Digital / AI / Software", "Business Unit / Market": "Supply Operations / Region B", "Owner": "Daniel Ortiz", "Status": "Draft", "Last Updated": "2026-09-10", "Profile": "digital"},
    ]


def archetype_default_drivers(archetype: str) -> list[str]:
    if archetype == CASE_ARCHETYPES[1]: return ["Cost Reduction"]
    if archetype == CASE_ARCHETYPES[2]: return ["Revenue Growth", "Cost Reduction", "Working Capital Improvement"]
    return ["Revenue Growth", "Working Capital Improvement"]


def _series(start: float, growth: float = 0.0) -> dict[str, float]:
    return {y: start * (1 + growth) ** i for i, y in enumerate(INVESTMENT_YEARS)}


def _annual(values: list[float]) -> dict[str, float]:
    values = (values + [values[-1] if values else 0.0] * 10)[:10]
    return dict(zip(INVESTMENT_YEARS, map(float, values)))


def _uses(archetype: str) -> list[dict[str, Any]]:
    if archetype == CASE_ARCHETYPES[1]:
        rows = [
            ("Software", 3_200_000, "Initial CAPEX", "Vendor quotation", "Initial platform licenses and configuration"),
            ("Integration", 2_000_000, "Implementation Costs", "IT implementation estimate", "Core-system and workflow integration"),
            ("Consulting", 1_400_000, "Implementation Costs", "Transformation estimate", "Design and implementation support"),
            ("Data Migration", 1_000_000, "Implementation Costs", "IT workplan", "Historical data preparation and migration"),
            ("Training", 900_000, "Implementation Costs", "HR / transformation estimate", "Role-based adoption and training program"),
            ("Other", 500_000, "Contingency / Other Uses", "Management contingency", "Controlled implementation contingency"),
        ]
    elif archetype == CASE_ARCHETYPES[2]:
        rows = [
            ("Purchase Price / Enterprise Value", 62_000_000, "Initial CAPEX", "Indicative valuation", "Current transaction value assumption"),
            ("Transaction Fees", 2_800_000, "Transaction Costs", "Advisor estimate", "Legal, diligence and advisory fees"),
            ("Integration Costs", 5_500_000, "Implementation Costs", "Integration office estimate", "Systems, organization and process integration"),
        ]
    else:
        rows = [
            ("Equipment", 22_000_000, "Initial CAPEX", "Vendor quotation", "Production equipment and installation"),
            ("Construction", 7_500_000, "Initial CAPEX", "Engineering estimate", "Facility modification and utilities"),
            ("Implementation", 3_000_000, "Implementation Costs", "Program workplan", "Commissioning and operating readiness"),
            ("Integration", 1_500_000, "Implementation Costs", "IT implementation estimate", "Manufacturing and planning-system integration"),
            ("Other", 1_000_000, "Contingency / Other Uses", "Management contingency", "Controlled delivery contingency"),
        ]
    return [{"Applicable": True, "Investment Component": n, "Funding Use Type": funding_type, "Amount": v, "Timing": "Before operational start", "Source / Basis": source, "Comment / Rationale": comment} for n, v, funding_type, source, comment in rows]


def _savings(archetype: str) -> list[dict[str, Any]]:
    if archetype == CASE_ARCHETYPES[1]:
        rows = [
            ("Personnel", 8_500_000, "Process automation", 3_100_000, .75, "Non-Manufacturing Personnel · Operations"),
            ("Logistics", 6_200_000, "Routing optimization", 900_000, .8, "Non-Manufacturing OPEX · Other Fixed Overhead"),
            ("IT", 4_000_000, "Application consolidation", 650_000, .7, "Non-Manufacturing OPEX · Software Licenses"),
        ]
    elif archetype == CASE_ARCHETYPES[2]:
        rows = [
            ("Procurement", 18_000_000, "Combined purchasing scale", 2_000_000, .6, "Manufacturing COGS · Direct Materials"),
            ("Personnel", 14_000_000, "Shared-service consolidation", 2_600_000, .55, "Non-Manufacturing Personnel · Operations"),
            ("Logistics", 9_000_000, "Network consolidation", 1_100_000, .5, "Non-Manufacturing OPEX · Other Fixed Overhead"),
        ]
    else:
        rows = [("Manufacturing", 15_000_000, "Yield and line efficiency", 650_000, .65, "Manufacturing COGS · Direct Materials")]
    return [{"Applicable": True, "Category": c, "Baseline Cost / Cost Pool": p, "Saving Mechanism": m, "Cost Line Mapping": mapping, "Gross Run-rate Saving": g, "Realization %": r, "Ramp Profile": "2-year ramp", "Custom Y1 Ramp %": 1/3, "Custom Y2 Ramp %": 2/3, "Custom Y3+ Ramp %": 1.0, "Realized Saving": g*r, "Source / Basis": "Functional estimate", "Comment": "Annual run-rate at maturity"} for c,p,m,g,r,mapping in rows]


def _costs(archetype: str) -> dict[str, list[dict[str, Any]]]:
    digital, acquisition = archetype == CASE_ARCHETYPES[1], archetype == CASE_ARCHETYPES[2]
    baseline_volume = 720_000.0
    if digital:
        manufacturing_cogs = [
            {"Applicable": True, "Cost Line": "Variable Manufacturing Overhead", "Cost Behavior": "Fixed / step-fixed — annual", "Baseline Input": 1_100_000, "Scenario Input": 1_650_000, "Annual Growth %": .02, "Source / Basis": "Operations estimate", "Comment": "Usage-based cloud and processing cost"},
        ]
    elif acquisition:
        manufacturing_cogs = [
            {"Applicable": True, "Cost Line": "Direct Materials", "Cost Behavior": "Fixed / step-fixed — annual", "Baseline Input": 18_432_000, "Scenario Input": 18_432_000, "Annual Growth %": .02, "Source / Basis": "Target diligence", "Comment": "Payable-bearing material and product cost"},
        ]
    else:
        manufacturing_cogs = [
            {"Applicable": True, "Cost Line": "Direct Materials", "Cost Behavior": "Variable — per unit", "Baseline Input": 14_000_000 / baseline_volume, "Scenario Input": 14_000_000 / baseline_volume, "Annual Growth %": .02, "Source / Basis": "Operations estimate", "Comment": "Payable-bearing material and product cost"},
            {"Applicable": True, "Cost Line": "Direct Labor", "Cost Behavior": "Fixed / step-fixed — annual", "Baseline Input": 3_200_000, "Scenario Input": 3_350_000, "Annual Growth %": .025, "Source / Basis": "Manufacturing plan", "Comment": "Production labor; step-fixed within planned capacity"},
            {"Applicable": True, "Cost Line": "Variable Manufacturing Overhead", "Cost Behavior": "Variable — per unit", "Baseline Input": 1_800_000 / baseline_volume, "Scenario Input": 1_800_000 / baseline_volume, "Annual Growth %": .02, "Source / Basis": "Manufacturing plan", "Comment": "Utilities and other activity-linked manufacturing overhead"},
            {"Applicable": True, "Cost Line": "Fixed Manufacturing Overhead", "Cost Behavior": "Fixed / step-fixed — annual", "Baseline Input": 1_880_000, "Scenario Input": 2_000_000, "Annual Growth %": .025, "Source / Basis": "Manufacturing plan", "Comment": "Fixed factory overhead within the relevant range"},
        ]
    return {
        "manufacturing_cogs": manufacturing_cogs,
        "non_manufacturing_personnel": [
            {"Applicable": True, "Cost Line": "Operations", "Baseline Y1": 6_200_000 if digital else 4_400_000, "Scenario Y1": 6_000_000 if digital else 4_900_000, "Annual Growth %": .025, "Source / Basis": "Operating plan", "Comment": "Relevant-scope personnel"},
            {"Applicable": acquisition, "Cost Line": "Other Personnel", "Baseline Y1": 1_500_000, "Scenario Y1": 5_200_000, "Annual Growth %": .025, "Source / Basis": "Target diligence", "Comment": "Target organization"}],
        "non_manufacturing_opex": [
            {"Applicable": True, "Cost Line": "Maintenance Contracts", "Baseline Y1": 1_200_000, "Scenario Y1": 1_450_000 if digital else 1_650_000, "Annual Growth %": .025, "Source / Basis": "Supplier estimate", "Comment": "Annual service envelope"},
            {"Applicable": True, "Cost Line": "Software Licenses", "Baseline Y1": 500_000, "Scenario Y1": 800_000 if digital else 550_000, "Annual Growth %": .025, "Source / Basis": "Commercial proposal", "Comment": "Fixed recurring licenses"},
            {"Applicable": True, "Cost Line": "Other Fixed Overhead", "Baseline Y1": 2_800_000, "Scenario Y1": 3_000_000, "Annual Growth %": .025, "Source / Basis": "Operating plan", "Comment": "Relevant fixed overhead"}]}


def _cost_schedules(
    costs: dict[str, list[dict[str, Any]]],
    baseline_volumes: dict[str, float] | None = None,
    scenario_volumes: dict[str, float] | None = None,
) -> dict[str, dict[str, dict[str, float]]]:
    schedules: dict[str, dict[str, dict[str, float]]] = {}
    for group, rows in costs.items():
        def annual_value(row: dict[str, Any], input_name: str, year: str, index: int) -> float:
            growth = (1 + float(row.get("Annual Growth %", 0.0))) ** index
            if group != "manufacturing_cogs":
                return float(row.get(input_name.replace(" Input", " Y1"), 0.0)) * growth
            value = float(row.get(input_name, 0.0)) * growth
            behavior = str(row.get("Cost Behavior", "Fixed / step-fixed — annual"))
            if behavior in {"Variable — per unit", "Unit-based"}:
                volumes = baseline_volumes if input_name == "Baseline Input" else scenario_volumes
                return value * float((volumes or {}).get(year, 0.0))
            return value

        schedules[group] = {
            "Baseline Cost": {
                year: sum(
                    annual_value(row, "Baseline Input", year, index)
                    for row in rows
                    if bool(row.get("Applicable", True))
                )
                for index, year in enumerate(INVESTMENT_YEARS)
            },
            "Scenario Cost": {
                year: sum(
                    annual_value(row, "Scenario Input", year, index)
                    for row in rows
                    if bool(row.get("Applicable", True))
                )
                for index, year in enumerate(INVESTMENT_YEARS)
            },
        }
    return schedules


def default_investment_inputs(case: dict[str, Any]) -> dict[str, Any]:
    archetype = str(case.get("Case Archetype") or (CASE_ARCHETYPES[1] if str(case.get("Profile")) in {"digital", "saving"} else CASE_ARCHETYPES[0]))
    if archetype not in CASE_ARCHETYPES: archetype = CASE_ARCHETYPES[0]
    digital = archetype == CASE_ARCHETYPES[1]
    operating_costs = _costs(archetype)
    capacity = {"Baseline Capacity": _series(900_000,.01), "Added Capacity from Investment": _series(360_000), "Baseline Volume": _series(720_000,.025), "Scenario Volume": _annual([792000,890000,970000,1045000,1085000,1105000,1120000,1130000,1140000,1150000]), "Baseline Net Price per Unit": _series(64,.02)}
    return {
        "schema_version": SCHEMA_VERSION,
        "settings": {"Case Name": str(case.get("Investment Case Name", "New Investment Case")), "Case Archetype": archetype, "Value Creation Drivers": archetype_default_drivers(archetype), "Financial Scope": str(case.get("Business Unit / Market", "Region A Operations")), "Currency": "USD", "Base Year": 2026, "Forecast Horizon": 10, "Investment Start Date": date(2026,10,1), "Operational Start Date": date(2027,7,1), "Applicable Tax Rate": .24, "Planning Inflation": .025, "Model Basis": "Nominal", "Model Version": "1.0", "As Of Date": date(2026,9,15), "Revenue Modeling Mode": "Unit-based"},
        "investment": {"uses": _uses(archetype), "Sustaining CAPEX": _series(220_000 if digital else 350_000, .02), "Sustaining CAPEX Source / Basis": "Long-range plan", "Sustaining CAPEX Comment / Rationale": "Maintenance capital", "CAPEX Avoidance": _series(0), "Useful Life": 10},
        "capacity": capacity,
        "capacity_input_methods": {"Baseline Capacity": "Y1 + Growth", "Baseline Volume": "Y1 + Growth", "Baseline Net Price per Unit": "Y1 + Growth"},
        "capacity_growth_rates": {"Baseline Capacity": .01, "Baseline Volume": .025, "Baseline Net Price per Unit": .02},
        "revenue_based": {"Baseline Revenue": _series(60_000_000 if digital else 46_080_000,.035), "Incremental Revenue / Revenue Uplift": _annual([0,1e6,2.5e6,4e6,5.5e6,6e6,6.5e6,7e6,7.5e6,8e6])},
        "revenue_input_method": "Y1 + Growth",
        "revenue_growth_rate": .035,
        "acquisition": {"Target Revenue": _series(34e6,.04), "Target Gross Margin %": _annual([.62] * 10), "Target EBITDA": _series(5.8e6,.05), "Target D&A": _series(1.1e6,.02), "Target EBIT": _series(4.7e6,.05), "Opening / Transaction Working Capital Reference": _series(4.8e6,.03), "Revenue Synergies": _series(3.5e6,.03), "Cost Synergies": _series(4e6,.025), "Synergy Ramp %": _annual([.25,.55,.8,1,1,1,1,1,1,1]), "One-off Integration Costs": _annual([4e6,2e6,.5e6,0,0,0,0,0,0,0])},
        "savings_register": _savings(archetype), "operating_costs": operating_costs,
        "operating_cost_input_methods": {group: "Y1 + Growth" for group in operating_costs},
        "operating_cost_schedules": _cost_schedules(operating_costs, capacity["Baseline Volume"], capacity["Scenario Volume"]),
        "working_capital": {"Relevant DSO": 52.0, "Relevant DIO": 64.0, "Relevant DPO": 48.0, "AP Cost Basis": "Direct Materials", "Selected Operating Cost Base %": 1.0},
        "capital": {"Cost of Equity Method": "CAPM – Own Beta", "Risk-Free Rate": .042, "Beta": .95, "Equity Risk Premium": .055, "Country Risk Premium": .01, "Peer Beta Source": "Selected listed peer group", "Unlevered Beta": .72, "Relevered Beta": .95, "Corporate Cost of Equity": .105, "Manual Cost of Equity": .105, "Pre-tax Cost of Debt": .062, "Target Debt %": .35, "Target Equity %": .65, "Corporate Hurdle Rate": .10, "Existing Business ROIC": .145, "Marginal Reinvestment Return": .118, "Treasury / Cash Yield": .04, "Source / Methodology": "FY27 corporate planning assumptions", "Effective Date": "2026-07-01", "Rationale": "Management capital-allocation screening rates."}}


def _n(v: Any) -> float:
    try:
        n=float(v); return n if isfinite(n) else 0.0
    except (TypeError,ValueError): return 0.0


def calculate_cost_of_equity(capital: dict[str, Any]) -> float:
    method = str(capital.get("Cost of Equity Method"))
    beta = _n(capital.get("Relevered Beta" if method == "CAPM – Peer / Proxy Beta" else "Beta"))
    if method.startswith("CAPM"):
        return _n(capital.get("Risk-Free Rate")) + beta * _n(capital.get("Equity Risk Premium")) + _n(capital.get("Country Risk Premium"))
    return _n(capital.get("Corporate Cost of Equity" if method == "Corporate Provided Cost of Equity" else "Manual Cost of Equity"))


def _v(s: dict[str,Any], y: str) -> float: return _n(s.get(y,0))
def _r(a: float,b: float)->float: return a/b if abs(b)>1e-12 else 0.0
def _line_total(lines:list[dict[str,Any]], field:str)->float: return sum(_n(x.get(field)) for x in lines if bool(x.get("Applicable",True)))
def _escalated(lines:list[dict[str,Any]], field:str, i:int)->float: return sum(_n(x.get(field))*(1+_n(x.get("Annual Growth %")))**i for x in lines if bool(x.get("Applicable",True)))
def _cost_value(x:dict[str,Any], group:str, field:str, year:str, index:int)->float:
    method=str(x.get("operating_cost_input_methods",{}).get(group,"Y1 + Growth"))
    if method=="Annual Schedule":
        schedule_name="Baseline Cost" if field=="Baseline Y1" else "Scenario Cost"
        return _v(x.get("operating_cost_schedules",{}).get(group,{}).get(schedule_name,{}),year)
    return _escalated(x["operating_costs"].get(group,[]),field,index)


def _manufacturing_costs(x: dict[str, Any], year: str, index: int, baseline_volume: float, scenario_volume: float) -> tuple[dict[str, float], dict[str, float]]:
    """Return the controlled manufacturing COGS bridge by component."""
    group = "manufacturing_cogs"
    rows = x.get("operating_costs", {}).get(group, [])
    method = str(x.get("operating_cost_input_methods", {}).get(group, "Y1 + Growth"))
    components = ["Direct Materials", "Direct Labor", "Variable Manufacturing Overhead", "Fixed Manufacturing Overhead"]
    baseline = {component: 0.0 for component in components}
    scenario = {component: 0.0 for component in components}
    if method == "Annual Schedule":
        baseline["Direct Materials"] = _v(x.get("operating_cost_schedules", {}).get(group, {}).get("Baseline Cost", {}), year)
        scenario["Direct Materials"] = _v(x.get("operating_cost_schedules", {}).get(group, {}).get("Scenario Cost", {}), year)
        return baseline, scenario
    for row in rows:
        if not bool(row.get("Applicable", True)):
            continue
        line = str(row.get("Cost Line", "Direct Materials"))
        if line not in baseline:
            line = "Variable Manufacturing Overhead"
        growth = (1 + _n(row.get("Annual Growth %"))) ** index
        behavior = str(row.get("Cost Behavior", "Fixed / step-fixed — annual"))
        if behavior in {"Variable — per unit", "Unit-based"}:
            baseline_input = row.get("Baseline Input", row.get("Baseline Unit Cost", 0.0))
            scenario_input = row.get("Scenario Input", row.get("Scenario Unit Cost", 0.0))
            baseline[line] += _n(baseline_input) * growth * baseline_volume
            scenario[line] += _n(scenario_input) * growth * scenario_volume
        else:
            baseline_input = row.get("Baseline Input", row.get("Baseline Y1", 0.0))
            scenario_input = row.get("Scenario Input", row.get("Scenario Y1", 0.0))
            baseline[line] += _n(baseline_input) * growth
            scenario[line] += _n(scenario_input) * growth
    return baseline, scenario


def _saving_cost_bucket(mapping: Any) -> str:
    value = str(mapping or "")
    if value.startswith("Manufacturing COGS"):
        return "manufacturing_cogs"
    if value.startswith("Non-Manufacturing Personnel"):
        return "non_manufacturing_personnel"
    return "non_manufacturing_opex"
def _modeled_input_value(x:dict[str,Any], section:str, metric:str, year:str, index:int)->float:
    if section=="capacity":
        method=str(x.get("capacity_input_methods",{}).get(metric,"Annual Schedule"))
        growth=_n(x.get("capacity_growth_rates",{}).get(metric,0))
    else:
        method=str(x.get("revenue_input_method","Annual Schedule"))
        growth=_n(x.get("revenue_growth_rate",0))
    values=x.get(section,{}).get(metric,{})
    return _v(values,"Y1")*(1+growth)**index if method=="Y1 + Growth" else _v(values,year)
def _savings_ramp(row:dict[str,Any], index:int)->float:
    profile=str(row.get("Ramp Profile","2-year ramp"))
    if profile=="Immediate": return 1.0
    if profile=="1-year ramp": return .5 if index==0 else 1.0
    if profile=="Custom":
        field="Custom Y1 Ramp %" if index==0 else "Custom Y2 Ramp %" if index==1 else "Custom Y3+ Ramp %"
        return min(1,max(0,_n(row.get(field))))
    return (1/3,2/3,1.0)[min(index,2)]
def _npv(rate:float,cf:list[float])->float: return sum(v/(1+rate)**i for i,v in enumerate(cf))


def _irr(cf:list[float])->float|None:
    if not cf or min(cf)>=0 or max(cf)<=0:return None
    lo,hi=-.99,10.; lv,hv=_npv(lo,cf),_npv(hi,cf)
    if lv*hv>0:return None
    for _ in range(200):
        mid=(lo+hi)/2; mv=_npv(mid,cf)
        if abs(mv)<.01:return mid
        if lv*mv<=0:hi,hv=mid,mv
        else:lo,lv=mid,mv
    return (lo+hi)/2


def _payback(cf:list[float])->float|None:
    total=cf[0]
    for i,v in enumerate(cf[1:],1):
        prior=total; total+=v
        if total>=0 and v>0:return (i-1)+abs(prior)/v
    return 0.0 if cf and cf[0]>=0 else None


def _shift_incremental_values(values: list[float], shift_months: float) -> list[float]:
    """Shift annual incremental economics using linear interpolation; zero shift is exact."""
    if abs(shift_months) < 1e-12 or not values:
        return list(values)
    shift_years = shift_months / 12.0
    shifted: list[float] = []
    for index in range(len(values)):
        source_position = index - shift_years
        if source_position < 0:
            lower_value = 0.0
            upper_value = values[0]
            fraction = source_position + 1.0
        elif source_position >= len(values) - 1:
            lower_value = values[-1]
            upper_value = values[-1]
            fraction = 0.0
        else:
            lower_index = int(source_position)
            fraction = source_position - lower_index
            lower_value = values[lower_index]
            upper_value = values[lower_index + 1]
        shifted.append(lower_value + (upper_value - lower_value) * min(1.0, max(0.0, fraction)))
    return shifted


def _pnl(rows:dict[str,dict[str,float]], years:list[str])->pd.DataFrame:
    order=["Revenue","COGS","Gross Profit","Gross Margin %","Non-Manufacturing Personnel","Non-Manufacturing OPEX","EBITDA","EBITDA Margin %","Depreciation & Amortization","EBIT","EBIT Margin %"]
    return pd.DataFrame([{"Metric":m,**{y:rows[m][y] for y in years}} for m in order])


def calculate_investment_model(raw:dict[str,Any])->dict[str,Any]:
    x=deepcopy(raw); s=x["settings"]; years=INVESTMENT_YEARS[:5 if int(s.get("Forecast Horizon",10))==5 else 10]
    archetype=str(s.get("Case Archetype",CASE_ARCHETYPES[0])); enabled=set(s.get("Value Creation Drivers",[])); rev="Revenue Growth" in enabled; saving="Cost Reduction" in enabled; wc_on="Working Capital Improvement" in enabled
    tax=min(1,max(0,_n(s.get("Applicable Tax Rate")))); c=x["capital"]
    ke=calculate_cost_of_equity(c)
    pre_tax_debt=_n(c.get("Pre-tax Cost of Debt")); kd=pre_tax_debt*(1-tax); debt=min(1,max(0,_n(c.get("Target Debt %")))); equity=1-debt; c["Target Equity %"]=equity; wacc=ke*equity+kd*debt
    initial=_line_total(x["investment"]["uses"],"Amount"); life=max(1,int(x["investment"].get("Useful Life",10)))
    metrics=["Revenue","COGS","Gross Profit","Gross Margin %","Non-Manufacturing Personnel","Non-Manufacturing OPEX","EBITDA","EBITDA Margin %","Depreciation & Amortization","EBIT","EBIT Margin %"]
    base={m:{} for m in metrics}; scenario=deepcopy(base); drivers={m:{} for m in ["Total Available Capacity","Capacity Utilization %","Baseline Revenue","Incremental Revenue","Scenario Revenue","Realized Savings"]}
    capacity_bridge={m:{} for m in ["Baseline Capacity","Baseline Volume","Baseline Idle Capacity","Baseline Utilization %","Added Capacity","Total Scenario Capacity","Scenario Volume","Scenario Idle Capacity","Scenario Utilization %","Baseline Revenue","Scenario Revenue","Incremental Revenue"]}
    cogs_components={name:{"Baseline":{},"Scenario":{}} for name in ["Direct Materials","Direct Labor","Variable Manufacturing Overhead","Fixed Manufacturing Overhead"]}
    sustaining_da={}; initial_da={}; baseline_da={}; target_da={}; baseline_materials={}; scenario_materials={}
    cumulative_sustaining=0.0
    for i,y in enumerate(years):
        bv=_modeled_input_value(x,"capacity","Baseline Volume",y,i); sv=_v(x["capacity"]["Scenario Volume"],y); bp=_modeled_input_value(x,"capacity","Baseline Net Price per Unit",y,i); mode=str(s.get("Revenue Modeling Mode","Unit-based"))
        if archetype==CASE_ARCHETYPES[0] and mode=="Unit-based":
            baseline_capacity=_modeled_input_value(x,"capacity","Baseline Capacity",y,i); added_capacity=_v(x["capacity"]["Added Capacity from Investment"],y); cap=baseline_capacity+added_capacity
            br=bv*bp; sr=sv*bp if rev else br; util=_r(sv,cap)
            bridge_values={"Baseline Capacity":baseline_capacity,"Baseline Volume":bv,"Baseline Idle Capacity":baseline_capacity-bv,"Baseline Utilization %":_r(bv,baseline_capacity),"Added Capacity":added_capacity,"Total Scenario Capacity":cap,"Scenario Volume":sv,"Scenario Idle Capacity":cap-sv,"Scenario Utilization %":util,"Baseline Revenue":br,"Scenario Revenue":sr,"Incremental Revenue":sr-br}
            for metric,value in bridge_values.items(): capacity_bridge[metric][y]=value
        else:
            br=_modeled_input_value(x,"revenue_based","Baseline Revenue",y,i); sr=br+(_v(x["revenue_based"]["Incremental Revenue / Revenue Uplift"],y) if rev else 0); cap=util=0
        ramp=1.0
        if archetype==CASE_ARCHETYPES[2]:
            ramp=min(1,max(0,_v(x["acquisition"]["Synergy Ramp %"],y))); sr=br+_v(x["acquisition"]["Target Revenue"],y)+(_v(x["acquisition"]["Revenue Synergies"],y)*ramp if rev else 0)
        b_components,s_components=_manufacturing_costs(x,y,i,bv,sv)
        realized_by_bucket={"manufacturing_cogs":0.0,"non_manufacturing_personnel":0.0,"non_manufacturing_opex":0.0}
        manufacturing_savings={component:0.0 for component in s_components}
        if saving and archetype!=CASE_ARCHETYPES[2]:
            for row in x.get("savings_register",[]):
                if not bool(row.get("Applicable",True)): continue
                amount=_n(row.get("Gross Run-rate Saving",row.get("Gross Saving")))*min(1,max(0,_n(row.get("Realization %"))))*_savings_ramp(row,i)
                bucket=_saving_cost_bucket(row.get("Cost Line Mapping")); realized_by_bucket[bucket]+=amount
                mapping=str(row.get("Cost Line Mapping",""))
                for component in manufacturing_savings:
                    if component in mapping:
                        manufacturing_savings[component]+=amount
                        break
        adjusted_s_components={component:max(0.0,value-manufacturing_savings[component]) for component,value in s_components.items()}
        bc=sum(b_components.values()); sc=sum(adjusted_s_components.values())
        if archetype==CASE_ARCHETYPES[2]:
            target_revenue=_v(x["acquisition"]["Target Revenue"],y); revenue_synergy=_v(x["acquisition"]["Revenue Synergies"],y)*ramp if rev else 0
            target_margin=min(1,max(0,_v(x["acquisition"].get("Target Gross Margin %",{}),y) or .62)); target_cogs=(target_revenue+revenue_synergy)*(1-target_margin); sc+=target_cogs; adjusted_s_components["Direct Materials"]+=target_cogs
        bpers=_cost_value(x,"non_manufacturing_personnel","Baseline Y1",y,i); spers=max(0.0,_cost_value(x,"non_manufacturing_personnel","Scenario Y1",y,i)-realized_by_bucket["non_manufacturing_personnel"])
        bo=_cost_value(x,"non_manufacturing_opex","Baseline Y1",y,i); s_o=max(0.0,_cost_value(x,"non_manufacturing_opex","Scenario Y1",y,i)-realized_by_bucket["non_manufacturing_opex"])
        cost_synergy=_v(x["acquisition"]["Cost Synergies"],y)*ramp if archetype==CASE_ARCHETYPES[2] and saving else 0
        realized=cost_synergy if archetype==CASE_ARCHETYPES[2] else sum(realized_by_bucket.values())
        integration=_v(x["acquisition"]["One-off Integration Costs"],y) if archetype==CASE_ARCHETYPES[2] else 0
        bgp,sgp=br-bc,sr-sc; be=bgp-bpers-bo
        if archetype==CASE_ARCHETYPES[2]:
            target_ebitda=_v(x["acquisition"]["Target EBITDA"],y); revenue_synergy=_v(x["acquisition"]["Revenue Synergies"],y)*ramp if rev else 0; target_margin=min(1,max(0,_v(x["acquisition"].get("Target Gross Margin %",{}),y) or .62))
            se=be+target_ebitda+revenue_synergy*target_margin+cost_synergy-integration; s_o=max(0.0,sgp-spers-se)
        else: se=sgp-spers-s_o
        cumulative_sustaining+=_v(x["investment"].get("Sustaining CAPEX",{}),y)
        baseline_da[y]=br*.025; initial_da[y]=initial/life; sustaining_da[y]=cumulative_sustaining/life; target_da[y]=_v(x["acquisition"].get("Target D&A",{}),y) if archetype==CASE_ARCHETYPES[2] else 0.0
        bda=baseline_da[y]; sda=bda+initial_da[y]+sustaining_da[y]+target_da[y]; bit,sit=be-bda,se-sda
        vals={"Revenue":(br,sr),"COGS":(bc,sc),"Gross Profit":(bgp,sgp),"Gross Margin %":(_r(bgp,br),_r(sgp,sr)),"Non-Manufacturing Personnel":(bpers,spers),"Non-Manufacturing OPEX":(bo,s_o),"EBITDA":(be,se),"EBITDA Margin %":(_r(be,br),_r(se,sr)),"Depreciation & Amortization":(bda,sda),"EBIT":(bit,sit),"EBIT Margin %":(_r(bit,br),_r(sit,sr))}
        for metric,pair in vals.items(): base[metric][y],scenario[metric][y]=pair
        for metric,value in {"Total Available Capacity":cap,"Capacity Utilization %":util,"Baseline Revenue":br,"Incremental Revenue":sr-br,"Scenario Revenue":sr,"Realized Savings":realized}.items(): drivers[metric][y]=value
        for component in cogs_components:
            cogs_components[component]["Baseline"][y]=b_components[component]
            cogs_components[component]["Scenario"][y]=adjusted_s_components[component]
        baseline_materials[y]=b_components["Direct Materials"]; scenario_materials[y]=adjusted_s_components["Direct Materials"]
    timing_shift_months=_n(s.get("Sensitivity Operational Start Shift Months",0))
    if abs(timing_shift_months)>1e-12:
        for metric in ["Revenue","COGS","Non-Manufacturing Personnel","Non-Manufacturing OPEX","Depreciation & Amortization"]:
            shifted=_shift_incremental_values([scenario[metric][year]-base[metric][year] for year in years],timing_shift_months)
            for year,delta in zip(years,shifted): scenario[metric][year]=base[metric][year]+delta
        shifted_materials=_shift_incremental_values([scenario_materials[y]-baseline_materials[y] for y in years],timing_shift_months)
        for year,delta in zip(years,shifted_materials): scenario_materials[year]=baseline_materials[year]+delta
        for year in years:
            scenario["Gross Profit"][year]=scenario["Revenue"][year]-scenario["COGS"][year]; scenario["Gross Margin %"][year]=_r(scenario["Gross Profit"][year],scenario["Revenue"][year])
            scenario["EBITDA"][year]=scenario["Gross Profit"][year]-scenario["Non-Manufacturing Personnel"][year]-scenario["Non-Manufacturing OPEX"][year]; scenario["EBITDA Margin %"][year]=_r(scenario["EBITDA"][year],scenario["Revenue"][year])
            scenario["EBIT"][year]=scenario["EBITDA"][year]-scenario["Depreciation & Amortization"][year]; scenario["EBIT Margin %"][year]=_r(scenario["EBIT"][year],scenario["Revenue"][year]); drivers["Scenario Revenue"][year]=scenario["Revenue"][year]; drivers["Incremental Revenue"][year]=scenario["Revenue"][year]-base["Revenue"][year]
    baseline,scenario_pnl=_pnl(base,years),_pnl(scenario,years)
    incremental=pd.DataFrame([{"Metric":f"Incremental {metric}",**{y:scenario[metric][y]-base[metric][y] for y in years}} for metric in ["Revenue","COGS","Gross Profit","Non-Manufacturing Personnel","Non-Manufacturing OPEX","EBITDA","Depreciation & Amortization","EBIT"]])
    wc=x.get("working_capital",{}); dso,dio,dpo=(_n(wc.get(k)) for k in ["Relevant DSO","Relevant DIO","Relevant DPO"]); ap_basis=str(wc.get("AP Cost Basis","Direct Materials")); selected_pct=min(1,max(0,_n(wc.get("Selected Operating Cost Base %",1))))
    wc_rows=[]; changes={}; prior=0.0
    for y in years:
        inc_revenue=scenario["Revenue"][y]-base["Revenue"][y]; inc_cogs=scenario["COGS"][y]-base["COGS"][y]
        if ap_basis=="Direct Materials": inc_payable=scenario_materials[y]-baseline_materials[y]
        elif ap_basis=="Selected Operating Cost Base": inc_payable=inc_cogs*selected_pct
        else: inc_payable=inc_cogs
        ar=inc_revenue*dso/365 if wc_on else 0.0; inventory=inc_cogs*dio/365 if wc_on else 0.0; ap=inc_payable*dpo/365 if wc_on else 0.0; nwc=ar+inventory-ap; changes[y]=nwc-prior; prior=nwc
        wc_rows.append({"Year":y,"Incremental Accounts Receivable":ar,"Incremental Inventory":inventory,"Incremental Accounts Payable":ap,"Incremental Net Working Capital":nwc,"Change in NWC":changes[y]})
    cf=[-initial]; disc=[-initial]; cum=dcum=-initial; loss_balance=0.0
    rows=[{"Year":"Y0","Incremental EBIT":0.0,"Cash Taxes":0.0,"D&A":0.0,"CAPEX":initial,"Change in NWC":0.0,"Avoided CAPEX":0.0,"Unlevered Free Cash Flow":-initial,"Cumulative FCF":cum,"Discount Factor":1.0,"Present Value of FCF":-initial,"Cumulative Discounted FCF":dcum}]
    tax_rows=[]
    for i,y in enumerate(years,1):
        ie=scenario["EBIT"][y]-base["EBIT"][y]; opening_loss=loss_balance
        if ie<0: loss_balance+=-ie; taxable=0.0; loss_used=0.0
        else: loss_used=min(loss_balance,ie); taxable=max(0.0,ie-loss_used); loss_balance-=loss_used
        taxes=taxable*tax; da=scenario["Depreciation & Amortization"][y]-base["Depreciation & Amortization"][y]; capex=max(0.0,_v(x["investment"].get("Sustaining CAPEX",{}),y)); avoided=_v(x["investment"].get("CAPEX Avoidance",{}),y) if "Asset / CAPEX Avoidance" in enabled else 0.0
        f=ie-taxes+da-capex-changes[y]+avoided; factor=1/(1+wacc)**i; pv=f*factor; cf.append(f); disc.append(pv); cum+=f; dcum+=pv
        tax_rows.append({"Year":y,"Incremental EBIT":ie,"Opening Tax Loss Balance":opening_loss,"Tax Loss Used":loss_used,"Taxable EBIT After Losses":taxable,"Cash Taxes":taxes,"Closing Tax Loss Balance":loss_balance})
        rows.append({"Year":y,"Incremental EBIT":ie,"Cash Taxes":taxes,"D&A":da,"CAPEX":capex,"Change in NWC":changes[y],"Avoided CAPEX":avoided,"Unlevered Free Cash Flow":f,"Cumulative FCF":cum,"Discount Factor":factor,"Present Value of FCF":pv,"Cumulative Discounted FCF":dcum})
    npv=sum(disc); irr=_irr(cf)
    returns={"Project NPV":npv,"Project IRR":irr,"Payback Period":_payback(cf),"Discounted Payback":_payback(disc),"Profitability Index":(npv+initial)/initial if initial else 0,"Cumulative Unlevered FCF":cum,"WACC":wacc,"Cost of Equity":ke,"Pre-tax Cost of Debt":pre_tax_debt,"After-tax Cost of Debt":kd,"Target Debt Weight":debt,"Target Equity Weight":equity}
    bridge_frame=pd.DataFrame([{"Metric":metric,**values} for metric,values in capacity_bridge.items()]) if archetype==CASE_ARCHETYPES[0] and str(s.get("Revenue Modeling Mode","Unit-based"))=="Unit-based" else pd.DataFrame()
    cogs_rows=[]
    for component,values in cogs_components.items(): cogs_rows.extend([{"COGS Component":component,"Case":"Baseline",**values["Baseline"]},{"COGS Component":component,"Case":"Investment Scenario",**values["Scenario"]}])
    cogs_rows.extend([{"COGS Component":"Total Manufacturing COGS","Case":"Baseline",**base["COGS"]},{"COGS Component":"Total Manufacturing COGS","Case":"Investment Scenario",**scenario["COGS"]}])
    if archetype==CASE_ARCHETYPES[0] and str(s.get("Revenue Modeling Mode","Unit-based"))=="Unit-based":
        cogs_rows.extend([
            {"COGS Component":"Baseline COGS per Unit","Case":"Unit Economics",**{y:_r(base["COGS"][y],capacity_bridge["Baseline Volume"][y]) for y in years}},
            {"COGS Component":"Investment Scenario COGS per Unit","Case":"Unit Economics",**{y:_r(scenario["COGS"][y],capacity_bridge["Scenario Volume"][y]) for y in years}},
        ])
    da_bridge=pd.DataFrame([{"D&A Component":"Baseline D&A (2.5% of baseline revenue)",**baseline_da},{"D&A Component":f"Initial Investment D&A (straight-line, {life} years)",**initial_da},{"D&A Component":f"Sustaining CAPEX D&A (straight-line by vintage, {life} years)",**sustaining_da},{"D&A Component":"Acquisition / Target D&A",**target_da},{"D&A Component":"Total Scenario D&A",**scenario["Depreciation & Amortization"]}])
    wacc_bridge=pd.DataFrame([{"Component":"Cost of Equity","Rate / Weight":ke},{"Component":"Equity Weight","Rate / Weight":equity},{"Component":"Pre-tax Cost of Debt","Rate / Weight":pre_tax_debt},{"Component":"After-tax Cost of Debt","Rate / Weight":kd},{"Component":"Debt Weight","Rate / Weight":debt},{"Component":"WACC","Rate / Weight":wacc}])
    return {"inputs":x,"years":years,"drivers":drivers,"capacity_bridge":bridge_frame,"cogs_bridge":pd.DataFrame(cogs_rows),"depreciation_bridge":da_bridge,"baseline_pnl":baseline,"scenario_pnl":scenario_pnl,"incremental":incremental,"working_capital":pd.DataFrame(wc_rows),"tax_bridge":pd.DataFrame(tax_rows),"cash_flow":pd.DataFrame(rows),"wacc_bridge":wacc_bridge,"returns":returns,"total_initial_investment":initial,"working_capital_enabled":wc_on,"capital_structure_valid":True}
