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
            ("Software", 3_200_000, "Vendor quotation", "Initial platform licenses and configuration"),
            ("Integration", 2_000_000, "IT implementation estimate", "Core-system and workflow integration"),
            ("Consulting", 1_400_000, "Transformation estimate", "Design and implementation support"),
            ("Data Migration", 1_000_000, "IT workplan", "Historical data preparation and migration"),
            ("Training", 900_000, "HR / transformation estimate", "Role-based adoption and training program"),
            ("Other", 500_000, "Management contingency", "Controlled implementation contingency"),
        ]
    elif archetype == CASE_ARCHETYPES[2]:
        rows = [
            ("Purchase Price / Enterprise Value", 62_000_000, "Indicative valuation", "Current transaction value assumption"),
            ("Transaction Fees", 2_800_000, "Advisor estimate", "Legal, diligence and advisory fees"),
            ("Integration Costs", 5_500_000, "Integration office estimate", "Systems, organization and process integration"),
        ]
    else:
        rows = [
            ("Equipment", 22_000_000, "Vendor quotation", "Production equipment and installation"),
            ("Construction", 7_500_000, "Engineering estimate", "Facility modification and utilities"),
            ("Implementation", 3_000_000, "Program workplan", "Commissioning and operating readiness"),
            ("Integration", 1_500_000, "IT implementation estimate", "Manufacturing and planning-system integration"),
            ("Other", 1_000_000, "Management contingency", "Controlled delivery contingency"),
        ]
    return [{"Applicable": True, "Investment Component": n, "Amount": v, "Timing": "Before operational start", "Source / Basis": source, "Comment / Rationale": comment} for n, v, source, comment in rows]


def _savings(archetype: str) -> list[dict[str, Any]]:
    if archetype == CASE_ARCHETYPES[1]: rows = [("Personnel", 8_500_000, "Process automation", 3_100_000, .75), ("Logistics", 6_200_000, "Routing optimization", 900_000, .8), ("IT", 4_000_000, "Application consolidation", 650_000, .7)]
    elif archetype == CASE_ARCHETYPES[2]: rows = [("Procurement", 18_000_000, "Combined purchasing scale", 2_000_000, .6), ("Personnel", 14_000_000, "Shared-service consolidation", 2_600_000, .55), ("Logistics", 9_000_000, "Network consolidation", 1_100_000, .5)]
    else: rows = [("Manufacturing", 15_000_000, "Yield and line efficiency", 650_000, .65)]
    return [{"Applicable": True, "Category": c, "Baseline Cost / Cost Pool": p, "Saving Mechanism": m, "Gross Saving": g, "Realization %": r, "Realized Saving": g*r, "Source / Basis": "Functional estimate", "Comment": "Annual run-rate at maturity"} for c,p,m,g,r in rows]


def _costs(archetype: str) -> dict[str, list[dict[str, Any]]]:
    digital, acquisition = archetype == CASE_ARCHETYPES[1], archetype == CASE_ARCHETYPES[2]
    return {
        "personnel": [
            {"Applicable": True, "Cost Line": "Operations", "Baseline Y1": 6_200_000 if digital else 4_400_000, "Scenario Y1": 6_000_000 if digital else 4_900_000, "Annual Growth %": .025, "Source / Basis": "Operating plan", "Comment": "Relevant-scope personnel"},
            {"Applicable": acquisition, "Cost Line": "Other Personnel", "Baseline Y1": 1_500_000, "Scenario Y1": 5_200_000, "Annual Growth %": .025, "Source / Basis": "Target diligence", "Comment": "Target organization"}],
        "variable": [{"Applicable": True, "Cost Line": "Usage-based Cloud / Processing" if digital else "Raw Materials", "Baseline Unit Cost": 0.0 if digital else 29.0, "Scenario Unit Cost": 0.0 if digital else 29.0, "Baseline Y1": 1_100_000 if digital else 0.0, "Scenario Y1": 1_650_000 if digital else 0.0, "Annual Growth %": .02, "Source / Basis": "Operations estimate", "Comment": "Activity-linked cost"}],
        "fixed": [
            {"Applicable": True, "Cost Line": "Maintenance Contracts", "Baseline Y1": 1_200_000, "Scenario Y1": 1_450_000 if digital else 1_650_000, "Annual Growth %": .025, "Source / Basis": "Supplier estimate", "Comment": "Annual service envelope"},
            {"Applicable": True, "Cost Line": "Software Licenses", "Baseline Y1": 500_000, "Scenario Y1": 800_000 if digital else 550_000, "Annual Growth %": .025, "Source / Basis": "Commercial proposal", "Comment": "Fixed recurring licenses"},
            {"Applicable": True, "Cost Line": "Other Fixed Overhead", "Baseline Y1": 2_800_000, "Scenario Y1": 3_000_000, "Annual Growth %": .025, "Source / Basis": "Operating plan", "Comment": "Relevant fixed overhead"}]}


