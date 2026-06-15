from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from deal_logic import (
    calculate_gross_profit,
    calculate_margin_pct,
    calculate_price_variance,
    calculate_revenue_variance,
    calculate_volume_variance,
    demo_customer_health,
    executive_recommendation,
    gross_profit_impact,
    safe_float,
    score_deal,
    summarize_lines,
)


BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR / "demo-data"

ROLE_ORDER = [
    "Sales Manager",
    "Pricing Analyst",
    "Market Access Director",
    "Finance Approver",
    "Operations Reviewer",
    "Legal Reviewer",
    "Commercial Executive",
]

PERSONAS = {
    "Maya Chen": "Sales Representative",
    "Jordan Blake": "Sales Manager",
    "Priya Nair": "Pricing Analyst",
    "Marcus Reed": "Market Access Director",
    "Daniel Ortiz": "Finance Approver",
    "Elena Rossi": "Operations Reviewer",
    "Aisha Khan": "Legal Reviewer",
    "Sarah Morgan": "Commercial Executive",
}

APPROVAL_STEP_STATUS = {
    "Sales Manager": "Pending Sales Manager",
    "Pricing Analyst": "Pending Pricing",
    "Finance Approver": "Pending Finance",
    "Operations Reviewer": "Pending Operations",
    "Commercial Executive": "Pending Executive",
}

STATUS_APPROVAL_STEP = {status: role for role, status in APPROVAL_STEP_STATUS.items()}

ACTIONABLE_APPROVAL_ROLES = [
    "Sales Manager",
    "Pricing Analyst",
    "Finance Approver",
    "Operations Reviewer",
    "Commercial Executive",
]

ACTIVE_APPROVAL_STATUSES = {
    "Submitted",
    "Pending Sales Manager",
    "Pending Pricing",
    "Pending Finance",
    "Pending Operations",
    "Pending Executive",
    "Changes Requested",
}

DECISIONS = ["Approve", "Request Changes", "Escalate", "Reject"]

ROLE_ALLOWED_DECISIONS = {
    "Sales Representative": [],
    "Sales Manager": ["Approve", "Request Changes", "Escalate"],
    "Pricing Analyst": ["Approve", "Request Changes", "Escalate"],
    "Finance Approver": ["Approve", "Request Changes", "Escalate"],
    "Operations Reviewer": ["Approve", "Request Changes", "Escalate"],
    "Commercial Executive": ["Approve", "Request Changes", "Reject"],
}


