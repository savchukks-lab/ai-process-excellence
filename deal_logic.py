from __future__ import annotations

import pandas as pd


def safe_float(value: object, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_price_variance(new_price: float, planned_price: float, new_quantity: float) -> float:
    return (safe_float(new_price) - safe_float(planned_price)) * safe_float(new_quantity)


def calculate_volume_variance(new_quantity: float, planned_quantity: float, new_price: float) -> float:
    return (safe_float(new_quantity) - safe_float(planned_quantity)) * safe_float(new_price)


def calculate_revenue_variance(price_variance: float, volume_variance: float) -> float:
    return safe_float(price_variance) + safe_float(volume_variance)


def calculate_gross_profit(unit_price: float, unit_cost: float, quantity: float) -> float:
    return (safe_float(unit_price) - safe_float(unit_cost)) * safe_float(quantity)


def calculate_margin_pct(revenue: float, gross_profit: float) -> float | None:
    revenue_value = safe_float(revenue)
    if revenue_value <= 0:
        return None
    return safe_float(gross_profit) / revenue_value


def summarize_lines(lines: pd.DataFrame) -> dict:
    if lines.empty:
        return {
            "total_list": 0,
            "total_gross": 0,
            "total_proposed": 0,
            "discount_amount": 0,
            "discount_pct": 0,
            "margin_pct": None,
            "weighted_target_margin": 0,
            "line_count": 0,
        }
    total_list = float(lines["Extended List"].sum())
    total_gross = float(lines.get("Extended Gross", lines["Extended List"]).sum())
    total_proposed = float(lines["Extended Proposed"].sum())
    cost = float((lines["Quantity"] * lines["Unit Cost"]).sum())
    gross_profit = total_proposed - cost
    margin = calculate_margin_pct(total_proposed, gross_profit)
    target = 0
    positive = lines[lines["Extended Proposed"] > 0].copy()
    if not positive.empty:
        target = float((positive["Extended Proposed"] * positive["Target Margin %"].fillna(0)).sum() / positive["Extended Proposed"].sum())
    discount_amount = total_gross - total_proposed
    return {
        "total_list": total_list,
        "total_gross": total_gross,
        "total_proposed": total_proposed,
        "discount_amount": discount_amount,
        "discount_pct": 0 if total_gross == 0 else discount_amount / total_gross,
        "margin_pct": margin,
        "weighted_target_margin": target,
        "line_count": len(lines),
    }


def calculate_customer_risk(credit_status: str, total_ar: float, overdue_ar: float) -> str:
    overdue_ratio = 0 if safe_float(total_ar) == 0 else safe_float(overdue_ar) / safe_float(total_ar)
    if str(credit_status) == "Hold" or overdue_ratio > 0.28:
        return "High"
    if str(credit_status) == "Watch" or overdue_ratio > 0.18:
        return "Medium"
    return "Low"


def demo_customer_health(customer: dict, customer_name: str) -> dict[str, float | str]:
    seed = sum(ord(char) for char in str(customer.get("Customer ID", customer_name)))
    revenue = safe_float(customer.get("Last 12M Revenue"), 1_400_000 + (seed % 85) * 52_000)
    units = 7_500 + (seed % 60) * 260
    gross_margin_pct = safe_float(customer.get("Last 12M Gross Margin %"), 0.24 + ((seed % 18) / 100))
    gross_margin = revenue * gross_margin_pct
    current_ar = safe_float(customer.get("Current AR"), revenue * 0.035)
    overdue_ar = safe_float(customer.get("Overdue AR"), 0)
    avg_net_price = revenue / units if units else 0
    total_ar = current_ar + overdue_ar
    ar_90 = overdue_ar if safe_float(customer.get("Oldest Overdue Days")) >= 90 else 0
    ar_60 = overdue_ar if 60 <= safe_float(customer.get("Oldest Overdue Days")) < 90 else 0
    ar_30 = overdue_ar if 0 < safe_float(customer.get("Oldest Overdue Days")) < 60 else 0
    risk = calculate_customer_risk(str(customer.get("Credit Status", "Good")), total_ar, overdue_ar)
    return {
        "Revenue last 12 months": revenue,
        "Units last 12 months": units,
        "Average net price last 12 months": avg_net_price,
        "Gross margin last 12 months": gross_margin,
        "Gross margin %": gross_margin_pct,
        "Total AR": total_ar,
        "Current AR": current_ar,
        "30+ days AR": ar_30,
        "60+ days AR": ar_60,
        "90+ days AR": ar_90,
        "Overdue AR": overdue_ar,
        "Risk Flag": risk,
    }


def calculate_financial_impact(lines: pd.DataFrame, plan_df: pd.DataFrame, incremental_df: pd.DataFrame, included_in_plan: bool) -> dict:
    proposed_revenue = safe_float(lines["Extended Proposed"].sum()) if not lines.empty else 0
    proposed_gp = safe_float(((lines["Proposed Unit Price"] - lines["Unit Cost"]) * lines["Quantity"]).sum()) if not lines.empty else 0
    proposed_margin = calculate_margin_pct(proposed_revenue, proposed_gp)
    if included_in_plan and not plan_df.empty:
        planned_revenue = safe_float(plan_df["Planned Revenue"].sum())
        net_variance = safe_float(plan_df["Revenue Variance"].sum())
        planned_gp = safe_float(plan_df["Planned Gross Profit"].sum())
        gp_variance = safe_float(plan_df["Gross Profit Variance"].sum())
        context = "Variance to latest financial plan"
    else:
        planned_revenue = 0
        planned_gp = 0
        net_variance = proposed_revenue
        gp_variance = proposed_gp
        context = "Incremental opportunity"
    return {
        "Context": context,
        "Planned Revenue": planned_revenue,
        "Proposed Revenue": proposed_revenue,
        "Net Revenue Variance": net_variance,
        "Revenue Variance": net_variance,
        "Planned Gross Profit": planned_gp,
        "Proposed Gross Profit": proposed_gp,
        "Gross Profit Variance": gp_variance,
        "Proposed Margin %": proposed_margin,
    }


def calculate_irp_risk(visibility: str, purpose: str, customer_risk: str) -> str:
    if str(visibility) == "Public":
        return "High"
    if str(purpose) in {"Tender", "Strategic account"} or str(customer_risk) == "High":
        return "Medium"
    return "Low"


def calculate_decision_score(
    summary: dict,
    plan_df: pd.DataFrame,
    incremental_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    aging_df: pd.DataFrame,
    competitor_df: pd.DataFrame,
    route_df: pd.DataFrame,
    included_in_plan: bool,
) -> tuple[pd.DataFrame, int, str, str]:
    margin_score = 18
    if included_in_plan and not plan_df.empty:
        gp_variance = safe_float(plan_df["Gross Profit Variance"].sum())
        net_variance = safe_float(plan_df["Net Revenue Variance"].sum())
        if gp_variance < -250_000:
            margin_score -= 8
        elif gp_variance < 0:
            margin_score -= 4
        if net_variance < -1_000_000:
            margin_score -= 4
    elif not incremental_df.empty:
        margin_diff = safe_float(incremental_df["Margin Difference"].dropna().mean())
        price_vs_hist = safe_float(incremental_df["Price vs Historical Price %"].dropna().mean())
        if margin_diff < -0.03:
            margin_score -= 7
        elif margin_diff < -0.01:
            margin_score -= 4
        if price_vs_hist < -0.04:
            margin_score -= 3
    if summary["margin_pct"] is not None and summary["margin_pct"] < summary["weighted_target_margin"]:
        margin_score -= 3

    strategic_score = 12
    roles = set(route_df["Role"]) if not route_df.empty else set()
    if "Market Access Director" in roles:
        strategic_score += 3
    if "General Manager" in roles:
        strategic_score += 4
    if summary["total_proposed"] > 1_000_000:
        strategic_score += 2

    inventory_score = 18
    if not inventory_df.empty:
        high_alloc = int((inventory_df["Allocation Risk"] == "High").sum())
        medium_alloc = int((inventory_df["Allocation Risk"] == "Medium").sum())
        high_cannibal = int((inventory_df["Cannibalization Risk"] == "High").sum())
        inventory_score -= high_alloc * 6 + medium_alloc * 2 + high_cannibal * 3
    if not aging_df.empty and (aging_df["Near Expiry Inventory"] == "Yes").any():
        inventory_score += 2

    competitive_score = 18
    if not competitor_df.empty:
        competitive_score -= int((competitor_df["Aggressive Competitor Pricing"] == "Yes").sum()) * 3
        competitive_score -= int((competitor_df["Incumbent Competitor"] == "Yes").sum()) * 2
        competitive_score -= int((competitor_df["Supply Issues"] == "Yes").sum()) * 1

    risk_score = 18
    if "Finance Director" in roles:
        risk_score -= 2
    if "Supply Chain Manager" in roles:
        risk_score -= 2
    if "General Manager" in roles:
        risk_score -= 2

    scores = {
        "Margin Score": max(0, min(20, int(round(margin_score)))),
        "Strategic Score": max(0, min(20, int(round(strategic_score)))),
        "Inventory Score": max(0, min(20, int(round(inventory_score)))),
        "Competitive Score": max(0, min(20, int(round(competitive_score)))),
        "Risk Score": max(0, min(20, int(round(risk_score)))),
    }
    total_score = sum(scores.values())

    has_shortage = not inventory_df.empty and safe_float(inventory_df["Inventory Shortage"].sum()) > 0
    has_near_expiry = not aging_df.empty and (aging_df["Near Expiry Inventory"] == "Yes").any()
    aggressive_pricing = not competitor_df.empty and (competitor_df["Aggressive Competitor Pricing"] == "Yes").any()
    executive_exposure = "General Manager" in roles

    if has_shortage and scores["Inventory Score"] <= 8:
        recommendation = "Request Supply Review"
    elif has_near_expiry and total_score < 70:
        recommendation = "Approve only if Aging Stock Allocated"
    elif scores["Margin Score"] <= 10 or (aggressive_pricing and scores["Competitive Score"] <= 12):
        recommendation = "Request Price Revision"
    elif executive_exposure:
        recommendation = "Escalate to GM"
    elif total_score >= 85:
        recommendation = "Approve"
    elif total_score >= 70:
        recommendation = "Approve with Conditions"
    else:
        recommendation = "Reject" if total_score < 50 else "Approve with Conditions"

    inv_reason = "inventory data is unavailable"
    if not inventory_df.empty:
        inv_reason = "; ".join(inventory_df["Finding"].dropna().astype(str).unique()[:2])
    comp_reason = "competitor data is unavailable"
    if not competitor_df.empty:
        comp_parts = []
        if aggressive_pricing:
            comp_parts.append("aggressive competitor pricing is present")
        if (competitor_df["Incumbent Competitor"] == "Yes").any():
            comp_parts.append("incumbent competitor pressure is present")
        if (competitor_df["Supply Issues"] == "Yes").any():
            comp_parts.append("competitor supply issues create a reliability opening")
        if not comp_parts:
            comp_parts.append("historical tender and nearby market signals are manageable")
        comp_reason = "; ".join(comp_parts)
    rationale = f"Selected because {inv_reason}. Competitor finding: {comp_reason}."
    display_names = {
        "Margin Score": "Margin",
        "Strategic Score": "Strategic",
        "Inventory Score": "Inventory",
        "Competitive Score": "Competitive",
        "Risk Score": "Risk",
    }
    score_df = pd.DataFrame([{"Component": display_names[key], "Score": value, "Max": 20} for key, value in scores.items()])
    return score_df, total_score, recommendation, rationale


def _money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"${float(value):,.0f}"


def generate_recommendation(
    raw_recommendation: str,
    score_df: pd.DataFrame,
    total_score: int,
    header: dict,
    inventory_df: pd.DataFrame,
    aging_df: pd.DataFrame,
    competitor_df: pd.DataFrame,
    gp_impact: dict,
    errors: list[str],
    warnings: list[str],
) -> dict[str, str]:
    score_lookup = score_df.set_index("Component")["Score"].to_dict() if not score_df.empty else {}
    margin_score = int(score_lookup.get("Margin", 0))
    risk_score = int(score_lookup.get("Risk", 0))
    customer_risk = str(header.get("Customer Risk Flag", "Low"))
    visibility = str(header.get("Visibility", "Confidential"))
    shortage = safe_float(inventory_df["Inventory Shortage"].sum()) if not inventory_df.empty else 0
    near_expiry = not aging_df.empty and (aging_df["Near Expiry Inventory"] == "Yes").any()
    aggressive = not competitor_df.empty and (competitor_df["Aggressive Competitor Pricing"] == "Yes").any()
    gp_variance = safe_float(gp_impact.get("Gross Profit Variance"))

    if errors:
        recommendation = "Request Changes"
    elif total_score < 50 or (margin_score <= 8 and risk_score <= 10):
        recommendation = "Reject"
    elif raw_recommendation in {"Escalate to GM", "Escalate"} or customer_risk == "High" or visibility == "Public":
        recommendation = "Escalate"
    elif raw_recommendation in {"Request Price Revision", "Request Supply Review"} or margin_score <= 10 or shortage > 0:
        recommendation = "Request Changes"
    elif warnings or near_expiry or aggressive or total_score < 85:
        recommendation = "Approve with Conditions"
    else:
        recommendation = "Approve"

    if gp_variance < 0 or margin_score <= 10:
        key_reason = f"Margin pressure requires review; gross profit variance is {_money(gp_variance)}."
    elif shortage > 0:
        key_reason = f"Inventory coverage is constrained by {shortage:,.0f} units."
    elif aggressive:
        key_reason = "Competitive pressure is material but manageable with documented guardrails."
    else:
        key_reason = "Deal economics and approval signals are within acceptable guardrails."

    if customer_risk == "High":
        key_risk = "High AR or credit exposure may affect collectability."
    elif visibility == "Public":
        key_risk = "Public pricing exposure may create reference-price or spillover risk."
    elif shortage > 0:
        key_risk = "Inventory allocation may constrain service levels or cannibalize other demand."
    elif aggressive:
        key_risk = "Aggressive bidder behavior may compress price and margin."
    else:
        key_risk = "No critical risk signal detected."

    if recommendation == "Approve":
        condition = "No approval condition required beyond standard commercial controls."
        next_action = "Submit to required approver queue."
    elif recommendation == "Approve with Conditions":
        condition = "Document pricing guardrail, customer commitment, and supply allocation assumptions."
        next_action = "Route for approval with conditions attached."
    elif recommendation == "Request Changes":
        condition = "Revise price, volume, supply allocation, or supporting rationale before approval."
        next_action = "Return to sales owner for update."
    elif recommendation == "Escalate":
        condition = "Executive approver must confirm strategic rationale, exposure, and exception tolerance."
        next_action = "Send to executive approval route."
    else:
        condition = "Do not proceed under current economics or risk profile."
        next_action = "Reject or rebuild the commercial offer."

    return {
        "Recommendation": recommendation,
        "Key Reason": key_reason,
        "Key Risk": key_risk,
        "Required Condition": condition,
        "Next Action": next_action,
    }


# Backward-compatible aliases used by the Streamlit MVP.
gross_profit_impact = calculate_financial_impact
score_deal = calculate_decision_score
executive_recommendation = generate_recommendation