def default_investment_inputs(case: dict[str, Any]) -> dict[str, Any]:
    archetype = str(case.get("Case Archetype") or (CASE_ARCHETYPES[1] if str(case.get("Profile")) in {"digital", "saving"} else CASE_ARCHETYPES[0]))
    if archetype not in CASE_ARCHETYPES: archetype = CASE_ARCHETYPES[0]
    digital = archetype == CASE_ARCHETYPES[1]
    return {
        "schema_version": SCHEMA_VERSION,
        "settings": {"Case Name": str(case.get("Investment Case Name", "New Investment Case")), "Case Archetype": archetype, "Value Creation Drivers": archetype_default_drivers(archetype), "Financial Scope": str(case.get("Business Unit / Market", "Region A Operations")), "Currency": "USD", "Base Year": 2026, "Forecast Horizon": 10, "Investment Start Date": date(2026,10,1), "Operational Start Date": date(2027,7,1), "Applicable Tax Rate": .24, "Planning Inflation": .025, "Model Basis": "Nominal", "Model Version": "1.0", "As Of Date": date(2026,9,15), "Revenue Modeling Mode": "Unit-based"},
        "investment": {"uses": _uses(archetype), "Sustaining CAPEX": _series(220_000 if digital else 350_000, .02), "CAPEX Avoidance": _series(0), "Useful Life": 10},
        "capacity": {"Baseline Capacity": _series(900_000,.01), "Added Capacity from Investment": _series(360_000), "Baseline Volume": _series(720_000,.025), "Scenario Volume": _annual([792000,890000,970000,1045000,1085000,1105000,1120000,1130000,1140000,1150000]), "Baseline Net Revenue per Unit": _series(64,.02), "Net Price Escalation %": {y:.02 for y in INVESTMENT_YEARS}},
        "revenue_based": {"Baseline Revenue": _series(60_000_000 if digital else 46_080_000,.035), "Revenue Growth %": {y:.035 for y in INVESTMENT_YEARS}, "Incremental Revenue / Revenue Uplift": _annual([0,1e6,2.5e6,4e6,5.5e6,6e6,6.5e6,7e6,7.5e6,8e6])},
        "acquisition": {"Target Revenue": _series(34e6,.04), "Target EBITDA": _series(5.8e6,.05), "Target D&A": _series(1.1e6,.02), "Target EBIT": _series(4.7e6,.05), "Target Working Capital": _series(4.8e6,.03), "Revenue Synergies": _series(3.5e6,.03), "Cost Synergies": _series(4e6,.025), "Synergy Ramp %": _annual([.25,.55,.8,1,1,1,1,1,1,1]), "One-off Integration Costs": _annual([4e6,2e6,.5e6,0,0,0,0,0,0,0])},
        "savings_register": _savings(archetype), "operating_costs": _costs(archetype),
        "working_capital": {"Relevant DSO": 52.0, "Relevant DIO": 64.0, "Relevant DPO": 48.0},
        "capital": {"Cost of Equity Method": "CAPM – Own Beta", "Risk-Free Rate": .042, "Beta": .95, "Equity Risk Premium": .055, "Country Risk Premium": .01, "Peer Beta Source": "Selected listed peer group", "Unlevered Beta": .72, "Relevered Beta": .95, "Corporate Cost of Equity": .105, "Manual Cost of Equity": .105, "Pre-tax Cost of Debt": .062, "Target Debt %": .35, "Target Equity %": .65, "Corporate Hurdle Rate": .10, "Existing Business ROIC": .145, "Marginal Reinvestment Return": .118, "Treasury / Cash Yield": .04, "Source / Methodology": "FY27 corporate planning assumptions", "Effective Date": "2026-07-01", "Rationale": "Management capital-allocation screening rates."}}


