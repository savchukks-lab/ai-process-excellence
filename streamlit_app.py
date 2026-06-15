from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st


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
    st.session_state.setdefault("draft_lines", None)
    st.session_state.setdefault("current_page", "Deal Request List")
    st.session_state.setdefault("nav_widget", "Deal Request List")
    st.session_state.setdefault("_sync_nav_widget", False)


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


def safe_float(value: object, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def status_badge(value: str) -> str:
    return f"<span class='status-pill'>{value}</span>"


def risk_badge(value: str) -> str:
    risk_class = {
        "High": "risk-high",
        "Medium": "risk-medium",
        "Low": "risk-low",
    }.get(str(value), "")
    return f"<span class='status-pill {risk_class}'>{value}</span>"


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
    st.session_state._sync_nav_widget = True
    add_audit(deal_id, "Deal viewed", details=f"Opened from {source}.")
    st.rerun()


def set_current_page(page: str) -> None:
    st.session_state.current_page = page
    st.session_state._sync_nav_widget = True
    st.rerun()


def sync_current_page_from_nav_widget() -> None:
    st.session_state.current_page = st.session_state.nav_widget


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
        proposed = float(row.get("Proposed Unit Price", 0) or 0)
        unit_cost = float(row.get("Unit Cost", prod.get("Standard Cost", 0)) or 0)
        extended_list = qty * list_price
        extended_proposed = qty * proposed
        discount = 0 if list_price == 0 else (list_price - proposed) / list_price
        margin = None if extended_proposed <= 0 else (extended_proposed - (qty * unit_cost)) / extended_proposed
        rows.append(
            {
                "SKU": sku,
                "Product Name": prod.get("Product Name", row.get("Product Name", "")),
                "Therapeutic Area": prod.get("Therapeutic Area", ""),
                "Product Type": prod.get("Product Type", ""),
                "Quantity": qty,
                "Unit List Price": list_price,
                "Unit Cost": unit_cost,
                "Proposed Unit Price": proposed,
                "Extended List": extended_list,
                "Extended Proposed": extended_proposed,
                "Discount %": discount,
                "Margin %": margin,
                "Target Margin %": prod.get("Target Margin %", 0),
                "Requested Delivery Date": row.get("Requested Delivery Date", None),
                "Storage": prod.get("Storage", ""),
                "Supply Risk": prod.get("Supply Risk", ""),
                "Inventory Tracked": prod.get("Inventory Tracked", ""),
                "Notes": row.get("Notes", ""),
            }
        )
    return pd.DataFrame(rows)


def summarize_lines(lines: pd.DataFrame) -> dict:
    if lines.empty:
        return {
            "total_list": 0,
            "total_proposed": 0,
            "discount_amount": 0,
            "discount_pct": 0,
            "margin_pct": None,
            "weighted_target_margin": 0,
            "line_count": 0,
        }
    total_list = float(lines["Extended List"].sum())
    total_proposed = float(lines["Extended Proposed"].sum())
    cost = float((lines["Quantity"] * lines["Unit Cost"]).sum())
    margin = None if total_proposed <= 0 else (total_proposed - cost) / total_proposed
    target = 0
    positive = lines[lines["Extended Proposed"] > 0].copy()
    if not positive.empty:
        target = float((positive["Extended Proposed"] * positive["Target Margin %"].fillna(0)).sum() / positive["Extended Proposed"].sum())
    return {
        "total_list": total_list,
        "total_proposed": total_proposed,
        "discount_amount": total_list - total_proposed,
        "discount_pct": 0 if total_list == 0 else (total_list - total_proposed) / total_list,
        "margin_pct": margin,
        "weighted_target_margin": target,
        "line_count": len(lines),
    }


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


def plan_price_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str, segment: str) -> pd.DataFrame:
    plan = data["commercial_plan"]
    if plan.empty or lines.empty:
        return pd.DataFrame()
    rows = []
    for _, line in lines.iterrows():
        match = find_plan_match(data, line, region, segment)
        if match is None:
            continue
        planned = float(match.get("Planned Net Price", 0) or 0)
        actual = float(line["Proposed Unit Price"])
        rows.append(
            {
                "SKU": line["SKU"],
                "Product": line["Product Name"],
                "Planned Net": planned,
                "Requested Net": actual,
                "Price Variance %": None if planned == 0 else (actual - planned) / planned,
                "Plan Units": match.get("Plan Units", None),
                "Requested Units": line["Quantity"],
            }
        )
    return pd.DataFrame(rows)


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