st.set_page_config(
    page_title="Commercial Deal Desk Copilot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
        [data-testid="stMetric"] {
            background: #f6f8fb;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 10px 12px;
        }
        .status-pill {
            display: inline-block;
            padding: 0.16rem 0.52rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 650;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
        }
        .risk-high { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .risk-medium { color: #92400e; background: #fef3c7; border-color: #fde68a; }
        .risk-low { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
        .section-note {
            color: #475569;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_sheet(filename: str, sheet_name: str) -> pd.DataFrame:
    path = DEMO_DIR / filename
    if not path.exists():
        st.error(f"Missing demo data file: {path}")
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=3)
    except Exception as exc:
        st.error(f"Could not read {filename} / {sheet_name}: {exc}")
        return pd.DataFrame()
    df = df.dropna(how="all").copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


@st.cache_data(show_spinner=False)
def load_demo_data() -> dict[str, pd.DataFrame]:
    return {
        "customers": read_sheet("Customer_Master.xlsx", "Customers"),
        "opportunities": read_sheet("Customer_Master.xlsx", "Opportunities"),
        "products": read_sheet("Product_Master.xlsx", "Products"),
        "price_book": read_sheet("Product_Master.xlsx", "Price Book"),
        "inventory_basic": read_sheet("Product_Master.xlsx", "Inventory"),
        "approval_matrix": read_sheet("Approval_Matrix.xlsx", "Approval Matrix"),
        "roles": read_sheet("Approval_Matrix.xlsx", "Roles"),
        "approver_roster": read_sheet("Approver_Roster.xlsx", "Approver Roster"),
        "deals": read_sheet("Sample_Deal_Requests.xlsx", "Deal Requests"),
        "line_items": read_sheet("Sample_Deal_Requests.xlsx", "Line Items"),
        "deal_summary": read_sheet("Sample_Deal_Requests.xlsx", "Deal Summary"),
        "commercial_plan": read_sheet("Commercial_Plan.xlsx", "Commercial Plan"),
        "price_volume": read_sheet("Price_Volume_History.xlsx", "Price Volume History"),
        "inventory_coverage": read_sheet("Inventory_Coverage.xlsx", "Inventory Coverage"),
        "expiry_aging": read_sheet("Expiry_Aging.xlsx", "Expiry Aging"),
        "tender_history": read_sheet("Tender_History.xlsx", "Tender History"),
        "competitor_intel": read_sheet("Competitor_Intelligence.xlsx", "Competitor Intelligence"),
    }


def init_state() -> None:
    st.session_state.setdefault("runtime_deals", [])
    st.session_state.setdefault("runtime_lines", [])
    st.session_state.setdefault("audit_events", [])
    st.session_state.setdefault("deal_status_overrides", {})
    st.session_state.setdefault("deal_approval_steps", {})
    st.session_state.setdefault("approval_confirmation", "")
    st.session_state.setdefault("deal_detail_confirmation", "")
    st.session_state.setdefault("selected_deal_id", None)
    st.session_state.setdefault("deal_detail_parent", "Deal Requests")
    st.session_state.setdefault("draft_lines", None)
    st.session_state.setdefault("current_page", "Deal Request List")


def add_audit(
    deal_id: str,
    action: str,
    entity: str = "Deal",
    details: str = "",
    decision: str = "",
    comment: str = "",
    approval_step: str = "",
    previous_status: str = "",
    new_status: str = "",
) -> None:
    event = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Deal ID": deal_id,
        "Actor": st.session_state.get("persona", "Demo User"),
        "Role": st.session_state.get("role", "Demo Role"),
        "Action": action,
        "Entity": entity,
        "Details": details,
        "Source": "Streamlit MVP v1",
        "Correlation ID": str(uuid4())[:8],
    }
    if decision:
        event["Decision"] = decision
    if comment:
        event["Comment"] = comment
    if approval_step:
        event["Approval Step"] = approval_step
    if previous_status:
        event["Previous Status"] = previous_status
    if new_status:
        event["New Status"] = new_status
    st.session_state.audit_events.append(event)


def money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"${float(value):,.0f}"


def pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def status_badge(value: str) -> str:
    return f"<span class='status-pill'>{value}</span>"


def risk_badge(value: str) -> str:
    risk_class = {
        "High": "risk-high",
        "Medium": "risk-medium",
        "Low": "risk-low",
    }.get(str(value), "")
    return f"<span class='status-pill {risk_class}'>{value}</span>"


def demo_commercial_price_defaults(data: dict[str, pd.DataFrame], sku: str) -> dict[str, float]:
    prod = product_lookup(data).get(str(sku), {})
    list_price = float(prod.get("WAC / List Price", 0) or 0)
    return {
        "Unit List Price": round(list_price, 2),
        "Gross Price": round(list_price * 0.98, 2),
        "Floor Price": round(list_price * 0.72, 2),
        "Guidance Price": round(list_price * 0.84, 2),
        "Walk-away Price": round(list_price * 0.68, 2),
    }


def ensure_commercial_line_columns(lines: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    enriched = lines.copy()
    if enriched.empty or "SKU" not in enriched:
        return enriched
    for idx, row in enriched.iterrows():
        defaults = demo_commercial_price_defaults(data, row.get("SKU", ""))
        for col, value in defaults.items():
            if col not in enriched.columns:
                enriched[col] = None
            enriched.at[idx, col] = value
        if "Requested Net Price" not in enriched.columns:
            enriched["Requested Net Price"] = None
        requested = row.get("Requested Net Price", row.get("Proposed Unit Price", None))
        if pd.isna(requested) or requested == "":
            requested = float(defaults["Unit List Price"]) * 0.9
        enriched.at[idx, "Requested Net Price"] = round(float(requested), 2)
        enriched.at[idx, "Proposed Unit Price"] = round(float(requested), 2)
        list_price = float(enriched.at[idx, "Unit List Price"] or 0)
        discount = 0 if list_price == 0 else (list_price - float(requested)) / list_price
        enriched.at[idx, "Requested Discount %"] = discount * 100
    return enriched


def get_runtime_deals_df() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.runtime_deals)


def get_runtime_lines_df() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.runtime_lines)


def combined_deals(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    seed = data["deals"].copy()
    runtime = get_runtime_deals_df()
    if not runtime.empty:
        seed = pd.concat([seed, runtime], ignore_index=True, sort=False)
    overrides = st.session_state.get("deal_status_overrides", {})
    if overrides and not seed.empty:
        for deal_id, values in overrides.items():
            mask = seed["Deal ID"].astype(str).eq(str(deal_id))
            for key, value in values.items():
                seed.loc[mask, key] = value
    return seed


def combined_lines(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    seed = data["line_items"].copy()
    runtime = get_runtime_lines_df()
    if not runtime.empty:
        seed = pd.concat([seed, runtime], ignore_index=True, sort=False)
    return seed


def navigate_to_deal_detail(deal_id: str, source: str) -> None:
    st.session_state.selected_deal_id = deal_id
    st.session_state.current_page = "Deal Detail"
    st.session_state.deal_detail_parent = "Approval Queue" if "approval" in source.lower() else "Deal Requests"
    add_audit(deal_id, "Deal viewed", details=f"Opened from {source}.")
    st.rerun()


def set_current_page(page: str) -> None:
    st.session_state.current_page = page
    st.rerun()


def get_selected_dataframe_deal_id(table_event: object, display_df: pd.DataFrame) -> str | None:
    if display_df.empty:
        return None
    if isinstance(table_event, dict):
        selected_rows = table_event.get("selection", {}).get("rows", [])
    else:
        selected_rows = getattr(getattr(table_event, "selection", None), "rows", [])
    if selected_rows:
        return str(display_df.iloc[selected_rows[0]]["Deal ID"])
    return None


def update_deal_status(
    deal_id: str,
    status: str,
    decision: str,
    comment: str,
    approval_step: str = "",
    previous_status: str = "",
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_runtime = False
    for deal in st.session_state.runtime_deals:
        if str(deal.get("Deal ID")) == str(deal_id):
            deal["Status"] = status
            deal["Last Decision"] = decision
            deal["Last Decision Comment"] = comment
            deal["Last Decision Timestamp"] = timestamp
            deal["Last Decision Actor"] = st.session_state.get("persona", "Demo User")
            deal["Last Decision Role"] = st.session_state.get("role", "Demo Role")
            deal["Last Approval Step"] = approval_step
            deal["Previous Status"] = previous_status
            updated_runtime = True
            break
    if not updated_runtime:
        st.session_state.deal_status_overrides[str(deal_id)] = {
            "Status": status,
            "Last Decision": decision,
            "Last Decision Comment": comment,
            "Last Decision Timestamp": timestamp,
            "Last Decision Actor": st.session_state.get("persona", "Demo User"),
            "Last Decision Role": st.session_state.get("role", "Demo Role"),
            "Last Approval Step": approval_step,
            "Previous Status": previous_status,
        }


def actionable_route_roles(route_df: pd.DataFrame) -> list[str]:
    if route_df.empty or "Role" not in route_df:
        return ["Sales Manager"]
    roles = [role for role in route_df["Role"].astype(str).tolist() if role in ACTIONABLE_APPROVAL_ROLES]
    return roles or ["Sales Manager"]


def completed_approval_steps(deal_id: str) -> list[str]:
    return list(st.session_state.get("deal_approval_steps", {}).get(str(deal_id), []))


def current_required_approval_role(deal_id: str, status: str, route_df: pd.DataFrame) -> str:
    clean_status = str(status or "").strip()
    if clean_status in {"Rejected", "Final Approved"}:
        return ""
    if clean_status == "Changes Requested":
        return "Sales Representative"
    if clean_status in STATUS_APPROVAL_STEP:
        return STATUS_APPROVAL_STEP[clean_status]
    roles = actionable_route_roles(route_df)
    completed = set(completed_approval_steps(deal_id))
    for role in roles:
        if role not in completed:
            return role
    return roles[-1] if roles else "Sales Manager"


def next_approval_status(deal_id: str, current_role: str, route_df: pd.DataFrame) -> str:
    roles = actionable_route_roles(route_df)
    if current_role == "Commercial Executive" and current_role not in roles:
        completed = completed_approval_steps(deal_id)
        if current_role not in completed:
            completed.append(current_role)
        st.session_state.deal_approval_steps[str(deal_id)] = completed
        return "Final Approved"
    completed = completed_approval_steps(deal_id)
    if current_role and current_role not in completed and current_role in roles:
        completed.append(current_role)
    st.session_state.deal_approval_steps[str(deal_id)] = completed
    for role in roles:
        if role not in completed:
            return APPROVAL_STEP_STATUS[role]
    return "Final Approved"


def allowed_decisions_for_role(role: str) -> list[str]:
    return ROLE_ALLOWED_DECISIONS.get(role, [])


def process_approval_decision(deal_id: str, decision: str, comment: str, route_df: pd.DataFrame, previous_status: str) -> tuple[bool, str]:
    current_role = current_required_approval_role(deal_id, previous_status, route_df)
    user_role = st.session_state.get("role", "Demo Role")
    allowed = allowed_decisions_for_role(user_role)
    if user_role != current_role or decision not in allowed:
        return False, f"{user_role} cannot capture `{decision}` for this step. Current required role is {current_role or 'none'}."

    if decision == "Approve":
        new_status = next_approval_status(deal_id, current_role, route_df)
    elif decision == "Request Changes":
        new_status = "Changes Requested"
    elif decision == "Reject":
        new_status = "Rejected"
    else:
        new_status = "Pending Executive"

    update_deal_status(deal_id, new_status, decision, comment, approval_step=current_role, previous_status=previous_status)
    add_audit(
        deal_id,
        f"Approval decision: {decision}",
        entity="Approval Step",
        details=f"Status changed from {previous_status} to {new_status}.",
        decision=decision,
        comment=comment,
        approval_step=current_role,
        previous_status=previous_status,
        new_status=new_status,
    )
    return True, f"Captured {decision} for {deal_id}. Status moved from {previous_status} to {new_status}."


def product_lookup(data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    if data["products"].empty:
        return {}
    return data["products"].set_index("SKU").to_dict("index")


def customer_lookup(data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    if data["customers"].empty:
        return {}
    return data["customers"].set_index("Customer Name").to_dict("index")


def normalize_lines(line_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    products = product_lookup(data)
    rows = []
    for _, row in line_df.dropna(how="all").iterrows():
        sku = str(row.get("SKU", "")).strip()
        if not sku or sku == "nan" or sku not in products:
            continue
        prod = products[sku]
        qty = float(row.get("Quantity", 0) or 0)
        list_price = float(row.get("Unit List Price", prod.get("WAC / List Price", 0)) or 0)
        gross_price = float(row.get("Gross Price", list_price * 0.98) or 0)
        proposed = float(row.get("Requested Net Price", row.get("Proposed Unit Price", 0)) or 0)
        floor_price = float(row.get("Floor Price", list_price * 0.72) or 0)
        guidance_price = float(row.get("Guidance Price", list_price * 0.84) or 0)
        walkaway_price = float(row.get("Walk-away Price", list_price * 0.68) or 0)
        unit_cost = float(row.get("Unit Cost", prod.get("Standard Cost", 0)) or 0)
        extended_list = qty * list_price
        extended_gross = qty * gross_price
        extended_proposed = qty * proposed
        discount = 0 if list_price == 0 else (list_price - proposed) / list_price
        margin = calculate_margin_pct(extended_proposed, calculate_gross_profit(proposed, unit_cost, qty))
        rows.append(
            {
                "SKU": sku,
                "Product Name": prod.get("Product Name", row.get("Product Name", "")),
                "Therapeutic Area": prod.get("Therapeutic Area", ""),
                "Product Type": prod.get("Product Type", ""),
                "Quantity": qty,
                "Unit List Price": list_price,
                "List Price": list_price,
                "Gross Price": gross_price,
                "Unit Cost": unit_cost,
                "Proposed Unit Price": proposed,
                "Requested Net Price": proposed,
                "Floor Price": floor_price,
                "Guidance Price": guidance_price,
                "Walk-away Price": walkaway_price,
                "Extended List": extended_list,
                "Extended Gross": extended_gross,
                "Extended Proposed": extended_proposed,
                "Extended Requested Net": extended_proposed,
                "Discount %": discount,
                "Requested Discount %": discount,
                "Margin %": margin,
                "Estimated Gross Margin %": margin,
                "Target Margin %": prod.get("Target Margin %", 0),
                "Requested Delivery Date": row.get("Requested Delivery Date", None),
                "Storage": prod.get("Storage", ""),
                "Supply Risk": prod.get("Supply Risk", ""),
                "Inventory Tracked": prod.get("Inventory Tracked", ""),
                "Notes": row.get("Notes", ""),
            }
        )
    return pd.DataFrame(rows)


def find_inventory(data: dict[str, pd.DataFrame], sku: str, region: str) -> pd.Series | None:
    inv = data["inventory_coverage"]
    if inv.empty or "SKU" not in inv:
        return None
    subset = inv[inv["SKU"].astype(str).eq(sku)]
    if subset.empty:
        return None
    regional = subset[subset["Region"].astype(str).eq(region)]
    if regional.empty:
        regional = subset
    return regional.sort_values("Coverage Days").iloc[0]


def find_expiry(data: dict[str, pd.DataFrame], sku: str, region: str) -> pd.Series | None:
    aging = data["expiry_aging"]
    if aging.empty or "SKU" not in aging:
        return None
    subset = aging[aging["SKU"].astype(str).eq(sku)]
    if subset.empty:
        return None
    regional = subset[subset["Region"].astype(str).eq(region)]
    if regional.empty:
        regional = subset
    eligible = regional[
        (pd.to_numeric(regional["Days To Expiry"], errors="coerce") > 0)
        & (regional["Quality Status"].astype(str).str.lower().ne("expired"))
    ]
    if not eligible.empty:
        regional = eligible
    return regional.sort_values("Days To Expiry").iloc[0]


def find_plan_match(data: dict[str, pd.DataFrame], line: pd.Series, region: str, segment: str) -> pd.Series | None:
    plan = data["commercial_plan"]
    if plan.empty or "SKU" not in plan:
        return None
    subset = plan[plan["SKU"].astype(str).eq(str(line["SKU"]))]
    if subset.empty:
        return None
    regional = subset[subset["Region"].astype(str).eq(region)]
    if regional.empty:
        regional = subset
    segmented = regional[regional["Segment"].astype(str).eq(segment)]
    if not segmented.empty:
        regional = segmented
    return regional.iloc[0]


def price_volume_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, channel: str) -> pd.DataFrame:
    history = data["price_volume"]
    if history.empty or lines.empty:
        return pd.DataFrame()
    rows = []
    for _, line in lines.iterrows():
        subset = history[history["SKU"].astype(str).eq(str(line["SKU"]))]
        if subset.empty:
            continue
        customer_subset = subset[subset["Customer"].astype(str).eq(customer)]
        if customer_subset.empty:
            customer_subset = subset[subset["Channel"].astype(str).eq(channel)]
        if customer_subset.empty:
            customer_subset = subset
        rows.append(
            {
                "SKU": line["SKU"],
                "Requested Discount": line["Discount %"],
                "Historical Approved Discount": customer_subset["Approved Discount %"].astype(float).mean(),
                "Historical Approved Net": customer_subset["Approved Net Price"].astype(float).mean(),
                "Comparable Rows": len(customer_subset),
            }
        )
    return pd.DataFrame(rows)


def tender_competitor_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, region: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    tender = data["tender_history"]
    intel = data["competitor_intel"]
    tender_rows = []
    intel_rows = []
    for _, line in lines.iterrows():
        sku = str(line["SKU"])
        if not tender.empty:
            t = tender[tender["SKU"].astype(str).eq(sku)]
            exact = t[t["Tendering Account"].astype(str).eq(customer)]
            if exact.empty:
                exact = t[t["Region"].astype(str).eq(region)]
            if exact.empty:
                exact = t
            if not exact.empty:
                r = exact.sort_values("Tender Date", ascending=False).iloc[0]
                tender_rows.append(
                    {
                        "SKU": sku,
                        "Tender ID": r.get("Tender ID"),
                        "Tendering Account": r.get("Tendering Account"),
                        "Outcome": r.get("Outcome"),
                        "Winning Discount %": r.get("Winning Discount %"),
                        "Primary Competitor": r.get("Primary Competitor"),
                        "Driver": r.get("Loss / Win Driver"),
                    }
                )
        if not intel.empty:
            c = intel[(intel["SKU"].astype(str).eq(sku)) | (intel["Customer"].astype(str).eq(customer))]
            if c.empty:
                c = intel[intel["Region"].astype(str).eq(region)]
            if not c.empty:
                r = c.sort_values("Observed Date", ascending=False).iloc[0]
                intel_rows.append(
                    {
                        "SKU": sku,
                        "Competitor": r.get("Competitor"),
                        "Signal": r.get("Signal Type"),
                        "Confidence": r.get("Confidence"),
                        "Freshness": r.get("Freshness"),
                        "Response": r.get("Recommended Response"),
                    }
                )
    return pd.DataFrame(tender_rows), pd.DataFrame(intel_rows)


def plan_impact_analysis(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str, segment: str) -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        match = find_plan_match(data, line, region, segment)
        if match is None:
            continue
        planned_price = safe_float(match.get("Planned Net Price"))
        planned_qty = safe_float(match.get("Plan Units"))
        new_price = safe_float(line.get("Proposed Unit Price"))
        new_qty = safe_float(line.get("Quantity"))
        standard_cost = safe_float(match.get("Standard Cost"), safe_float(line.get("Unit Cost")))
        planned_revenue = planned_price * planned_qty
        proposed_revenue = new_price * new_qty
        planned_gp = calculate_gross_profit(planned_price, standard_cost, planned_qty)
        proposed_gp = calculate_gross_profit(new_price, standard_cost, new_qty)
        price_variance = calculate_price_variance(new_price, planned_price, new_qty)
        volume_variance = calculate_volume_variance(new_qty, planned_qty, new_price)
        revenue_variance = calculate_revenue_variance(price_variance, volume_variance)
        rows.append(
            {
                "SKU": line["SKU"],
                "Product": line["Product Name"],
                "Planned Price": planned_price,
                "New Price": new_price,
                "Planned Net Price": planned_price,
                "Proposed Net Price": new_price,
                "Planned Quantity": planned_qty,
                "New Quantity": new_qty,
                "Planned Revenue": planned_revenue,
                "Proposed Revenue": proposed_revenue,
                "Price Variance": price_variance,
                "Volume Variance": volume_variance,
                "Revenue Variance": revenue_variance,
                "Net Revenue Variance": revenue_variance,
                "Planned Gross Profit": planned_gp,
                "Proposed Gross Profit": proposed_gp,
                "Gross Profit Variance": proposed_gp - planned_gp,
                "Planned Margin %": calculate_margin_pct(planned_revenue, planned_gp),
                "Proposed Margin %": calculate_margin_pct(proposed_revenue, proposed_gp),
            }
        )
    return pd.DataFrame(rows)


def incremental_opportunity_analysis(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, channel: str) -> pd.DataFrame:
    history = data["price_volume"]
    rows = []
    for _, line in lines.iterrows():
        sku = str(line["SKU"])
        proposed_price = safe_float(line.get("Proposed Unit Price"))
        proposed_qty = safe_float(line.get("Quantity"))
        unit_cost = safe_float(line.get("Unit Cost"))
        hist = history[history["SKU"].astype(str).eq(sku)] if not history.empty else pd.DataFrame()
        if not hist.empty:
            customer_hist = hist[hist["Customer"].astype(str).eq(customer)]
            if customer_hist.empty:
                customer_hist = hist[hist["Channel"].astype(str).eq(channel)]
            if customer_hist.empty:
                customer_hist = hist
            avg_price = safe_float(customer_hist["Approved Net Price"].astype(float).mean())
        else:
            avg_price = 0
        hist_margin = calculate_margin_pct(avg_price, calculate_gross_profit(avg_price, unit_cost, 1))
        proposed_margin = calculate_margin_pct(proposed_price, calculate_gross_profit(proposed_price, unit_cost, 1))
        incremental_revenue = proposed_price * proposed_qty
        incremental_gp = calculate_gross_profit(proposed_price, unit_cost, proposed_qty)
        rows.append(
            {
                "SKU": sku,
                "Product": line["Product Name"],
                "Incremental Revenue": incremental_revenue,
                "Incremental Gross Profit": incremental_gp,
                "Average Historical Price": avg_price,
                "Historical Average Net Price": avg_price,
                "Price vs Historical Price %": None if avg_price <= 0 else (proposed_price - avg_price) / avg_price,
                "Historical Average Margin %": hist_margin,
                "Historical Margin %": hist_margin,
                "Proposed Margin %": proposed_margin,
                "Margin Difference": None if hist_margin is None or proposed_margin is None else proposed_margin - hist_margin,
                "Margin Difference vs Historical Margin %": None if hist_margin is None or proposed_margin is None else proposed_margin - hist_margin,
            }
        )
    return pd.DataFrame(rows)


def enhanced_inventory_analysis(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str) -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        inv = find_inventory(data, str(line["SKU"]), region)
        if inv is None:
            continue
        requested = safe_float(line.get("Quantity"))
        available = safe_float(inv.get("Available Qty"))
        avg_monthly = safe_float(inv.get("Avg Monthly Demand"))
        coverage_days = safe_float(inv.get("Coverage Days"))
        lead_time = safe_float(inv.get("Lead Time Days"))
        shortage = max(requested - available, 0)
        excess = max(available - requested, 0)
        allocation_note = str(inv.get("Allocation Note", ""))
        coverage_status = str(inv.get("Coverage Status", ""))
        allocation_risk = "High" if shortage > 0 or coverage_days < lead_time else "Medium" if "Watch" in allocation_note or coverage_days < 45 else "Low"
        cannibalization_risk = "High" if shortage > 0 else "Medium" if avg_monthly > 0 and requested > avg_monthly * 0.5 else "Low"
        rows.append(
            {
                "SKU": line["SKU"],
                "Requested Qty": requested,
                "Available Qty": available,
                "Excess Inventory": excess,
                "Inventory Shortage": shortage,
                "Demand Forecast": avg_monthly,
                "Coverage Days": coverage_days,
                "Lead Time Days": lead_time,
                "Coverage Status": coverage_status,
                "Allocation Risk": allocation_risk,
                "Cannibalization Risk": cannibalization_risk,
                "Finding": f"{allocation_risk} allocation risk; {cannibalization_risk.lower()} cannibalization risk; {coverage_status}; {allocation_note}".strip("; "),
            }
        )
    return pd.DataFrame(rows)


def enhanced_aging_analysis(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str) -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        exp = find_expiry(data, str(line["SKU"]), region)
        if exp is None:
            continue
        days = safe_float(exp.get("Days To Expiry"))
        near_expiry = "Yes" if 0 < days <= 180 else "No"
        aging_inventory = "Yes" if 0 < days <= 365 else "No"
        rows.append(
            {
                "SKU": line["SKU"],
                "Lot ID": exp.get("Lot ID"),
                "Days To Expiry": days,
                "Expiry Bucket": exp.get("Expiry Bucket"),
                "Near Expiry Inventory": near_expiry,
                "Aging Inventory": aging_inventory,
                "Quantity On Hand": exp.get("Quantity On Hand"),
                "Quality Status": exp.get("Quality Status"),
                "Disposition": exp.get("Disposition Recommendation"),
            }
        )
    return pd.DataFrame(rows)


def enhanced_competitor_intelligence(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, region: str) -> pd.DataFrame:
    tender_df, intel_df = tender_competitor_summary(data, lines, customer, region)
    rows = []
    for _, line in lines.iterrows():
        sku = str(line["SKU"])
        tender_row = tender_df[tender_df["SKU"].astype(str).eq(sku)]
        intel_row = intel_df[intel_df["SKU"].astype(str).eq(sku)]
        tender = tender_row.iloc[0] if not tender_row.empty else pd.Series(dtype=object)
        intel = intel_row.iloc[0] if not intel_row.empty else pd.Series(dtype=object)
        signal = str(intel.get("Signal", ""))
        driver = str(tender.get("Driver", ""))
        response = str(intel.get("Response", ""))
        competitor = str(intel.get("Competitor", tender.get("Primary Competitor", "")))
        aggressive_price = "Yes" if "price" in signal.lower() or "price" in driver.lower() else "No"
        incumbent = "Yes" if "incumbent" in signal.lower() or "incumb" in driver.lower() else "No"
        supply_issue = "Yes" if "supply" in signal.lower() or "supply" in response.lower() or "supply" in driver.lower() else "No"
        nearby_behavior = "Current regional signal" if not intel_row.empty else "Historical tender proxy"
        rows.append(
            {
                "SKU": sku,
                "Historical Tender Outcome": tender.get("Outcome", "n/a"),
                "Historical Tender Discount": tender.get("Winning Discount %", None),
                "Incumbent Competitor": incumbent,
                "Aggressive Competitor Pricing": aggressive_price,
                "Supply Issues": supply_issue,
                "Nearby Market Behavior": nearby_behavior,
                "Competitor": competitor,
                "Recommended Response": response or tender.get("Driver", ""),
            }
        )
    return pd.DataFrame(rows)


def inventory_aging_recommendation(inventory_df: pd.DataFrame, aging_df: pd.DataFrame) -> str:
    findings = []
    if not inventory_df.empty:
        shortage = safe_float(inventory_df["Inventory Shortage"].sum())
        high_allocation = int((inventory_df["Allocation Risk"] == "High").sum())
        excess = safe_float(inventory_df["Excess Inventory"].sum())
        if shortage > 0 or high_allocation:
            findings.append(f"Supply review recommended: {shortage:,.0f} units short and {high_allocation} line(s) with high allocation risk.")
        elif excess > 0:
            findings.append(f"Inventory can support the request with {excess:,.0f} units of excess coverage across analyzed lines.")
        else:
            findings.append("Inventory appears balanced against requested quantity and demand forecast.")
    if not aging_df.empty:
        near_expiry = int((aging_df["Near Expiry Inventory"] == "Yes").sum())
        aging = int((aging_df["Aging Inventory"] == "Yes").sum())
        if near_expiry:
            findings.append(f"Use FEFO allocation and prioritize {near_expiry} near-expiry line(s) where quality status permits.")
        elif aging:
            findings.append(f"Aging inventory exists on {aging} line(s); allocate older released lots first.")
        else:
            findings.append("No near-expiry inventory condition is required beyond standard FEFO controls.")
    return " ".join(findings) if findings else "Inventory and aging data is not available for this deal."


def competitor_summary(competitor_df: pd.DataFrame) -> str:
    if competitor_df.empty:
        return "No competitor intelligence was found for the selected deal lines."
    aggressive = int((competitor_df["Aggressive Competitor Pricing"] == "Yes").sum())
    incumbent = int((competitor_df["Incumbent Competitor"] == "Yes").sum())
    supply = int((competitor_df["Supply Issues"] == "Yes").sum())
    responses = competitor_df["Recommended Response"].dropna().astype(str)
    summary = []
    if aggressive:
        summary.append(f"{aggressive} line(s) show aggressive competitor pricing pressure.")
    if incumbent:
        summary.append(f"{incumbent} line(s) have incumbent competitor pressure.")
    if supply:
        summary.append(f"{supply} line(s) indicate competitor supply issues that may create a reliability opening.")
    if not summary:
        summary.append("Historical tender and nearby-market signals are manageable.")
    if not responses.empty:
        summary.append(f"Recommended response: {responses.iloc[0]}.")
    return " ".join(summary)


def route_with_trigger_reasons(route_df: pd.DataFrame, inventory_df: pd.DataFrame, competitor_df: pd.DataFrame, gp_impact: dict) -> pd.DataFrame:
    if route_df.empty:
        return route_df
    rows = []
    shortage = safe_float(inventory_df["Inventory Shortage"].sum()) if not inventory_df.empty else 0
    aggressive_pricing = not competitor_df.empty and (competitor_df["Aggressive Competitor Pricing"] == "Yes").any()
    incumbent = not competitor_df.empty and (competitor_df["Incumbent Competitor"] == "Yes").any()
    for _, row in route_df.iterrows():
        trigger = row["Reason"]
        role = row["Role"]
        if role == "Pricing Analyst" and aggressive_pricing:
            trigger += " Competitor pricing signals require guardrail review."
        if role == "Market Access Director" and incumbent:
            trigger += " Incumbent competitor or access defense is present."
        if role == "Finance Approver":
            trigger += f" Gross profit variance is {money(gp_impact['Gross Profit Variance'])}."
        if role == "Operations Reviewer" and shortage > 0:
            trigger += f" Inventory shortage is {shortage:,.0f} units across requested lines."
        if role == "Commercial Executive":
            trigger += " GM-level visibility is recommended for strategic exposure."
        item = row.to_dict()
        item["Trigger Reason"] = trigger
        rows.append(item)
    return pd.DataFrame(rows)


def approval_route_dashboard(route_df: pd.DataFrame, header: dict, lines: pd.DataFrame, inventory_df: pd.DataFrame, competitor_df: pd.DataFrame, gp_impact: dict) -> pd.DataFrame:
    trigger_df = route_with_trigger_reasons(route_df, inventory_df, competitor_df, gp_impact)
    if trigger_df.empty:
        return trigger_df
    rows = []
    customer_risk = str(header.get("Customer Risk Flag", "Low"))
    visibility = str(header.get("Visibility", "Confidential"))
    purpose = str(header.get("Purpose", ""))
    shortage = safe_float(inventory_df["Inventory Shortage"].sum()) if not inventory_df.empty else 0
    aggressive = not competitor_df.empty and (competitor_df["Aggressive Competitor Pricing"] == "Yes").any()
    for _, row in trigger_df.iterrows():
        role = str(row.get("Role", ""))
        reason = str(row.get("Trigger Reason", row.get("Reason", "")))
        if role == "Pricing Analyst" and not lines.empty and (lines["Requested Net Price"] < lines["Floor Price"]).any():
            reason += " Margin below floor."
        if role == "Finance Approver" and customer_risk in {"Medium", "High"}:
            reason += f" {customer_risk} AR exposure."
        if role in {"Market Access Director", "Commercial Executive"} and purpose == "Strategic account":
            reason += " Strategic account."
        if role == "Operations Reviewer" and shortage > 0:
            reason += " High inventory risk."
        if role in {"Pricing Analyst", "Commercial Executive"} and visibility == "Public":
            reason += " Public pricing exposure."
        if role == "Pricing Analyst" and aggressive:
            reason += " Aggressive competitor pricing."
        item = row.to_dict()
        item["Approver"] = role
        item["Trigger Reason"] = reason
        rows.append(item)
    display_cols = [col for col in ["Sequence", "Approver", "Role", "Trigger Reason", "SLA Hours"] if col in pd.DataFrame(rows)]
    return pd.DataFrame(rows)[display_cols]


def build_deal_context(data: dict[str, pd.DataFrame], deal_id: str) -> dict | None:
    deals = combined_deals(data)
    if deals.empty or deal_id not in set(deals["Deal ID"].astype(str)):
        return None
    deal = deals[deals["Deal ID"].astype(str).eq(str(deal_id))].iloc[0].to_dict()
    lines = combined_lines(data)
    calc_lines = normalize_lines(lines[lines["Deal ID"].astype(str).eq(str(deal_id))], data)
    summary = summarize_lines(calc_lines)
    customer = deal.get("Customer Name", "")
    region = deal.get("Region", "")
    segment = deal.get("Segment", "")
    account = customer_lookup(data).get(customer, {})
    channel = account.get("Account Type", "")
    included_value = str(deal.get("Included_In_Latest_Financial_Plan", "Yes")).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, calc_lines, region, segment)
    incremental_df = incremental_opportunity_analysis(data, calc_lines, customer, channel)
    inventory_df = enhanced_inventory_analysis(data, calc_lines, region)
    aging_df = enhanced_aging_analysis(data, calc_lines, region)
    competitor_df = enhanced_competitor_intelligence(data, calc_lines, customer, region)
    gp_impact = gross_profit_impact(calc_lines, plan_df, incremental_df, included_in_plan)
    header = {
        "Customer Name": customer,
        "Region": region,
        "Segment": segment,
        "Account Type": channel,
        "Channel": deal.get("Channel", channel),
        "Payment Terms": deal.get("Payment Terms"),
        "Contract Months": deal.get("Contract Months", 0),
        "Special Terms Requested": False,
    }
    route_df = route_preview(header, calc_lines, summary, data)
    score_df, total_score, recommendation, rationale = score_deal(
        summary,
        plan_df,
        incremental_df,
        inventory_df,
        aging_df,
        competitor_df,
        route_df,
        included_in_plan,
    )
    route_triggers = route_with_trigger_reasons(route_df, inventory_df, competitor_df, gp_impact)
    return {
        "deal": deal,
        "lines": calc_lines,
        "summary": summary,
        "included_value": included_value,
        "included_in_plan": included_in_plan,
        "plan_df": plan_df,
        "incremental_df": incremental_df,
        "inventory_df": inventory_df,
        "aging_df": aging_df,
        "competitor_df": competitor_df,
        "gp_impact": gp_impact,
        "route_df": route_df,
        "route_triggers": route_triggers,
        "score_df": score_df,
        "total_score": total_score,
        "recommendation": recommendation,
        "rationale": rationale,
    }


def render_inline_deal_preview(context: dict, compact: bool = False) -> None:
    deal = context["deal"]
    gp_impact = context["gp_impact"]
    st.subheader("Selected Deal Preview")
    st.write(
        f"**{deal.get('Deal Title', '')}** · {deal.get('Customer Name', '')} · "
        f"Status: **{deal.get('Status', '')}** · Plan flag: **{context['included_value']}**"
    )
    metrics = st.columns(4)
    metrics[0].metric("Proposed Value", money(gp_impact["Proposed Revenue"]))
    metrics[1].metric("Decision Score", f"{context['total_score']}/100")
    metrics[2].metric("Recommendation", context["recommendation"])
    metrics[3].metric("Gross Profit Impact", money(gp_impact["Gross Profit Variance"]))
    st.caption(context["rationale"])
    if compact:
        st.info(inventory_aging_recommendation(context["inventory_df"], context["aging_df"]))
        st.info(competitor_summary(context["competitor_df"]))
        return
    left, right = st.columns(2)
    with left:
        st.markdown("**Inventory / Aging Summary**")
        st.info(inventory_aging_recommendation(context["inventory_df"], context["aging_df"]))
        st.dataframe(context["inventory_df"], use_container_width=True, hide_index=True)
        st.dataframe(context["aging_df"], use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Competitor Summary**")
        st.info(competitor_summary(context["competitor_df"]))
        st.dataframe(context["competitor_df"], use_container_width=True, hide_index=True)
    st.markdown("**Approval Route Trigger Reasons**")
    st.dataframe(context["route_triggers"], use_container_width=True, hide_index=True)


def approval_review_summary(context: dict) -> dict:
    summary = context["summary"]
    inventory_df = context["inventory_df"]
    aging_df = context["aging_df"]
    competitor_df = context["competitor_df"]
    key_risk = "No material risk signal detected."
    if not inventory_df.empty and safe_float(inventory_df["Inventory Shortage"].sum()) > 0:
        key_risk = f"Inventory shortage of {safe_float(inventory_df['Inventory Shortage'].sum()):,.0f} units requires review."
    elif not competitor_df.empty and (competitor_df["Aggressive Competitor Pricing"] == "Yes").any():
        key_risk = "Aggressive competitor pricing may pressure approval economics."
    elif summary["margin_pct"] is not None and summary["margin_pct"] < summary["weighted_target_margin"]:
        key_risk = "Estimated margin is below weighted target margin."

    required_condition = "No special condition required."
    if not aging_df.empty and (aging_df["Near Expiry Inventory"] == "Yes").any():
        required_condition = "Use FEFO and confirm aging or near-expiry stock allocation before approval."
    elif not inventory_df.empty and (inventory_df["Allocation Risk"] == "High").any():
        required_condition = "Operations must confirm allocation feasibility and supply continuity."
    elif context["recommendation"] in {"Request Price Revision", "Approve with Conditions"}:
        required_condition = "Pricing or finance reviewer must document approval guardrails."

    return {
        "Key Reason": context["rationale"],
        "Key Risk": key_risk,
        "Required Condition": required_condition,
        "Inventory Summary": inventory_aging_recommendation(inventory_df, aging_df),
        "Aging Summary": aging_df[["SKU", "Days To Expiry", "Near Expiry Inventory", "Aging Inventory", "Disposition"]].copy() if not aging_df.empty else pd.DataFrame(),
        "Competitor Summary": competitor_summary(competitor_df),
    }


def render_approval_review_panel(context: dict) -> None:
    deal = context["deal"]
    summary = context["summary"]
    review = approval_review_summary(context)

    st.subheader("Selected Deal Review")
    top = st.columns(5)
    top[0].metric("Deal ID", str(deal.get("Deal ID", "")))
    top[1].metric("Status", str(deal.get("Status", "")))
    top[2].metric("Proposed Value", money(summary["total_proposed"]))
    top[3].metric("Discount", pct(summary["discount_pct"]))
    top[4].metric("Est. Margin", pct(summary["margin_pct"]))

    st.write(f"Customer: **{deal.get('Customer Name', '')}**")
    st.write(f"Deal title: **{deal.get('Deal Title', '')}**")

    decision_cols = st.columns(2)
    decision_cols[0].metric("Decision Score", f"{context['total_score']}/100")
    decision_cols[1].metric("Recommendation", context["recommendation"])

    st.markdown("**Key reason**")
    st.write(review["Key Reason"])
    st.markdown("**Key risk**")
    st.warning(review["Key Risk"])
    st.markdown("**Required condition**")
    st.info(review["Required Condition"])

    left, right = st.columns(2)
    with left:
        st.markdown("**Inventory summary**")
        st.info(review["Inventory Summary"])
        st.markdown("**Aging summary**")
        if review["Aging Summary"].empty:
            st.caption("No aging summary available.")
        else:
            st.dataframe(review["Aging Summary"], use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Competitor summary**")
        st.info(review["Competitor Summary"])

    st.markdown("**Approval route trigger reasons**")
    st.dataframe(context["route_triggers"], use_container_width=True, hide_index=True)


def validate_deal(header: dict, lines: pd.DataFrame, data: dict[str, pd.DataFrame]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    required = ["Deal Title", "Customer Name", "Deal Type", "Region", "Currency", "Target Close Date", "Requested Effective Date", "Payment Terms"]
    for field in required:
        if not header.get(field):
            errors.append(f"{field} is required.")
    if not header.get("Contract Months") or int(header.get("Contract Months", 0)) <= 0:
        errors.append("Contract months must be greater than zero.")
    if lines.empty:
        errors.append("At least one valid line item is required.")
    else:
        for _, line in lines.iterrows():
            if line["Quantity"] <= 0:
                errors.append(f"{line['SKU']} quantity must be greater than zero.")
            if line["Proposed Unit Price"] < 0 and line["SKU"] != "REB-FORM":
                errors.append(f"{line['SKU']} proposed price cannot be negative.")
            if line["Inventory Tracked"] == "Yes" and pd.isna(line.get("Requested Delivery Date")):
                warnings.append(f"{line['SKU']} is inventory tracked and should have a requested delivery date.")
            threshold = 0.18 if line["Product Type"] == "Biosimilar" else 0.12
            if line["SKU"] != "REB-FORM" and line["Discount %"] > threshold:
                warnings.append(f"{line['SKU']} discount exceeds policy threshold.")
    if not header.get("Business Justification"):
        errors.append("Business justification is required.")
    if header.get("Special Terms Requested") and not header.get("Special Terms Description"):
        errors.append("Special terms description is required.")
    if header.get("Payment Terms") in {"Net 75", "Net 90"}:
        warnings.append("Extended payment terms will require Finance and Legal review.")
    if int(header.get("Contract Months", 0) or 0) > 36:
        warnings.append("Contract duration above 36 months will require Legal review.")
    customer = customer_lookup(data).get(header.get("Customer Name", ""), {})
    if customer.get("Credit Status") == "Watch":
        warnings.append("Customer credit status is Watch.")
    if customer.get("Credit Status") == "Hold":
        warnings.append("Customer credit status is Hold and should trigger Finance review.")
    return errors, warnings


def route_preview(header: dict, lines: pd.DataFrame, summary: dict, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = [{"Role": "Sales Manager", "Sequence": 1, "Reason": "Every submitted deal requires baseline sales management review.", "SLA Hours": 24}]
    customer = customer_lookup(data).get(header.get("Customer Name", ""), {})
    has_high_discount = False
    has_supply_risk = False
    for _, line in lines.iterrows():
        threshold = 0.18 if line["Product Type"] == "Biosimilar" else 0.12
        if line["SKU"] != "REB-FORM" and line["Discount %"] > threshold:
            has_high_discount = True
        if line["Supply Risk"] in {"Medium", "High"}:
            has_supply_risk = True
    if has_high_discount:
        rows.append({"Role": "Pricing Analyst", "Sequence": 2, "Reason": "Discount exceeds product policy threshold.", "SLA Hours": 24})
    if header.get("Account Type") in {"Payer", "Group Purchasing Organization"} or header.get("Channel") in {"Payer", "GPO"} or (not lines.empty and "REB-FORM" in set(lines["SKU"])):
        rows.append({"Role": "Market Access Director", "Sequence": 2, "Reason": "Payer/GPO or formulary rebate concession is present.", "SLA Hours": 24})
    if summary["total_proposed"] > 1_000_000 or (summary["margin_pct"] is not None and summary["margin_pct"] < summary["weighted_target_margin"]) or customer.get("Credit Status") == "Hold":
        rows.append({"Role": "Finance Approver", "Sequence": 3, "Reason": "Deal value, margin, or credit risk requires finance review.", "SLA Hours": 36})
    if has_supply_risk:
        rows.append({"Role": "Operations Reviewer", "Sequence": 3, "Reason": "Supply risk, cold-chain, or inventory tracking requires operations review.", "SLA Hours": 24})
    if header.get("Special Terms Requested") or int(header.get("Contract Months", 0) or 0) > 36 or header.get("Payment Terms") in {"Net 75", "Net 90"}:
        rows.append({"Role": "Legal Reviewer", "Sequence": 4, "Reason": "Non-standard terms, long duration, or extended payment terms.", "SLA Hours": 48})
    if customer.get("Strategic Account") == "Yes" and summary["total_proposed"] > 2_500_000:
        rows.append({"Role": "Commercial Executive", "Sequence": 5, "Reason": "Strategic account and deal value exceeds executive threshold.", "SLA Hours": 48})
    return pd.DataFrame(rows).drop_duplicates(subset=["Role"]).sort_values(["Sequence", "Role"])


def breadcrumb_for_current_page() -> str:
    page = st.session_state.get("current_page", "Deal Request List")
    if page == "Deal Request List":
        return "Deal Requests"
    if page == "New Deal Intake":
        return "Deals > New Deal"
    if page == "Deal Detail":
        deal_id = st.session_state.get("selected_deal_id") or "Deal"
        parent = st.session_state.get("deal_detail_parent", "Deal Requests")
        return f"{parent} > {deal_id}"
    if page == "Approval Queue Preview":
        selected = st.session_state.get("approval_queue_selected_deal_id")
        return f"Approval Queue > {selected}" if selected else "Approval Queue"
    if page == "Reference Data":
        return "Admin > Reference Data"
    if page == "Audit Log":
        return "Admin > Audit Log"
    return str(page)


def render_header(title: str, subtitle: str = "") -> None:
    st.caption(breadcrumb_for_current_page())
    st.title(title)
    if subtitle:
        st.markdown(f"<div class='section-note'>{subtitle}</div>", unsafe_allow_html=True)


def page_deal_list(data: dict[str, pd.DataFrame]) -> None:
    render_header("Deal Requests", "Seeded and session-created commercial deal requests.")
    deals = combined_deals(data)
    if deals.empty:
        st.info("No deal requests available.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Deals", len(deals))
    c2.metric("Draft", int((deals["Status"] == "Draft").sum()) if "Status" in deals else 0)
    c3.metric("Submitted", int((deals["Status"] == "Submitted").sum()) if "Status" in deals else 0)
    c4.metric("Changes Requested", int((deals["Status"] == "Changes Requested").sum()) if "Status" in deals else 0)
    c5.metric("High Risk", int((deals.get("Intake Risk", pd.Series(dtype=str)) == "High").sum()))

    st.divider()
    filters = st.columns([1, 1, 1, 1, 1])
    status = filters[0].multiselect("Status", sorted(deals["Status"].dropna().unique()), default=[])
    region = filters[1].multiselect("Region", sorted(deals["Region"].dropna().unique()), default=[])
    segment = filters[2].multiselect("Segment", sorted(deals["Segment"].dropna().unique()), default=[])
    owner = filters[3].multiselect("Sales Owner", sorted(deals["Sales Owner"].dropna().unique()), default=[])
    risk_options = sorted(deals.get("Intake Risk", pd.Series(dtype=str)).dropna().unique())
    risk = filters[4].multiselect("Risk", risk_options, default=[])

    filtered = deals.copy()
    for col, selected in [("Status", status), ("Region", region), ("Segment", segment), ("Sales Owner", owner), ("Intake Risk", risk)]:
        if selected and col in filtered:
            filtered = filtered[filtered[col].isin(selected)]

    if st.button("Create New Deal", type="secondary"):
        set_current_page("New Deal Intake")
    if filtered.empty:
        st.info("No deals match the current filters.")
        return

    display_cols = [col for col in ["Deal ID", "Deal Title", "Customer Name", "Deal Type", "Region", "Status", "Target Close Date", "Payment Terms", "Intake Risk", "Expected Route"] if col in filtered]
    display_df = filtered[display_cols].reset_index(drop=True)
    table_event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="deal_request_list_table",
    )
    table_selected = get_selected_dataframe_deal_id(table_event, display_df)
    if table_selected:
        st.session_state.deal_list_selected_deal_id = table_selected
        st.session_state.selected_deal_id = table_selected
    else:
        st.session_state.deal_list_selected_deal_id = None

    if table_selected:
        context = build_deal_context(data, table_selected)
        if context:
            render_inline_deal_preview(context, compact=True)
            if st.button("Open Deal Detail", type="primary"):
                navigate_to_deal_detail(table_selected, "deal request list row selection")
    else:
        st.caption("Select a deal row using the checkbox column to preview it here.")


def build_default_line(data: dict[str, pd.DataFrame], sku: str | None = None) -> dict:
    products = data["products"]
    if products.empty:
        return {}
    prod = products.iloc[0] if not sku else products[products["SKU"].eq(sku)].iloc[0]
    list_price = float(prod.get("WAC / List Price", 0))
    target = list_price * 0.9
    return {
        "SKU": prod["SKU"],
        "Quantity": 1,
        "Unit List Price": round(list_price, 2),
        "Gross Price": round(list_price * 0.98, 2),
        "Requested Net Price": round(target, 2),
        "Requested Discount %": 10.0,
        "Floor Price": round(list_price * 0.72, 2),
        "Guidance Price": round(list_price * 0.84, 2),
        "Walk-away Price": round(list_price * 0.68, 2),
        "Proposed Unit Price": round(target, 2),
        "Requested Delivery Date": date.today() + timedelta(days=int(prod.get("Lead Time Days", 14) or 14)),
        "Notes": "",
    }


def page_new_deal(data: dict[str, pd.DataFrame]) -> None:
    render_header("New Deal Intake", "Create a draft or submit a pharmaceutical commercial deal request.")
    customers = data["customers"]
    opportunities = data["opportunities"]
    products = data["products"]
    if customers.empty or products.empty:
        st.error("Customer and product reference data are required.")
        return

    if st.session_state.draft_lines is None:
        st.session_state.draft_lines = pd.DataFrame([build_default_line(data, "RX-ONC-100")])

    tabs = st.tabs(["Context", "Commercials", "Customer & Market", "Financial Impact", "Approval Recommendation"])

    with tabs[0]:
        st.subheader("Deal Context")
        customer_name = st.selectbox("Customer", customers["Customer Name"].tolist(), key="form_customer")
        customer = customers[customers["Customer Name"].eq(customer_name)].iloc[0].to_dict()
        opps = opportunities[opportunities["Customer ID"].eq(customer["Customer ID"])]
        opp_options = [""] + opps["Opportunity Name"].tolist()
        opportunity_name = st.selectbox("Opportunity", opp_options, key="form_opportunity")
        account_cols = st.columns(3)
        ship_to_account = account_cols[0].text_input("Ship-to account", value=str(customer.get("Customer Name", customer_name)), key="form_ship_to")
        bill_to_account = account_cols[1].text_input("Bill-to account", value=str(customer.get("Customer Name", customer_name)), key="form_bill_to")
        country = account_cols[2].text_input("Country", value=str(customer.get("Country", "United States")), key="form_country")
        deal_cols = st.columns(2)
        deal_title = deal_cols[0].text_input("Deal Title", value=f"{customer_name} Commercial Deal", key="form_title")
        deal_type = deal_cols[0].selectbox("Deal Type", ["New Sale", "Renewal", "Expansion", "Competitive replacement", "Strategic exception"], key="form_type")
        region = deal_cols[1].selectbox("Region", sorted(data["commercial_plan"]["Region"].dropna().unique()), index=0, key="form_region")
        currency = deal_cols[1].selectbox("Currency", ["USD", "EUR"], key="form_currency")
        purpose = st.selectbox(
            "Purpose",
            ["Tender", "Competitive defense", "New listing", "Contract renewal", "Inventory liquidation", "Expiry mitigation", "Strategic account", "Other"],
            key="form_purpose",
        )
        if purpose == "Tender":
            tender_cols = st.columns(4)
            tender_name = tender_cols[0].text_input("Tender name", value=f"{customer_name} access tender", key="form_tender_name")
            tender_id = tender_cols[1].text_input("Tender ID", value=f"TND-{date.today().year}-{str(customer.get('Customer ID', '000'))[-3:]}", key="form_tender_id")
            tender_closing = tender_cols[2].date_input("Tender closing date", value=date.today() + timedelta(days=28), key="form_tender_closing")
            award_date = tender_cols[3].date_input("Award date", value=date.today() + timedelta(days=60), key="form_award_date")
            tender_mechanism = st.selectbox("Tender mechanism", ["Winner takes all", "Multi-award", "Framework agreement", "Unknown"], key="form_tender_mechanism")
        else:
            tender_name = st.session_state.get("form_tender_name", "")
            tender_id = st.session_state.get("form_tender_id", "")
            tender_closing = st.session_state.get("form_tender_closing", None)
            award_date = st.session_state.get("form_award_date", None)
            tender_mechanism = st.session_state.get("form_tender_mechanism", "")
        if purpose == "Expiry mitigation":
            expiry_cols = st.columns(3)
            quantity_at_risk = expiry_cols[0].number_input("Quantity at risk", min_value=0, value=500, step=50, key="form_quantity_at_risk")
            shelf_life = expiry_cols[1].number_input("Remaining shelf life", min_value=0, value=90, step=15, key="form_shelf_life")
            inventory_value_at_risk = expiry_cols[2].number_input("Inventory value at risk", min_value=0.0, value=125000.0, step=5000.0, key="form_inventory_value_at_risk")
        else:
            quantity_at_risk = st.session_state.get("form_quantity_at_risk", 0)
            shelf_life = st.session_state.get("form_shelf_life", 0)
            inventory_value_at_risk = st.session_state.get("form_inventory_value_at_risk", 0.0)
        owner_cols = st.columns(4)
        sales_owner = owner_cols[0].selectbox("Sales Owner", sorted(PERSONAS.keys()), index=0, key="form_owner")
        sales_manager = owner_cols[1].selectbox("Sales Manager", ["Jordan Blake", "Lena Torres", "Sarah Morgan"], key="form_manager")
        target_close = owner_cols[2].date_input("Target Close Date", value=date.today() + timedelta(days=45), key="form_close")
        effective_date = owner_cols[3].date_input("Requested Effective Date", value=date.today() + timedelta(days=60), key="form_effective")
        st.divider()
        cols = st.columns(4)
        cols[0].metric("Account Type", customer.get("Account Type", ""))
        cols[1].metric("Segment", customer.get("Segment", ""))
        cols[2].metric("Region", st.session_state.get("form_region", customer.get("Region", "")))
        cols[3].metric("Credit", customer.get("Credit Status", ""))
        st.info(str(customer.get("Commercial Notes", "")))
        if customer.get("Credit Status") == "Watch":
            st.warning("Credit status is Watch. Finance review is likely.")
        if customer.get("Credit Status") == "Hold":
            st.error("Credit status is Hold. Submission should route to Finance before approval.")

    with tabs[1]:
        st.subheader("Commercial Terms")
        c1, c2, c3 = st.columns(3)
        payment_terms = c1.selectbox("Payment Terms", ["Net 30", "Net 45", "Net 60", "Net 75", "Net 90"], key="form_terms")
        contract_months = c2.number_input("Contract Months", min_value=1, max_value=72, value=24, step=1, key="form_contract")
        billing = c3.selectbox("Billing Frequency", ["Annual", "Quarterly", "Monthly", "Milestone"], key="form_billing")
        special_terms = st.checkbox("Special terms requested", key="form_special")
        special_desc = st.text_area("Special Terms Description", value="", key="form_special_desc")
        st.divider()
        st.subheader("Visibility")
        visibility = st.radio("Visibility", ["Confidential", "Bid Only", "Public"], horizontal=True, key="form_visibility")
        if visibility == "Public":
            pub_cols = st.columns(2)
            publication_source = pub_cols[0].text_input("Publication source", value="National tender portal", key="form_publication_source")
            publication_url = pub_cols[1].text_input("Publication URL", value="https://example-tender-portal.local/opportunities", key="form_publication_url")
            access_description = st.text_area("Access description", value="Publicly accessible tender notice with award criteria and bid submission instructions.", key="form_access_description")
        else:
            publication_source = st.session_state.get("form_publication_source", "")
            publication_url = st.session_state.get("form_publication_url", "")
            access_description = st.session_state.get("form_access_description", "")
        st.divider()
        st.subheader("Products, Volume, and Requested Pricing")
        st.caption("Edit SKU, quantity, proposed price, delivery date, and notes. Product metadata and calculations appear below.")
        st.session_state.draft_lines = ensure_commercial_line_columns(st.session_state.draft_lines, data)
        editor_config = {
            "SKU": st.column_config.SelectboxColumn("SKU", options=products["SKU"].tolist(), required=True),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1),
            "Unit List Price": st.column_config.NumberColumn("List Price", min_value=0.0, step=1.0, format="$%.2f"),
            "Gross Price": st.column_config.NumberColumn("Gross Price", min_value=0.0, step=1.0, format="$%.2f"),
            "Requested Net Price": st.column_config.NumberColumn("Requested Net Price", min_value=-1_000_000.0, step=1.0, format="$%.2f"),
            "Requested Discount %": st.column_config.NumberColumn("Requested Discount %", min_value=-100.0, max_value=100.0, step=0.1, format="%.1f%%"),
            "Floor Price": st.column_config.NumberColumn("Floor Price", min_value=0.0, step=1.0, format="$%.2f"),
            "Guidance Price": st.column_config.NumberColumn("Guidance Price", min_value=0.0, step=1.0, format="$%.2f"),
            "Walk-away Price": st.column_config.NumberColumn("Walk-away Price", min_value=0.0, step=1.0, format="$%.2f"),
            "Requested Delivery Date": st.column_config.DateColumn("Requested Delivery Date"),
            "Notes": st.column_config.TextColumn("Notes"),
        }
        visible_line_cols = [
            "SKU",
            "Quantity",
            "Unit List Price",
            "Gross Price",
            "Requested Net Price",
            "Requested Discount %",
            "Floor Price",
            "Guidance Price",
            "Walk-away Price",
            "Requested Delivery Date",
            "Notes",
        ]
        st.session_state.draft_lines = st.data_editor(
            st.session_state.draft_lines[[col for col in visible_line_cols if col in st.session_state.draft_lines]],
            num_rows="dynamic",
            use_container_width=True,
            column_config=editor_config,
            disabled=["Unit List Price", "Gross Price", "Requested Discount %", "Floor Price", "Guidance Price", "Walk-away Price"],
            hide_index=True,
            key="line_editor",
        )
        st.session_state.draft_lines = ensure_commercial_line_columns(st.session_state.draft_lines, data)
        calc_lines = normalize_lines(st.session_state.draft_lines, data)
        summary = summarize_lines(calc_lines)
        metric_cols = st.columns(5)
        metric_cols[0].metric("Total List Value", money(summary["total_list"]))
        metric_cols[1].metric("Total Gross Value", money(summary["total_gross"]))
        metric_cols[2].metric("Total Requested Net Value", money(summary["total_proposed"]))
        metric_cols[3].metric("Weighted Discount %", pct(summary["discount_pct"]))
        metric_cols[4].metric("Estimated Gross Margin %", pct(summary["margin_pct"]))
        if not calc_lines.empty:
            view_cols = [
                "SKU",
                "Product Name",
                "Quantity",
                "List Price",
                "Gross Price",
                "Requested Net Price",
                "Requested Discount %",
                "Floor Price",
                "Guidance Price",
                "Walk-away Price",
                "Extended Requested Net",
                "Storage",
                "Supply Risk",
            ]
            view = calc_lines[[col for col in view_cols if col in calc_lines]].copy()
            if "Requested Discount %" in view:
                view["Requested Discount %"] = view["Requested Discount %"] * 100
            st.dataframe(view, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Customer Health")
        health = demo_customer_health(customer, customer_name)
        health_cols = st.columns(5)
        health_cols[0].metric("Revenue last 12 months", money(health["Revenue last 12 months"]))
        health_cols[1].metric("Units last 12 months", f"{health['Units last 12 months']:,.0f}")
        health_cols[2].metric("Average net price last 12 months", money(health["Average net price last 12 months"]))
        health_cols[3].metric("Gross margin last 12 months", money(health["Gross margin last 12 months"]))
        health_cols[4].metric("Gross margin %", pct(health["Gross margin %"]))
        ar_cols = st.columns(6)
        ar_cols[0].metric("Total AR", money(health["Total AR"]))
        ar_cols[1].metric("Current AR", money(health["Current AR"]))
        ar_cols[2].metric("30+ days AR", money(health["30+ days AR"]))
        ar_cols[3].metric("60+ days AR", money(health["60+ days AR"]))
        ar_cols[4].metric("90+ days AR", money(health["90+ days AR"]))
        ar_cols[5].metric("Overdue AR", money(health["Overdue AR"]))
        risk_flag = str(health["Risk Flag"])
        if risk_flag == "High":
            st.error("Customer risk flag: High")
        elif risk_flag == "Medium":
            st.warning("Customer risk flag: Medium")
        else:
            st.success("Customer risk flag: Low")

        st.divider()
        st.subheader("Market Intelligence")
        market_left, market_right = st.columns([1, 1])
        with market_left:
            business_justification = st.text_area("Business Justification", height=130, key="form_justification")
            expected_competitors = st.multiselect(
                "Expected competitors",
                ["NovaThera", "HelixBio", "Orion Generics", "VitaCore", "MedAxis", "Unknown"],
                default=["NovaThera"] if st.session_state.get("form_purpose") == "Tender" else [],
                key="form_expected_competitors",
            )
            competitor_type = st.selectbox(
                "Competitor type",
                ["Incumbent", "Aggressive bidder", "Supply constrained", "Unknown"],
                key="form_competitor_type",
            )
            competitive_situation = st.selectbox("Competitive Situation", ["None known", "Incumbent competitor", "Price pressure", "Feature comparison", "Unknown"], key="form_competitive")
            known_competitor = st.text_input("Known Competitor", key="form_competitor")
        with market_right:
            expected_bid_range = st.text_input("Expected bid range", value="8% to 16% below list", key="form_expected_bid_range")
            customer_bidding_strategy = st.selectbox(
                "Customer bidding strategy",
                ["Lowest compliant price", "Balanced price and supply reliability", "Incumbent preference", "Multi-supplier risk mitigation", "Unknown"],
                key="form_customer_bidding_strategy",
            )
            margin_retention = st.slider("Margin retention assumption", min_value=0.0, max_value=1.0, value=0.82, step=0.01, key="form_margin_retention")
            decision_deadline = st.date_input("Customer Decision Deadline", value=date.today() + timedelta(days=30), key="form_deadline")
            expansion_impact = st.text_area("Renewal or Expansion Impact", height=100, key="form_expansion")

        st.markdown("**Market summary**")
        summary_cols = st.columns(3)
        summary_cols[0].info(f"Competitor posture: {competitor_type}")
        summary_cols[1].info(f"Bid range: {expected_bid_range}")
        summary_cols[2].info(f"Margin retention: {margin_retention * 100:.0f}%")

        st.divider()
        st.subheader("Reconciliation")
        reconciliation_type = st.radio("Reconciliation type", ["None", "Credit Note", "Chargeback", "Rebate", "Other"], horizontal=True, key="form_reconciliation_type")
        reconciliation_description = st.text_area(
            "Reconciliation description",
            value="" if reconciliation_type == "None" else "Describe settlement timing, claim evidence, accrual owner, and expected customer documentation.",
            key="form_reconciliation_description",
        )
        rec_cols = st.columns(2)
        rec_cols[0].info(f"Selected reconciliation: {reconciliation_type}")
        rec_cols[1].info("Finance should validate accrual treatment before final approval when reconciliation is not None.")

    header = {
        "Deal Title": st.session_state.get("form_title", ""),
        "Deal Type": st.session_state.get("form_type", ""),
        "Customer Name": customer_name,
        "Customer ID": customer.get("Customer ID"),
        "Ship-to Account": st.session_state.get("form_ship_to", ""),
        "Bill-to Account": st.session_state.get("form_bill_to", ""),
        "Country": st.session_state.get("form_country", "United States"),
        "Opportunity Name": opportunity_name,
        "Purpose": st.session_state.get("form_purpose", ""),
        "Tender Name": st.session_state.get("form_tender_name", ""),
        "Tender ID": st.session_state.get("form_tender_id", ""),
        "Tender Closing Date": st.session_state.get("form_tender_closing", ""),
        "Award Date": st.session_state.get("form_award_date", ""),
        "Tender Mechanism": st.session_state.get("form_tender_mechanism", ""),
        "Quantity at Risk": st.session_state.get("form_quantity_at_risk", 0),
        "Remaining Shelf Life": st.session_state.get("form_shelf_life", 0),
        "Inventory Value at Risk": st.session_state.get("form_inventory_value_at_risk", 0.0),
        "Region": st.session_state.get("form_region", customer.get("Region")),
        "Segment": customer.get("Segment"),
        "Account Type": customer.get("Account Type"),
        "Channel": customer.get("Account Type"),
        "Currency": st.session_state.get("form_currency", "USD"),
        "Target Close Date": st.session_state.get("form_close", target_close),
        "Requested Effective Date": st.session_state.get("form_effective", effective_date),
        "Payment Terms": st.session_state.get("form_terms", payment_terms),
        "Contract Months": st.session_state.get("form_contract", contract_months),
        "Billing Frequency": st.session_state.get("form_billing", billing),
        "Special Terms Requested": st.session_state.get("form_special", False),
        "Special Terms Description": st.session_state.get("form_special_desc", ""),
        "Visibility": st.session_state.get("form_visibility", "Confidential"),
        "Publication Source": st.session_state.get("form_publication_source", ""),
        "Publication URL": st.session_state.get("form_publication_url", ""),
        "Access Description": st.session_state.get("form_access_description", ""),
        "Included_In_Latest_Financial_Plan": st.session_state.get("form_included_plan", "Yes"),
        "Customer Risk Flag": health.get("Risk Flag", ""),
        "Revenue L12M": health.get("Revenue last 12 months", 0),
        "Units L12M": health.get("Units last 12 months", 0),
        "Average Net Price L12M": health.get("Average net price last 12 months", 0),
        "Gross Margin L12M": health.get("Gross margin last 12 months", 0),
        "Gross Margin % L12M": health.get("Gross margin %", 0),
        "Total AR": health.get("Total AR", 0),
        "Overdue AR": health.get("Overdue AR", 0),
        "Expected Competitors": ", ".join(st.session_state.get("form_expected_competitors", [])),
        "Competitor Type": st.session_state.get("form_competitor_type", ""),
        "Expected Bid Range": st.session_state.get("form_expected_bid_range", ""),
        "Customer Bidding Strategy": st.session_state.get("form_customer_bidding_strategy", ""),
        "Margin Retention Assumption": st.session_state.get("form_margin_retention", 0),
        "Reconciliation Type": st.session_state.get("form_reconciliation_type", "None"),
        "Reconciliation Description": st.session_state.get("form_reconciliation_description", ""),
        "Business Justification": st.session_state.get("form_justification", ""),
        "Competitive Situation": st.session_state.get("form_competitive", ""),
        "Known Competitor": st.session_state.get("form_competitor", ""),
        "Sales Owner": st.session_state.get("form_owner", sales_owner),
        "Sales Manager": st.session_state.get("form_manager", sales_manager),
    }
    calc_lines = normalize_lines(st.session_state.draft_lines, data)
    summary = summarize_lines(calc_lines)
    errors, warnings = validate_deal(header, calc_lines, data)
    route_df = route_preview(header, calc_lines, summary, data)

    with tabs[3]:
        st.subheader("Financial Impact")
        included_value = st.selectbox("Included_In_Latest_Financial_Plan", ["Yes", "No"], key="form_included_plan")
        included_in_plan = included_value == "Yes"
        plan_df = plan_impact_analysis(data, calc_lines, header["Region"], header["Segment"])
        incremental_df = incremental_opportunity_analysis(data, calc_lines, customer_name, header["Channel"])
        proposed_revenue = safe_float(summary["total_proposed"])
        proposed_gp = safe_float(((calc_lines["Proposed Unit Price"] - calc_lines["Unit Cost"]) * calc_lines["Quantity"]).sum()) if not calc_lines.empty else 0
        proposed_margin = None if proposed_revenue <= 0 else proposed_gp / proposed_revenue

        if included_in_plan:
            planned_revenue = safe_float(plan_df["Planned Revenue"].sum()) if not plan_df.empty else 0
            planned_gp = safe_float(plan_df["Planned Gross Profit"].sum()) if not plan_df.empty else 0
            price_variance = safe_float(plan_df["Price Variance"].sum()) if not plan_df.empty else 0
            volume_variance = safe_float(plan_df["Volume Variance"].sum()) if not plan_df.empty else 0
            revenue_variance = price_variance + volume_variance
            gp_variance = proposed_gp - planned_gp
            planned_net = 0 if plan_df.empty or safe_float(plan_df["Planned Quantity"].sum()) <= 0 else safe_float((plan_df["Planned Net Price"] * plan_df["Planned Quantity"]).sum()) / safe_float(plan_df["Planned Quantity"].sum())
            proposed_net = 0 if calc_lines.empty or safe_float(calc_lines["Quantity"].sum()) <= 0 else safe_float((calc_lines["Proposed Unit Price"] * calc_lines["Quantity"]).sum()) / safe_float(calc_lines["Quantity"].sum())
            planned_margin = None if planned_revenue <= 0 else planned_gp / planned_revenue

            st.info("Plan logic uses only Price Variance and Volume Variance.")
            kpis = st.columns(5)
            kpis[0].metric("Planned Revenue", money(planned_revenue))
            kpis[1].metric("Proposed Revenue", money(proposed_revenue), delta=money(revenue_variance))
            kpis[2].metric("Planned Gross Profit", money(planned_gp))
            kpis[3].metric("Proposed Gross Profit", money(proposed_gp))
            kpis[4].metric("Gross Profit Variance", money(gp_variance))
            margin_cols = st.columns(4)
            margin_cols[0].metric("Planned Net Price", money(planned_net))
            margin_cols[1].metric("Proposed Net Price", money(proposed_net))
            margin_cols[2].metric("Planned Margin %", pct(planned_margin))
            margin_cols[3].metric("Proposed Margin %", pct(proposed_margin))

            st.markdown("**Revenue variance bridge**")
            bridge_df = pd.DataFrame(
                [
                    {"Component": "Price Variance", "Value": price_variance},
                    {"Component": "Volume Variance", "Value": volume_variance},
                    {"Component": "Revenue Variance", "Value": revenue_variance},
                    {"Component": "Gross Profit Variance", "Value": gp_variance},
                ]
            )
            st.bar_chart(bridge_df.set_index("Component"))
            st.dataframe(
                plan_df[
                    [
                        "SKU",
                        "Product",
                        "Planned Net Price",
                        "Proposed Net Price",
                        "Planned Quantity",
                        "New Quantity",
                        "Planned Revenue",
                        "Proposed Revenue",
                        "Price Variance",
                        "Volume Variance",
                        "Revenue Variance",
                        "Planned Gross Profit",
                        "Proposed Gross Profit",
                        "Gross Profit Variance",
                        "Planned Margin %",
                        "Proposed Margin %",
                    ]
                ] if not plan_df.empty else plan_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            incremental_revenue = safe_float(incremental_df["Incremental Revenue"].sum()) if not incremental_df.empty else proposed_revenue
            incremental_gp = safe_float(incremental_df["Incremental Gross Profit"].sum()) if not incremental_df.empty else proposed_gp
            hist_price = safe_float(incremental_df["Historical Average Net Price"].dropna().mean()) if not incremental_df.empty else 0
            price_vs_hist = safe_float(incremental_df["Price vs Historical Price %"].dropna().mean()) if not incremental_df.empty else 0
            hist_margin = safe_float(incremental_df["Historical Margin %"].dropna().mean()) if not incremental_df.empty else None
            margin_difference = None if hist_margin is None or proposed_margin is None else proposed_margin - hist_margin

            st.info("Classified as Incremental Opportunity because it is not included in the latest financial plan.")
            kpis = st.columns(4)
            kpis[0].metric("Incremental Revenue", money(incremental_revenue))
            kpis[1].metric("Incremental Gross Profit", money(incremental_gp))
            kpis[2].metric("Proposed Margin %", pct(proposed_margin))
            kpis[3].metric("Historical Average Net Price", money(hist_price))
            benchmark_cols = st.columns(3)
            benchmark_cols[0].metric("Price Difference vs Historical Average %", pct(price_vs_hist))
            benchmark_cols[1].metric("Historical Margin %", pct(hist_margin))
            benchmark_cols[2].metric("Margin Difference vs Historical Margin %", pct(margin_difference))

            st.markdown("**Incremental economics bridge**")
            bridge_df = pd.DataFrame(
                [
                    {"Component": "Incremental Revenue", "Value": incremental_revenue},
                    {"Component": "Incremental Gross Profit", "Value": incremental_gp},
                ]
            )
            st.bar_chart(bridge_df.set_index("Component"))
            display_cols = [
                "SKU",
                "Product",
                "Incremental Revenue",
                "Incremental Gross Profit",
                "Historical Average Net Price",
                "Price vs Historical Price %",
                "Historical Margin %",
                "Proposed Margin %",
                "Margin Difference vs Historical Margin %",
            ]
            st.dataframe(incremental_df[[col for col in display_cols if col in incremental_df]], use_container_width=True, hide_index=True)

        st.markdown("**Financial Review Signals**")
        if errors:
            st.error("Blocking issues must be resolved before submission.")
            for err in errors:
                st.write(f"- {err}")
        elif warnings:
            st.warning("Reviewer attention required.")
            for warn in warnings:
                st.write(f"- {warn}")
        else:
            st.success("No blocking commercial validation issues detected.")

    with tabs[4]:
        st.subheader("Approval Recommendation")
        included_value = st.session_state.get("form_included_plan", "Yes")
        included_in_plan = included_value == "Yes"
        plan_df = plan_impact_analysis(data, calc_lines, header["Region"], header["Segment"])
        incremental_df = incremental_opportunity_analysis(data, calc_lines, customer_name, header["Channel"])
        inventory_df = enhanced_inventory_analysis(data, calc_lines, header["Region"])
        aging_df = enhanced_aging_analysis(data, calc_lines, header["Region"])
        competitor_df = enhanced_competitor_intelligence(data, calc_lines, customer_name, header["Region"])
        gp_impact = gross_profit_impact(calc_lines, plan_df, incremental_df, included_in_plan)
        score_df, total_score, model_recommendation, score_rationale = score_deal(
            summary,
            plan_df,
            incremental_df,
            inventory_df,
            aging_df,
            competitor_df,
            route_df,
            included_in_plan,
        )
        executive = executive_recommendation(
            model_recommendation,
            score_df,
            total_score,
            header,
            inventory_df,
            aging_df,
            competitor_df,
            gp_impact,
            errors,
            warnings,
        )
        recommendation = executive["Recommendation"]
        route_dashboard = approval_route_dashboard(route_df, header, calc_lines, inventory_df, competitor_df, gp_impact)

        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-note">Executive approval view</div>
                <h3>{executive["Recommendation"]}</h3>
                <p><strong>{header["Deal Title"]}</strong> for <strong>{customer_name}</strong></p>
                <p>Decision score: <strong>{total_score}/100</strong> | Proposed value: <strong>{money(summary["total_proposed"])}</strong> | Gross profit impact: <strong>{money(gp_impact["Gross Profit Variance"])}</strong></p>
                <p>{executive["Key Reason"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        score_cols = st.columns(6)
        score_cols[0].metric("Decision Score", f"{total_score}/100")
        for idx, component in enumerate(["Margin", "Strategic", "Inventory", "Competitive", "Risk"], start=1):
            value = int(score_df.loc[score_df["Component"].eq(component), "Score"].iloc[0]) if component in set(score_df["Component"]) else 0
            label = "Strategic Value" if component == "Strategic" else "Competitive Position" if component == "Competitive" else component
            score_cols[idx].metric(label, f"{value}/20")
        st.progress(total_score / 100, text=f"Total Decision Score: {total_score}/100")

        st.markdown("**Score components**")
        score_display = score_df.copy()
        score_display["Component"] = score_display["Component"].replace({"Strategic": "Strategic Value", "Competitive": "Competitive Position"})
        st.dataframe(score_display, use_container_width=True, hide_index=True)

        reason_cols = st.columns(4)
        reason_cols[0].info(f"Key Reason: {executive['Key Reason']}")
        reason_cols[1].warning(f"Key Risk: {executive['Key Risk']}")
        reason_cols[2].info(f"Required Condition: {executive['Required Condition']}")
        reason_cols[3].success(f"Next Action: {executive['Next Action']}")

        st.subheader("Approval Route")
        if route_dashboard.empty:
            st.info("No approval route could be generated from current deal inputs.")
        else:
            st.dataframe(route_dashboard, use_container_width=True, hide_index=True)

        with st.expander("Commercial summary"):
            st.write(f"Customer: **{customer_name}**")
            st.write(f"Plan inclusion: **{included_value}**")
            st.write(f"Rationale: {header['Business Justification'] or 'Not provided'}")
            st.caption(score_rationale)
            st.dataframe(calc_lines, use_container_width=True, hide_index=True)

        if errors:
            st.error("Blocking issues")
            for err in errors:
                st.write(f"- {err}")
        if warnings:
            st.warning("Warnings")
            for warn in warnings:
                st.write(f"- {warn}")

        a, b, c = st.columns([1, 1, 4])
        if a.button("Save Draft", type="secondary"):
            save_runtime_deal(header, calc_lines, summary, route_df, status="Draft", recommendation=recommendation)
            st.success("Draft saved for this session.")
        if b.button("Submit Deal", type="primary", disabled=bool(errors)):
            deal_id = save_runtime_deal(header, calc_lines, summary, route_df, status="Submitted", recommendation=recommendation)
            add_audit(deal_id, "Deal submitted", details=f"Recommendation: {recommendation}")
            navigate_to_deal_detail(deal_id, "new deal intake submission")


def save_runtime_deal(header: dict, lines: pd.DataFrame, summary: dict, route_df: pd.DataFrame, status: str, recommendation: str) -> str:
    deal_id = f"DEAL-S-{len(st.session_state.runtime_deals) + 1:04d}"
    opportunity_id = ""
    workflow_status = "Pending Sales Manager" if status == "Submitted" else status
    st.session_state.runtime_deals.append(
        {
            "Deal ID": deal_id,
            "Deal Title": header["Deal Title"],
            "Customer ID": header["Customer ID"],
            "Customer Name": header["Customer Name"],
            "Ship-to Account": header.get("Ship-to Account", ""),
            "Bill-to Account": header.get("Bill-to Account", ""),
            "Country": header.get("Country", ""),
            "Opportunity ID": opportunity_id,
            "Purpose": header.get("Purpose", ""),
            "Tender Name": header.get("Tender Name", ""),
            "Tender ID": header.get("Tender ID", ""),
            "Tender Mechanism": header.get("Tender Mechanism", ""),
            "Visibility": header.get("Visibility", ""),
            "Customer Risk Flag": header.get("Customer Risk Flag", ""),
            "Revenue L12M": header.get("Revenue L12M", 0),
            "Overdue AR": header.get("Overdue AR", 0),
            "Competitor Type": header.get("Competitor Type", ""),
            "Expected Competitors": header.get("Expected Competitors", ""),
            "Reconciliation Type": header.get("Reconciliation Type", "None"),
            "Deal Type": header["Deal Type"],
            "Region": header["Region"],
            "Segment": header["Segment"],
            "Sales Owner": header["Sales Owner"],
            "Sales Manager": header["Sales Manager"],
            "Status": workflow_status,
            "Target Close Date": str(header["Target Close Date"]),
            "Payment Terms": header["Payment Terms"],
            "Contract Months": header["Contract Months"],
            "Strategic Rationale": header["Business Justification"],
            "Intake Risk": "High" if "Commercial Executive" in set(route_df["Role"]) else "Medium" if len(route_df) > 2 else "Low",
            "Channel": header["Channel"],
            "Included_In_Latest_Financial_Plan": header.get("Included_In_Latest_Financial_Plan", "Yes"),
            "Expected Route": " + ".join(route_df["Role"].tolist()),
            "Total Proposed": summary["total_proposed"],
            "Discount %": summary["discount_pct"],
            "Recommendation": recommendation,
        }
    )
    for i, (_, line) in enumerate(lines.iterrows(), start=1):
        item = line.to_dict()
        item["Deal ID"] = deal_id
        item["Line #"] = i
        st.session_state.runtime_lines.append(item)
    add_audit(deal_id, "Deal draft saved" if status == "Draft" else "Deal created", details=f"Status: {workflow_status}")
    return deal_id


def page_deal_detail(data: dict[str, pd.DataFrame]) -> None:
    render_header("Deal Detail", "Review intake, analysis context, route preview, and audit trail.")
    deals = combined_deals(data)
    if deals.empty:
        st.info("No deals available.")
        return
    default = st.session_state.selected_deal_id if st.session_state.selected_deal_id in set(deals["Deal ID"]) else deals.iloc[0]["Deal ID"]
    selected = st.selectbox("Deal", deals["Deal ID"].tolist(), index=deals["Deal ID"].tolist().index(default))
    st.session_state.selected_deal_id = selected
    deal = deals[deals["Deal ID"].eq(selected)].iloc[0].to_dict()
    lines = combined_lines(data)
    deal_lines = lines[lines["Deal ID"].astype(str).eq(str(selected))]
    calc_lines = normalize_lines(deal_lines, data)
    summary = summarize_lines(calc_lines)
    header = {
        "Customer Name": deal.get("Customer Name"),
        "Region": deal.get("Region"),
        "Segment": deal.get("Segment"),
        "Account Type": customer_lookup(data).get(deal.get("Customer Name"), {}).get("Account Type", ""),
        "Channel": customer_lookup(data).get(deal.get("Customer Name"), {}).get("Account Type", ""),
        "Payment Terms": deal.get("Payment Terms"),
        "Contract Months": deal.get("Contract Months", 0),
        "Special Terms Requested": False,
    }
    route_df = route_preview(header, calc_lines, summary, data)
    deal_status = str(deal.get("Status", "")).strip()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", deal_status)
    c2.metric("Total Proposed", money(summary["total_proposed"]))
    c3.metric("Discount", pct(summary["discount_pct"]))
    c4.metric("Est. Margin", pct(summary["margin_pct"]))
    st.markdown(status_badge(deal_status), unsafe_allow_html=True)

    confirmation = st.session_state.get("deal_detail_confirmation", "")
    if confirmation:
        st.success(confirmation)
        st.session_state.deal_detail_confirmation = ""

    if deal_status in ACTIVE_APPROVAL_STATUSES:
        context = build_deal_context(data, selected)
        if context:
            st.divider()
            st.subheader("Decision Panel")
            route_summary = " -> ".join(context["route_triggers"]["Role"].astype(str).tolist()) if not context["route_triggers"].empty else "No route available"
            current_role = current_required_approval_role(selected, deal_status, context["route_df"])
            user_role = st.session_state.get("role", "Demo Role")
            allowed_decisions = allowed_decisions_for_role(user_role)
            st.write(f"**Recommendation:** {context['recommendation']}")
            panel_cols = st.columns(4)
            panel_cols[0].metric("Decision Score", f"{context['total_score']}/100")
            panel_cols[1].metric("Approval Route Summary", route_summary)
            panel_cols[2].metric("Current Required Role", current_role or "None")
            panel_cols[3].metric("Current User Role", user_role)
            can_act_on_step = bool(current_role) and user_role == current_role and bool(allowed_decisions)
            if can_act_on_step:
                st.success("Current user can capture a decision for this approval step.")
            else:
                st.warning(f"{user_role} cannot approve this step. Required role: {current_role or 'none'}.")
            with st.expander("Approval route trigger reasons", expanded=False):
                st.dataframe(context["route_triggers"], use_container_width=True, hide_index=True)

            detail_decision = st.radio(
                "Decision",
                DECISIONS,
                horizontal=True,
                key=f"detail_decision_{selected}",
            )
            detail_comment = st.text_area("Decision comment", key=f"detail_decision_comment_{selected}")
            can_capture = can_act_on_step and detail_decision in allowed_decisions
            if detail_decision not in allowed_decisions:
                st.warning(f"{user_role} is not permitted to capture `{detail_decision}`.")
            if st.button("Capture Decision", type="primary", key=f"detail_capture_decision_{selected}", disabled=not can_capture):
                success, message = process_approval_decision(selected, detail_decision, detail_comment, context["route_df"], deal_status)
                st.session_state.selected_deal_id = selected
                if success:
                    st.session_state.deal_detail_confirmation = message
                    st.rerun()
                else:
                    st.error(message)
            if not can_act_on_step and st.button("Add Comment", type="secondary", key=f"detail_add_comment_{selected}", disabled=not detail_comment.strip()):
                add_audit(
                    selected,
                    "Approval comment added",
                    entity="Approval Comment",
                    details="Comment added without status change.",
                    comment=detail_comment,
                    approval_step=current_role,
                    previous_status=deal_status,
                    new_status=deal_status,
                )
                st.session_state.deal_detail_confirmation = f"Comment added for {selected}. Status remains {deal_status}."
                st.rerun()

    tabs = st.tabs(["Overview", "Line Items", "Analysis", "Route Preview", "Audit"])
    with tabs[0]:
        st.write(f"**{deal.get('Deal Title')}**")
        st.write(f"Customer: {deal.get('Customer Name')}")
        st.write(f"Strategic rationale: {deal.get('Strategic Rationale', '')}")
        st.dataframe(pd.DataFrame([deal]), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(calc_lines, use_container_width=True, hide_index=True)
    with tabs[2]:
        render_analysis_blocks(data, deal, calc_lines)
    with tabs[3]:
        st.dataframe(route_df, use_container_width=True, hide_index=True)
    with tabs[4]:
        audit = pd.DataFrame(st.session_state.audit_events)
        if not audit.empty:
            audit = audit[audit["Deal ID"].astype(str).eq(str(selected))]
        st.dataframe(audit, use_container_width=True, hide_index=True)


def render_analysis_blocks(data: dict[str, pd.DataFrame], deal: dict, lines: pd.DataFrame) -> None:
    region = deal.get("Region", "")
    customer = deal.get("Customer Name", "")
    segment = deal.get("Segment", "")
    account = customer_lookup(data).get(customer, {})
    channel = account.get("Account Type", "")
    summary = summarize_lines(lines)
    included_value = str(deal.get("Included_In_Latest_Financial_Plan", "Yes")).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, lines, region, segment)
    incremental_df = incremental_opportunity_analysis(data, lines, customer, channel)
    inventory_df = enhanced_inventory_analysis(data, lines, region)
    aging_df = enhanced_aging_analysis(data, lines, region)
    competitor_df = enhanced_competitor_intelligence(data, lines, customer, region)
    gp_impact = gross_profit_impact(lines, plan_df, incremental_df, included_in_plan)
    header = {
        "Customer Name": customer,
        "Region": region,
        "Segment": segment,
        "Account Type": channel,
        "Channel": deal.get("Channel", channel),
        "Payment Terms": deal.get("Payment Terms"),
        "Contract Months": deal.get("Contract Months", 0),
        "Special Terms Requested": False,
    }
    route_df = route_preview(header, lines, summary, data)
    score_df, total_score, recommendation, rationale = score_deal(
        summary,
        plan_df,
        incremental_df,
        inventory_df,
        aging_df,
        competitor_df,
        route_df,
        included_in_plan,
    )
    route_triggers = route_with_trigger_reasons(route_df, inventory_df, competitor_df, gp_impact)

    st.subheader("Executive Summary")
    st.write(
        f"**{recommendation}** for {deal.get('Deal Title', 'selected deal')}. "
        f"The deal is classified as **{'included in latest financial plan' if included_in_plan else 'incremental opportunity'}** "
        f"with proposed revenue of **{money(gp_impact['Proposed Revenue'])}**, gross profit impact of "
        f"**{money(gp_impact['Gross Profit Variance'])}**, and a decision score of **{total_score}/100**."
    )
    st.caption(rationale)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision Score", f"{total_score}/100")
    c2.metric("Recommendation", recommendation)
    c3.metric("Plan Inclusion Flag", included_value)
    c4.metric("Gross Profit Impact", money(gp_impact["Gross Profit Variance"]))

    st.subheader("Score Breakdown")
    st.dataframe(score_df, use_container_width=True, hide_index=True)
    st.progress(total_score / 100, text=f"Total Decision Score: {total_score}/100")

    st.subheader("Plan Inclusion Flag")
    flag_message = (
        "Deal is evaluated against planned price, planned quantity, net revenue variance, and gross profit variance."
        if included_in_plan
        else "Deal is evaluated as incremental revenue using historical price and margin benchmarks."
    )
    st.info(f"Included_In_Latest_Financial_Plan = {included_value}. {flag_message}")

    st.subheader("Planned vs Unplanned Logic")
    if included_in_plan:
        st.write(
            "Planned deal logic: compare requested price and quantity against the latest commercial plan. "
            "Price variance is `(New Price - Planned Price) * New Quantity`; volume variance is "
            "`(New Quantity - Planned Quantity) * New Price`; gross profit impact is proposed gross profit minus planned gross profit."
        )
    else:
        st.write(
            "Unplanned deal logic: classify as an incremental opportunity and compare requested economics against historical outcomes. "
            "The app shows incremental revenue, average historical price, price versus historical average percent, and proposed margin versus historical margin."
        )

    if included_in_plan:
        st.subheader("Plan Impact Analysis")
        st.dataframe(plan_df, use_container_width=True, hide_index=True)
    else:
        st.subheader("Incremental Opportunity Analysis")
        st.dataframe(incremental_df, use_container_width=True, hide_index=True)

    st.subheader("Gross Profit Impact")
    gp_cols = st.columns(5)
    gp_cols[0].metric("Context", gp_impact["Context"])
    gp_cols[1].metric("Planned Revenue", money(gp_impact["Planned Revenue"]))
    gp_cols[2].metric("Proposed Revenue", money(gp_impact["Proposed Revenue"]))
    gp_cols[3].metric("Net Revenue Variance", money(gp_impact["Net Revenue Variance"]))
    gp_cols[4].metric("Proposed Margin", pct(gp_impact["Proposed Margin %"]))

    st.subheader("Price-Volume Benchmark")
    st.dataframe(price_volume_summary(data, lines, customer, channel), use_container_width=True, hide_index=True)

    st.subheader("Inventory Analysis")
    st.info(inventory_aging_recommendation(inventory_df, aging_df))
    st.dataframe(inventory_df, use_container_width=True, hide_index=True)

    st.subheader("Aging Analysis")
    st.dataframe(aging_df, use_container_width=True, hide_index=True)

    tender_df, intel_df = tender_competitor_summary(data, lines, customer, region)
    st.subheader("Tender History")
    st.dataframe(tender_df, use_container_width=True, hide_index=True)

    st.subheader("Competitor Intelligence")
    st.info(competitor_summary(competitor_df))
    st.dataframe(competitor_df, use_container_width=True, hide_index=True)
    with st.expander("Raw competitor signals"):
        st.dataframe(intel_df, use_container_width=True, hide_index=True)

    st.subheader("Approval Route with Trigger Reasons")
    st.dataframe(route_triggers, use_container_width=True, hide_index=True)


def page_approval_queue(data: dict[str, pd.DataFrame]) -> None:
    render_header("Approval Queue Preview", "Simulated role-based approval queue for submitted deals.")
    st.info("Select a deal from the approval queue to review details and capture a decision.")
    deals = combined_deals(data)
    confirmation = st.session_state.get("approval_confirmation", "")
    if confirmation:
        st.success(confirmation)
        st.session_state.approval_confirmation = ""
    submitted = deals[deals["Status"].astype(str).str.strip().isin(ACTIVE_APPROVAL_STATUSES - {"Changes Requested"})].copy()
    if submitted.empty:
        st.info("No submitted deals available.")
        return
    role = st.selectbox("Queue Role", ROLE_ORDER, index=ROLE_ORDER.index(st.session_state.get("role", "Sales Manager")) if st.session_state.get("role") in ROLE_ORDER else 0)
    lines = combined_lines(data)
    rows = []
    for _, deal in submitted.iterrows():
        calc_lines = normalize_lines(lines[lines["Deal ID"].astype(str).eq(str(deal["Deal ID"]))], data)
        summary = summarize_lines(calc_lines)
        header = {
            "Customer Name": deal.get("Customer Name"),
            "Region": deal.get("Region"),
            "Segment": deal.get("Segment"),
            "Account Type": customer_lookup(data).get(deal.get("Customer Name"), {}).get("Account Type", ""),
            "Channel": customer_lookup(data).get(deal.get("Customer Name"), {}).get("Account Type", ""),
            "Payment Terms": deal.get("Payment Terms"),
            "Contract Months": deal.get("Contract Months", 0),
            "Special Terms Requested": False,
        }
        route = route_preview(header, calc_lines, summary, data)
        current_role = current_required_approval_role(str(deal["Deal ID"]), str(deal.get("Status", "")).strip(), route)
        if role == current_role:
            reason = route[route["Role"].eq(role)].iloc[0]["Reason"] if role in set(route["Role"]) else "Current required approval step."
            rows.append(
                {
                    "Deal ID": deal["Deal ID"],
                    "Customer": deal["Customer Name"],
                    "Deal Title": deal["Deal Title"],
                    "Value": summary["total_proposed"],
                    "Discount %": summary["discount_pct"],
                    "Risk": deal.get("Intake Risk", ""),
                    "Role": role,
                    "Current Status": deal.get("Status", ""),
                    "Trigger Reason": reason,
                }
            )
    queue = pd.DataFrame(rows)
    if queue.empty:
        st.info(f"No deals currently require {role}.")
        return
    table_event = st.dataframe(
        queue,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="approval_queue_table",
    )
    selected = get_selected_dataframe_deal_id(table_event, queue)
    if selected:
        st.session_state.approval_queue_selected_deal_id = selected
        st.session_state.selected_deal_id = selected
    else:
        st.session_state.approval_queue_selected_deal_id = None
    if not selected:
        st.warning("Select a deal row using the checkbox column to review details and capture a decision.")
        return

    context = build_deal_context(data, selected)
    if not context:
        st.warning("Selected deal details are no longer available.")
        return

    render_approval_review_panel(context)
    previous_status = str(context["deal"].get("Status", "")).strip()
    current_role = current_required_approval_role(selected, previous_status, context["route_df"])
    user_role = st.session_state.get("role", "Demo Role")
    allowed_decisions = allowed_decisions_for_role(user_role)
    can_act_on_step = bool(current_role) and user_role == current_role and bool(allowed_decisions)
    role_cols = st.columns(3)
    role_cols[0].metric("Current Required Role", current_role or "None")
    role_cols[1].metric("Current User Role", user_role)
    role_cols[2].metric("Can Approve", "Yes" if can_act_on_step else "No")
    if not can_act_on_step:
        st.warning(f"{user_role} cannot capture a decision for this step. Required role: {current_role or 'none'}.")

    st.subheader("Decision")
    decision = st.radio("Decision", DECISIONS, horizontal=True, key=f"decision_{selected}")
    comment = st.text_area("Decision comment", key=f"decision_comment_{selected}")
    can_capture = can_act_on_step and decision in allowed_decisions
    if decision not in allowed_decisions:
        st.warning(f"{user_role} is not permitted to capture `{decision}`.")
    if st.button("Capture Decision", type="primary", disabled=not can_capture):
        success, message = process_approval_decision(selected, decision, comment, context["route_df"], previous_status)
        if success:
            st.session_state.approval_confirmation = message
            st.rerun()
        else:
            st.error(message)
    if not can_act_on_step and st.button("Add Comment", type="secondary", disabled=not comment.strip()):
        add_audit(
            selected,
            "Approval comment added",
            entity="Approval Comment",
            details="Comment added without status change.",
            comment=comment,
            approval_step=current_role,
            previous_status=previous_status,
            new_status=previous_status,
        )
        st.session_state.approval_confirmation = f"Comment added for {selected}. Status remains {previous_status}."
        st.rerun()

    if st.button("Open Full Deal Detail", type="secondary"):
        navigate_to_deal_detail(selected, "approval queue preview")


def page_reference_data(data: dict[str, pd.DataFrame]) -> None:
    render_header("Reference Data", "Inspect source datasets powering the MVP.")
    labels = {
        "customers": "Customers",
        "opportunities": "Opportunities",
        "products": "Products",
        "price_book": "Price Book",
        "commercial_plan": "Commercial Plan",
        "price_volume": "Price-Volume History",
        "inventory_coverage": "Inventory Coverage",
        "expiry_aging": "Expiry Aging",
        "tender_history": "Tender History",
        "competitor_intel": "Competitor Intelligence",
        "approval_matrix": "Approval Matrix",
        "approver_roster": "Approver Roster",
    }
    selected = st.selectbox("Dataset", list(labels.keys()), format_func=lambda key: labels[key])
    df = data[selected]
    query = st.text_input("Search within displayed data")
    view = df.copy()
    if query:
        mask = view.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        view = view[mask]
    st.caption(f"{len(view):,} rows shown")
    st.dataframe(view, use_container_width=True, hide_index=True)


def page_audit_log() -> None:
    render_header("Audit Log", "Session-level audit events for the Streamlit MVP.")
    audit = pd.DataFrame(st.session_state.audit_events)
    if audit.empty:
        st.info("No audit events in this session yet.")
        return
    st.dataframe(audit.sort_values("Timestamp", ascending=False), use_container_width=True, hide_index=True)


def sidebar() -> str:
    st.sidebar.title("Deal Desk Copilot")
    persona = st.sidebar.selectbox("Demo Persona", list(PERSONAS.keys()), key="persona")
    st.session_state.role = PERSONAS[persona]
    st.sidebar.caption(f"Role: {st.session_state.role}")
    menu_pages = {
        "Deal Request List": "Deal Requests",
        "New Deal Intake": "New Deal",
        "Approval Queue Preview": "Approval Queue",
        "Reference Data": "Reference Data",
        "Audit Log": "Audit Log",
    }
    valid_pages = set(menu_pages) | {"Deal Detail"}
    if st.session_state.get("current_page") not in valid_pages:
        st.session_state.current_page = "Deal Request List"

    def menu_button(page: str, label: str) -> None:
        active = st.session_state.get("current_page") == page
        prefix = "▸ " if active else ""
        if st.sidebar.button(f"{prefix}{label}", key=f"menu_{page}", use_container_width=True, type="primary" if active else "secondary"):
            st.session_state.current_page = page
            st.rerun()

    st.sidebar.markdown("### 📥 Deals")
    menu_button("Deal Request List", "Deal Requests")
    menu_button("New Deal Intake", "New Deal")
    st.sidebar.markdown("### ✅ Reviews")
    menu_button("Approval Queue Preview", "Approval Queue")
    st.sidebar.markdown("### ⚙️ Admin")
    menu_button("Reference Data", "Reference Data")
    menu_button("Audit Log", "Audit Log")
    st.sidebar.divider()
    st.sidebar.metric("Session Deals", len(st.session_state.runtime_deals))
    st.sidebar.metric("Audit Events", len(st.session_state.audit_events))
    if st.sidebar.button("Reset Demo Session"):
        st.session_state.runtime_deals = []
        st.session_state.runtime_lines = []
        st.session_state.audit_events = []
        st.session_state.deal_status_overrides = {}
        st.session_state.deal_approval_steps = {}
        st.session_state.approval_confirmation = ""
        st.session_state.deal_detail_confirmation = ""
        st.session_state.deal_list_selected_deal_id = None
        st.session_state.approval_queue_selected_deal_id = None
        st.session_state.selected_deal_id = None
        st.session_state.deal_detail_parent = "Deal Requests"
        st.session_state.draft_lines = None
        st.session_state.current_page = "Deal Request List"
        st.rerun()
    return st.session_state.current_page


def main() -> None:
    inject_css()
    init_state()
    data = load_demo_data()
    page = sidebar()
    if page == "Deal Request List":
        page_deal_list(data)
    elif page == "New Deal Intake":
        page_new_deal(data)
    elif page == "Deal Detail":
        page_deal_detail(data)
    elif page == "Approval Queue Preview":
        page_approval_queue(data)
    elif page == "Reference Data":
        page_reference_data(data)
    elif page == "Audit Log":
        page_audit_log()


if __name__ == "__main__":
    main()