def _n(v: Any) -> float:
    try:
        n=float(v); return n if isfinite(n) else 0.0
    except (TypeError,ValueError): return 0.0


def _v(s: dict[str,Any], y: str) -> float: return _n(s.get(y,0))
def _r(a: float,b: float)->float: return a/b if abs(b)>1e-12 else 0.0
def _line_total(lines:list[dict[str,Any]], field:str)->float: return sum(_n(x.get(field)) for x in lines if bool(x.get("Applicable",True)))
def _escalated(lines:list[dict[str,Any]], field:str, i:int)->float: return sum(_n(x.get(field))*(1+_n(x.get("Annual Growth %")))**i for x in lines if bool(x.get("Applicable",True)))
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


def _pnl(rows:dict[str,dict[str,float]], years:list[str])->pd.DataFrame:
    order=["Revenue","COGS","Gross Profit","Gross Margin %","Personnel","Other Operating Expenses","EBITDA","EBITDA Margin %","Depreciation & Amortization","EBIT","EBIT Margin %"]
    return pd.DataFrame([{"Metric":m,**{y:rows[m][y] for y in years}} for m in order])


def calculate_investment_model(raw:dict[str,Any])->dict[str,Any]:
    x=deepcopy(raw); s=x["settings"]; years=INVESTMENT_YEARS[:5 if int(s.get("Forecast Horizon",10))==5 else 10]
    archetype=str(s.get("Case Archetype",CASE_ARCHETYPES[0])); enabled=set(s.get("Value Creation Drivers",[])); rev="Revenue Growth" in enabled; saving="Cost Reduction" in enabled; wc_on="Working Capital Improvement" in enabled
    tax=min(1,max(0,_n(s.get("Applicable Tax Rate")))); c=x["capital"]; method=str(c.get("Cost of Equity Method")); beta=_n(c.get("Relevered Beta" if method=="CAPM – Peer / Proxy Beta" else "Beta"))
    ke=(_n(c.get("Risk-Free Rate"))+beta*_n(c.get("Equity Risk Premium"))+_n(c.get("Country Risk Premium"))) if method.startswith("CAPM") else _n(c.get("Corporate Cost of Equity" if method=="Corporate Provided Cost of Equity" else "Manual Cost of Equity"))
    kd=_n(c.get("Pre-tax Cost of Debt"))*(1-tax); debt,equity=_n(c.get("Target Debt %")),_n(c.get("Target Equity %")); wacc=ke*equity+kd*debt
    initial=_line_total(x["investment"]["uses"],"Amount"); life=max(1,int(x["investment"].get("Useful Life",10))); costs=x["operating_costs"]
    annual_saving=sum(_n(z.get("Gross Saving"))*min(1,max(0,_n(z.get("Realization %")))) for z in x["savings_register"] if z.get("Applicable",True)) if saving else 0
    metrics=["Revenue","COGS","Gross Profit","Gross Margin %","Personnel","Other Operating Expenses","EBITDA","EBITDA Margin %","Depreciation & Amortization","EBIT","EBIT Margin %"]
    base={m:{} for m in metrics}; scenario=deepcopy(base); drivers={m:{} for m in ["Total Available Capacity","Capacity Utilization %","Baseline Revenue","Incremental Revenue","Scenario Revenue","Realized Savings"]}; bnwc={}; snwc={}
    for i,y in enumerate(years):
        bv,sv,bp=_v(x["capacity"]["Baseline Volume"],y),_v(x["capacity"]["Scenario Volume"],y),_v(x["capacity"]["Baseline Net Revenue per Unit"],y); mode=str(s.get("Revenue Modeling Mode","Unit-based"))
        if archetype==CASE_ARCHETYPES[0] and mode=="Unit-based":
            br=bv*bp; scenario_price=bp*(1+_v(x["capacity"]["Net Price Escalation %"],y)); sr=sv*scenario_price if rev else br; cap=_v(x["capacity"]["Baseline Capacity"],y)+_v(x["capacity"]["Added Capacity from Investment"],y); util=_r(sv,cap)
        else:
            br=_v(x["revenue_based"]["Baseline Revenue"],y); sr=br+(_v(x["revenue_based"]["Incremental Revenue / Revenue Uplift"],y) if rev else 0); cap=util=0
        ramp=1.0
        if archetype==CASE_ARCHETYPES[2]:
            ramp=min(1,max(0,_v(x["acquisition"]["Synergy Ramp %"],y))); sr=br+_v(x["acquisition"]["Target Revenue"],y)+(_v(x["acquisition"]["Revenue Synergies"],y)*ramp if rev else 0)
        bc=_escalated(costs["variable"],"Baseline Y1",i); sc=_escalated(costs["variable"],"Scenario Y1",i)
        if archetype==CASE_ARCHETYPES[0] and mode=="Unit-based":
            bc+=sum(_n(z.get("Baseline Unit Cost"))*(1+_n(z.get("Annual Growth %")))**i*bv for z in costs["variable"] if z.get("Applicable",True)); sc+=sum(_n(z.get("Scenario Unit Cost"))*(1+_n(z.get("Annual Growth %")))**i*sv for z in costs["variable"] if z.get("Applicable",True))
        bpers,spers=_escalated(costs["personnel"],"Baseline Y1",i),_escalated(costs["personnel"],"Scenario Y1",i); bf,sf=_escalated(costs["fixed"],"Baseline Y1",i),_escalated(costs["fixed"],"Scenario Y1",i)
        realized=annual_saving*min(1,(i+1)/3)+( _v(x["acquisition"]["Cost Synergies"],y)*ramp if archetype==CASE_ARCHETYPES[2] and saving else 0); integration=_v(x["acquisition"]["One-off Integration Costs"],y) if archetype==CASE_ARCHETYPES[2] else 0
        bgp,sgp=br-bc,sr-sc; bo=bf; be=bgp-bpers-bo; bda=br*.025
        if archetype==CASE_ARCHETYPES[2]:
            target_ebitda=_v(x["acquisition"]["Target EBITDA"],y)
            revenue_synergy=_v(x["acquisition"]["Revenue Synergies"],y)*ramp if rev else 0
            se=be+target_ebitda+revenue_synergy+realized-integration
            s_o=sgp-spers-se
            sda=bda+_v(x["acquisition"]["Target D&A"],y)+initial/life
        else:
            s_o=sf+integration-realized
            se=sgp-spers-s_o
            sda=bda+initial/life
        bit, sit=be-bda,se-sda
        vals={"Revenue":(br,sr),"COGS":(bc,sc),"Gross Profit":(bgp,sgp),"Gross Margin %":(_r(bgp,br),_r(sgp,sr)),"Personnel":(bpers,spers),"Other Operating Expenses":(bo,s_o),"EBITDA":(be,se),"EBITDA Margin %":(_r(be,br),_r(se,sr)),"Depreciation & Amortization":(bda,sda),"EBIT":(bit,sit),"EBIT Margin %":(_r(bit,br),_r(sit,sr))}
        for m,pair in vals.items():base[m][y],scenario[m][y]=pair
        for m,val in {"Total Available Capacity":cap,"Capacity Utilization %":util,"Baseline Revenue":br,"Incremental Revenue":sr-br,"Scenario Revenue":sr,"Realized Savings":realized}.items():drivers[m][y]=val
        if wc_on:
            wc=x["working_capital"]; dso,dio,dpo=(_n(wc.get(k)) for k in ["Relevant DSO","Relevant DIO","Relevant DPO"]); bnwc[y]=br*dso/365+bc*dio/365-bc*dpo/365; snwc[y]=sr*dso/365+sc*dio/365-sc*dpo/365+(_v(x["acquisition"]["Target Working Capital"],y) if archetype==CASE_ARCHETYPES[2] else 0)
        else:bnwc[y]=snwc[y]=0
    baseline,scenario_pnl=_pnl(base,years),_pnl(scenario,years); incremental=pd.DataFrame([{"Metric":f"Incremental {m}",**{y:scenario[m][y]-base[m][y] for y in years}} for m in ["Revenue","Gross Profit","EBITDA","EBIT"]])
    wc_rows=[]; changes={}; prior=0
    for y in years:
        inc=snwc[y]-bnwc[y]; changes[y]=inc-prior; prior=inc; wc=x["working_capital"]
        wc_rows.append({"Year":y,"Accounts Receivable":scenario["Revenue"][y]*_n(wc.get("Relevant DSO"))/365 if wc_on else 0,"Inventory":scenario["COGS"][y]*_n(wc.get("Relevant DIO"))/365 if wc_on else 0,"Accounts Payable":scenario["COGS"][y]*_n(wc.get("Relevant DPO"))/365 if wc_on else 0,"Net Working Capital":snwc[y],"Change in NWC":changes[y]})
    cf=[-initial]; disc=[-initial]; cum=dcum=-initial; rows=[{"Year":"Y0","Incremental EBIT":0,"Cash Taxes":0,"D&A":0,"CAPEX":initial,"Change in NWC":0,"Unlevered Free Cash Flow":-initial,"Discount Factor":1,"Present Value of FCF":-initial,"Cumulative FCF":cum,"Cumulative Discounted FCF":dcum}]
    for i,y in enumerate(years,1):
        ie=scenario["EBIT"][y]-base["EBIT"][y]; taxes=max(0,ie*tax); da=scenario["Depreciation & Amortization"][y]-base["Depreciation & Amortization"][y]; capex=max(0,_v(x["investment"]["Sustaining CAPEX"],y)-(_v(x["investment"]["CAPEX Avoidance"],y) if "Asset / CAPEX Avoidance" in enabled else 0)); f=ie-taxes+da-capex-changes[y]; factor=1/(1+wacc)**i; pv=f*factor; cf.append(f);disc.append(pv);cum+=f;dcum+=pv;rows.append({"Year":y,"Incremental EBIT":ie,"Cash Taxes":taxes,"D&A":da,"CAPEX":capex,"Change in NWC":changes[y],"Unlevered Free Cash Flow":f,"Discount Factor":factor,"Present Value of FCF":pv,"Cumulative FCF":cum,"Cumulative Discounted FCF":dcum})
    npv=sum(disc); irr=_irr(cf); returns={"Project NPV":npv,"Project IRR":irr,"Payback Period":_payback(cf),"Discounted Payback":_payback(disc),"Profitability Index":(npv+initial)/initial if initial else 0,"Cumulative Unlevered FCF":cum,"WACC":wacc,"Cost of Equity":ke,"After-tax Cost of Debt":kd}
    return {"inputs":x,"years":years,"drivers":drivers,"baseline_pnl":baseline,"scenario_pnl":scenario_pnl,"incremental":incremental,"working_capital":pd.DataFrame(wc_rows),"cash_flow":pd.DataFrame(rows),"returns":returns,"total_initial_investment":initial,"working_capital_enabled":wc_on,"capital_structure_valid":abs(debt+equity-1)<.0001}