def inventory_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str) -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        inv = find_inventory(data, str(line["SKU"]), region)
        if inv is None:
            continue
        qty = float(line["Quantity"])
        rows.append(
            {
                "SKU": line["SKU"],
                "Requested Qty": qty,
                "Available Qty": inv.get("Available Qty"),
                "Coverage Days": inv.get("Coverage Days"),
                "Lead Time Days": inv.get("Lead Time Days"),
                "Coverage Status": inv.get("Coverage Status"),
                "Quantity Status": "Sufficient" if float(inv.get("Available Qty", 0)) >= qty else "Short",
            }
        )
    return pd.DataFrame(rows)


def aging_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str) -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        exp = find_expiry(data, str(line["SKU"]), region)
        if exp is None:
            continue
        rows.append(
            {
                "SKU": line["SKU"],
                "Lot ID": exp.get("Lot ID"),
                "Days To Expiry": exp.get("Days To Expiry"),
                "Expiry Bucket": exp.get("Expiry Bucket"),
                "Quantity On Hand": exp.get("Quantity On Hand"),
                "Quality Status": exp.get("Quality Status"),
                "Disposition": exp.get("Disposition Recommendation"),
            }
        )
    return pd.DataFrame(rows)


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
        planned_gp = (planned_price - standard_cost) * planned_qty
        proposed_gp = (new_price - standard_cost) * new_qty
        rows.append(
            {
                "SKU": line["SKU"],
                "Product": line["Product Name"],
                "Planned Price": planned_price,
                "New Price": new_price,
                "Planned Quantity": planned_qty,
                "New Quantity": new_qty,
                "Planned Revenue": planned_revenue,
                "Proposed Revenue": proposed_revenue,
                "Price Variance": (new_price - planned_price) * new_qty,
                "Volume Variance": (new_qty - planned_qty) * new_price,
                "Net Revenue Variance": proposed_revenue - planned_revenue,
                "Gross Profit Variance": proposed_gp - planned_gp,
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
        hist_margin = None if avg_price <= 0 else (avg_price - unit_cost) / avg_price
        proposed_margin = None if proposed_price <= 0 else (proposed_price - unit_cost) / proposed_price
        rows.append(
            {
                "SKU": sku,
                "Product": line["Product Name"],
                "Incremental Revenue": proposed_price * proposed_qty,
                "Average Historical Price": avg_price,
                "Price vs Historical Price %": None if avg_price <= 0 else (proposed_price - avg_price) / avg_price,
                "Historical Average Margin %": hist_margin,
                "Proposed Margin %": proposed_margin,
                "Margin Difference": None if hist_margin is None or proposed_margin is None else proposed_margin - hist_margin,
            }
        )
    return pd.DataFrame(rows)


def gross_profit_impact(lines: pd.DataFrame, plan_df: pd.DataFrame, incremental_df: pd.DataFrame, included_in_plan: bool) -> dict:
    proposed_revenue = safe_float(lines["Extended Proposed"].sum()) if not lines.empty else 0
    proposed_gp = safe_float(((lines["Proposed Unit Price"] - lines["Unit Cost"]) * lines["Quantity"]).sum()) if not lines.empty else 0
    proposed_margin = None if proposed_revenue <= 0 else proposed_gp / proposed_revenue
    if included_in_plan and not plan_df.empty:
        planned_revenue = safe_float(plan_df["Planned Revenue"].sum())
        net_variance = safe_float(plan_df["Net Revenue Variance"].sum())
        gp_variance = safe_float(plan_df["Gross Profit Variance"].sum())
        context = "Variance to latest financial plan"
    else:
        planned_revenue = 0
        net_variance = proposed_revenue
        gp_variance = proposed_gp
        context = "Incremental opportunity"
    return {
        "Context": context,
        "Planned Revenue": planned_revenue,
        "Proposed Revenue": proposed_revenue,
        "Net Revenue Variance": net_variance,
        "Proposed Gross Profit": proposed_gp,
        "Gross Profit Variance": gp_variance,
        "Proposed Margin %": proposed_margin,
    }


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


def score_deal(
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
    if "Commercial Executive" in roles:
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
    if "Legal Reviewer" in roles:
        risk_score -= 3
    if "Finance Approver" in roles:
        risk_score -= 2
    if "Operations Reviewer" in roles:
        risk_score -= 2
    if "Commercial Executive" in roles:
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
    executive_exposure = "Commercial Executive" in roles

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


def final_recommendation(errors: list[str], warnings: list[str], summary: dict, route_df: pd.DataFrame) -> tuple[str, str]:
    if errors:
        return "Request revision", "Blocking validation issues must be resolved before submission."
    if "Commercial Executive" in set(route_df["Role"]):
        return "Escalate / approve with conditions", "Strategic or high-value exception requires executive review."
    if summary["margin_pct"] is not None and summary["margin_pct"] < summary["weighted_target_margin"]:
        return "Approve with conditions", "Margin is below weighted target and requires reviewer conditions."
    if warnings:
        return "Approve with conditions", "Warnings are present but do not block submission."
    return "Approve", "No blocking issues or material warning conditions detected."


def render_header(title: str, subtitle: str = "") -> None:
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
    target = float(prod.get("WAC / List Price", 0)) * 0.9
    return {
        "SKU": prod["SKU"],
        "Quantity": 1,
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

    tabs = st.tabs(["Customer", "Deal Terms", "Line Items", "Rationale", "Review"])

    with tabs[0]:
        customer_name = st.selectbox("Customer", customers["Customer Name"].tolist(), key="form_customer")
        customer = customers[customers["Customer Name"].eq(customer_name)].iloc[0].to_dict()
        opps = opportunities[opportunities["Customer ID"].eq(customer["Customer ID"])]
        opp_options = [""] + opps["Opportunity Name"].tolist()
        opportunity_name = st.selectbox("Opportunity", opp_options, key="form_opportunity")
        cols = st.columns(4)
        cols[0].metric("Account Type", customer.get("Account Type", ""))
        cols[1].metric("Segment", customer.get("Segment", ""))
        cols[2].metric("Region", customer.get("Region", ""))
        cols[3].metric("Credit", customer.get("Credit Status", ""))
        st.info(str(customer.get("Commercial Notes", "")))
        if customer.get("Credit Status") == "Watch":
            st.warning("Credit status is Watch. Finance review is likely.")
        if customer.get("Credit Status") == "Hold":
            st.error("Credit status is Hold. Submission should route to Finance before approval.")

    with tabs[1]:
        left, right = st.columns(2)
        deal_title = left.text_input("Deal Title", value=f"{customer_name} Commercial Deal", key="form_title")
        deal_type = left.selectbox("Deal Type", ["New Sale", "Renewal", "Expansion", "Competitive replacement", "Strategic exception"], key="form_type")
        sales_owner = left.selectbox("Sales Owner", sorted(PERSONAS.keys()), index=0, key="form_owner")
        sales_manager = left.selectbox("Sales Manager", ["Jordan Blake", "Lena Torres", "Sarah Morgan"], key="form_manager")
        region = right.selectbox("Region", sorted(data["commercial_plan"]["Region"].dropna().unique()), index=0, key="form_region")
        currency = right.selectbox("Currency", ["USD", "EUR"], key="form_currency")
        target_close = right.date_input("Target Close Date", value=date.today() + timedelta(days=45), key="form_close")
        effective_date = right.date_input("Requested Effective Date", value=date.today() + timedelta(days=60), key="form_effective")
        c1, c2, c3 = st.columns(3)
        payment_terms = c1.selectbox("Payment Terms", ["Net 30", "Net 45", "Net 60", "Net 75", "Net 90"], key="form_terms")
        contract_months = c2.number_input("Contract Months", min_value=1, max_value=72, value=24, step=1, key="form_contract")
        billing = c3.selectbox("Billing Frequency", ["Annual", "Quarterly", "Monthly", "Milestone"], key="form_billing")
        special_terms = st.checkbox("Special terms requested", key="form_special")
        special_desc = st.text_area("Special Terms Description", value="", key="form_special_desc")

    with tabs[2]:
        st.caption("Edit SKU, quantity, proposed price, delivery date, and notes. Product metadata and calculations appear below.")
        editor_config = {
            "SKU": st.column_config.SelectboxColumn("SKU", options=products["SKU"].tolist(), required=True),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1),
            "Proposed Unit Price": st.column_config.NumberColumn("Proposed Unit Price", min_value=-1_000_000.0, step=1.0),
            "Requested Delivery Date": st.column_config.DateColumn("Requested Delivery Date"),
            "Notes": st.column_config.TextColumn("Notes"),
        }
        st.session_state.draft_lines = st.data_editor(
            st.session_state.draft_lines,
            num_rows="dynamic",
            use_container_width=True,
            column_config=editor_config,
            hide_index=True,
            key="line_editor",
        )
        calc_lines = normalize_lines(st.session_state.draft_lines, data)
        summary = summarize_lines(calc_lines)
        metric_cols = st.columns(5)
        metric_cols[0].metric("Line Items", summary["line_count"])
        metric_cols[1].metric("Total List", money(summary["total_list"]))
        metric_cols[2].metric("Total Proposed", money(summary["total_proposed"]))
        metric_cols[3].metric("Discount", pct(summary["discount_pct"]))
        metric_cols[4].metric("Est. Margin", pct(summary["margin_pct"]))
        if not calc_lines.empty:
            view = calc_lines[["SKU", "Product Name", "Quantity", "Unit List Price", "Proposed Unit Price", "Discount %", "Extended Proposed", "Storage", "Supply Risk"]].copy()
            st.dataframe(view, use_container_width=True, hide_index=True)

    with tabs[3]:
        business_justification = st.text_area("Business Justification", height=130, key="form_justification")
        competitive_situation = st.selectbox("Competitive Situation", ["None known", "Incumbent competitor", "Price pressure", "Feature comparison", "Unknown"], key="form_competitive")
        known_competitor = st.text_input("Known Competitor", key="form_competitor")
        decision_deadline = st.date_input("Customer Decision Deadline", value=date.today() + timedelta(days=30), key="form_deadline")
        expansion_impact = st.text_area("Renewal or Expansion Impact", height=100, key="form_expansion")

    header = {
        "Deal Title": st.session_state.get("form_title", ""),
        "Deal Type": st.session_state.get("form_type", ""),
        "Customer Name": customer_name,
        "Customer ID": customer.get("Customer ID"),
        "Opportunity Name": opportunity_name,
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
    recommendation, rec_reason = final_recommendation(errors, warnings, summary, route_df)

    with tabs[4]:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Commercial Summary")
            st.write(f"Customer: **{customer_name}**")
            st.write(f"Deal: **{header['Deal Title']}**")
            st.write(f"Rationale: {header['Business Justification'] or 'Not provided'}")
            st.dataframe(calc_lines, use_container_width=True, hide_index=True)
        with col2:
            st.subheader("Readiness")
            st.metric("Total Proposed", money(summary["total_proposed"]))
            st.metric("Discount", pct(summary["discount_pct"]))
            st.metric("Est. Margin", pct(summary["margin_pct"]))
            st.markdown(risk_badge("High" if warnings else "Low"), unsafe_allow_html=True)
            if errors:
                st.error("Blocking issues")
                for err in errors:
                    st.write(f"- {err}")
            if warnings:
                st.warning("Warnings")
                for warn in warnings:
                    st.write(f"- {warn}")
            st.subheader("Route Preview")
            st.dataframe(route_df, use_container_width=True, hide_index=True)
            st.subheader("Recommendation")
            st.write(f"**{recommendation}**")
            st.caption(rec_reason)

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
            "Opportunity ID": opportunity_id,
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
            "Included_In_Latest_Financial_Plan": "Yes",
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
    pages = ["Deal Request List", "New Deal Intake", "Deal Detail", "Approval Queue Preview", "Reference Data", "Audit Log"]
    if st.session_state.get("current_page") not in pages:
        st.session_state.current_page = pages[0]
        st.session_state._sync_nav_widget = True
    if st.session_state.get("nav_widget") not in pages or st.session_state.get("_sync_nav_widget"):
        st.session_state.nav_widget = st.session_state.current_page
        st.session_state._sync_nav_widget = False
    st.sidebar.radio("Navigation", pages, key="nav_widget", on_change=sync_current_page_from_nav_widget)
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
        st.session_state.approval_deal_to_review = ""
        st.session_state.deal_list_selected_deal_id = None
        st.session_state.approval_queue_selected_deal_id = None
        st.session_state.selected_deal_id = None
        st.session_state.draft_lines = None
        st.session_state.current_page = pages[0]
        st.session_state._sync_nav_widget = True
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
