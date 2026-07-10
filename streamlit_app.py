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
    "KAM North",
    "KAM South",
    "Sales Manager",
    "Pricing Governance Owner",
    "Finance Director",
    "Operations Manager",
    "General Manager",
    "System Administrator",
]

PERSONAS = {
    "Maya Chen": "KAM North",
    "Ethan Brooks": "KAM South",
    "Jordan Blake": "Sales Manager",
    "Priya Nair": "Pricing Governance Owner",
    "Daniel Ortiz": "Finance Director",
    "Elena Rossi": "Operations Manager",
    "Sarah Morgan": "General Manager",
    "Admin User": "System Administrator",
}

SALES_MANAGER_TEAMS = {
    "Jordan Blake": ["Maya Chen", "Ethan Brooks"],
}

APPROVAL_STEP_STATUS = {
    "Sales Manager": "Pending Sales Manager",
    "Pricing Governance Owner": "Pending Governance Review",
    "Finance Director": "Pending Governance Review",
    "Operations Manager": "Pending Governance Review",
    "General Manager": "Pending General Manager",
}

STATUS_APPROVAL_STEP = {
    "Pending Sales Manager": "Sales Manager",
    "Pending Pricing Governance": "Pricing Governance Owner",
    "Pending Finance": "Finance Director",
    "Pending Supply Chain": "Operations Manager",
    "Pending Operations": "Operations Manager",
    "Pending General Manager": "General Manager",
}

ACTIONABLE_APPROVAL_ROLES = [
    "Sales Manager",
    "Pricing Governance Owner",
    "Finance Director",
    "Operations Manager",
    "General Manager",
]

ACTIVE_APPROVAL_STATUSES = {
    "Submitted",
    "Pending Sales Manager",
    "Pending Pricing Governance",
    "Pending Finance",
    "Pending Supply Chain",
    "Pending Operations",
    "Pending Governance Review",
    "Pending General Manager",
    "Changes Requested",
}

ARCHIVE_STATUSES = {"Approved", "Final Approved", "Rejected", "Withdrawn"}

DECISIONS = ["Approve", "Request Changes", "Reject"]

KAM_RISK_LEVELS = ["Low", "Medium", "High", "Critical"]

RISK_REASON_VALUES = [
    "Competitor price pressure",
    "Public tender",
    "Incumbent defense",
    "Customer consolidation",
    "New account acquisition",
    "Budget constraints",
    "Volume commitment requirement",
    "Inventory / expiry mitigation",
]

RISK_LEVEL_SCORE = {"Low": 1, "Medium": 3, "High": 5, "Critical": 7}
LARGE_DEAL_VALUE_THRESHOLD = 1_000_000

ROLE_ALLOWED_DECISIONS = {
    "KAM North": [],
    "KAM South": [],
    "Sales Manager": ["Approve", "Request Changes", "Reject"],
    "Pricing Governance Owner": ["Approve", "Request Changes", "Reject"],
    "Finance Director": ["Approve", "Request Changes", "Reject"],
    "Operations Manager": ["Approve", "Request Changes", "Reject"],
    "General Manager": ["Approve", "Request Changes", "Reject"],
    "System Administrator": [],
}

SENSITIVE_FIELD_PATTERNS = [
    "COGS",
    "Cost",
    "Gross Margin",
    "Gross Profit",
    "Margin %",
    "Margin Variance",
    "Floor Price",
    "Walk-away Price",
    "Guidance Price",
    "Target Margin",
    "Price Corridor",
    "IRP",
    "Plan Impact",
    "Planned Gross Profit",
    "Proposed Gross Profit",
    "Gross Profit Variance",
    "Net Revenue Variance",
    "Revenue Variance",
    "Planned Revenue",
    "Proposed Revenue",
    "Planned Net Price",
    "Historical Margin",
    "Margin Difference",
]

ROLE_VISIBLE_SENSITIVE_PATTERNS = {
    "KAM North": [],
    "KAM South": [],
    "Sales Manager": ["Proposed Revenue", "Planned Revenue", "Net Revenue Variance", "Revenue Variance"],
    "Pricing Governance Owner": SENSITIVE_FIELD_PATTERNS,
    "Finance Director": SENSITIVE_FIELD_PATTERNS,
    "Operations Manager": [],
    "General Manager": SENSITIVE_FIELD_PATTERNS,
    "System Administrator": SENSITIVE_FIELD_PATTERNS,
}


st.set_page_config(
    page_title="Commercial Deal Desk Copilot",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 100px;
            padding-bottom: 1.25rem;
            max-width: 100%;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        h1 {
            font-size: 1.55rem !important;
            margin: 0.1rem 0 0.35rem !important;
        }
        h2 {
            font-size: 1.16rem !important;
            margin: 0.55rem 0 0.25rem !important;
        }
        h3 {
            font-size: 1rem !important;
            margin: 0.45rem 0 0.2rem !important;
        }
        div[data-testid="stMarkdownContainer"] p {
            margin-bottom: 0.35rem;
        }
        div[data-testid="stExpander"] {
            margin-top: 0.35rem;
        }
        div[data-testid="stTabs"] {
            margin-top: 0.65rem;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid #cbd5e1;
            overflow-x: auto;
            scrollbar-width: thin;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            flex: 0 0 auto;
            min-height: 2.55rem;
            padding: 0.55rem 0.9rem;
            color: #334155;
            background: #f8fafc;
            border: 1px solid #d7dee8;
            border-bottom: 0;
            border-radius: 7px 7px 0 0;
            font-weight: 600;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            color: #0f513f;
            background: #ffffff;
            border-color: #16805d;
            box-shadow: inset 0 -3px 0 #16805d;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {
            color: inherit !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ai-support-marker) {
            background: #f8fbfa;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-action-marker) {
            position: sticky;
            top: 0.75rem;
            z-index: 20;
            background: #ffffff;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
        }
        hr {
            margin: 0.55rem 0 !important;
        }
        [data-testid="stMetric"] {
            background: #f6f8fb;
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 7px 10px;
        }
        [data-testid="stMetric"] label {
            font-size: 0.76rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.18rem;
        }
        button[kind="primary"] {
            background: #16805d !important;
            border-color: #16805d !important;
        }
        button[kind="primary"]:hover {
            background: #116c4e !important;
            border-color: #116c4e !important;
        }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stMultiSelect"] label {
            font-size: 0.76rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #d7dee8;
            border-radius: 6px;
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
            font-size: 0.86rem;
            margin-bottom: 0.35rem;
        }
        .page-breadcrumb {
            color: #64748b;
            font-size: 0.76rem;
            margin: 0 0 0.05rem;
        }
        .nav-marker {
            display: none;
        }
        @media (max-width: 760px) {
            html, body, [data-testid="stAppViewContainer"] {
                overflow-x: hidden;
            }
            .block-container {
                padding-left: 0.65rem;
                padding-right: 0.65rem;
            }
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 0.45rem !important;
            }
            [data-testid="stColumn"],
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 auto !important;
            }
            [data-testid="stColumn"]:has(.nav-title-marker),
            [data-testid="column"]:has(.nav-title-marker) {
                order: 1;
            }
            [data-testid="stColumn"]:has(.nav-user-marker),
            [data-testid="column"]:has(.nav-user-marker) {
                order: 2;
            }
            [data-testid="stColumn"]:has(.nav-new-marker),
            [data-testid="column"]:has(.nav-new-marker) {
                order: 3;
            }
            [data-testid="stColumn"]:has(.nav-governance-marker),
            [data-testid="column"]:has(.nav-governance-marker) {
                order: 4;
            }
            h1 {
                font-size: 1.32rem !important;
            }
            [data-testid="stMetric"] {
                padding: 6px 8px;
            }
            div[data-testid="stTabs"] {
                max-width: 100%;
                overflow: hidden;
            }
            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                flex-wrap: nowrap;
                width: 100%;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-action-marker) {
                position: static;
                box-shadow: none;
            }
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
    data = {
        "customers": read_sheet("Customer_Master.xlsx", "Customers"),
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
        "competitor_intel": read_sheet("Competitor_Intelligence.xlsx", "External Market Signals"),
    }
    data["deal_summary_source"] = data["deal_summary"]
    data["deal_summary"] = calculated_deal_summary(data)
    return data


def init_state() -> None:
    st.session_state.setdefault("persona", "Maya Chen")
    st.session_state.setdefault("role", PERSONAS[st.session_state.persona])
    st.session_state.setdefault("runtime_deals", [])
    st.session_state.setdefault("runtime_lines", [])
    st.session_state.setdefault("audit_events", [])
    st.session_state.setdefault("deal_status_overrides", {})
    st.session_state.setdefault("deal_approval_steps", {})
    st.session_state.setdefault("approval_assignments", {})
    st.session_state.setdefault("workflow_audit_keys", [])
    st.session_state.setdefault("delegate_overrides", None)
    st.session_state.setdefault("approval_matrix_overrides", None)
    st.session_state.setdefault("role_permission_overrides", None)
    st.session_state.setdefault("requestor_followups", [])
    st.session_state.setdefault("approval_confirmation", "")
    st.session_state.setdefault("deal_detail_confirmation", "")
    st.session_state.setdefault("selected_deal_id", None)
    st.session_state.setdefault("deal_list_view_mode", "Active")
    st.session_state.setdefault("deal_list_table_revision", 0)
    st.session_state.setdefault("deal_detail_parent", "Deal Requests")
    st.session_state.setdefault("draft_lines", None)
    st.session_state.setdefault("line_editor_rows", None)
    st.session_state.setdefault("line_editor_revision", 0)
    st.session_state.setdefault("editing_deal_id", None)
    st.session_state.setdefault("editing_deal_original_status", "")
    st.session_state.setdefault("editing_review_comment", "")
    st.session_state.setdefault("deal_edit_active", False)
    st.session_state.setdefault("current_draft_snapshot", None)
    st.session_state.setdefault("role_selector_version", 0)
    st.session_state.setdefault("pending_role_switch", None)
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
    sensitive_fields_visible: str | None = None,
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
        "Sensitive Fields Visible": sensitive_fields_visible if sensitive_fields_visible is not None else sensitive_fields_visible_for_role(st.session_state.get("role", "")),
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


def display_timestamp(value: str) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return str(value or "Not recorded")
    return timestamp.strftime("%d-%b-%Y %H:%M")


def status_badge(value: str) -> str:
    return f"<span class='status-pill'>{value}</span>"


def risk_badge(value: str) -> str:
    risk_class = {
        "High": "risk-high",
        "Medium": "risk-medium",
        "Low": "risk-low",
    }.get(str(value), "")
    return f"<span class='status-pill {risk_class}'>{value}</span>"


def current_persona() -> str:
    return st.session_state.get("persona", "Maya Chen")


def current_role() -> str:
    return st.session_state.get("role", PERSONAS.get(current_persona(), "KAM North"))


def default_role_permission_config() -> list[dict]:
    return [
        {"Role": "KAM North", "Sensitive Visibility": "Restricted", "Margin Visibility": "Hidden", "Configuration Rights": False},
        {"Role": "KAM South", "Sensitive Visibility": "Restricted", "Margin Visibility": "Hidden", "Configuration Rights": False},
        {"Role": "Sales Manager", "Sensitive Visibility": "Restricted", "Margin Visibility": "Status Only", "Configuration Rights": False},
        {"Role": "Pricing Governance Owner", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": False},
        {"Role": "Finance Director", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": False},
        {"Role": "Operations Manager", "Sensitive Visibility": "Restricted", "Margin Visibility": "Hidden", "Configuration Rights": False},
        {"Role": "General Manager", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": False},
        {"Role": "System Administrator", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": True},
    ]


def role_permission_config() -> pd.DataFrame:
    if st.session_state.get("role_permission_overrides") is None:
        st.session_state.role_permission_overrides = default_role_permission_config()
    config = pd.DataFrame(st.session_state.role_permission_overrides)
    if config.empty:
        config = pd.DataFrame(default_role_permission_config())
    config["Configuration Rights"] = config["Configuration Rights"].astype(bool)
    return config


def role_permission_profile(role: str | None = None) -> dict:
    role_name = role or current_role()
    config = role_permission_config()
    match = config[config["Role"].astype(str).eq(str(role_name))]
    if match.empty:
        return {}
    return match.iloc[0].to_dict()


def margin_visibility_for_role(role: str | None = None) -> str:
    return str(role_permission_profile(role).get("Margin Visibility", "Hidden"))


def is_kam_role(role: str | None = None) -> bool:
    return (role or current_role()) in {"KAM North", "KAM South"}


def has_full_visibility(role: str | None = None) -> bool:
    profile = role_permission_profile(role)
    if profile:
        return profile.get("Sensitive Visibility") == "Full"
    return (role or current_role()) in {
        "Pricing Governance Owner",
        "Finance Director",
        "General Manager",
        "System Administrator",
    }


def can_configure_system(role: str | None = None) -> bool:
    profile = role_permission_profile(role)
    if profile:
        return bool(profile.get("Configuration Rights"))
    return (role or current_role()) == "System Administrator"


def can_create_request(role: str | None = None) -> bool:
    role_name = role or current_role()
    return is_kam_role(role_name) or role_name == "System Administrator"


def can_view_reference_data(role: str | None = None) -> bool:
    return (role or current_role()) in {
        "Finance Director",
        "Pricing Governance Owner",
        "General Manager",
        "System Administrator",
    }


def margin_status(margin_value: object, target_value: object) -> str:
    margin = safe_float(margin_value)
    target = safe_float(target_value)
    return "Above Margin Target" if margin >= target else "Below Margin Target"


def margin_display(summary: dict, role: str | None = None) -> str:
    role_name = role or current_role()
    if margin_visibility_for_role(role_name) == "Status Only":
        return margin_status(summary.get("margin_pct"), summary.get("weighted_target_margin"))
    return sensitive_pct("Gross Margin %", summary.get("margin_pct"), role_name)


def margin_value_display(value: object, target: object | None = None, role: str | None = None) -> str:
    role_name = role or current_role()
    if margin_visibility_for_role(role_name) == "Status Only":
        return margin_status(value, target) if target is not None else "Margin Status Only"
    return sensitive_pct("Gross Margin %", value, role_name)


def customer_margin_display(customer: dict, role: str | None = None) -> str:
    role_name = role or current_role()
    margin = safe_float(customer.get("Last 12M Gross Margin %"))
    if margin_visibility_for_role(role_name) == "Exact" or has_full_visibility(role_name):
        return pct(margin)
    return "Above target" if margin >= 0.35 else "Below target"


def render_credit_warning_banner(customer: dict) -> None:
    credit_status = str(customer.get("Credit Status", ""))
    overdue_ar = safe_float(customer.get("Overdue AR"))
    if credit_status == "Hold":
        st.error("Credit status is Hold. Finance Director approval is mandatory before final approval.")
    elif overdue_ar > 0:
        st.warning(f"Overdue receivables are {money(overdue_ar)}. Finance Director approval is mandatory.")


def render_customer_information_panel(customer: dict) -> None:
    st.subheader("Customer Information")
    render_credit_warning_banner(customer)
    row1 = st.columns(3)
    row1[0].metric("Customer Type", customer_type(customer))
    row1[1].metric("Strategic Account", str(customer.get("Strategic Account", "")))
    row1[2].metric("Credit Status", str(customer.get("Credit Status", "")))
    row2 = st.columns(3)
    row2[0].metric("Current AR", money(customer.get("Current AR")))
    row2[1].metric("Overdue AR", money(customer.get("Overdue AR")))
    row2[2].metric("Oldest Overdue Days", f"{safe_float(customer.get('Oldest Overdue Days')):,.0f}")
    row3 = st.columns(2)
    row3[0].metric("Last 12M Revenue", money(customer.get("Last 12M Revenue")))
    row3[1].metric("Last 12M Gross Margin %", customer_margin_display(customer))


def is_sensitive_field(field_name: object) -> bool:
    name = str(field_name)
    return any(pattern.lower() in name.lower() for pattern in SENSITIVE_FIELD_PATTERNS)


def can_view_sensitive_field(role: str, field_name: object) -> bool:
    if not is_sensitive_field(field_name):
        return True
    profile = role_permission_profile(role)
    if profile.get("Sensitive Visibility") == "Full":
        return True
    if "margin" in str(field_name).lower() and profile.get("Margin Visibility") == "Exact":
        return True
    allowed = ROLE_VISIBLE_SENSITIVE_PATTERNS.get(str(role), [])
    return any(pattern.lower() in str(field_name).lower() for pattern in allowed)


def sensitive_fields_visible_for_role(role: str) -> str:
    allowed = ROLE_VISIBLE_SENSITIVE_PATTERNS.get(str(role), [])
    return "Yes" if allowed == SENSITIVE_FIELD_PATTERNS or bool(allowed) else "No"


def mask_sensitive_dataframe(df: pd.DataFrame, role: str | None = None, replacement: str = "Restricted") -> pd.DataFrame:
    if df.empty:
        return df
    role_name = role or current_role()
    masked = df.copy()
    if margin_visibility_for_role(role_name) == "Status Only":
        target_col = next((col for col in masked.columns if "target margin" in str(col).lower()), None)
        margin_cols = [
            col
            for col in masked.columns
            if "margin" in str(col).lower()
            and "target margin" not in str(col).lower()
            and is_sensitive_field(col)
        ]
        for col in margin_cols:
            if target_col:
                masked[col] = [
                    margin_status(row.get(col), row.get(target_col))
                    for _, row in masked.iterrows()
                ]
            else:
                masked[col] = "Margin Status Only"
    for col in masked.columns:
        if margin_visibility_for_role(role_name) == "Status Only" and "margin" in str(col).lower() and "target margin" not in str(col).lower():
            continue
        if is_sensitive_field(col) and not can_view_sensitive_field(role_name, col):
            masked[col] = replacement
    return masked


def sensitive_data_note() -> None:
    st.caption("Sensitive fields are displayed based on role permissions.")


def sensitive_value(field_name: str, value: object, role: str | None = None, replacement: str = "Restricted") -> object:
    role_name = role or current_role()
    if is_sensitive_field(field_name) and not can_view_sensitive_field(role_name, field_name):
        return replacement
    return value


def sensitive_money(field_name: str, value: object, role: str | None = None) -> str:
    masked = sensitive_value(field_name, value, role)
    return str(masked) if masked == "Restricted" else money(masked)


def sensitive_pct(field_name: str, value: object, role: str | None = None) -> str:
    masked = sensitive_value(field_name, value, role)
    return str(masked) if masked == "Restricted" else pct(masked)


def route_visible_deal_ids_for_roles(deals: pd.DataFrame, data: dict[str, pd.DataFrame], roles: list[str]) -> set[str]:
    if deals.empty or not roles:
        return set()
    lines = combined_lines(data)
    visible_ids: set[str] = set()
    for _, deal in deals.iterrows():
        calc_lines = normalize_lines(lines[lines["Deal ID"].astype(str).eq(str(deal["Deal ID"]))], data)
        summary = summarize_lines(calc_lines)
        route = route_preview(build_route_header(deal.to_dict(), data), calc_lines, summary, data)
        status = str(deal.get("Status", "")).strip()
        active_status = status in ACTIVE_APPROVAL_STATUSES - {"Changes Requested"}
        route_roles = set(route.get("Role", pd.Series(dtype=str)).astype(str)) if not route.empty else set()
        if active_status and route_roles.intersection(roles):
            visible_ids.add(str(deal["Deal ID"]))
    return visible_ids


def parse_percent_threshold(text: object, default: float = 0.0) -> float:
    import re

    match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(text))
    return float(match.group(1)) / 100 if match else default


def parse_numeric_threshold(text: object, default: float = 0.0) -> float:
    import re

    match = re.search(r"(\d+(?:\.\d+)?)", str(text).replace(",", ""))
    return float(match.group(1)) if match else default


def discount_trigger_matches(trigger: object, discount_pct: float) -> bool:
    text = str(trigger).replace(" ", "").lower()
    if not text or text in {"nan", "any"}:
        return False
    if "<=" in text and ">" not in text:
        return discount_pct <= parse_percent_threshold(text)
    if ">" in text and "<=" in text:
        parts = text.split("and") if "and" in text else text.split("/")
        lower = parse_percent_threshold(parts[0])
        upper = parse_percent_threshold(parts[-1])
        return discount_pct > lower and discount_pct <= upper
    if ">" in text:
        return discount_pct > parse_percent_threshold(text)
    return False


def comparison_trigger_matches(trigger: object, value: float) -> bool:
    text = str(trigger).replace(" ", "").lower()
    if not text or text in {"nan", "any"}:
        return False
    threshold = parse_percent_threshold(text, parse_numeric_threshold(text))
    if "<=" in text:
        return value <= threshold
    if "<" in text:
        return value < threshold
    if ">=" in text:
        return value >= threshold
    if ">" in text:
        return value > threshold
    return False


def approval_rule_rows(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if st.session_state.get("approval_matrix_overrides") is None:
        st.session_state.approval_matrix_overrides = data.get("approval_matrix", pd.DataFrame()).to_dict("records")
    rules = pd.DataFrame(st.session_state.approval_matrix_overrides).copy()
    if rules.empty:
        rules = data.get("approval_matrix", pd.DataFrame()).copy()
    if rules.empty or "Required Role" not in rules:
        return pd.DataFrame()
    rules["Policy ID"] = rules.get("Policy ID", pd.Series(dtype=str)).astype(str)
    rules["Rule Type"] = rules["Policy ID"].str.extract(r"POL-([A-Z]+)", expand=False).fillna("")
    return rules


def add_route_rule(rows: list[dict], rule: pd.Series, reason: str) -> None:
    rows.append(
        {
            "Role": str(rule.get("Required Role", "")),
            "Sequence": int(safe_float(rule.get("Sequence"), 99)),
            "Reason": reason,
            "SLA Hours": int(safe_float(rule.get("SLA Hours"), 24)),
            "Policy ID": str(rule.get("Policy ID", "")),
            "Policy Name": str(rule.get("Policy Name", "")),
        }
    )


def compact_route(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Role", "Sequence", "Reason", "SLA Hours", "Policy ID", "Policy Name"])
    route = pd.DataFrame(rows)
    route = route[route["Role"].astype(str).str.strip().ne("")]
    if route.empty:
        return route
    grouped = []
    for role, part in route.groupby("Role", sort=False):
        part = part.sort_values(["Sequence", "Policy ID"])
        grouped.append(
            {
                "Role": role,
                "Sequence": int(part["Sequence"].min()),
                "Reason": " ".join(dict.fromkeys(part["Reason"].astype(str).tolist())),
                "SLA Hours": int(part["SLA Hours"].min()),
                "Policy ID": "; ".join(dict.fromkeys(part["Policy ID"].astype(str).tolist())),
                "Policy Name": "; ".join(dict.fromkeys(part["Policy Name"].astype(str).tolist())),
            }
        )
    compact = pd.DataFrame(grouped)
    role_rank = {role: index for index, role in enumerate(ROLE_ORDER)}
    compact["_Role Rank"] = compact["Role"].map(role_rank).fillna(len(role_rank))
    return compact.sort_values(["Sequence", "_Role Rank"]).drop(columns="_Role Rank")


def build_route_header(deal: dict, data: dict[str, pd.DataFrame]) -> dict:
    customer_name = deal.get("Sold-To Customer Name", deal.get("Customer Name"))
    account = customer_lookup(data).get(customer_name, {})
    health = demo_customer_health(account, str(customer_name)) if account else {}
    return {
        "Customer Name": customer_name,
        "Region": deal.get("Region"),
        "Segment": deal_customer_type(deal),
        "Customer Type": deal_customer_type(deal) or customer_type(account),
        "Account Type": customer_type(account),
        "Channel": deal.get("Channel", deal_customer_type(deal) or customer_type(account)),
        "Payment Terms": deal.get("Payment Terms"),
        "Contract Months": deal.get("Contract Months", 0),
        "Special Terms Requested": bool(deal.get("Special Terms Requested", False)),
        "Visibility": deal.get("Visibility", "Confidential"),
        "Overdue AR": deal.get("Overdue AR", health.get("Overdue AR", 0)),
        "Credit Status": deal.get("Credit Status", account.get("Credit Status", "")),
        "Customer Risk Flag": deal.get("Customer Risk Flag", health.get("Risk Flag", "")),
    }


def role_persona(role: str) -> str:
    for persona, persona_role in PERSONAS.items():
        if persona_role == role:
            return persona
    return ""


def default_delegate_config(data: dict[str, pd.DataFrame]) -> list[dict]:
    roster = data.get("approver_roster", pd.DataFrame()).copy()
    rows = []
    for role in ACTIONABLE_APPROVAL_ROLES:
        match = roster[roster.get("Role", pd.Series(dtype=str)).astype(str).eq(role)] if not roster.empty else pd.DataFrame()
        item = match.iloc[0].to_dict() if not match.empty else {}
        primary = str(item.get("Primary Approver", item.get("Approver Name", role_persona(role))) or role_persona(role))
        delegate = str(item.get("Delegate Approver", item.get("Delegate", "")) or "")
        enabled = str(item.get("Delegation Enabled", "No")).strip().lower() in {"yes", "true", "1", "enabled"}
        rows.append(
            {
                "Role": role,
                "Primary Approver": primary,
                "Delegate Approver": delegate,
                "Delegation Enabled": enabled,
                "Target Response Hours": int(
                    safe_float(
                        item.get(
                            "Target Response Time (Hours)",
                            item.get("Target Response Hours", item.get("SLA Hours", 24)),
                        ),
                        24,
                    )
                ),
            }
        )
    return rows


def delegate_config(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if st.session_state.get("delegate_overrides") is None:
        st.session_state.delegate_overrides = default_delegate_config(data)
    config = pd.DataFrame(st.session_state.delegate_overrides)
    if config.empty:
        config = pd.DataFrame(default_delegate_config(data))
    config["Delegation Enabled"] = config["Delegation Enabled"].astype(bool)
    config["Target Response Hours"] = pd.to_numeric(config["Target Response Hours"], errors="coerce").fillna(24).astype(int)
    return config


def delegate_record(data: dict[str, pd.DataFrame], role: str) -> dict:
    config = delegate_config(data)
    match = config[config["Role"].astype(str).eq(str(role))]
    if match.empty:
        return {
            "Role": role,
            "Primary Approver": role_persona(role),
            "Delegate Approver": "",
            "Delegation Enabled": False,
            "Target Response Hours": 24,
        }
    return match.iloc[0].to_dict()


def active_approver_for_role(data: dict[str, pd.DataFrame], role: str) -> str:
    record = delegate_record(data, role)
    if bool(record.get("Delegation Enabled")) and str(record.get("Delegate Approver", "")).strip():
        return str(record.get("Delegate Approver"))
    return str(record.get("Primary Approver", ""))


def role_display_label(data: dict[str, pd.DataFrame], role: str) -> str:
    record = delegate_record(data, role)
    return f"{role} (Delegated)" if bool(record.get("Delegation Enabled")) else role


def user_can_act_for_role(data: dict[str, pd.DataFrame], route_role: str, persona: str, user_role: str) -> bool:
    if user_role == route_role:
        return True
    record = delegate_record(data, route_role)
    return bool(record.get("Delegation Enabled")) and str(record.get("Delegate Approver", "")) == persona


def delegated_roles_for_persona(data: dict[str, pd.DataFrame], persona: str) -> list[str]:
    config = delegate_config(data)
    if config.empty:
        return []
    delegated = config[
        config["Delegation Enabled"]
        & config["Delegate Approver"].astype(str).eq(str(persona))
    ]
    return delegated["Role"].astype(str).tolist()


def enrich_route_with_approvers(route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if route_df.empty:
        return route_df
    route = route_df.copy()
    records = [delegate_record(data, role) for role in route["Role"].astype(str)]
    route["Primary Approver"] = [record.get("Primary Approver", "") for record in records]
    route["Delegate Approver"] = [record.get("Delegate Approver", "") for record in records]
    route["Delegation Enabled"] = ["Yes" if bool(record.get("Delegation Enabled")) else "No" for record in records]
    route["Active Approver"] = [active_approver_for_role(data, role) for role in route["Role"].astype(str)]
    route["Approver"] = [role_display_label(data, role) for role in route["Role"].astype(str)]
    route["SLA Hours"] = [int(record.get("Target Response Hours", row.get("SLA Hours", 24))) for record, (_, row) in zip(records, route.iterrows())]
    return route


def workflow_audit_once(key: str, deal_id: str, action: str, **kwargs) -> None:
    keys = set(st.session_state.get("workflow_audit_keys", []))
    if key in keys:
        return
    add_audit(deal_id, action, **kwargs)
    keys.add(key)
    st.session_state.workflow_audit_keys = sorted(keys)


def assignment_key(deal_id: str, role: str) -> str:
    return f"{deal_id}::{role}"


def ensure_approval_assignments(deal_id: str, route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    if route_df.empty:
        return
    assignments = st.session_state.setdefault("approval_assignments", {})
    now = datetime.now()
    for _, row in route_df.iterrows():
        role = str(row.get("Role", ""))
        key = assignment_key(deal_id, role)
        if key not in assignments:
            sla_hours = int(safe_float(row.get("SLA Hours"), delegate_record(data, role).get("Target Response Hours", 24)))
            assigned_at = now
            due_at = assigned_at + timedelta(hours=sla_hours)
            assignments[key] = {
                "Deal ID": deal_id,
                "Role": role,
                "Assigned At": assigned_at.isoformat(timespec="seconds"),
                "Due At": due_at.isoformat(timespec="seconds"),
                "SLA Hours": sla_hours,
                "Primary Approver": str(row.get("Primary Approver", "")),
                "Delegate Approver": str(row.get("Delegate Approver", "")),
                "Active Approver": str(row.get("Active Approver", "")),
                "Delegation Enabled": str(row.get("Delegation Enabled", "No")),
            }
            workflow_audit_once(
                f"{key}::assigned",
                deal_id,
                "Approval Assigned",
                entity="Approval Step",
                details=f"{role_display_label(data, role)} assigned to {row.get('Active Approver', '')}; target response {sla_hours}h.",
                approval_step=role,
            )


def assignment_status(deal_id: str, role: str) -> dict:
    assignment = st.session_state.get("approval_assignments", {}).get(assignment_key(deal_id, role), {})
    if not assignment:
        return {}
    due_at = datetime.fromisoformat(assignment["Due At"])
    assigned_at = datetime.fromisoformat(assignment["Assigned At"])
    now = datetime.now()
    remaining = due_at - now
    elapsed = now - assigned_at
    return {
        **assignment,
        "Hours Elapsed": elapsed.total_seconds() / 3600,
        "Hours Remaining": remaining.total_seconds() / 3600,
        "Is Breached": remaining.total_seconds() < 0,
    }


def update_sla_breach_audit(deal_id: str, role: str, data: dict[str, pd.DataFrame]) -> None:
    status = assignment_status(deal_id, role)
    if status.get("Is Breached"):
        workflow_audit_once(
            f"{assignment_key(deal_id, role)}::breached",
            deal_id,
            "SLA Breached",
            entity="Approval SLA",
            details=f"{role_display_label(data, role)} exceeded target response time of {status.get('SLA Hours')}h.",
            approval_step=role,
        )


def pending_approval_roles_for_deal(deal: pd.Series | dict, data: dict[str, pd.DataFrame], lines: pd.DataFrame | None = None) -> list[str]:
    item = deal.to_dict() if isinstance(deal, pd.Series) else dict(deal)
    deal_id = str(item.get("Deal ID", ""))
    all_lines = combined_lines(data) if lines is None else lines
    calc_lines = normalize_lines(all_lines[all_lines["Deal ID"].astype(str).eq(deal_id)], data)
    summary = summarize_lines(calc_lines)
    route = route_preview(build_route_header(item, data), calc_lines, summary, data)
    return current_required_approval_roles(deal_id, str(item.get("Status", "")).strip(), route)


def pending_approval_role_for_deal(deal: pd.Series | dict, data: dict[str, pd.DataFrame], lines: pd.DataFrame | None = None) -> str:
    roles = pending_approval_roles_for_deal(deal, data, lines)
    return roles[0] if roles else ""


def visible_deals_for_current_role(deals: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if deals.empty:
        return deals
    role = current_role()
    persona = current_persona()
    if role == "System Administrator":
        return deals
    if is_kam_role(role):
        own_mask = deals.get("Sales Owner", pd.Series(dtype=str)).astype(str).eq(persona)
        return deals[own_mask].copy()

    delegated_roles = set(delegated_roles_for_persona(data, persona))
    actionable_roles = {role, *delegated_roles}
    all_lines = combined_lines(data)
    pending_roles = deals.apply(lambda deal: pending_approval_roles_for_deal(deal, data, all_lines), axis=1)
    pending_mask = pending_roles.apply(lambda roles: bool(set(roles).intersection(actionable_roles)))
    if role == "Sales Manager":
        team = SALES_MANAGER_TEAMS.get(persona, SALES_MANAGER_TEAMS.get("Jordan Blake", []))
        assigned_mask = (
            deals.get("Sales Owner", pd.Series(index=deals.index, dtype=str)).astype(str).isin(team)
            | deals.get("Sales Manager", pd.Series(index=deals.index, dtype=str)).astype(str).eq(persona)
        )
        pending_mask &= assigned_mask | pending_roles.apply(lambda roles: bool(set(roles).intersection(delegated_roles)))
    return deals[pending_mask].copy()


def reviewer_participated_in_deal(deal_id: str, role: str, persona: str | None = None) -> bool:
    actor = str(persona or "").strip()
    for event in st.session_state.get("audit_events", []):
        if str(event.get("Deal ID", "")) != str(deal_id):
            continue
        if str(event.get("Role", "")) != role:
            continue
        if actor and str(event.get("Actor", "")) != actor:
            continue
        if str(event.get("Action", "")).startswith("Approval decision"):
            return True
    if not actor and role in completed_approval_steps(deal_id):
        return True
    return False


def archive_visible_to_current_user(deal: pd.Series | dict) -> bool:
    item = deal.to_dict() if isinstance(deal, pd.Series) else dict(deal)
    role = current_role()
    persona = current_persona()
    if role == "System Administrator":
        return True
    if str(item.get("Sales Owner", "")).strip() == persona:
        return True
    if role in ACTIONABLE_APPROVAL_ROLES and reviewer_participated_in_deal(str(item.get("Deal ID", "")), role, persona):
        return True
    return False


def archived_deals_for_current_role(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty or "Status" not in deals:
        return deals.iloc[0:0].copy()
    archived = deals[deals["Status"].astype(str).isin(ARCHIVE_STATUSES)].copy()
    return archived[archived.apply(archive_visible_to_current_user, axis=1)].copy()


def deal_detail_visible_deals(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    all_deals = combined_deals(data)
    role = current_role()
    if role in ACTIONABLE_APPROVAL_ROLES:
        review_roles = [role, *delegated_roles_for_persona(data, current_persona())]
        visible_ids = route_visible_deal_ids_for_roles(all_deals, data, review_roles)
        active = all_deals[all_deals["Deal ID"].astype(str).isin(visible_ids)].copy()
    else:
        active = visible_deals_for_current_role(all_deals, data)
    archived = archived_deals_for_current_role(all_deals)
    return pd.concat([active, archived], ignore_index=True).drop_duplicates(subset=["Deal ID"])


def demo_commercial_price_defaults(data: dict[str, pd.DataFrame], sku: str) -> dict[str, float]:
    prod = product_lookup(data).get(str(sku), {})
    list_price = product_list_price(prod)
    gross_price = product_gross_price(prod)
    return {
        "Unit List Price": round(list_price, 2),
        "Unit Gross Price": round(gross_price, 2),
        "Gross Price": round(gross_price, 2),
        "Floor Price": round(list_price * 0.72, 2),
        "Guidance Price": round(list_price * 0.84, 2),
        "Walk-away Price": round(list_price * 0.68, 2),
    }


def ensure_commercial_line_columns(lines: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    enriched = lines.copy()
    if enriched.empty or "SKU" not in enriched:
        return enriched
    if "Line Commercial Rationale" not in enriched.columns:
        enriched["Line Commercial Rationale"] = enriched["Notes"] if "Notes" in enriched.columns else ""
    for idx, row in enriched.iterrows():
        defaults = demo_commercial_price_defaults(data, row.get("SKU", ""))
        for col, value in defaults.items():
            if col not in enriched.columns:
                enriched[col] = None
            enriched.at[idx, col] = value
        if "Requested Net Price" not in enriched.columns:
            enriched["Requested Net Price"] = None
        gross_price = safe_float(defaults["Unit Gross Price"])
        product = product_lookup(data).get(str(row.get("SKU", "")), {})
        base_discount = safe_float(product.get("Base Rebate %", 0))
        current_net_price = gross_price
        enriched.at[idx, "Base Discount %"] = base_discount
        enriched.at[idx, "Current Net Price"] = round(current_net_price, 2)
        requested_discount = row.get("Requested Total Discount %", row.get("Requested Discount %", row.get("Discount %", None)))
        requested_discount = safe_float(requested_discount) if requested_discount is not None and not pd.isna(requested_discount) else None
        if requested_discount is not None and abs(requested_discount) > 1:
            requested_discount = requested_discount / 100
        requested = row.get("Requested Net Price", row.get("Proposed Unit Price", None))
        if requested_discount is not None:
            requested = gross_price * (1 - requested_discount)
        elif pd.isna(requested) or requested == "":
            requested = gross_price * (1 - (requested_discount if requested_discount is not None else 0.10))
        enriched.at[idx, "Requested Net Price"] = round(float(requested), 2)
        enriched.at[idx, "Proposed Unit Price"] = round(float(requested), 2)
        discount = 0 if gross_price == 0 else (gross_price - float(requested)) / gross_price
        enriched.at[idx, "Requested Total Discount %"] = discount
        enriched.at[idx, "Requested Discount %"] = discount
        quantity = safe_float(row.get("Quantity", 0))
        enriched.at[idx, "Gross Revenue"] = round(quantity * gross_price, 2)
        enriched.at[idx, "Proposed Net Revenue"] = round(quantity * float(requested), 2)
    return enriched


def get_runtime_deals_df() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.runtime_deals)


def get_runtime_lines_df() -> pd.DataFrame:
    return pd.DataFrame(st.session_state.runtime_lines)


def combined_deals(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    seed = data["deals"].copy()
    runtime = get_runtime_deals_df()
    if not runtime.empty:
        if not seed.empty and "Deal ID" in seed and "Deal ID" in runtime:
            runtime_ids = set(runtime["Deal ID"].astype(str))
            seed = seed[~seed["Deal ID"].astype(str).isin(runtime_ids)]
        seed = pd.concat([seed, runtime], ignore_index=True, sort=False)
    seed = normalize_deal_headers(seed)
    overrides = st.session_state.get("deal_status_overrides", {})
    if overrides and not seed.empty:
        for deal_id, values in overrides.items():
            mask = seed["Deal ID"].astype(str).eq(str(deal_id))
            for key, value in values.items():
                seed.loc[mask, key] = value
    return seed


def normalize_deal_headers(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty:
        return deals
    normalized = deals.copy()
    alias_pairs = {
        "Customer ID": "Sold-To Customer ID",
        "Customer Name": "Sold-To Customer Name",
        "Target Close Date": "Expected Award / Decision Date",
        "Requested Effective Date": "Requested Delivery Start",
        "Intake Risk": "KAM Risk Assessment",
        "Included_In_Latest_Financial_Plan": "Included In Latest Financial Plan",
        "Segment": "Customer Type",
    }
    for legacy, canonical in alias_pairs.items():
        if legacy not in normalized and canonical in normalized:
            normalized[legacy] = normalized[canonical]
        if canonical not in normalized and legacy in normalized:
            normalized[canonical] = normalized[legacy]
    if "End Account ID" not in normalized and "Sold-To Customer ID" in normalized:
        normalized["End Account ID"] = normalized["Sold-To Customer ID"]
    if "End Account Name" not in normalized and "Sold-To Customer Name" in normalized:
        normalized["End Account Name"] = normalized["Sold-To Customer Name"]
    return normalized


def combined_lines(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    seed = data["line_items"].copy()
    runtime = get_runtime_lines_df()
    if not runtime.empty:
        seed = pd.concat([seed, runtime], ignore_index=True, sort=False)
    return seed


def navigate_to_deal_detail(deal_id: str, source: str) -> None:
    st.session_state.selected_deal_id = deal_id
    st.session_state.current_page = "Deal Detail"
    st.session_state.deal_detail_parent = "Review Queue" if "approval" in source.lower() else "Deal Requests"
    add_audit(deal_id, "Deal viewed", details=f"Opened from {source}.")
    if sensitive_fields_visible_for_role(current_role()) == "Yes":
        add_audit(deal_id, "Sensitive deal data accessed", details=f"Opened from {source}.", sensitive_fields_visible="Yes")
    st.rerun()


def set_current_page(page: str) -> None:
    st.session_state.current_page = page
    st.rerun()


def clear_deal_editor_state() -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith("form_") or key == "line_editor":
            del st.session_state[key]
    st.session_state.draft_lines = None
    st.session_state.line_editor_rows = None
    st.session_state.line_editor_revision += 1
    st.session_state.editing_deal_id = None
    st.session_state.editing_deal_original_status = ""
    st.session_state.editing_review_comment = ""
    st.session_state.deal_edit_active = False
    st.session_state.current_draft_snapshot = None


def begin_draft_edit(deal: dict, lines: pd.DataFrame) -> None:
    clear_deal_editor_state()
    deal_type_aliases = {
        "New Account / Launch": "New Account Launch",
        "Tender": "Tender Bid",
        "Strategic Exception": "Strategic Opportunity",
    }
    saved_deal_type = str(deal.get("Deal Type", "Contract Renewal"))
    def saved_date(value: object, fallback: date) -> date:
        parsed = pd.to_datetime(value, errors="coerce")
        return fallback if pd.isna(parsed) else parsed.date()

    field_map = {
        "form_customer": deal.get("Customer Name", deal.get("Sold-To Customer Name", "")),
        "form_ship_to": deal.get("End Account Name", ""),
        "form_delivery_model": deal.get("Delivery Model", "Direct customer delivery"),
        "form_title": deal.get("Deal Title", ""),
        "form_type": deal_type_aliases.get(saved_deal_type, saved_deal_type),
        "form_owner": deal.get("Sales Owner", current_persona()),
        "form_manager": deal.get("Sales Manager", "Jordan Blake"),
        "form_terms": deal.get("Payment Terms", "Net 30"),
        "form_contract": int(safe_float(deal.get("Contract Months"), 24)),
        "form_billing": deal.get("Billing Frequency", "Annual"),
        "form_special": str(deal.get("Special Terms Requested", "False")).lower() in {"true", "yes", "1"},
        "form_special_desc": deal.get("Special Terms Description", ""),
        "form_visibility": deal.get("Visibility", "Confidential"),
        "form_publication_source": deal.get("Publication Source", ""),
        "form_publication_url": deal.get("Publication URL", ""),
        "form_access_description": deal.get("Access Description", ""),
        "form_tender_name": deal.get("Tender Name", ""),
        "form_tender_id": deal.get("Tender ID", ""),
        "form_tender_mechanism": deal.get("Tender Mechanism", ""),
        "form_tender_closing": saved_date(
            deal.get("Submission Deadline"), date.today() + timedelta(days=28)
        ),
        "form_award_date": saved_date(deal.get("Award Date"), date.today() + timedelta(days=60)),
        "form_close": saved_date(
            deal.get("Expected Award / Decision Date", deal.get("Target Close Date")),
            date.today() + timedelta(days=45),
        ),
        "form_effective": saved_date(
            deal.get("Requested Delivery Start"), date.today() + timedelta(days=60)
        ),
        "form_delivery_end": saved_date(
            deal.get("Requested Delivery End"), date.today() + timedelta(days=120)
        ),
        "form_justification": deal.get("Strategic Rationale", ""),
        "form_kam_risk_assessment": deal.get("KAM Risk Assessment", "Medium"),
        "form_risk_reason": deal.get("Risk Reason", RISK_REASON_VALUES[0]),
        "form_included_plan": deal.get("Included In Latest Financial Plan", "Yes"),
    }
    for key, value in field_map.items():
        if value is not None and value != "":
            st.session_state[key] = value
    st.session_state.draft_lines = lines.copy()
    editor_rows = lines.copy()
    if "Requested Total Discount %" not in editor_rows and "Requested Discount %" in editor_rows:
        editor_rows["Requested Total Discount %"] = editor_rows["Requested Discount %"]
    if "Requested Total Discount %" in editor_rows:
        editor_rows["Requested Total Discount %"] = pd.to_numeric(
            editor_rows["Requested Total Discount %"], errors="coerce"
        ).fillna(0) * 100
    st.session_state.line_editor_rows = editor_rows
    st.session_state.editing_deal_id = str(deal.get("Deal ID", ""))
    saved_status = str(deal.get("Status", "")).strip()
    returned_for_changes = str(deal.get("Returned For Changes", "False")).lower() in {"true", "yes", "1"}
    st.session_state.editing_deal_original_status = (
        "Changes Requested" if saved_status == "Draft" and returned_for_changes else saved_status
    )
    st.session_state.editing_review_comment = str(
        deal.get("Last Decision Comment", deal.get("Last Requested Change Comment", ""))
    ).strip()
    st.session_state.deal_edit_active = True
    st.session_state.current_page = "New Deal Intake"


def sync_context_customer_defaults() -> None:
    customer_name = str(st.session_state.get("form_customer", ""))
    st.session_state.form_title = f"{customer_name} - {date.today().isoformat()}"
    if st.session_state.get("form_delivery_model", "Direct customer delivery") == "Direct customer delivery":
        st.session_state.form_ship_to = customer_name


def sync_delivery_model() -> None:
    if st.session_state.get("form_delivery_model") == "Direct customer delivery":
        st.session_state.form_ship_to = str(st.session_state.get("form_customer", ""))


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


def current_required_approval_roles(deal_id: str, status: str, route_df: pd.DataFrame) -> list[str]:
    clean_status = str(status or "").strip()
    if clean_status in {"Draft", "Rejected", "Approved", "Final Approved"}:
        return []
    if clean_status == "Changes Requested":
        return []
    if clean_status in STATUS_APPROVAL_STEP and clean_status != "Pending Governance Review":
        return [STATUS_APPROVAL_STEP[clean_status]]
    if route_df.empty or "Role" not in route_df:
        return ["Sales Manager"]
    route = route_df[route_df["Role"].astype(str).isin(ACTIONABLE_APPROVAL_ROLES)].copy()
    if route.empty:
        return ["Sales Manager"]
    route["Sequence"] = pd.to_numeric(route.get("Sequence"), errors="coerce").fillna(99).astype(int)
    completed = set(completed_approval_steps(deal_id))
    route = route[~route["Role"].astype(str).isin(completed)]
    if route.empty:
        return []
    current_sequence = int(route["Sequence"].min())
    current = route[route["Sequence"].eq(current_sequence)].copy()
    role_rank = {role: index for index, role in enumerate(ROLE_ORDER)}
    current["_Role Rank"] = current["Role"].map(role_rank).fillna(len(role_rank))
    return current.sort_values("_Role Rank")["Role"].astype(str).tolist()


def current_required_approval_role(deal_id: str, status: str, route_df: pd.DataFrame) -> str:
    roles = current_required_approval_roles(deal_id, status, route_df)
    return roles[0] if roles else ""


def next_approval_status(deal_id: str, current_role: str, route_df: pd.DataFrame) -> str:
    completed = completed_approval_steps(deal_id)
    roles = actionable_route_roles(route_df)
    if current_role and current_role not in completed:
        completed.append(current_role)
    st.session_state.deal_approval_steps[str(deal_id)] = completed
    pending = current_required_approval_roles(deal_id, "", route_df)
    if not pending:
        return "Approved"
    if len(pending) > 1 or any(role in {"Pricing Governance Owner", "Finance Director", "Operations Manager"} for role in pending):
        return "Pending Governance Review"
    return APPROVAL_STEP_STATUS[pending[0]]


def allowed_decisions_for_role(role: str) -> list[str]:
    return ROLE_ALLOWED_DECISIONS.get(role, [])


def process_approval_decision(deal_id: str, decision: str, comment: str, route_df: pd.DataFrame, previous_status: str, data: dict[str, pd.DataFrame]) -> tuple[bool, str]:
    current_roles = current_required_approval_roles(deal_id, previous_status, route_df)
    persona = st.session_state.get("persona", "Demo User")
    user_role = st.session_state.get("role", "Demo Role")
    allowed = allowed_decisions_for_role(user_role)
    current_role = next((role for role in current_roles if user_can_act_for_role(data, role, persona, user_role)), "")
    if not current_role or decision not in allowed:
        required = ", ".join(role_display_label(data, role) for role in current_roles) or "none"
        return False, f"{user_role} cannot capture `{decision}` for this step. Current required roles: {required}."
    if decision in {"Request Changes", "Reject"} and not str(comment).strip():
        return False, f"A comment is required for {decision}."

    if decision == "Approve":
        new_status = next_approval_status(deal_id, current_role, route_df)
    elif decision == "Request Changes":
        new_status = "Changes Requested"
    elif decision == "Reject":
        new_status = "Rejected"
    else:
        new_status = "Rejected"

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
    if decision in {"Request Changes", "Reject"}:
        deal_match = combined_deals(data)
        deal_match = deal_match[deal_match["Deal ID"].astype(str).eq(str(deal_id))]
        creator = str(deal_match.iloc[0].get("Sales Owner", "Submitting KAM")) if not deal_match.empty else "Submitting KAM"
        add_audit(
            deal_id,
            "Creator Notified",
            entity="Workflow Notification",
            details=f"{creator} notified that the deal was {decision.lower()}. No email was sent.",
            comment=comment,
            approval_step=current_role,
            previous_status=previous_status,
            new_status=new_status,
        )
    return True, f"Captured {decision} for {deal_id}. Status moved from {previous_status} to {new_status}."


def resubmit_deal_for_approval(deal_id: str, data: dict[str, pd.DataFrame]) -> tuple[bool, str]:
    deals = combined_deals(data)
    match = deals[deals["Deal ID"].astype(str).eq(str(deal_id))]
    if match.empty:
        return False, "Deal is no longer available."
    deal = match.iloc[0].to_dict()
    if str(deal.get("Status", "")).strip() != "Changes Requested":
        return False, "Only deals with requested changes can be resubmitted."
    if not is_kam_role() or str(deal.get("Sales Owner", "")) != current_persona():
        return False, "Only the submitting KAM can resubmit this deal."

    requested_change_comment = str(deal.get("Last Decision Comment", "")).strip()
    st.session_state.deal_approval_steps[str(deal_id)] = []
    assignments = st.session_state.get("approval_assignments", {})
    st.session_state.approval_assignments = {
        key: value for key, value in assignments.items() if str(value.get("Deal ID", "")) != str(deal_id)
    }
    update_deal_status(
        deal_id,
        "Submitted",
        "Resubmit",
        "Resubmitted after requested changes.",
        previous_status="Changes Requested",
    )
    for runtime_deal in st.session_state.runtime_deals:
        if str(runtime_deal.get("Deal ID", "")) == str(deal_id):
            runtime_deal["Last Requested Change Comment"] = requested_change_comment
    if str(deal_id) in st.session_state.deal_status_overrides:
        st.session_state.deal_status_overrides[str(deal_id)]["Last Requested Change Comment"] = requested_change_comment
    add_audit(
        deal_id,
        "Deal resubmitted",
        details="Submitting KAM resubmitted the deal. Approval progress restarted with Sales Manager review.",
        decision="Resubmit",
        previous_status="Changes Requested",
        new_status="Submitted",
    )
    return True, f"{deal_id} was resubmitted and returned to Sales Manager review."


def product_lookup(data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    if data["products"].empty:
        return {}
    return data["products"].set_index("SKU").to_dict("index")


def product_value(product: dict, primary: str, fallback: str = "", default: object = None) -> object:
    value = product.get(primary, None)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        value = product.get(fallback, default) if fallback else default
    return default if value is None or (isinstance(value, float) and pd.isna(value)) else value


def product_list_price(product: dict) -> float:
    return safe_float(product_value(product, "List Price", "WAC / List Price", 0))


def product_target_margin(product: dict) -> float:
    return safe_float(product_value(product, "Target Gross Margin %", "Target Margin %", 0))


def product_gross_price(product: dict) -> float:
    list_price = product_list_price(product)
    base_rebate = safe_float(product.get("Base Rebate %", 0))
    return safe_float(product.get("Gross Price", list_price * (1 - base_rebate)), list_price)


def commercial_product_name(sku: str, fallback: str = "") -> str:
    skus = [
        "RX-ONC-100",
        "RX-ONC-500",
        "BIO-RA-200",
        "RX-CARD-50",
        "RX-RARE-10",
        "DX-COMP-01",
        "RX-HOSP-20",
        "BIO-DERM-80",
        "RX-ONC-ORAL",
        "RX-RARE-INF",
        "DX-GENE-02",
        "SVC-PAT-01",
        "SVC-START",
        "REB-FORM",
    ]
    names = [
        "Alpha",
        "Beta",
        "Gamma",
        "Delta",
        "Epsilon",
        "Zeta",
        "Eta",
        "Theta",
        "Iota",
        "Kappa",
        "Lambda",
        "Mu",
        "Nu",
        "Xi",
    ]
    if sku in skus:
        return f"Product {names[skus.index(sku)]}"
    return fallback or sku


def finance_trigger_margin(target_margin: float) -> float:
    return max(0, safe_float(target_margin) - 0.10)


def gm_trigger_margin(target_margin: float) -> float:
    return max(0, safe_float(target_margin) - 0.20)


def customer_lookup(data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    if data["customers"].empty:
        return {}
    return data["customers"].set_index("Customer Name").to_dict("index")


def customer_type(customer: dict) -> str:
    return str(customer.get("Customer Type", customer.get("Account Type", customer.get("Segment", ""))))


def deal_customer_type(deal: dict) -> str:
    return str(deal.get("Customer Type", deal.get("Segment", deal.get("Channel", ""))))


def normalize_lines(line_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    products = product_lookup(data)
    rows = []
    for _, row in line_df.dropna(how="all").iterrows():
        sku = str(row.get("SKU", "")).strip()
        if not sku or sku == "nan" or sku not in products:
            continue
        prod = products[sku]
        qty = float(row.get("Quantity", 0) or 0)
        list_price = float(row.get("Unit List Price", product_list_price(prod)) or 0)
        gross_price = float(row.get("Unit Gross Price", row.get("Gross Price", product_gross_price(prod))) or 0)
        requested_discount = row.get("Requested Discount %", row.get("Discount %", None))
        requested_discount = safe_float(requested_discount) if requested_discount is not None and not pd.isna(requested_discount) else None
        if requested_discount is not None and abs(requested_discount) > 1:
            requested_discount = requested_discount / 100
        proposed = float(row.get("Requested Net Price", row.get("Proposed Unit Price", 0)) or 0)
        if requested_discount is not None and gross_price:
            proposed = gross_price * (1 - requested_discount)
        floor_price = float(row.get("Floor Price", list_price * 0.72) or 0)
        guidance_price = float(row.get("Guidance Price", list_price * 0.84) or 0)
        walkaway_price = float(row.get("Walk-away Price", list_price * 0.68) or 0)
        unit_cost = float(row.get("Unit Cost", prod.get("Standard Cost", 0)) or 0)
        extended_list = qty * list_price
        extended_gross = safe_float(row.get("Gross Revenue"), qty * gross_price)
        extended_proposed = safe_float(row.get("Proposed Net Revenue"), qty * proposed)
        discount = 0 if gross_price == 0 else (gross_price - proposed) / gross_price
        margin = calculate_margin_pct(extended_proposed, calculate_gross_profit(proposed, unit_cost, qty))
        rows.append(
            {
                "Deal ID": row.get("Deal ID", ""),
                "Line #": row.get("Line #", ""),
                "SKU": sku,
                "Product Name": row.get("Product Name", commercial_product_name(sku, prod.get("Product Name", ""))) or commercial_product_name(sku, prod.get("Product Name", "")),
                "Product Category": prod.get("Product Category", prod.get("Product Type", "")),
                "Product Type": prod.get("Product Type", prod.get("Product Category", "")),
                "Quantity": qty,
                "Unit List Price": list_price,
                "List Price": list_price,
                "Gross Price": gross_price,
                "Unit Gross Price": gross_price,
                "Unit Cost": unit_cost,
                "Proposed Unit Price": proposed,
                "Requested Net Price": proposed,
                "Floor Price": floor_price,
                "Guidance Price": guidance_price,
                "Walk-away Price": walkaway_price,
                "Extended List": extended_list,
                "Extended Gross": extended_gross,
                "Extended Proposed": extended_proposed,
                "Gross Revenue": extended_gross,
                "Proposed Net Revenue": extended_proposed,
                "Extended Requested Net": extended_proposed,
                "Discount %": discount,
                "Requested Discount %": discount,
                "Margin %": margin,
                "Estimated Gross Margin %": margin,
                "Base Rebate %": prod.get("Base Rebate %", 0),
                "Target Margin %": product_target_margin(prod),
                "Target Gross Margin %": product_target_margin(prod),
                "Finance Director Trigger Margin": finance_trigger_margin(product_target_margin(prod)),
                "General Manager Trigger Margin": gm_trigger_margin(product_target_margin(prod)),
                "Requested Delivery Date": row.get("Requested Delivery Date", None),
                "Inventory Tracked": prod.get("Inventory Tracked", ""),
                "Line Commercial Rationale": row.get("Line Commercial Rationale", row.get("Notes", "")),
                "Notes": row.get("Line Commercial Rationale", row.get("Notes", "")),
            }
        )
    return pd.DataFrame(rows)


def commercial_line_items_view(lines: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Deal ID",
        "Line #",
        "SKU",
        "Product Name",
        "Quantity",
        "Unit List Price",
        "Unit Gross Price",
        "Base Rebate %",
        "Requested Discount %",
        "Requested Net Price",
        "Unit Cost",
        "Gross Revenue",
        "Proposed Net Revenue",
        "Requested Delivery Date",
        "Line Commercial Rationale",
    ]
    available = [col for col in cols if col in lines.columns]
    view = lines[available].copy() if available else lines.copy()
    return mask_sensitive_dataframe(view)


def commercial_pricing_view(lines: pd.DataFrame) -> pd.DataFrame:
    if lines.empty:
        return pd.DataFrame(columns=["SKU", "Product", "Quantity", "Gross Price", "Net Price", "Discount %", "Revenue", "Gross Margin"])
    view = pd.DataFrame(
        {
            "SKU": lines.get("SKU", pd.Series(dtype=str)),
            "Product": lines.get("Product Name", pd.Series(dtype=str)),
            "Quantity": pd.to_numeric(lines.get("Quantity", pd.Series(dtype=float)), errors="coerce").fillna(0),
            "Gross Price": pd.to_numeric(lines.get("Unit Gross Price", pd.Series(dtype=float)), errors="coerce"),
            "Net Price": pd.to_numeric(lines.get("Requested Net Price", pd.Series(dtype=float)), errors="coerce"),
            "Discount %": pd.to_numeric(lines.get("Requested Discount %", lines.get("Discount %", pd.Series(dtype=float))), errors="coerce"),
            "Revenue": pd.to_numeric(lines.get("Proposed Net Revenue", lines.get("Extended Proposed", pd.Series(dtype=float))), errors="coerce"),
            "Gross Margin": pd.to_numeric(lines.get("Margin %", lines.get("Estimated Gross Margin %", pd.Series(dtype=float))), errors="coerce"),
        }
    )
    return mask_sensitive_dataframe(view)


def contract_duration_months(deal: dict) -> int:
    months = int(safe_float(deal.get("Contract Months", deal.get("Contract Duration Months", 12))))
    return max(months, 1)


def financial_projection_values(deal: dict, lines: pd.DataFrame, summary: dict) -> dict:
    months = contract_duration_months(deal)
    total_revenue = safe_float(summary.get("total_proposed"))
    annual_revenue = total_revenue if months == 12 else total_revenue * 12 / months
    total_cost = safe_float((lines["Quantity"] * lines["Unit Cost"]).sum()) if not lines.empty else 0
    gross_profit = total_revenue - total_cost
    return {
        "Contract Duration": f"{months} months",
        "Annual Revenue": money(annual_revenue),
        "Total Contract Revenue": money(total_revenue),
        "Gross Profit": money(gross_profit) if has_full_visibility() else "Restricted",
        "Gross Margin %": landing_margin_display(summary),
    }


def find_inventory(data: dict[str, pd.DataFrame], sku: str, region: str) -> pd.Series | None:
    inv = data["inventory_coverage"]
    if inv.empty or "SKU" not in inv:
        return None
    subset = inv[inv["SKU"].astype(str).eq(sku)]
    if subset.empty:
        return None
    return subset.sort_values("Coverage Days").iloc[0]


def find_expiry(data: dict[str, pd.DataFrame], sku: str, region: str) -> pd.Series | None:
    aging = data["expiry_aging"]
    if aging.empty or "SKU" not in aging:
        return None
    subset = aging[aging["SKU"].astype(str).eq(sku)]
    if subset.empty:
        return None
    eligible = subset[
        (pd.to_numeric(subset["Days To Expiry"], errors="coerce") > 0)
        & ~subset["Quality Control Status"].astype(str).isin(["Rejected", "Under Investigation"])
    ]
    if not eligible.empty:
        subset = eligible
    return subset.sort_values("Days To Expiry").iloc[0]


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
    active = regional[regional["Version Status"].astype(str).eq("Active")]
    if not active.empty:
        regional = active
    return regional.sort_values("Period", ascending=False).iloc[0]


def price_volume_summary(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, channel: str) -> pd.DataFrame:
    history = data["price_volume"]
    if history.empty or lines.empty:
        return pd.DataFrame()
    rows = []
    for _, line in lines.iterrows():
        subset = history[history["SKU"].astype(str).eq(str(line["SKU"]))]
        if subset.empty:
            continue
        customer_subset = subset[
            subset.get("Sold-To Customer Name", pd.Series(dtype=str)).astype(str).eq(customer)
            | subset.get("End Account Name", pd.Series(dtype=str)).astype(str).eq(customer)
        ]
        if customer_subset.empty:
            customer_subset = subset
        customer_avg = safe_float(customer_subset.get("Customer Avg Net Price 12M", customer_subset.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
        product_avg = safe_float(subset.get("Product Avg Net Price 12M", subset.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
        plan_subset = customer_subset[customer_subset.get("Included In Latest Financial Plan", pd.Series(dtype=str)).astype(str).eq("Yes")]
        planned_net = safe_float(plan_subset.get("Planned Net Price", pd.Series(dtype=float)).dropna().astype(float).mean()) if not plan_subset.empty else None
        rows.append(
            {
                "SKU": line["SKU"],
                "Product": line.get("Product Name", ""),
                "Requested Net Price": line.get("Requested Net Price", line.get("Proposed Unit Price")),
                "Customer Avg Net Price 12M": customer_avg,
                "Product Avg Net Price 12M": product_avg,
                "Planned Net Price": planned_net,
                "Included In Latest Financial Plan": "Yes" if planned_net is not None else "No",
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
        product_name = str(line.get("Product Name", ""))
        if not tender.empty:
            t = tender[tender["SKU"].astype(str).eq(sku)]
            exact = t[t["End Account"].astype(str).eq(customer)]
            if exact.empty:
                exact = t
            if not exact.empty:
                r = exact.sort_values("Tender Date", ascending=False).iloc[0]
                tender_rows.append(
                    {
                        "SKU": sku,
                        "End Account": r.get("End Account"),
                        "Result": r.get("Result"),
                        "Winning Discount %": r.get("Winning Discount %"),
                        "Winning Net Price": r.get("Winning Net Price"),
                        "Tender Net Value": r.get("Tender Net Value"),
                        "Driver": r.get("Win / Loss Driver"),
                        "Contract Term": r.get("Contract Term"),
                    }
                )
        if not intel.empty:
            context_match = intel["Customer / Market Context"].astype(str).str.contains(customer, case=False, regex=False, na=False)
            c = intel[intel["Product Name"].astype(str).eq(product_name) | context_match]
            if not c.empty:
                r = c.sort_values("Observed Date", ascending=False).iloc[0]
                intel_rows.append(
                    {
                        "Product Name": product_name,
                        "Competitor": r.get("Competitor"),
                        "Signal": r.get("Signal Type"),
                        "Confidence Level": r.get("Confidence Level"),
                        "Market Context": r.get("Customer / Market Context"),
                        "Potential Business Impact": r.get("Potential Business Impact"),
                        "Response": r.get("Suggested Commercial Response"),
                    }
                )
    return pd.DataFrame(tender_rows), pd.DataFrame(intel_rows)


def historical_plan_match(data: dict[str, pd.DataFrame], line: pd.Series, customer: str = "") -> pd.DataFrame:
    history = data.get("price_volume", pd.DataFrame())
    if history.empty or "SKU" not in history:
        return pd.DataFrame()
    subset = history[
        history["SKU"].astype(str).eq(str(line["SKU"]))
        & history.get("Included In Latest Financial Plan", pd.Series(dtype=str)).astype(str).eq("Yes")
    ]
    if customer and not subset.empty:
        customer_subset = subset[
            subset.get("Sold-To Customer Name", pd.Series(dtype=str)).astype(str).eq(customer)
            | subset.get("End Account Name", pd.Series(dtype=str)).astype(str).eq(customer)
        ]
        if not customer_subset.empty:
            subset = customer_subset
    return subset


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    value_series = pd.to_numeric(values, errors="coerce").fillna(0)
    weight_series = pd.to_numeric(weights, errors="coerce").fillna(0)
    total_weight = safe_float(weight_series.sum())
    if total_weight <= 0:
        return safe_float(value_series.mean())
    return safe_float((value_series * weight_series).sum() / total_weight)


def plan_impact_analysis(data: dict[str, pd.DataFrame], lines: pd.DataFrame, region: str, segment: str, customer: str = "") -> pd.DataFrame:
    rows = []
    for _, line in lines.iterrows():
        hist_match = historical_plan_match(data, line, customer)
        legacy_match = find_plan_match(data, line, region, segment) if hist_match.empty else None
        if hist_match.empty and legacy_match is None:
            continue
        if not hist_match.empty:
            planned_qty = safe_float(hist_match["Planned Volume"].sum())
            planned_price = weighted_average(hist_match["Planned Net Price"], hist_match["Planned Volume"])
            customer_avg = safe_float(hist_match.get("Customer Avg Net Price 12M", hist_match.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
            product_avg = safe_float(hist_match.get("Product Avg Net Price 12M", hist_match.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
        else:
            planned_price = safe_float(legacy_match.get("Planned Net Price"))
            planned_qty = safe_float(legacy_match.get("Planned Volume"))
            customer_avg = None
            product_avg = None
        new_price = safe_float(line.get("Proposed Unit Price"))
        new_qty = safe_float(line.get("Quantity"))
        standard_cost = safe_float(line.get("Unit Cost"))
        planned_revenue = planned_price * planned_qty
        proposed_revenue = new_price * new_qty
        planned_gp = calculate_gross_profit(planned_price, standard_cost, planned_qty)
        proposed_gp = calculate_gross_profit(new_price, standard_cost, new_qty)
        price_variance = calculate_price_variance(new_price, planned_price, planned_qty)
        volume_variance = calculate_volume_variance(new_qty, planned_qty, new_price)
        revenue_variance = calculate_revenue_variance(price_variance, volume_variance)
        rows.append(
            {
                "SKU": line["SKU"],
                "Product": line["Product Name"],
                "Requested Net Price": new_price,
                "Planned Price": planned_price,
                "New Price": new_price,
                "Planned Net Price": planned_price,
                "Proposed Net Price": new_price,
                "Customer Avg Net Price 12M": customer_avg,
                "Product Avg Net Price 12M": product_avg,
                "Planned Quantity": planned_qty,
                "New Quantity": new_qty,
                "Planned Revenue": planned_revenue,
                "Proposed Revenue": proposed_revenue,
                "Price Variance": price_variance,
                "Price Variance vs Plan": price_variance,
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
        product_avg = 0
        if not hist.empty:
            customer_hist = hist[
                hist.get("Sold-To Customer Name", pd.Series(dtype=str)).astype(str).eq(customer)
                | hist.get("End Account Name", pd.Series(dtype=str)).astype(str).eq(customer)
            ]
            if customer_hist.empty:
                customer_hist = hist
            avg_price = safe_float(customer_hist.get("Customer Avg Net Price 12M", customer_hist.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
            product_avg = safe_float(hist.get("Product Avg Net Price 12M", hist.get("Net Price", pd.Series(dtype=float))).dropna().astype(float).mean())
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
                "Requested Net Price": proposed_price,
                "Customer Avg Net Price 12M": avg_price,
                "Product Avg Net Price 12M": product_avg,
                "Average Historical Price": avg_price,
                "Historical Average Net Price": avg_price,
                "Price vs Historical Price %": None if avg_price <= 0 else (proposed_price - avg_price) / avg_price,
                "Price vs Customer Avg Net Price 12M %": None if avg_price <= 0 else (proposed_price - avg_price) / avg_price,
                "Price vs Product Avg Net Price 12M %": None if product_avg <= 0 else (proposed_price - product_avg) / product_avg,
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
        available = safe_float(inv.get("Available Inventory"))
        avg_monthly = safe_float(inv.get("Average Monthly Demand 6M"))
        coverage_days = safe_float(inv.get("Coverage Days"))
        lead_time = safe_float(inv.get("Lead Time Days"))
        shortage = max(requested - available, 0)
        excess = max(available - requested, 0)
        supply_recommendation = str(inv.get("Supply Recommendation", ""))
        coverage_status = str(inv.get("Coverage Status", ""))
        allocation_risk = "High" if shortage > 0 or coverage_status == "Critical" else "Medium" if coverage_status in {"At Risk", "Tight"} else "Low"
        cannibalization_risk = "High" if shortage > 0 else "Medium" if avg_monthly > 0 and requested > avg_monthly * 0.5 else "Low"
        rows.append(
            {
                "SKU": line["SKU"],
                "Requested Qty": requested,
                "Available Inventory": available,
                "Excess Inventory": excess,
                "Inventory Shortage": shortage,
                "Demand Forecast": avg_monthly,
                "Coverage Days": coverage_days,
                "Lead Time Days": lead_time,
                "Coverage Status": coverage_status,
                "Allocation Risk": allocation_risk,
                "Cannibalization Risk": cannibalization_risk,
                "Finding": f"{allocation_risk} allocation risk; {cannibalization_risk.lower()} cannibalization risk; {coverage_status}; {supply_recommendation}".strip("; "),
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
        months = safe_float(exp.get("Months To Expiry"))
        near_expiry = "Yes" if 0 < months < 6 else "No"
        aging_inventory = "Yes" if 0 < months <= 12 else "No"
        rows.append(
            {
                "SKU": line["SKU"],
                "Warehouse Location": exp.get("Warehouse Location"),
                "Days To Expiry": days,
                "Months To Expiry": months,
                "Expiry Bucket": exp.get("Expiry Bucket"),
                "Near Expiry Inventory": near_expiry,
                "Aging Inventory": aging_inventory,
                "Quantity On Hand": exp.get("Quantity On Hand"),
                "Quality Control Status": exp.get("Quality Control Status"),
                "Recommended Action": exp.get("Recommended Action"),
            }
        )
    return pd.DataFrame(rows)


def enhanced_competitor_intelligence(data: dict[str, pd.DataFrame], lines: pd.DataFrame, customer: str, region: str) -> pd.DataFrame:
    tender_df, intel_df = tender_competitor_summary(data, lines, customer, region)
    rows = []
    for _, line in lines.iterrows():
        sku = str(line["SKU"])
        tender_row = tender_df[tender_df["SKU"].astype(str).eq(sku)] if "SKU" in tender_df else pd.DataFrame()
        product_name = str(line.get("Product Name", ""))
        intel_row = intel_df[intel_df["Product Name"].astype(str).eq(product_name)] if "Product Name" in intel_df else pd.DataFrame()
        tender = tender_row.iloc[0] if not tender_row.empty else pd.Series(dtype=object)
        intel = intel_row.iloc[0] if not intel_row.empty else pd.Series(dtype=object)
        signal = str(intel.get("Signal", ""))
        driver = str(tender.get("Driver", ""))
        response = str(intel.get("Response", ""))
        competitor = str(intel.get("Competitor", ""))
        aggressive_price = "Yes" if signal in {"Pricing Change", "Aggressive Contracting"} or driver == "Lowest Price" else "No"
        incumbent = "Yes" if driver in {"Incumbent Supplier", "Relationship Advantage"} else "No"
        supply_issue = "Yes" if "supply" in signal.lower() or "supply" in response.lower() or "supply" in driver.lower() else "No"
        nearby_behavior = "External market signal" if not intel_row.empty else "Internal tender precedent"
        rows.append(
            {
                "SKU": sku,
                "Historical Tender Result": tender.get("Result", "n/a"),
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
            findings.append(f"Use earliest-expiry-first allocation and prioritize {near_expiry} near-expiry line(s) where quality control status permits.")
        elif aging:
            findings.append(f"Aging inventory exists on {aging} line(s); allocate older released lots first.")
        else:
            findings.append("No near-expiry inventory condition is required beyond standard earliest-expiry-first controls.")
    return " ".join(findings) if findings else "Inventory and aging data is not available for this deal."


def competitor_summary(competitor_df: pd.DataFrame) -> str:
    if competitor_df.empty:
        return "No external market signals or tender precedents were found for the selected deal lines."
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
        summary.append("Internal tender precedent and external market signals are manageable.")
    if not responses.empty:
        summary.append(f"Recommended response: {responses.iloc[0]}.")
    return " ".join(summary)


def market_intelligence_insights(signal_df: pd.DataFrame, competitor_df: pd.DataFrame) -> list[tuple[str, str]]:
    insights = []
    if signal_df.empty and competitor_df.empty:
        return [("Market Signals", "No material external market signal is available for the selected products.")]
    if not competitor_df.empty:
        insights.append(("Competitive Pressure", competitor_summary(competitor_df)))
    if not signal_df.empty:
        signal_types = ", ".join(signal_df.get("Signal", signal_df.get("Signal Type", pd.Series(dtype=str))).dropna().astype(str).unique()[:3])
        impact = signal_df.get("Potential Business Impact", pd.Series(dtype=str)).dropna().astype(str)
        response = signal_df.get("Response", signal_df.get("Suggested Commercial Response", pd.Series(dtype=str))).dropna().astype(str)
        insights.append(("Pricing and Market Signals", signal_types or "External market signals identified."))
        if not impact.empty:
            insights.append(("Market Risk", short_business_text(impact.iloc[0], "Market impact is not specified.", 180)))
        if not response.empty:
            insights.append(("Suggested Response", short_business_text(response.iloc[0], "No response guidance is specified.", 180)))
    return insights


def supply_inventory_insights(inventory_df: pd.DataFrame, aging_df: pd.DataFrame) -> list[tuple[str, str]]:
    insights = [("Supply Summary", inventory_aging_recommendation(inventory_df, aging_df))]
    if not inventory_df.empty:
        shortage = safe_float(inventory_df.get("Inventory Shortage", pd.Series(dtype=float)).sum())
        high_allocation = int(inventory_df.get("Allocation Risk", pd.Series(dtype=str)).astype(str).eq("High").sum())
        available = safe_float(inventory_df.get("Available Inventory", pd.Series(dtype=float)).sum())
        insights.append(("Inventory Availability", f"Available inventory across requested lines is {available:,.0f} units; shortage is {shortage:,.0f} units."))
        insights.append(("Allocation Risk", f"{high_allocation} line(s) show high allocation risk."))
    if not aging_df.empty:
        near_expiry = int(aging_df.get("Near Expiry Inventory", pd.Series(dtype=str)).astype(str).eq("Yes").sum())
        actions = aging_df.get("Recommended Action", pd.Series(dtype=str)).dropna().astype(str)
        action = actions.iloc[0] if not actions.empty else "Use normal inventory rotation."
        insights.append(("Expiry Exposure", f"{near_expiry} line(s) have near-expiry exposure. Recommended action: {action}"))
    return insights


def tender_intelligence_insights(tender_df: pd.DataFrame) -> list[tuple[str, str]]:
    if tender_df.empty:
        return [("Tender Precedent", "No comparable tender precedent is available for the selected account and products.")]
    result_counts = tender_df.get("Result", pd.Series(dtype=str)).astype(str).value_counts()
    outcomes = ", ".join(f"{status}: {count}" for status, count in result_counts.items())
    discounts = pd.to_numeric(tender_df.get("Winning Discount %", pd.Series(dtype=float)), errors="coerce").dropna()
    if discounts.empty:
        discount_range = "No winning discount benchmark is available."
    else:
        discount_range = f"Typical winning discount range is {pct(discounts.min())} to {pct(discounts.max())}."
    drivers = tender_df.get("Win / Loss Driver", tender_df.get("Driver", pd.Series(dtype=str))).dropna().astype(str)
    driver_text = ", ".join(drivers.unique()[:3]) if not drivers.empty else "No driver detail is available."
    return [
        ("Previous Tender Outcomes", outcomes or "Prior tender outcomes are not classified."),
        ("Winning Discount Range", discount_range),
        ("Win/Loss Drivers", driver_text),
        ("Key Lesson", "Compare the requested discount and supply commitment against prior winning levels before approving."),
    ]


def render_insight_cards(insights: list[tuple[str, str]], columns: int = 2) -> None:
    if not insights:
        return
    cols = st.columns(columns)
    for index, (title, body) in enumerate(insights):
        with cols[index % columns].container(border=True):
            st.markdown(f"**{title}**")
            st.write(body)


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
        if role == "Pricing Governance Owner" and aggressive_pricing:
            trigger += " Competitor pricing signals require guardrail review."
        if role == "Finance Director":
            trigger += " Gross profit variance requires finance review."
        if role == "Operations Manager" and shortage > 0:
            trigger += f" Inventory shortage is {shortage:,.0f} units across requested lines."
        if role == "General Manager":
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
        if role == "Pricing Governance Owner" and not lines.empty and (lines["Requested Net Price"] < lines["Floor Price"]).any():
            reason += " Margin below floor."
        if role == "Finance Director" and customer_risk in {"Medium", "High"}:
            reason += f" {customer_risk} AR exposure."
        if role == "General Manager" and purpose == "Strategic account":
            reason += " Strategic account."
        if role == "Operations Manager" and shortage > 0:
            reason += " High inventory risk."
        if role in {"Pricing Governance Owner", "General Manager"} and visibility == "Public":
            reason += " Public pricing exposure."
        if role == "Pricing Governance Owner" and aggressive:
            reason += " Aggressive competitor pricing."
        item = row.to_dict()
        item["Approver"] = row.get("Approver", role)
        item["Trigger Reason"] = reason
        rows.append(item)
    display_cols = [col for col in ["Sequence", "Approver", "Role", "Active Approver", "Primary Approver", "Delegate Approver", "SLA Hours", "Trigger Reason"] if col in pd.DataFrame(rows)]
    return pd.DataFrame(rows)[display_cols]


def build_deal_context(data: dict[str, pd.DataFrame], deal_id: str) -> dict | None:
    deals = combined_deals(data)
    if deals.empty or deal_id not in set(deals["Deal ID"].astype(str)):
        return None
    deal = deals[deals["Deal ID"].astype(str).eq(str(deal_id))].iloc[0].to_dict()
    lines = combined_lines(data)
    calc_lines = normalize_lines(lines[lines["Deal ID"].astype(str).eq(str(deal_id))], data)
    summary = summarize_lines(calc_lines)
    customer = deal.get("Sold-To Customer Name", deal.get("Customer Name", ""))
    region = deal.get("Region", "")
    segment = deal_customer_type(deal)
    account = customer_lookup(data).get(customer, {})
    channel = customer_type(account)
    included_value = str(deal.get("Included In Latest Financial Plan", deal.get("Included_In_Latest_Financial_Plan", "Yes"))).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, calc_lines, region, segment, customer)
    incremental_df = incremental_opportunity_analysis(data, calc_lines, customer, channel)
    inventory_df = enhanced_inventory_analysis(data, calc_lines, region)
    aging_df = enhanced_aging_analysis(data, calc_lines, region)
    competitor_df = enhanced_competitor_intelligence(data, calc_lines, customer, region)
    gp_impact = gross_profit_impact(calc_lines, plan_df, incremental_df, included_in_plan)
    header = build_route_header(deal, data)
    route_df = route_preview(header, calc_lines, summary, data)
    ensure_approval_assignments(str(deal_id), route_df, data)
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
        "customer": account,
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


def short_business_text(value: object, fallback: str, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return fallback
    return text if len(text) <= limit else f"{text[: limit - 3].rstrip()}..."


def margin_threshold_display(summary: dict, role: str | None = None) -> str:
    status = "Above Threshold" if safe_float(summary.get("margin_pct")) >= safe_float(summary.get("weighted_target_margin")) else "Below Threshold"
    if margin_visibility_for_role(role) == "Exact":
        variance = safe_float(summary.get("margin_pct")) - safe_float(summary.get("weighted_target_margin"))
        return f"{pct(variance)}"
    return status


def landing_margin_display(summary: dict, role: str | None = None) -> str:
    if margin_visibility_for_role(role) == "Exact":
        return pct(summary.get("margin_pct"))
    return "Above Threshold" if safe_float(summary.get("margin_pct")) >= safe_float(summary.get("weighted_target_margin")) else "Below Threshold"


def revenue_at_risk(context: dict) -> float:
    deal = context["deal"]
    customer = context.get("customer", {})
    risk = str(deal.get("KAM Risk Assessment", deal.get("Intake Risk", "")))
    credit_risk = str(customer.get("Credit Status", "")) == "Hold" or safe_float(customer.get("Overdue AR")) > 0
    supply_risk = not context["inventory_df"].empty and safe_float(context["inventory_df"]["Inventory Shortage"].sum()) > 0
    return safe_float(context["summary"].get("total_proposed")) if risk in {"High", "Critical"} or credit_risk or supply_risk else 0


def render_inline_deal_preview(context: dict, compact: bool = False) -> None:
    deal = context["deal"]
    summary = context["summary"]
    role = current_role()
    st.subheader("Selected Deal Preview")
    st.caption(
        f"{deal.get('Deal Title', '')} | {deal.get('Sold-To Customer Name', deal.get('Customer Name', ''))} | "
        f"{deal.get('Status', '')}"
    )

    metrics = st.columns(5)
    metrics[0].metric("Requested Net Revenue", money(summary["total_proposed"]))
    metrics[1].metric("Requested Discount %", pct(summary["discount_pct"]))
    margin_label = "Resulting Gross Margin %" if margin_visibility_for_role(role) == "Exact" else "Margin Status"
    metrics[2].metric(margin_label, landing_margin_display(summary, role))
    metrics[3].metric("Margin vs Approval Threshold", margin_threshold_display(summary, role))
    metrics[4].metric("Financial Plan Status", "Included" if context["included_in_plan"] else "Outside Plan")

    context_cols = st.columns(3)
    with context_cols[0].container(border=True):
        st.markdown("**Commercial Context**")
        st.write(
            short_business_text(
                deal.get("Strategic Rationale", deal.get("Business Justification", "")),
                "Commercial rationale is not available.",
            )
        )
        st.caption(short_business_text(competitor_summary(context["competitor_df"]), "No material competitor precedent identified.", 150))
    with context_cols[1].container(border=True):
        st.markdown("**Financial Impact**")
        st.write(f"Requested discount: **{pct(summary['discount_pct'])}**")
        st.write(f"Margin: **{landing_margin_display(summary, role)}**")
        if context["included_in_plan"]:
            variance = safe_float(context["gp_impact"].get("Net Revenue Variance"))
            st.caption(f"Included in plan. Net revenue variance: {money(variance)}.")
        else:
            st.caption(f"Incremental opportunity of {money(summary['total_proposed'])} outside the latest financial plan.")
    with context_cols[2].container(border=True):
        st.markdown("**Supply & Operations**")
        st.write(short_business_text(inventory_aging_recommendation(context["inventory_df"], context["aging_df"]), "No supply information available."))

    required_roles = context["route_df"].sort_values("Sequence")["Approver"].astype(str).tolist() if not context["route_df"].empty else []
    pending_role = current_required_approval_role(str(deal.get("Deal ID", "")), str(deal.get("Status", "")), context["route_df"])
    pending_match = context["route_df"][context["route_df"]["Role"].astype(str).eq(pending_role)] if pending_role and not context["route_df"].empty else pd.DataFrame()
    pending_label = str(pending_match.iloc[0].get("Approver", pending_role)) if not pending_match.empty else pending_role
    route_cols = st.columns([3, 1])
    route_cols[0].markdown(f"**Required approvals:** {' → '.join(required_roles) if required_roles else 'None'}")
    route_cols[1].markdown(f"**Pending:** {pending_label if pending_label else 'Complete'}")

    if compact:
        return
    st.dataframe(mask_sensitive_dataframe(context["route_triggers"]), use_container_width=True, hide_index=True)


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
        required_condition = "Use earliest-expiry-first rotation and confirm aging or near-expiry stock allocation before approval."
    elif not inventory_df.empty and (inventory_df["Allocation Risk"] == "High").any():
        required_condition = "Supply chain must confirm allocation feasibility and supply continuity."
    elif context["recommendation"] in {"Request Price Revision", "Approve with Conditions"}:
        required_condition = "Pricing or finance reviewer must document approval guardrails."

    return {
        "Key Reason": context["rationale"],
        "Key Risk": key_risk,
        "Required Condition": required_condition,
        "Inventory Summary": inventory_aging_recommendation(inventory_df, aging_df),
        "Aging Summary": aging_df[["SKU", "Days To Expiry", "Months To Expiry", "Expiry Bucket", "Near Expiry Inventory", "Recommended Action"]].copy() if not aging_df.empty else pd.DataFrame(),
        "Competitor Summary": competitor_summary(competitor_df),
    }


def render_approval_review_panel(context: dict) -> None:
    deal = context["deal"]
    summary = context["summary"]
    customer = context.get("customer", {})
    review = approval_review_summary(context)

    st.subheader("Selected Deal Review")
    top = st.columns(5)
    top[0].metric("Deal ID", str(deal.get("Deal ID", "")))
    top[1].metric("Status", str(deal.get("Status", "")))
    top[2].metric("Proposed Value", money(summary["total_proposed"]))
    top[3].metric("Discount", pct(summary["discount_pct"]))
    top[4].metric("Est. Margin", margin_display(summary))

    st.write(f"Customer: **{deal.get('Customer Name', '')}**")
    st.write(f"Deal title: **{deal.get('Deal Title', '')}**")
    if customer:
        render_customer_information_panel(customer)

    decision_cols = st.columns(2)
    decision_cols[0].metric("Decision Score", f"{context['total_score']}/100")
    decision_cols[1].metric("Recommendation", context["recommendation"])
    sensitive_data_note()

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
            st.dataframe(mask_sensitive_dataframe(review["Aging Summary"]), use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Competitor summary**")
        st.info(review["Competitor Summary"])

    st.markdown("**Approval route trigger reasons**")
    st.dataframe(mask_sensitive_dataframe(context["route_triggers"]), use_container_width=True, hide_index=True)


def validate_deal(header: dict, lines: pd.DataFrame, data: dict[str, pd.DataFrame]) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    required = ["Deal Title", "Customer Name", "Deal Type", "Region", "Target Close Date", "Payment Terms"]
    for field in required:
        if not header.get(field):
            errors.append(f"{field} is required.")
    if not header.get("Contract Months") or int(header.get("Contract Months", 0)) <= 0:
        errors.append("Contract months must be greater than zero.")
    if lines.empty:
        errors.append("At least one valid line item is required.")
    else:
        pricing_rules = approval_rule_rows(data)
        discount_review_rules = pricing_rules[
            pricing_rules["Rule Type"].eq("DISC")
            & ~pricing_rules["Policy ID"].astype(str).eq("POL-DISC-LOW")
        ]
        for _, line in lines.iterrows():
            if line["Quantity"] <= 0:
                errors.append(f"{line['SKU']} quantity must be greater than zero.")
            if line["Proposed Unit Price"] < 0 and line["SKU"] != "REB-FORM":
                errors.append(f"{line['SKU']} proposed price cannot be negative.")
            if line["Inventory Tracked"] == "Yes" and pd.isna(line.get("Requested Delivery Date")):
                warnings.append(f"{line['SKU']} is inventory tracked and should have a requested delivery date.")
            if line["SKU"] != "REB-FORM" and any(discount_trigger_matches(rule.get("Discount Trigger"), safe_float(line["Discount %"])) for _, rule in discount_review_rules.iterrows()):
                warnings.append(f"{line['SKU']} discount triggers configured approval routing.")
    if not header.get("Business Justification"):
        errors.append("Business justification is required.")
    if header.get("Payment Terms") in {"Net 75", "Net 90"}:
        warnings.append("Extended payment terms will require Finance and Legal review.")
    if int(header.get("Contract Months", 0) or 0) > 36:
        warnings.append("Contract duration above 36 months will require Legal review.")
    customer = customer_lookup(data).get(header.get("Customer Name", ""), {})
    overdue_ar = safe_float(header.get("Overdue AR", customer.get("Overdue AR", 0)))
    if customer.get("Credit Status") == "Watch":
        warnings.append("Customer credit status is Watch.")
    if customer.get("Credit Status") == "Hold":
        warnings.append("Customer credit status is Hold. Finance approval is mandatory before final approval.")
    if overdue_ar > 0:
        warnings.append("Customer has overdue receivables. Finance approval is mandatory.")
    return errors, warnings


def route_preview(header: dict, lines: pd.DataFrame, summary: dict, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rules = approval_rule_rows(data)
    rows: list[dict] = []
    discount_pct = safe_float(summary.get("discount_pct"))
    margin_pct = safe_float(summary.get("margin_pct"))
    target_margin = safe_float(summary.get("weighted_target_margin"))
    fd_trigger = finance_trigger_margin(target_margin)
    gm_trigger = gm_trigger_margin(target_margin)
    visibility = str(header.get("Visibility", "Confidential"))
    overdue_ar = safe_float(header.get("Overdue AR"))
    credit_status = str(header.get("Credit Status", "Good"))
    inventory_df = enhanced_inventory_analysis(data, lines, str(header.get("Region", "")))
    shortage = safe_float(inventory_df["Inventory Shortage"].sum()) if not inventory_df.empty else 0

    for _, rule in rules.iterrows():
        rule_type = str(rule.get("Rule Type", ""))
        if rule_type == "DISC" and discount_trigger_matches(rule.get("Discount Trigger"), discount_pct):
            add_route_rule(rows, rule, f"Weighted discount {pct(discount_pct)} matches configured tier {rule.get('Discount Trigger')}.")
        elif rule_type == "MARGIN":
            role = str(rule.get("Required Role", ""))
            if role == "Finance Director" and margin_pct < fd_trigger:
                add_route_rule(rows, rule, f"Estimated gross margin {pct(margin_pct)} is below Finance trigger {pct(fd_trigger)} based on target margin {pct(target_margin)}.")
            elif role == "General Manager" and margin_pct < gm_trigger:
                add_route_rule(rows, rule, f"Estimated gross margin {pct(margin_pct)} is below GM trigger {pct(gm_trigger)} based on target margin {pct(target_margin)}.")
        elif rule_type == "PUBLIC" and visibility == "Public":
            add_route_rule(rows, rule, "Deal is marked Public and may impact public/list price.")
        elif rule_type == "CREDIT" and (credit_status == "Hold" or comparison_trigger_matches(rule.get("Value / Margin Trigger"), overdue_ar)):
            if credit_status == "Hold":
                add_route_rule(rows, rule, "Customer credit status is Hold; Finance approval is mandatory before final approval.")
            else:
                add_route_rule(rows, rule, f"Customer overdue receivables are {money(overdue_ar)}.")
        elif rule_type == "SUPPLY" and comparison_trigger_matches(rule.get("Value / Margin Trigger"), shortage):
            add_route_rule(rows, rule, f"Inventory shortage is {shortage:,.0f} units across requested lines.")

    return enrich_route_with_approvers(compact_route(rows), data)


def approval_route_text(route_df: pd.DataFrame, data: dict[str, pd.DataFrame] | None = None) -> str:
    if route_df.empty or "Role" not in route_df:
        return ""
    roles = [str(role) for role in route_df.sort_values("Sequence")["Role"].tolist()]
    if data is not None:
        roles = [role_display_label(data, role) for role in roles]
    return " \u2192 ".join(dict.fromkeys(roles))


def customer_record_for_deal(deal: dict, data: dict[str, pd.DataFrame]) -> dict:
    customers = customer_lookup(data)
    for key in ["Sold-To Customer Name", "Customer Name", "End Account Name"]:
        name = str(deal.get(key, "")).strip()
        if name and name in customers:
            return customers[name]
    return {}


def system_risk_score(deal: dict, summary: dict, data: dict[str, pd.DataFrame], lines: pd.DataFrame | None = None) -> int:
    risk_reason = str(deal.get("Risk Reason", ""))
    deal_type = str(deal.get("Deal Type", ""))
    visibility = str(deal.get("Visibility", ""))
    score = 0
    if risk_reason == "Public tender" or deal_type == "Tender":
        score += 2
    if risk_reason == "Competitor price pressure":
        score += 2
    customer = customer_record_for_deal(deal, data)
    if str(customer.get("Strategic Account", deal.get("Strategic Account", ""))).strip().lower() in {"yes", "true", "1"}:
        score += 1
    if safe_float(summary.get("total_proposed")) >= LARGE_DEAL_VALUE_THRESHOLD:
        score += 1
    if visibility == "Public" or risk_reason == "Public tender":
        score += 2
    overdue_ar = safe_float(deal.get("Overdue AR", customer.get("Overdue AR", 0)))
    credit_status = str(deal.get("Credit Status", customer.get("Credit Status", "")))
    if credit_status == "Hold" or overdue_ar > 0:
        score += 2
    if lines is not None and not lines.empty:
        inventory_df = enhanced_inventory_analysis(data, lines, str(deal.get("Region", "")))
        if not inventory_df.empty and safe_float(inventory_df["Inventory Shortage"].sum()) > 0:
            score += 1
    return score


def system_risk_level(score: int) -> str:
    if score >= 6:
        return "Critical"
    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


def kam_risk_exceeds_system_score(kam_risk: object, system_score: int) -> bool:
    kam_level = str(kam_risk or "Low")
    return RISK_LEVEL_SCORE.get(kam_level, 0) > RISK_LEVEL_SCORE.get(system_risk_level(system_score), 0)


def business_recommendation(summary: dict, lines: pd.DataFrame, route_df: pd.DataFrame, deal: dict, system_score: int) -> str:
    roles = set(route_df.get("Role", pd.Series(dtype=str)).astype(str)) if not route_df.empty else set()
    if not lines.empty and "Floor Price" in lines and (lines["Requested Net Price"] < lines["Floor Price"]).any():
        return "Reject - Below Margin Floor"
    if kam_risk_exceeds_system_score(deal.get("KAM Risk Assessment"), system_score):
        return "Request Revision"
    if "General Manager" in roles:
        return "Escalate to General Manager"
    if "Pricing Governance Owner" in roles:
        return "Approve with Pricing Governance Review"
    if "Finance Director" in roles:
        return "Approve with Finance Review"
    return "Approve"


def calculated_deal_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    deals = normalize_deal_headers(data.get("deals", pd.DataFrame()))
    line_items = data.get("line_items", pd.DataFrame())
    rows = []
    for _, deal_row in deals.iterrows():
        deal = deal_row.to_dict()
        deal_id = str(deal.get("Deal ID", ""))
        calc_lines = normalize_lines(line_items[line_items["Deal ID"].astype(str).eq(deal_id)], data) if not line_items.empty else pd.DataFrame()
        summary = summarize_lines(calc_lines)
        route_df = route_preview(build_route_header(deal, data), calc_lines, summary, data)
        system_score = system_risk_score(deal, summary, data, calc_lines)
        gross_profit = summary["total_proposed"] - safe_float((calc_lines["Quantity"] * calc_lines["Unit Cost"]).sum()) if not calc_lines.empty else 0
        rows.append(
            {
                "Deal ID": deal_id,
                "Deal Title": deal.get("Deal Title", ""),
                "Sold-To Customer": deal.get("Sold-To Customer Name", deal.get("Customer Name", "")),
                "End Account": deal.get("End Account Name", deal.get("Customer Name", "")),
                "Gross Revenue": summary["total_gross"],
                "Proposed Net Revenue": summary["total_proposed"],
                "Discount Amount": summary["discount_amount"],
                "Discount %": summary["discount_pct"],
                "Gross Profit": gross_profit,
                "Gross Margin %": summary["margin_pct"],
                "KAM Risk Assessment": deal.get("KAM Risk Assessment", deal.get("Intake Risk", "")),
                "Risk Reason": deal.get("Risk Reason", ""),
                "System Risk Score": system_score,
                "Approval Route": approval_route_text(route_df),
                "Business Recommendation": business_recommendation(summary, calc_lines, route_df, deal, system_score),
                "Status": deal.get("Status", ""),
                "Included In Latest Financial Plan": deal.get("Included In Latest Financial Plan", deal.get("Included_In_Latest_Financial_Plan", "")),
            }
        )
    return pd.DataFrame(rows)


def executive_summary_record(deal: dict, lines: pd.DataFrame, summary: dict, route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> dict:
    system_score = system_risk_score(deal, summary, data, lines)
    gross_profit = summary["total_proposed"] - safe_float((lines["Quantity"] * lines["Unit Cost"]).sum()) if not lines.empty else 0
    return {
        "Deal ID": deal.get("Deal ID", ""),
        "Deal Title": deal.get("Deal Title", ""),
        "Sold-To Customer": deal.get("Sold-To Customer Name", deal.get("Customer Name", "")),
        "End Account": deal.get("End Account Name", deal.get("Customer Name", "")),
        "Gross Revenue": summary["total_gross"],
        "Proposed Net Revenue": summary["total_proposed"],
        "Discount Amount": summary["discount_amount"],
        "Discount %": summary["discount_pct"],
        "Gross Profit": gross_profit,
        "Gross Margin %": summary["margin_pct"],
        "KAM Risk Assessment": deal.get("KAM Risk Assessment", deal.get("Intake Risk", "")),
        "Risk Reason": deal.get("Risk Reason", ""),
        "System Risk Score": system_score,
        "Approval Route": approval_route_text(route_df),
        "Business Recommendation": business_recommendation(summary, lines, route_df, deal, system_score),
        "Status": deal.get("Status", ""),
        "Included In Latest Financial Plan": deal.get("Included In Latest Financial Plan", deal.get("Included_In_Latest_Financial_Plan", "")),
    }


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
        return f"Review Queue > {selected}" if selected else "Review Queue"
    if page == "Reference Data":
        return "Reference & Governance > Reference Data"
    if page == "Approval Matrix":
        return "Reference & Governance > Approval Rules & Matrix"
    if page == "Approver Roster":
        return "System Administration > Approver Roster"
    if page == "System Administrator Settings":
        return "Reference & Governance > Configuration"
    if page == "Delegate Administration":
        return "Reference & Governance > Delegation"
    if page == "Audit Log":
        return "Reference & Governance > Audit Trail"
    return str(page)


def render_header(title: str, subtitle: str = "") -> None:
    breadcrumb = breadcrumb_for_current_page()
    if breadcrumb and breadcrumb != title:
        st.markdown(f"<div class='page-breadcrumb'>{breadcrumb}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-note'>{subtitle}</div>", unsafe_allow_html=True)


def render_landing_kpis(cockpit: pd.DataFrame, role: str) -> None:
    kpis = st.columns(5)
    status = cockpit.get("Status", pd.Series(dtype=str)).astype(str)
    risk = cockpit.get("Risk", pd.Series(dtype=str)).astype(str)
    pending = cockpit.get("Pending Role", pd.Series(dtype=str)).astype(str)
    pending_groups = cockpit.get("Pending Roles", pd.Series([[] for _ in range(len(cockpit))], index=cockpit.index))
    values = pd.to_numeric(cockpit.get("Requested Value", pd.Series(dtype=float)), errors="coerce").fillna(0)
    due_dates = pd.to_datetime(cockpit.get("Decision Due Date", pd.Series(dtype="datetime64[ns]")), errors="coerce")
    active = status.isin(ACTIVE_APPROVAL_STATUSES)
    today = pd.Timestamp(date.today())
    due_today = due_dates.dt.normalize().eq(today) & active
    overdue = due_dates.dt.normalize().lt(today) & active
    if is_kam_role(role):
        kpis[0].metric("Draft", int(status.eq("Draft").sum()))
        kpis[1].metric("Submitted", int(status.eq("Submitted").sum()))
        kpis[2].metric("Changes Requested", int(status.eq("Changes Requested").sum()))
        kpis[3].metric("Approved", int(status.isin(["Approved", "Final Approved"]).sum()))
        kpis[4].metric("Rejected", int(status.eq("Rejected").sum()))
    elif role == "General Manager":
        strategic = cockpit.get("Strategic Account", pd.Series(dtype=bool)).fillna(False).astype(bool)
        kpis[0].metric("Pending GM Review", int(pending_groups.apply(lambda roles: "General Manager" in roles).sum()))
        kpis[1].metric("Strategic Accounts", int(strategic.sum()))
        kpis[2].metric("High Value Requests", int(values.ge(LARGE_DEAL_VALUE_THRESHOLD).sum()))
        kpis[3].metric("Due Today", int(due_today.sum()))
        kpis[4].metric("Total Exposure", money(values.sum()))
    else:
        pending_mask = pending_groups.apply(lambda roles: role in roles)
        if role == "System Administrator":
            pending_mask = pending_groups.apply(bool)
        kpis[0].metric("Pending My Review", int(pending_mask.sum()))
        kpis[1].metric("High Risk", int(risk.isin(["High", "Critical"]).sum()))
        kpis[2].metric("Due Today", int(due_today.sum()))
        kpis[3].metric("Overdue", int(overdue.sum()))
        kpis[4].metric("Total Requested Value", money(values.sum()))


def requestor_workspace_records(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, dict]]:
    own_deals = combined_deals(data)
    if own_deals.empty:
        return pd.DataFrame(), {}
    own_deals = own_deals[own_deals.get("Sales Owner", pd.Series(index=own_deals.index, dtype=str)).astype(str).eq(current_persona())]
    records = []
    contexts: dict[str, dict] = {}
    for _, deal_row in own_deals.iterrows():
        deal_id = str(deal_row.get("Deal ID", ""))
        context = build_deal_context(data, deal_id)
        if not context:
            continue
        contexts[deal_id] = context
        deal = context["deal"]
        lines = context["lines"]
        summary = context["summary"]
        products = lines["Product Name"].dropna().astype(str).unique().tolist() if not lines.empty else []
        status = str(deal.get("Status", "")).strip()
        pending_roles = current_required_approval_roles(deal_id, status, context["route_df"])
        pending_role = pending_roles[0] if pending_roles else ""
        current_reviewer = active_approver_for_role(data, pending_role) if pending_role else ""
        sla = assignment_status(deal_id, pending_role) if pending_role else {}
        hours_elapsed = safe_float(sla.get("Hours Elapsed"))
        days_waiting = max(0, int(hours_elapsed // 24)) if hours_elapsed else 0
        sla_text = f"{days_waiting}d waiting" if pending_role else "n/a"
        if sla.get("Is Breached"):
            sla_text = f"Overdue by {abs(int(safe_float(sla.get('Hours Remaining')) // 24))}d"
        deadline = pd.to_datetime(deal.get("Expected Award / Decision Date"), errors="coerce")
        records.append(
            {
                "Case ID": deal_id,
                "Account": deal.get("End Account Name", deal.get("Sold-To Customer Name", deal.get("Customer Name", ""))),
                "Product": products[0] if products else "",
                "Scenario": deal.get("Deal Type", deal.get("Risk Reason", "")),
                "Status": business_deal_status(status),
                "Raw Status": status,
                "Current Reviewer": current_reviewer or pending_role or "None",
                "Pending Role": pending_role,
                "SLA / Days Waiting": sla_text,
                "Days Waiting": days_waiting,
                "Deadline": deadline.strftime("%Y-%m-%d") if not pd.isna(deadline) else "",
                "Deadline Date": deadline,
                "Requested Value": safe_float(summary.get("total_proposed")),
                "Included In Latest Financial Plan": context.get("included_value", ""),
            }
        )
    return pd.DataFrame(records), contexts


def requestor_kpi_values(records: pd.DataFrame) -> list[tuple[str, str]]:
    if records.empty:
        return [
            ("Active Cases", "0"),
            ("Draft Cases", "0"),
            ("Waiting for Review", "0"),
            ("Need My Action", "0"),
            ("Cases Near Deadline", "0"),
            ("Approved This Month", "0"),
            ("Average Approval Time", "n/a"),
            ("Executed Cases with Price Deviations", "0"),
        ]
    raw_status = records["Raw Status"].astype(str)
    deadlines = pd.to_datetime(records["Deadline Date"], errors="coerce")
    today = pd.Timestamp(date.today())
    active = ~raw_status.isin(ARCHIVE_STATUSES)
    near_deadline = active & deadlines.notna() & deadlines.dt.normalize().between(today, today + pd.Timedelta(days=5))
    approved = raw_status.isin(["Approved", "Final Approved"])
    approved_month = approved & deadlines.notna() & deadlines.dt.to_period("M").eq(pd.Period(today, freq="M"))
    waiting_days = pd.to_numeric(records.get("Days Waiting", pd.Series(dtype=float)), errors="coerce").fillna(0)
    avg_waiting = f"{waiting_days[waiting_days > 0].mean():.1f}d" if (waiting_days > 0).any() else "n/a"
    price_deviation = approved & records.get("Included In Latest Financial Plan", pd.Series(dtype=str)).astype(str).str.lower().eq("yes")
    return [
        ("Active Cases", str(int(active.sum()))),
        ("Draft Cases", str(int(raw_status.eq("Draft").sum()))),
        ("Waiting for Review", str(int((active & records["Pending Role"].astype(str).ne("")).sum()))),
        ("Need My Action", str(int(raw_status.isin(["Draft", "Changes Requested"]).sum()))),
        ("Cases Near Deadline", str(int(near_deadline.sum()))),
        ("Approved This Month", str(int(approved_month.sum()))),
        ("Average Approval Time", avg_waiting),
        ("Executed Cases with Price Deviations", str(int(price_deviation.sum()))),
    ]


def render_requestor_kpis(records: pd.DataFrame) -> None:
    values = requestor_kpi_values(records)
    first_row = st.columns(4)
    second_row = st.columns(4)
    for index, (label, value) in enumerate(values):
        target = first_row if index < 4 else second_row
        target[index % 4].metric(label, value)


def requestor_action_items(records: pd.DataFrame) -> list[tuple[str, str]]:
    if records.empty:
        return []
    raw_status = records["Raw Status"].astype(str)
    deadlines = pd.to_datetime(records["Deadline Date"], errors="coerce")
    today = pd.Timestamp(date.today())
    items = []
    returned = records[raw_status.eq("Changes Requested")]
    for _, row in returned.head(3).iterrows():
        items.append(("Cases returned for changes", f"{row['Case ID']} needs revision before it can continue approval."))
    drafts = records[raw_status.eq("Draft")]
    for _, row in drafts.head(2).iterrows():
        items.append(("Questions to answer", f"{row['Case ID']} is still in draft and needs final submission inputs."))
    approaching = records[deadlines.notna() & deadlines.dt.normalize().between(today, today + pd.Timedelta(days=5))]
    for _, row in approaching.head(3).iterrows():
        items.append(("Deadlines approaching", f"{row['Case ID']} is due by {row['Deadline']}."))
    waiting = records[pd.to_numeric(records.get("Days Waiting", pd.Series(dtype=float)), errors="coerce").fillna(0).ge(1)]
    for _, row in waiting.head(3).iterrows():
        items.append(("Reviewers waiting too long", f"{row['Current Reviewer']} has had {row['Case ID']} for {row['SLA / Days Waiting']}."))
    return items


def render_requestor_action_center(records: pd.DataFrame) -> None:
    st.subheader("Action Center")
    items = requestor_action_items(records)
    if not items:
        st.info("No requestor actions need attention right now.")
        return
    cols = st.columns(2)
    for index, (title, body) in enumerate(items[:6]):
        with cols[index % 2].container(border=True):
            st.markdown(f"**{title}**")
            st.write(body)


def render_ai_daily_brief(records: pd.DataFrame) -> None:
    st.subheader("AI Daily Brief")
    if records.empty:
        st.info("No active requestor cases are available for today.")
        return
    actionable = requestor_action_items(records)
    near_deadline = records[pd.to_datetime(records["Deadline Date"], errors="coerce").notna()].sort_values("Deadline Date").head(1)
    waiting = records[pd.to_numeric(records.get("Days Waiting", pd.Series(dtype=float)), errors="coerce").fillna(0).ge(1)].head(1)
    with st.container(border=True):
        st.markdown("**Attention today**")
        st.write(actionable[0][1] if actionable else "No urgent requestor action is required today.")
        st.markdown("**Closest deadline**")
        if near_deadline.empty:
            st.write("No dated case deadline is available.")
        else:
            row = near_deadline.iloc[0]
            st.write(f"{row['Case ID']} is due by {row['Deadline']}.")
        st.markdown("**Reviewer follow-up**")
        if waiting.empty:
            st.write("No reviewer follow-up is currently recommended.")
        else:
            row = waiting.iloc[0]
            st.write(f"Follow up with {row['Current Reviewer']} on {row['Case ID']} ({row['SLA / Days Waiting']}).")


def log_requestor_followup(case_id: str, reviewer: str) -> None:
    event = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Case ID": case_id,
        "Reviewer": reviewer,
        "Actor": current_persona(),
        "Action": "Follow-up Reviewer",
    }
    st.session_state.requestor_followups.append(event)


def render_requestor_active_cases(records: pd.DataFrame, contexts: dict[str, dict]) -> None:
    st.subheader("My Active Cases")
    active = records[~records["Raw Status"].astype(str).isin(ARCHIVE_STATUSES)].copy()
    if active.empty:
        st.info("No active cases are open for this requestor.")
        return
    headers = st.columns([0.8, 1.35, 1.05, 1.0, 0.95, 1.15, 0.9, 0.9, 1.25])
    for col, label in zip(headers, ["Case ID", "Account", "Product", "Scenario", "Status", "Current Reviewer", "SLA / Days Waiting", "Deadline", "Action"]):
        col.markdown(f"**{label}**")
    for _, row in active.head(8).iterrows():
        row_cols = st.columns([0.8, 1.35, 1.05, 1.0, 0.95, 1.15, 0.9, 0.9, 1.25])
        case_id = str(row["Case ID"])
        row_cols[0].write(case_id)
        row_cols[1].write(short_business_text(row["Account"], "", 32))
        row_cols[2].write(short_business_text(row["Product"], "", 24))
        row_cols[3].write(short_business_text(row["Scenario"], "", 24))
        row_cols[4].write(row["Status"])
        row_cols[5].write(short_business_text(row["Current Reviewer"], "", 28))
        row_cols[6].write(row["SLA / Days Waiting"])
        row_cols[7].write(row["Deadline"])
        if row_cols[8].button("Open", key=f"requestor_open_{case_id}"):
            navigate_to_deal_detail(case_id, "requestor workspace")
        if row["Pending Role"] and row_cols[8].button("Follow-up Reviewer", key=f"requestor_followup_{case_id}"):
            log_requestor_followup(case_id, str(row["Current Reviewer"]))
            st.success(f"Follow-up logged for {row['Current Reviewer']} on {case_id}. No email or Teams message was sent.")


def page_requestor_workspace(data: dict[str, pd.DataFrame]) -> None:
    render_header("Requestor Workspace")
    records, contexts = requestor_workspace_records(data)
    render_requestor_kpis(records)
    workspace_cols = st.columns([3.2, 1.15])
    with workspace_cols[0]:
        render_requestor_action_center(records)
        render_requestor_active_cases(records, contexts)
    with workspace_cols[1]:
        render_ai_daily_brief(records)


def page_deal_list(data: dict[str, pd.DataFrame]) -> None:
    if is_kam_role():
        page_requestor_workspace(data)
        return
    render_header("Deal Requests")
    all_deals = combined_deals(data)
    active_deals = visible_deals_for_current_role(all_deals, data)
    active_deals = active_deals[~active_deals["Status"].astype(str).isin(ARCHIVE_STATUSES)]
    archived_deals = archived_deals_for_current_role(all_deals)
    list_mode = st.radio(
        "Queue",
        ["Active", "Archive"],
        horizontal=True,
        label_visibility="collapsed",
        key="deal_list_view_mode",
    )
    deals = active_deals if list_mode == "Active" else archived_deals

    records = []
    contexts: dict[str, dict] = {}
    for _, deal_row in deals.iterrows():
        deal_id = str(deal_row.get("Deal ID", ""))
        context = build_deal_context(data, deal_id)
        if not context:
            continue
        contexts[deal_id] = context
        deal = context["deal"]
        lines = context["lines"]
        summary = context["summary"]
        products = lines["Product Name"].dropna().astype(str).unique().tolist() if not lines.empty else []
        required_roles = context["route_df"]["Role"].astype(str).tolist() if not context["route_df"].empty else []
        pending_roles = current_required_approval_roles(deal_id, str(deal.get("Status", "")), context["route_df"])
        pending_role = pending_roles[0] if pending_roles else ""
        deadline = pd.to_datetime(deal.get("Expected Award / Decision Date"), errors="coerce")
        sla = assignment_status(deal_id, pending_role) if pending_role else {}
        if sla.get("Due At"):
            deadline = pd.to_datetime(sla["Due At"], errors="coerce")
        account = customer_record_for_deal(deal, data)
        records.append(
            {
                "Deal ID": deal_id,
                "Deal": deal.get("Deal Title", deal_id),
                "Sold-To Customer": deal.get("Sold-To Customer Name", deal.get("Customer Name", "")),
                "End Account": deal.get("End Account Name", deal.get("Customer Name", "")),
                "Main Product": products[0] if products else "",
                "All Products": products,
                "Requested Discount %": pct(summary.get("discount_pct")),
                "Resulting Gross Margin %": landing_margin_display(summary),
                "Risk": deal.get("KAM Risk Assessment", deal.get("Intake Risk", "")),
                "Decision Due": deadline.strftime("%Y-%m-%d") if not pd.isna(deadline) else "",
                "Decision Due Date": deadline,
                "Status": deal.get("Status", ""),
                "Customer Type": deal.get("Customer Type", deal.get("Segment", "")),
                "Sales Owner": deal.get("Sales Owner", ""),
                "Reviewer Roles": required_roles,
                "Pending Role": pending_role,
                "Pending Roles": pending_roles,
                "Requested Value": safe_float(summary.get("total_proposed")),
                "Strategic Account": str(account.get("Strategic Account", "")).lower() == "yes",
            }
        )
    cockpit = pd.DataFrame(records)
    role = current_role()
    if cockpit.empty:
        render_landing_kpis(cockpit, role)
        st.info("No active deals are currently awaiting this user's review." if list_mode == "Active" else "No archived deals are visible to this user.")
        return

    render_landing_kpis(cockpit, role)

    product_options = sorted({product for values in cockpit["All Products"] for product in values})
    with st.expander("Search & Filters", expanded=False):
        filters = st.columns([1.25, 1.15, 0.8, 1, 1.15])
        selected_products = filters[0].multiselect("Product", product_options)
        selected_types = filters[1].multiselect("Customer Type", sorted(cockpit["Customer Type"].dropna().astype(str).unique()))
        selected_risks = filters[2].multiselect("Risk", sorted(cockpit["Risk"].dropna().astype(str).unique()))
        selected_owners = filters[3].multiselect("Sales Owner", sorted(cockpit["Sales Owner"].dropna().astype(str).unique()))
        selected_reviewers = filters[4].multiselect("Reviewer Role", ACTIONABLE_APPROVAL_ROLES)

    filtered = cockpit.copy()
    if selected_products:
        filtered = filtered[filtered["All Products"].apply(lambda values: bool(set(values).intersection(selected_products)))]
    if selected_types:
        filtered = filtered[filtered["Customer Type"].isin(selected_types)]
    if selected_risks:
        filtered = filtered[filtered["Risk"].isin(selected_risks)]
    if selected_owners:
        filtered = filtered[filtered["Sales Owner"].isin(selected_owners)]
    if selected_reviewers:
        filtered = filtered[filtered["Reviewer Roles"].apply(lambda values: bool(set(values).intersection(selected_reviewers)))]

    if filtered.empty:
        st.info("No deals match the current filters.")
        return

    st.caption("Select a deal to preview the commercial, financial and supply context.")
    display_cols = [
        "Deal ID",
        "Deal",
        "Sold-To Customer",
        "End Account",
        "Main Product",
        "Requested Discount %",
        "Resulting Gross Margin %",
        "Risk",
        "Decision Due",
        "Status",
    ]
    display_df = filtered[display_cols].reset_index(drop=True)
    table_event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"deal_request_list_table_{st.session_state.deal_list_table_revision}",
        column_config={
            "Deal ID": None,
            "Deal": st.column_config.TextColumn("Deal", width="large"),
            "Sold-To Customer": st.column_config.TextColumn("Sold-To Customer", width="medium"),
            "End Account": st.column_config.TextColumn("End Account", width="medium"),
            "Main Product": st.column_config.TextColumn("Main Product", width="medium"),
            "Requested Discount %": st.column_config.TextColumn("Requested Discount %", width="small"),
            "Resulting Gross Margin %": st.column_config.TextColumn("Resulting Gross Margin %", width="small"),
            "Risk": st.column_config.TextColumn("Risk", width="small"),
            "Decision Due": st.column_config.TextColumn("Decision Due", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )
    table_selected = get_selected_dataframe_deal_id(table_event, display_df)
    if table_selected:
        st.session_state.deal_list_selected_deal_id = table_selected
        st.session_state.selected_deal_id = table_selected
    else:
        st.session_state.deal_list_selected_deal_id = None

    if table_selected:
        context = contexts.get(table_selected) or build_deal_context(data, table_selected)
        if context:
            render_inline_deal_preview(context, compact=True)
            actions = st.columns([1, 5])
            if actions[0].button("Open Deal Detail", type="primary"):
                navigate_to_deal_detail(table_selected, "deal request list row selection")
    else:
        st.caption("Use the selection control at the left of a row to open its preview.")


def build_default_line(data: dict[str, pd.DataFrame], sku: str | None = None) -> dict:
    products = data["products"]
    if products.empty:
        return {}
    prod = products.iloc[0] if not sku else products[products["SKU"].eq(sku)].iloc[0]
    prod_dict = prod.to_dict()
    list_price = product_list_price(prod_dict)
    gross_price = product_gross_price(prod_dict)
    target = gross_price * 0.9
    return {
        "SKU": prod["SKU"],
        "Product Name": commercial_product_name(str(prod["SKU"]), str(prod.get("Product Name", ""))),
        "Quantity": 1,
        "Unit List Price": round(list_price, 2),
        "Unit Gross Price": round(gross_price, 2),
        "Gross Price": round(gross_price, 2),
        "Requested Net Price": round(target, 2),
        "Requested Total Discount %": 0.10,
        "Requested Discount %": 0.10,
        "Floor Price": round(list_price * 0.72, 2),
        "Guidance Price": round(list_price * 0.84, 2),
        "Walk-away Price": round(list_price * 0.68, 2),
        "Proposed Unit Price": round(target, 2),
        "Requested Delivery Date": date.today() + timedelta(days=int(prod.get("Lead Time Days", 14) or 14)),
        "Gross Revenue": round(gross_price, 2),
        "Proposed Net Revenue": round(target, 2),
        "Line Commercial Rationale": "",
    }


def page_new_deal(data: dict[str, pd.DataFrame]) -> None:
    render_header("New Deal Intake", "Create a draft or submit a commercial deal request.")
    review_comment = str(st.session_state.get("editing_review_comment", "")).strip()
    original_status = str(st.session_state.get("editing_deal_original_status", "")).strip()
    if original_status == "Changes Requested":
        st.warning(
            "Changes requested by reviewer:\n\n"
            f"{review_comment or 'Review the requested changes before resubmitting.'}"
        )
    customers = data["customers"]
    products = data["products"]
    if customers.empty or products.empty:
        st.error("Customer and product reference data are required.")
        return

    if st.session_state.draft_lines is None:
        st.session_state.draft_lines = pd.DataFrame([build_default_line(data, "RX-ONC-100")])
    if st.session_state.line_editor_rows is None:
        editor_seed = st.session_state.draft_lines.copy()
        if "Requested Total Discount %" in editor_seed:
            editor_seed["Requested Total Discount %"] = pd.to_numeric(
                editor_seed["Requested Total Discount %"], errors="coerce"
            ).fillna(0) * 100
        st.session_state.line_editor_rows = editor_seed
    st.session_state.deal_edit_active = True

    tabs = st.tabs(["Context", "Commercials", "Customer & Market", "Financial Impact", "Approval Recommendation"])

    with tabs[0]:
        st.subheader("Deal Context")
        customer_name = st.selectbox(
            "Customer",
            customers["Customer Name"].tolist(),
            key="form_customer",
            on_change=sync_context_customer_defaults,
        )
        customer = customers[customers["Customer Name"].eq(customer_name)].iloc[0].to_dict()
        delivery_model = st.radio(
            "Delivery Model",
            ["Direct customer delivery", "Distributor delivery to end account"],
            horizontal=True,
            key="form_delivery_model",
            on_change=sync_delivery_model,
        )
        if "form_ship_to" not in st.session_state:
            st.session_state.form_ship_to = customer_name
        if delivery_model == "Direct customer delivery":
            st.session_state.form_ship_to = customer_name
        ship_to_account = st.text_input(
            "End Account Name",
            key="form_ship_to",
            disabled=delivery_model == "Direct customer delivery",
        )
        deal_cols = st.columns(2)
        if "form_title" not in st.session_state:
            st.session_state.form_title = f"{customer_name} - {date.today().isoformat()}"
        deal_title = deal_cols[0].text_input("Deal Title", key="form_title")
        deal_type = deal_cols[0].selectbox(
            "Deal Type",
            [
                "New Account Launch",
                "Tender Bid",
                "Contract Renewal",
                "Competitive Defense",
                "Strategic Opportunity",
            ],
            key="form_type",
        )
        region = str(customer.get("Region", "Region A"))
        deal_cols[1].text_input("Region", value=region, disabled=True)
        if deal_type == "Tender Bid":
            tender_cols = st.columns(4)
            tender_name = tender_cols[0].text_input("Tender Name", value=f"{customer_name} access tender", key="form_tender_name")
            tender_id = tender_cols[1].text_input("Tender ID", value=f"TND-{date.today().year}-{str(customer.get('Customer ID', '000'))[-3:]}", key="form_tender_id")
            tender_closing = tender_cols[2].date_input("Submission Deadline", value=date.today() + timedelta(days=28), key="form_tender_closing")
            award_date = tender_cols[3].date_input("Award Date", value=date.today() + timedelta(days=60), key="form_award_date")
            tender_mechanism = st.selectbox("Tender Mechanism", ["Winner takes all", "Multi-award", "Framework agreement", "Unknown"], key="form_tender_mechanism")
        else:
            tender_name = st.session_state.get("form_tender_name", "")
            tender_id = st.session_state.get("form_tender_id", "")
            tender_closing = st.session_state.get("form_tender_closing", None)
            award_date = st.session_state.get("form_award_date", None)
            tender_mechanism = st.session_state.get("form_tender_mechanism", "")
        owner_cols = st.columns(4)
        kam_users = [name for name, role in PERSONAS.items() if is_kam_role(role)]
        default_owner = current_persona() if current_persona() in kam_users else kam_users[0]
        sales_owner = owner_cols[0].selectbox("Sales Owner", kam_users, index=kam_users.index(default_owner), key="form_owner")
        sales_manager = owner_cols[1].selectbox("Sales Manager", list(SALES_MANAGER_TEAMS.keys()), key="form_manager")
        target_close = owner_cols[2].date_input("Commercial Decision Deadline", value=date.today() + timedelta(days=45), key="form_close")
        effective_date = owner_cols[3].date_input("Requested Delivery Start", value=date.today() + timedelta(days=60), key="form_effective")
        requested_delivery_end = st.date_input("Requested Delivery End", value=date.today() + timedelta(days=120), key="form_delivery_end")
        st.divider()
        cols = st.columns(4)
        cols[0].metric("Customer Type", customer_type(customer))
        cols[1].metric("Strategic", customer.get("Strategic Account", ""))
        cols[2].metric("Region", st.session_state.get("form_region", customer.get("Region", "")))
        cols[3].metric("Credit", customer.get("Credit Status", ""))
        st.info(str(customer.get("Account Notes", "")))
        if safe_float(customer.get("Overdue AR", 0)) > 0:
            st.warning(f"Credit warning: overdue receivables are {money(customer.get('Overdue AR'))}. Finance review is mandatory.")
        if customer.get("Credit Status") == "Watch":
            st.warning("Credit status is Watch. Finance review is likely.")
        if customer.get("Credit Status") == "Hold":
            st.error("Credit status is Hold. Finance review is mandatory before final approval.")

    with tabs[1]:
        st.subheader("Commercial Terms")
        c1, c2, c3 = st.columns(3)
        payment_terms = c1.selectbox("Payment Terms", ["Net 30", "Net 45", "Net 60", "Net 90", "Custom"], key="form_terms")
        contract_months = c2.number_input("Contract Duration Months", min_value=1, max_value=72, value=24, step=1, key="form_contract")
        billing = c3.selectbox("Billing Frequency", ["Annual", "Quarterly", "Monthly", "Milestone"], key="form_billing")
        special_terms = st.checkbox("Special terms requested", key="form_special")
        if special_terms:
            special_desc = st.text_area("Special Terms Description", key="form_special_desc")
            if not str(special_desc).strip():
                st.warning("Special Terms Description is required when special terms are requested.")
        else:
            special_desc = ""
            st.session_state.form_special_desc = ""
        st.divider()
        st.subheader("Visibility")
        visibility = st.radio(
            "Visibility",
            ["Confidential", "Bid Only", "Pricing Confidential", "Public"],
            horizontal=True,
            key="form_visibility",
        )
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
        st.caption(
            "Requested Total Discount % represents the full customer-facing discount from List Price. "
            "Any standard contractual discounts or rebates are considered part of the requested total discount."
        )
        line_actions = st.columns([1, 6])
        if line_actions[0].button("+ Add SKU", key="add_sku_line"):
            current_rows = st.session_state.line_editor_rows.copy()
            new_line = build_default_line(data, products.iloc[0]["SKU"])
            new_line["Requested Total Discount %"] = safe_float(new_line.get("Requested Total Discount %")) * 100
            st.session_state.line_editor_rows = pd.concat([current_rows, pd.DataFrame([new_line])], ignore_index=True)
            st.session_state.line_editor_revision += 1
            st.rerun()
        editor_source = st.session_state.line_editor_rows.copy()
        editor_config = {
            "SKU": st.column_config.SelectboxColumn("SKU", options=products["SKU"].tolist(), required=True),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1),
            "Requested Total Discount %": st.column_config.NumberColumn(
                "Requested Total Discount %",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                format="%.1f%%",
            ),
        }
        editable_line_cols = [
            "SKU",
            "Quantity",
            "Requested Total Discount %",
        ]
        editor_key = f"line_editor_{st.session_state.line_editor_revision}"
        edited_rows = st.data_editor(
            editor_source[[col for col in editable_line_cols if col in editor_source]],
            num_rows="dynamic",
            use_container_width=True,
            column_config=editor_config,
            hide_index=True,
            key=editor_key,
        )
        st.session_state.line_editor_rows = edited_rows.copy()
        calculation_rows = st.session_state.line_editor_rows.copy()
        calculation_rows["Requested Total Discount %"] = pd.to_numeric(
            calculation_rows["Requested Total Discount %"], errors="coerce"
        ).fillna(0) / 100
        st.session_state.draft_lines = ensure_commercial_line_columns(calculation_rows, data)
        calc_lines = normalize_lines(st.session_state.draft_lines, data)
        summary = summarize_lines(calc_lines)
        metric_cols = st.columns(5)
        metric_cols[0].metric("Total List Value", money(summary["total_list"]))
        metric_cols[1].metric("Total Gross Value", money(summary["total_gross"]))
        metric_cols[2].metric("Total Requested Net Value", money(summary["total_proposed"]))
        metric_cols[3].metric("Weighted Discount %", pct(summary["discount_pct"]))
        metric_cols[4].metric("Estimated Gross Margin %", margin_display(summary))
        if not calc_lines.empty:
            view_cols = [
                "SKU",
                "Product Name",
                "Product Category",
                "Quantity",
                "Unit List Price",
                "Unit Gross Price",
                "Base Discount %",
                "Current Net Price",
                "Requested Total Discount %",
                "Requested Net Price",
                "Gross Revenue",
                "Proposed Net Revenue",
                "Floor Price",
                "Guidance Price",
                "Walk-away Price",
                "Target Gross Margin %",
                "Finance Director Trigger Margin",
                "General Manager Trigger Margin",
            ]
            view = calc_lines[[col for col in view_cols if col in calc_lines]].copy()
            view = view.rename(columns={"Unit List Price": "List Price"})
            if "Requested Discount %" in view:
                view["Requested Discount %"] = view["Requested Discount %"] * 100
            st.dataframe(mask_sensitive_dataframe(view), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Customer Health")
        health = demo_customer_health(customer, customer_name)
        health_cols = st.columns(5)
        health_cols[0].metric("Last 12M Revenue", money(health["Revenue last 12 months"]))
        health_cols[1].metric("Oldest Overdue Days", f"{safe_float(customer.get('Oldest Overdue Days', 0)):,.0f}")
        health_cols[2].metric("Average net price last 12 months", money(health["Average net price last 12 months"]))
        health_cols[3].metric("Last 12M Gross Margin", sensitive_money("Gross Profit", health["Gross margin last 12 months"]))
        health_cols[4].metric("Last 12M Gross Margin %", sensitive_pct("Gross Margin %", health["Gross margin %"]))
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
                default=["NovaThera"] if st.session_state.get("form_type") == "Tender Bid" else [],
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
        st.subheader("KAM Risk Assessment")
        risk_cols = st.columns(2)
        kam_risk_assessment = risk_cols[0].selectbox("KAM Risk Assessment", KAM_RISK_LEVELS, index=1, key="form_kam_risk_assessment")
        risk_reason = risk_cols[1].selectbox("Risk Reason", RISK_REASON_VALUES, key="form_risk_reason")

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
        "Sold-To Customer ID": customer.get("Customer ID"),
        "Sold-To Customer Name": customer_name,
        "End Account ID": customer.get("Customer ID"),
        "End Account Name": st.session_state.get("form_ship_to", customer_name),
        "Ship-to Account": st.session_state.get("form_ship_to", ""),
        "Bill-to Account": customer_name,
        "Delivery Model": st.session_state.get("form_delivery_model", "Direct customer delivery"),
        "Purpose": st.session_state.get("form_type", ""),
        "Tender Name": st.session_state.get("form_tender_name", ""),
        "Tender ID": st.session_state.get("form_tender_id", ""),
        "Tender Closing Date": st.session_state.get("form_tender_closing", ""),
        "Submission Deadline": st.session_state.get("form_tender_closing", ""),
        "Award Date": st.session_state.get("form_award_date", ""),
        "Tender Mechanism": st.session_state.get("form_tender_mechanism", ""),
        "Quantity at Risk": st.session_state.get("form_quantity_at_risk", 0),
        "Remaining Shelf Life": st.session_state.get("form_shelf_life", 0),
        "Inventory Value at Risk": st.session_state.get("form_inventory_value_at_risk", 0.0),
        "Region": region,
        "Segment": customer_type(customer),
        "Customer Type": customer_type(customer),
        "Account Type": customer_type(customer),
        "Channel": customer_type(customer),
        "Target Close Date": st.session_state.get("form_close", target_close),
        "Commercial Decision Deadline": st.session_state.get("form_close", target_close),
        "Requested Effective Date": st.session_state.get("form_effective", effective_date),
        "Expected Award / Decision Date": st.session_state.get("form_close", target_close),
        "Requested Delivery Start": st.session_state.get("form_effective", effective_date),
        "Requested Delivery End": st.session_state.get("form_delivery_end", requested_delivery_end),
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
        "Included In Latest Financial Plan": st.session_state.get("form_included_plan", "Yes"),
        "Customer Risk Flag": health.get("Risk Flag", ""),
        "Revenue L12M": health.get("Revenue last 12 months", 0),
        "Units L12M": health.get("Units last 12 months", 0),
        "Average Net Price L12M": health.get("Average net price last 12 months", 0),
        "Gross Margin L12M": health.get("Gross margin last 12 months", 0),
        "Gross Margin % L12M": health.get("Gross margin %", 0),
        "Total AR": health.get("Total AR", 0),
        "Current AR": health.get("Current AR", 0),
        "Overdue AR": health.get("Overdue AR", 0),
        "Oldest Overdue Days": customer.get("Oldest Overdue Days", 0),
        "Credit Status": customer.get("Credit Status", ""),
        "Expected Competitors": ", ".join(st.session_state.get("form_expected_competitors", [])),
        "Competitor Type": st.session_state.get("form_competitor_type", ""),
        "Expected Bid Range": st.session_state.get("form_expected_bid_range", ""),
        "Customer Bidding Strategy": st.session_state.get("form_customer_bidding_strategy", ""),
        "Margin Retention Assumption": st.session_state.get("form_margin_retention", 0),
        "Reconciliation Type": st.session_state.get("form_reconciliation_type", "None"),
        "Reconciliation Description": st.session_state.get("form_reconciliation_description", ""),
        "Business Justification": st.session_state.get("form_justification", ""),
        "Strategic Rationale": st.session_state.get("form_justification", ""),
        "KAM Risk Assessment": st.session_state.get("form_kam_risk_assessment", "Medium"),
        "Risk Reason": st.session_state.get("form_risk_reason", "Competitor price pressure"),
        "Competitive Situation": st.session_state.get("form_competitive", ""),
        "Known Competitor": st.session_state.get("form_competitor", ""),
        "Sales Owner": st.session_state.get("form_owner", sales_owner),
        "Sales Manager": st.session_state.get("form_manager", sales_manager),
    }
    calc_lines = normalize_lines(st.session_state.draft_lines, data)
    summary = summarize_lines(calc_lines)
    errors, warnings = validate_deal(header, calc_lines, data)
    if header.get("Special Terms Requested") and not str(header.get("Special Terms Description", "")).strip():
        errors.append("Special Terms Description is required when special terms are requested.")
    route_df = route_preview(header, calc_lines, summary, data)
    st.session_state.current_draft_snapshot = {
        "header": header,
        "lines": calc_lines.copy(),
        "summary": summary,
        "route_df": route_df.copy(),
    }
    system_score = system_risk_score(header, summary, data, calc_lines)
    if kam_risk_exceeds_system_score(header.get("KAM Risk Assessment"), system_score):
        warnings.append("KAM risk assessment exceeds system score; additional rationale required.")

    with tabs[3]:
        st.subheader("Financial Impact")
        sensitive_data_note()
        included_value = st.selectbox("Included In Latest Financial Plan", ["Yes", "No"], key="form_included_plan")
        included_in_plan = included_value == "Yes"
        plan_df = plan_impact_analysis(data, calc_lines, header["Region"], header["Segment"], customer_name)
        incremental_df = incremental_opportunity_analysis(data, calc_lines, customer_name, header["Channel"])
        proposed_revenue = safe_float(summary["total_proposed"])
        proposed_gp = safe_float(((calc_lines["Proposed Unit Price"] - calc_lines["Unit Cost"]) * calc_lines["Quantity"]).sum()) if not calc_lines.empty else 0
        proposed_margin = None if proposed_revenue <= 0 else proposed_gp / proposed_revenue
        proposed_net = 0 if calc_lines.empty or safe_float(calc_lines["Quantity"].sum()) <= 0 else safe_float((calc_lines["Proposed Unit Price"] * calc_lines["Quantity"]).sum()) / safe_float(calc_lines["Quantity"].sum())

        if included_in_plan:
            planned_revenue = safe_float(plan_df["Planned Revenue"].sum()) if not plan_df.empty else 0
            planned_gp = safe_float(plan_df["Planned Gross Profit"].sum()) if not plan_df.empty else 0
            price_variance = safe_float(plan_df["Price Variance"].sum()) if not plan_df.empty else 0
            volume_variance = safe_float(plan_df["Volume Variance"].sum()) if not plan_df.empty else 0
            revenue_variance = price_variance + volume_variance
            gp_variance = proposed_gp - planned_gp
            planned_net = 0 if plan_df.empty or safe_float(plan_df["Planned Quantity"].sum()) <= 0 else safe_float((plan_df["Planned Net Price"] * plan_df["Planned Quantity"]).sum()) / safe_float(plan_df["Planned Quantity"].sum())
            customer_avg_net = safe_float(plan_df["Customer Avg Net Price 12M"].dropna().mean()) if not plan_df.empty and "Customer Avg Net Price 12M" in plan_df else 0
            product_avg_net = safe_float(plan_df["Product Avg Net Price 12M"].dropna().mean()) if not plan_df.empty and "Product Avg Net Price 12M" in plan_df else 0
            planned_margin = None if planned_revenue <= 0 else planned_gp / planned_revenue

            st.info("Included in the latest financial plan: price variance is calculated as (Requested Net Price - Planned Net Price) x Planned Volume.")
            kpis = st.columns(5)
            kpis[0].metric("Planned Revenue", sensitive_money("Planned Revenue", planned_revenue))
            kpis[1].metric("Proposed Revenue", sensitive_money("Proposed Revenue", proposed_revenue), delta=sensitive_money("Revenue Variance", revenue_variance))
            kpis[2].metric("Planned Gross Profit", sensitive_money("Planned Gross Profit", planned_gp))
            kpis[3].metric("Proposed Gross Profit", sensitive_money("Proposed Gross Profit", proposed_gp))
            kpis[4].metric("Gross Profit Variance", sensitive_money("Gross Profit Variance", gp_variance))
            margin_cols = st.columns(5)
            margin_cols[0].metric("Requested Net Price", money(proposed_net))
            margin_cols[1].metric("Customer Avg Net Price 12M", money(customer_avg_net))
            margin_cols[2].metric("Product Avg Net Price 12M", money(product_avg_net))
            margin_cols[3].metric("Planned Net Price", sensitive_money("Planned Net Price", planned_net))
            margin_cols[4].metric("Price Variance vs Plan", sensitive_money("Price Variance", price_variance))

            st.markdown("**Revenue variance bridge**")
            bridge_df = pd.DataFrame(
                [
                    {"Component": "Price Variance", "Value": price_variance},
                    {"Component": "Volume Variance", "Value": volume_variance},
                    {"Component": "Revenue Variance", "Value": revenue_variance},
                    {"Component": "Gross Profit Variance", "Value": gp_variance},
                ]
            )
            if can_view_sensitive_field(current_role(), "Revenue Variance"):
                st.bar_chart(bridge_df.set_index("Component"))
            else:
                st.info("Variance visualization is visible to Finance/Pricing only.")
            st.dataframe(
                mask_sensitive_dataframe(plan_df[
                    [
                        "SKU",
                        "Product",
                        "Requested Net Price",
                        "Customer Avg Net Price 12M",
                        "Product Avg Net Price 12M",
                        "Planned Net Price",
                        "Proposed Net Price",
                        "Planned Quantity",
                        "New Quantity",
                        "Planned Revenue",
                        "Proposed Revenue",
                        "Price Variance vs Plan",
                        "Volume Variance",
                        "Revenue Variance",
                        "Planned Gross Profit",
                        "Proposed Gross Profit",
                        "Gross Profit Variance",
                        "Planned Margin %",
                        "Proposed Margin %",
                    ]
                ] if not plan_df.empty else plan_df),
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

            st.info("Incremental volume not included in the latest financial plan: no plan price variance is applied.")
            kpis = st.columns(5)
            kpis[0].metric("Incremental Revenue", money(incremental_revenue))
            kpis[1].metric("Incremental Gross Profit", sensitive_money("Gross Profit", incremental_gp))
            kpis[2].metric("Proposed Margin %", margin_value_display(proposed_margin, summary["weighted_target_margin"]))
            kpis[3].metric("Requested Net Price", money(proposed_net))
            kpis[4].metric("Customer Avg Net Price 12M", money(hist_price))
            benchmark_cols = st.columns(3)
            benchmark_cols[0].metric("Price Difference vs Historical Average %", pct(price_vs_hist))
            product_avg_net = safe_float(incremental_df["Product Avg Net Price 12M"].dropna().mean()) if not incremental_df.empty and "Product Avg Net Price 12M" in incremental_df else 0
            benchmark_cols[1].metric("Product Avg Net Price 12M", money(product_avg_net))
            benchmark_cols[2].metric("Margin Difference vs Historical Margin %", sensitive_pct("Margin Difference vs Historical Margin %", margin_difference))

            st.markdown("**Incremental economics bridge**")
            bridge_df = pd.DataFrame(
                [
                    {"Component": "Incremental Revenue", "Value": incremental_revenue},
                    {"Component": "Incremental Gross Profit", "Value": incremental_gp},
                ]
            )
            if can_view_sensitive_field(current_role(), "Gross Profit"):
                st.bar_chart(bridge_df.set_index("Component"))
            else:
                st.info("Gross profit visualization is visible to Finance/Pricing only.")
            display_cols = [
                "SKU",
                "Product",
                "Requested Net Price",
                "Customer Avg Net Price 12M",
                "Product Avg Net Price 12M",
                "Incremental Revenue",
                "Incremental Gross Profit",
                "Price vs Customer Avg Net Price 12M %",
                "Price vs Product Avg Net Price 12M %",
                "Historical Margin %",
                "Proposed Margin %",
                "Margin Difference vs Historical Margin %",
            ]
            st.dataframe(mask_sensitive_dataframe(incremental_df[[col for col in display_cols if col in incremental_df]]), use_container_width=True, hide_index=True)

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
        plan_df = plan_impact_analysis(data, calc_lines, header["Region"], header["Segment"], customer_name)
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
                <p>Decision score: <strong>{total_score}/100</strong> | Proposed value: <strong>{money(summary["total_proposed"])}</strong> | Gross profit impact: <strong>{sensitive_money("Gross Profit Variance", gp_impact["Gross Profit Variance"])}</strong></p>
                <p>{executive["Key Reason"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sensitive_data_note()

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
            st.dataframe(mask_sensitive_dataframe(route_dashboard), use_container_width=True, hide_index=True)

        with st.expander("Commercial summary"):
            st.write(f"Customer: **{customer_name}**")
            st.write(f"Plan inclusion: **{included_value}**")
            st.write(f"Rationale: {header['Business Justification'] or 'Not provided'}")
            st.caption(score_rationale)
            st.dataframe(commercial_line_items_view(calc_lines), use_container_width=True, hide_index=True)

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
        submit_label = "Resubmit Deal" if original_status == "Changes Requested" else "Submit Deal"
        if b.button(submit_label, type="primary", disabled=bool(errors)):
            deal_id = save_runtime_deal(header, calc_lines, summary, route_df, status="Submitted", recommendation=recommendation)
            if original_status == "Changes Requested":
                add_audit(
                    deal_id,
                    "Deal resubmitted",
                    details="Submitting KAM updated and resubmitted the deal. Approval progress restarted with Sales Manager review.",
                    decision="Resubmit",
                    comment=review_comment,
                    previous_status="Changes Requested",
                    new_status="Submitted",
                )
            else:
                add_audit(deal_id, "Deal submitted", details=f"Recommendation: {recommendation}")
            navigate_to_deal_detail(deal_id, "new deal intake submission")


def save_runtime_deal(header: dict, lines: pd.DataFrame, summary: dict, route_df: pd.DataFrame, status: str, recommendation: str) -> str:
    editing_deal_id = str(st.session_state.get("editing_deal_id") or "")
    deal_id = editing_deal_id or f"DEAL-S-{len(st.session_state.runtime_deals) + 1:04d}"
    workflow_status = "Pending Sales Manager" if status == "Submitted" else status
    risk_assessment = header.get("KAM Risk Assessment", "Medium")
    previous_record: dict = {}
    if editing_deal_id:
        existing = combined_deals(load_demo_data())
        match = existing[existing["Deal ID"].astype(str).eq(deal_id)]
        if not match.empty:
            previous_record = match.iloc[-1].to_dict()
    returned_for_changes = status == "Draft" and (
        str(st.session_state.get("editing_deal_original_status", "")).strip() == "Changes Requested"
        or str(previous_record.get("Returned For Changes", "False")).lower() in {"true", "yes", "1"}
    )
    record = {
            "Deal ID": deal_id,
            "Deal Title": header["Deal Title"],
            "Sold-To Customer ID": header.get("Sold-To Customer ID", header["Customer ID"]),
            "Sold-To Customer Name": header.get("Sold-To Customer Name", header["Customer Name"]),
            "End Account ID": header.get("End Account ID", header["Customer ID"]),
            "End Account Name": header.get("End Account Name", header["Customer Name"]),
            "Customer ID": header["Customer ID"],
            "Customer Name": header["Customer Name"],
            "Ship-to Account": header.get("Ship-to Account", ""),
            "Bill-to Account": header.get("Bill-to Account", ""),
            "Purpose": header.get("Purpose", ""),
            "Delivery Model": header.get("Delivery Model", "Direct customer delivery"),
            "Tender Name": header.get("Tender Name", ""),
            "Tender ID": header.get("Tender ID", ""),
            "Tender Mechanism": header.get("Tender Mechanism", ""),
            "Submission Deadline": str(header.get("Submission Deadline", "")),
            "Award Date": str(header.get("Award Date", "")),
            "Visibility": header.get("Visibility", ""),
            "Publication Source": header.get("Publication Source", ""),
            "Publication URL": header.get("Publication URL", ""),
            "Access Description": header.get("Access Description", ""),
            "Customer Risk Flag": header.get("Customer Risk Flag", ""),
            "Credit Status": header.get("Credit Status", ""),
            "Revenue L12M": header.get("Revenue L12M", 0),
            "Current AR": header.get("Current AR", 0),
            "Overdue AR": header.get("Overdue AR", 0),
            "Oldest Overdue Days": header.get("Oldest Overdue Days", 0),
            "Competitor Type": header.get("Competitor Type", ""),
            "Expected Competitors": header.get("Expected Competitors", ""),
            "Reconciliation Type": header.get("Reconciliation Type", "None"),
            "Deal Type": header["Deal Type"],
            "Region": header["Region"],
            "Customer Type": header.get("Customer Type", header["Segment"]),
            "Segment": header.get("Customer Type", header["Segment"]),
            "Sales Owner": header["Sales Owner"],
            "Sales Manager": header["Sales Manager"],
            "Status": workflow_status,
            "Returned For Changes": returned_for_changes,
            "Target Close Date": str(header["Target Close Date"]),
            "Expected Award / Decision Date": str(header.get("Expected Award / Decision Date", header["Target Close Date"])),
            "Requested Delivery Start": str(header.get("Requested Delivery Start", header.get("Requested Effective Date", ""))),
            "Requested Delivery End": str(header.get("Requested Delivery End", "")),
            "Payment Terms": header["Payment Terms"],
            "Contract Months": header["Contract Months"],
            "Billing Frequency": header.get("Billing Frequency", "Annual"),
            "Special Terms Requested": header.get("Special Terms Requested", False),
            "Special Terms Description": header.get("Special Terms Description", ""),
            "Strategic Rationale": header["Business Justification"],
            "KAM Risk Assessment": risk_assessment,
            "Risk Reason": header.get("Risk Reason", "Generated from configured approval route and commercial risk signals."),
            "Intake Risk": risk_assessment,
            "Channel": header["Channel"],
            "Included_In_Latest_Financial_Plan": header.get("Included_In_Latest_Financial_Plan", "Yes"),
            "Included In Latest Financial Plan": header.get("Included In Latest Financial Plan", header.get("Included_In_Latest_Financial_Plan", "Yes")),
            "Expected Route": approval_route_text(route_df),
            "Total Proposed": summary["total_proposed"],
            "Discount %": summary["discount_pct"],
            "Recommendation": recommendation,
        }
    for key in [
        "Last Decision",
        "Last Decision Comment",
        "Last Decision Timestamp",
        "Last Decision Actor",
        "Last Decision Role",
        "Last Approval Step",
        "Last Requested Change Comment",
    ]:
        if key in previous_record:
            record[key] = previous_record[key]
    existing_index = next(
        (index for index, item in enumerate(st.session_state.runtime_deals) if str(item.get("Deal ID", "")) == deal_id),
        None,
    )
    if existing_index is None:
        st.session_state.runtime_deals.append(record)
    else:
        st.session_state.runtime_deals[existing_index] = record
    st.session_state.deal_status_overrides.pop(deal_id, None)
    st.session_state.runtime_lines = [
        item for item in st.session_state.runtime_lines if str(item.get("Deal ID", "")) != deal_id
    ]
    for i, (_, line) in enumerate(lines.iterrows(), start=1):
        item = line.to_dict()
        item["Deal ID"] = deal_id
        item["Line #"] = i
        st.session_state.runtime_lines.append(item)
    add_audit(deal_id, "Deal draft saved" if status == "Draft" else "Deal created", details=f"Status: {workflow_status}")
    if status == "Submitted":
        st.session_state.deal_approval_steps[deal_id] = []
        assignments = st.session_state.get("approval_assignments", {})
        st.session_state.approval_assignments = {
            key: value
            for key, value in assignments.items()
            if str(value.get("Deal ID", "")) != str(deal_id)
        }
        ensure_approval_assignments(deal_id, route_df, load_demo_data())
        st.session_state.deal_edit_active = False
        st.session_state.editing_deal_id = None
    return deal_id


def credit_values_visible(role: str | None = None) -> bool:
    return (role or current_role()) in {"Finance Director", "General Manager", "System Administrator"}


def strategic_account_context(customer: dict, data: dict[str, pd.DataFrame]) -> str:
    revenue = safe_float(customer.get("Last 12M Revenue"))
    visible_customers = data.get("customers", pd.DataFrame())
    portfolio = safe_float(pd.to_numeric(visible_customers.get("Last 12M Revenue", pd.Series(dtype=float)), errors="coerce").sum())
    share = revenue / portfolio if portfolio > 0 else 0
    return f"Last 12M Revenue: {money(revenue)} | Share of portfolio: {pct(share)}"


def render_customer_risk_strip(customer: dict, data: dict[str, pd.DataFrame]) -> None:
    strategic = str(customer.get("Strategic Account", "No"))
    st.caption(
        "Strategic Account: An account flagged as strategically important due to revenue scale, growth potential, "
        "market access relevance, or executive priority."
    )
    if credit_values_visible():
        values = [
            ("Customer Type", customer_type(customer)),
            ("Strategic Account", strategic),
            ("Credit Status", customer.get("Credit Status", "")),
            ("Current AR", money(customer.get("Current AR"))),
            ("Overdue AR", money(customer.get("Overdue AR"))),
            ("Oldest Overdue Days", f"{safe_float(customer.get('Oldest Overdue Days')):,.0f}"),
            ("Last 12M Revenue", money(customer.get("Last 12M Revenue"))),
        ]
        strip = st.columns(len(values))
        for column, (label, value) in zip(strip, values):
            column.metric(label, value)
    else:
        strip = st.columns(2)
        strip[0].metric("Credit Status", str(customer.get("Credit Status", "")))
        warning = "Credit warning" if str(customer.get("Credit Status", "")) == "Hold" or safe_float(customer.get("Overdue AR")) > 0 else "No credit warning"
        strip[1].metric("Credit Warning", warning)
    strategic_context = f" {strategic_account_context(customer, data)}" if credit_values_visible() else ""
    st.caption(f"Strategic Account: {strategic}.{strategic_context}")


def deal_decision_support(context: dict, data: dict[str, pd.DataFrame]) -> tuple[str, list[tuple[str, str]]]:
    reasons: list[tuple[str, str]] = []
    summary = context["summary"]
    deal = context["deal"]
    customer = context.get("customer", {})
    margin = safe_float(summary.get("margin_pct"))
    target = safe_float(summary.get("weighted_target_margin"))
    gm_floor = gm_trigger_margin(target)
    discount = safe_float(summary.get("discount_pct"))
    shortage = safe_float(context["inventory_df"].get("Inventory Shortage", pd.Series(dtype=float)).sum())
    credit_hold = str(customer.get("Credit Status", "")).strip() == "Hold"
    overdue_ar = safe_float(customer.get("Overdue AR"))

    if margin >= target:
        reasons.append(("positive", "Margin remains above the product approval threshold."))
    elif margin >= gm_floor:
        reasons.append(("attention", "Margin is below the product target and requires the configured finance review."))
    else:
        reasons.append(("critical", "Margin is below the General Manager approval threshold."))

    if discount <= 0.07:
        reasons.append(("positive", "Requested discount remains within the standard pricing tier."))
    else:
        reasons.append(("attention", "Requested discount exceeds the standard pricing tier and requires governance approval."))

    if shortage > 0:
        reasons.append(("attention", f"Available supply is short by {shortage:,.0f} units for the requested volume."))
    else:
        reasons.append(("positive", "Supply is available with no projected shortage."))

    if credit_hold:
        reasons.append(("critical", "Customer credit status is Hold and Finance approval is mandatory."))
    elif overdue_ar > 0:
        reasons.append(("attention", "Customer has overdue receivables and Finance approval is mandatory."))
    else:
        reasons.append(("positive", "No customer credit warning is currently identified."))

    end_account = str(deal.get("End Account Name", deal.get("Customer Name", "")))
    tender_df, signal_df = tender_competitor_summary(data, context["lines"], end_account, str(deal.get("Region", "")))
    if not tender_df.empty:
        wins = int(tender_df.get("Result", pd.Series(dtype=str)).astype(str).eq("Won").sum())
        precedent = "supports" if wins > 0 else "provides"
        reasons.append(("positive" if wins > 0 else "attention", f"Historical tender precedent {precedent} comparison with the requested price level."))
    elif not signal_df.empty:
        reasons.append(("attention", "External market signals should be considered in the commercial decision."))
    else:
        reasons.append(("attention", "No directly comparable tender precedent is available."))

    if margin <= 0:
        recommendation = "Reject"
    elif margin < gm_floor or credit_hold or shortage > 0:
        recommendation = "Request Changes"
    else:
        recommendation = "Approve"
    return recommendation, reasons


def approval_actor_for_role(deal_id: str, role: str, data: dict[str, pd.DataFrame]) -> str:
    for event in reversed(st.session_state.get("audit_events", [])):
        if (
            str(event.get("Deal ID", "")) == str(deal_id)
            and str(event.get("Approval Step", "")) == role
            and str(event.get("Decision", "")) == "Approve"
        ):
            return str(event.get("Actor", "")) or active_approver_for_role(data, role)
    return active_approver_for_role(data, role)


def approval_decision_events(deal_id: str) -> list[dict]:
    events = [
        event
        for event in st.session_state.get("audit_events", [])
        if str(event.get("Deal ID", "")) == str(deal_id)
        and str(event.get("Action", "")).startswith("Approval decision")
    ]
    return sorted(events, key=lambda event: str(event.get("Timestamp", "")))


def latest_review_event(deal: dict, deal_id: str) -> dict | None:
    commented_events = [event for event in approval_decision_events(deal_id) if str(event.get("Comment", "")).strip()]
    if commented_events:
        return commented_events[-1]
    comment = str(deal.get("Last Decision Comment", "")).strip()
    if not comment:
        return None
    return {
        "Role": deal.get("Last Decision Role", deal.get("Last Approval Step", "")),
        "Actor": deal.get("Last Decision Actor", ""),
        "Decision": deal.get("Last Decision", ""),
        "Timestamp": "",
        "Comment": comment,
    }


def render_latest_reviewer_comment(deal: dict, deal_id: str) -> None:
    event = latest_review_event(deal, deal_id)
    if not event:
        return
    role = str(event.get("Role", "")).strip() or "Reviewer"
    comment = str(event.get("Comment", "")).strip()
    with st.container(border=True):
        st.subheader("Latest Reviewer Comment")
        st.markdown(f"**{role}**")
        st.write(f'"{comment}"')


def business_approval_status(deal_status: str, pending_role: str) -> str:
    if pending_role:
        return f"Awaiting {pending_role} Review"
    if deal_status == "Changes Requested":
        return "Awaiting KAM Revision"
    if deal_status in {"Approved", "Final Approved"}:
        return "Approved"
    if deal_status == "Rejected":
        return "Rejected"
    return deal_status or "Not Submitted"


def business_deal_status(deal_status: str) -> str:
    if deal_status in ACTIVE_APPROVAL_STATUSES - {"Changes Requested"}:
        return "In Review"
    if deal_status == "Changes Requested":
        return "Changes Requested"
    if deal_status in {"Approved", "Final Approved"}:
        return "Approved"
    return deal_status or "Draft"


def render_approval_handoff(
    deal: dict,
    data: dict[str, pd.DataFrame],
    deal_id: str,
    deal_status: str,
    route_df: pd.DataFrame,
) -> None:
    roles = actionable_route_roles(route_df)
    completed = completed_approval_steps(deal_id)
    current_roles = current_required_approval_roles(deal_id, deal_status, route_df)
    approved_by = ", ".join(approval_actor_for_role(deal_id, role, data) for role in completed if role in roles)
    current_reviewer = ", ".join(active_approver_for_role(data, role) for role in current_roles)
    remaining = [role for role in roles if role not in completed and role not in current_roles]
    submitted_by = str(deal.get("Sales Owner", deal.get("Submitted By", ""))) or "Submitting KAM"

    handoff = st.columns(4)
    handoff[0].metric("Submitted by", submitted_by)
    handoff[1].metric("Approved by", approved_by or "Not yet approved")
    handoff[2].metric("Current reviewer", current_reviewer or "Review complete")
    handoff[3].metric("Remaining approvals", " → ".join(remaining) if remaining else "None")


def render_ai_decision_support(context: dict, data: dict[str, pd.DataFrame]) -> None:
    recommendation, reasons = deal_decision_support(context, data)
    with st.container(border=True):
        st.markdown("<span class='ai-support-marker'></span>", unsafe_allow_html=True)
        st.subheader("AI Decision Support")
        st.markdown(f"**Recommended action: {recommendation}**")
        st.markdown("**Why**")
        for tone, reason in reasons:
            prefix = "Positive" if tone == "positive" else "Attention" if tone == "attention" else "Critical"
            st.write(f"**{prefix}:** {reason}")


def render_deal_approval_action(
    selected: str,
    deal_status: str,
    pending_roles: list[str],
    pending_label: str,
    route_df: pd.DataFrame,
    data: dict[str, pd.DataFrame],
) -> None:
    if deal_status in ARCHIVE_STATUSES:
        return
    user_role = current_role()
    allowed = allowed_decisions_for_role(user_role)
    can_act = any(user_can_act_for_role(data, role, current_persona(), user_role) for role in pending_roles) and bool(allowed)
    with st.container(border=True):
        st.markdown("<span class='approval-action-marker'></span>", unsafe_allow_html=True)
        st.subheader("Your Decision")
        if not can_act:
            st.info("You can review this case, but only the current reviewer can capture a decision.")
        controls = st.columns([2.2, 3.2, 1.3])
        decision = controls[0].radio(
            "Decision",
            DECISIONS,
            horizontal=True,
            key=f"detail_decision_{selected}",
            disabled=not can_act,
        )
        comment = controls[1].text_input(
            "Decision comment",
            key=f"detail_decision_comment_{selected}",
            placeholder="Required for Request Changes and Reject.",
            disabled=not can_act,
        )
        comment_required = decision in {"Request Changes", "Reject"}
        capture_disabled = not can_act or decision not in allowed or (comment_required and not comment.strip())
        controls[2].markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
        if controls[2].button(
            "Capture Decision",
            type="primary",
            key=f"detail_capture_decision_{selected}",
            disabled=capture_disabled,
            use_container_width=True,
        ):
            success, message = process_approval_decision(selected, decision, comment, route_df, deal_status, data)
            if success:
                st.session_state.deal_detail_confirmation = message
                st.rerun()
            st.error(message)


def human_route_reason(row: pd.Series) -> str:
    policy = str(row.get("Policy ID", ""))
    reason = str(row.get("Reason", row.get("Trigger Reason", "")))
    if "DISC-HIGH" in policy:
        return "Discount exceeds 15% tier"
    if "DISC-MED" in policy:
        return "Discount exceeds 7% governance tier"
    if "MARGIN" in policy:
        return "Resulting margin below product threshold"
    if "PUBLIC" in policy:
        return "Public tender price visibility risk"
    if "SUPPLY" in policy:
        return "Supply review required"
    if "CREDIT" in policy:
        return "Credit review required"
    return short_business_text(reason, "Configured approval rule", 100)


def render_approval_timeline(deal_id: str, deal_status: str, route_df: pd.DataFrame) -> None:
    roles = actionable_route_roles(route_df)
    completed = set(completed_approval_steps(deal_id))
    current = set(current_required_approval_roles(deal_id, deal_status, route_df))
    timeline = ["Submitted by KAM"]
    for role in roles:
        if role in completed:
            timeline.append(f"Approved by {role}")
        elif role in current:
            timeline.append(f"Awaiting {role} Review")
        else:
            timeline.append(f"Next: {role}")
    if deal_status in {"Approved", "Final Approved"}:
        timeline.append("Approved")
    elif deal_status == "Rejected":
        timeline.append("Rejected")
    st.markdown(" → ".join(f"**{item}**" if item.startswith("Pending:") else item for item in timeline))


def render_approval_progress(deal_id: str, deal_status: str, route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    roles = actionable_route_roles(route_df)
    completed = set(completed_approval_steps(deal_id))
    current = set(current_required_approval_roles(deal_id, deal_status, route_df))
    items = []
    for role in roles:
        if role in completed:
            marker = "✓"
        elif role in current:
            marker = "●"
        else:
            marker = "○"
        items.append(f"**{marker} {role_display_label(data, role)}**")
    if items:
        st.markdown(" &nbsp; ".join(items), unsafe_allow_html=True)
    st.caption("✓ completed  |  ● current reviewer  |  ○ upcoming reviewer")
    current_names = ", ".join(active_approver_for_role(data, role) for role in current) or "None"
    remaining = [role for role in roles if role not in completed and role not in current]
    progress_cols = st.columns(2)
    progress_cols[0].metric("Current Approver", current_names)
    progress_cols[1].metric("Next Approvers", " -> ".join(remaining) if remaining else "None")


def approval_history_rows(deal_id: str, deal_status: str, route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> list[dict]:
    roles = actionable_route_roles(route_df)
    completed = set(completed_approval_steps(deal_id))
    current = set(current_required_approval_roles(deal_id, deal_status, route_df))
    events = approval_decision_events(deal_id)
    rows = []
    for role in roles:
        role_events = [event for event in events if str(event.get("Approval Step", "")) == role]
        event = role_events[-1] if role_events else {}
        if role in completed or event:
            rows.append(
                {
                    "State": "completed",
                    "Reviewer": str(event.get("Actor", "")) or approval_actor_for_role(deal_id, role, data),
                    "Role": role_display_label(data, role),
                    "Decision": str(event.get("Decision", "Approved") or "Approved"),
                    "Timestamp": display_timestamp(str(event.get("Timestamp", ""))),
                    "Comment": str(event.get("Comment", "")).strip() or "No reviewer comment recorded.",
                }
            )
        elif role in current:
            rows.append(
                {
                    "State": "current",
                    "Reviewer": active_approver_for_role(data, role),
                    "Role": role_display_label(data, role),
                    "Decision": "Pending",
                    "Timestamp": "",
                    "Comment": "",
                }
            )
    return rows


def render_approval_history(deal_id: str, deal_status: str, route_df: pd.DataFrame, data: dict[str, pd.DataFrame]) -> None:
    rows = approval_history_rows(deal_id, deal_status, route_df, data)
    if not rows:
        return
    st.subheader("Approval History")
    for row in rows:
        marker = "✓" if row["State"] == "completed" else "⏳"
        with st.container(border=True):
            st.markdown(f"**{marker} {row['Reviewer']}**")
            st.write(row["Role"])
            st.markdown(f"**{row['Decision']}**")
            if row["Timestamp"]:
                st.write(row["Timestamp"])
            if row["Comment"]:
                st.markdown("**Comment:**")
                st.write(f'"{row["Comment"]}"')


def render_technical_route_details(context: dict) -> None:
    with st.expander("Approval rule details", expanded=False):
        route = context["route_df"].copy()
        if route.empty:
            st.info("No approval route is required.")
            return
        route["Trigger Reason"] = route.apply(human_route_reason, axis=1)
        columns = [column for column in ["Sequence", "Role", "Active Approver", "SLA Hours", "Trigger Reason"] if column in route]
        st.dataframe(route[columns], use_container_width=True, hide_index=True)


def page_deal_detail(data: dict[str, pd.DataFrame]) -> None:
    deals = deal_detail_visible_deals(data)
    if deals.empty:
        st.info("No deal details are visible for the current user.")
        return
    default = st.session_state.selected_deal_id if st.session_state.selected_deal_id in set(deals["Deal ID"]) else deals.iloc[0]["Deal ID"]
    selected = str(default)
    st.session_state.selected_deal_id = selected

    breadcrumb_cols = st.columns([0.72, 4.6])
    if breadcrumb_cols[0].button("Deal Requests", key=f"detail_breadcrumb_home_{selected}"):
        set_current_page("Deal Request List")
    breadcrumb_cols[1].markdown(f"<div class='page-breadcrumb'>&gt; {selected}</div>", unsafe_allow_html=True)

    deal = deals[deals["Deal ID"].astype(str).eq(selected)].iloc[0].to_dict()
    context = build_deal_context(data, selected)
    if not context:
        st.warning("Deal context is unavailable.")
        return
    calc_lines = context["lines"]
    summary = context["summary"]
    route_df = context["route_df"]
    deal_status = str(deal.get("Status", "")).strip()
    is_creator = is_kam_role() and str(deal.get("Sales Owner", "")) == current_persona()
    if deal_status in {"Draft", "Changes Requested"} and is_creator:
        begin_draft_edit(deal, calc_lines)
        st.rerun()
    pending_roles = current_required_approval_roles(selected, deal_status, route_df)
    pending_role = pending_roles[0] if pending_roles else ""
    pending_label = (
        ", ".join(role_display_label(data, role) for role in pending_roles)
        if pending_roles
        else "KAM Revision Required"
        if deal_status == "Changes Requested"
        else "Complete"
        if deal_status in ARCHIVE_STATUSES
        else "Not Submitted"
    )

    st.markdown(f"<h1>{deal.get('Deal Title', selected)}</h1>", unsafe_allow_html=True)
    metrics = st.columns(5)
    metrics[0].metric("Status", business_deal_status(deal_status))
    metrics[1].metric("Requested Net Revenue", money(summary["total_proposed"]))
    metrics[2].metric("Requested Discount %", pct(summary["discount_pct"]))
    margin_label = "Resulting Gross Margin %" if margin_visibility_for_role() == "Exact" else "Margin Status"
    metrics[3].metric(margin_label, landing_margin_display(summary))
    status_role = " + ".join(pending_roles)
    metrics[4].metric("Approval Status", business_approval_status(deal_status, status_role))

    customer = customer_record_for_deal(deal, data)
    confirmation = st.session_state.get("deal_detail_confirmation", "")
    if confirmation:
        st.success(confirmation)
        st.session_state.deal_detail_confirmation = ""
    if deal_status == "Draft":
        if is_creator:
            if st.button("Edit Draft", type="primary", key=f"edit_draft_{selected}"):
                begin_draft_edit(deal, calc_lines)
                st.rerun()
        else:
            st.info("This draft is read-only. Only the deal creator can edit, save, or submit it.")
    last_comment = str(deal.get("Last Decision Comment", "")).strip()
    if deal_status == "Changes Requested":
        st.warning(f"Changes requested: {last_comment or 'Review the requested changes before resubmitting.'}")
        st.info("This deal is read-only. Only the original creator can edit and resubmit it.")
    elif deal_status == "Rejected" and last_comment:
        st.error(f"Rejected: {last_comment}")

    render_ai_decision_support(context, data)
    if is_creator:
        owner_status = "Returned for Revision" if deal_status == "Changes Requested" else business_approval_status(deal_status, " + ".join(pending_roles))
        with st.container(border=True):
            st.subheader("Current Approval Status")
            st.write(owner_status)
    else:
        render_latest_reviewer_comment(deal, selected)
        render_approval_history(selected, deal_status, route_df, data)
        st.subheader("Approval Progress")
        render_approval_progress(selected, deal_status, route_df, data)
        render_deal_approval_action(selected, deal_status, pending_roles, pending_label, route_df, data)

    tabs = st.tabs(["Executive Summary", "Financials & Pricing", "Insights & Supply", "Audit Trail"])
    with tabs[0]:
        plan_status = "✓ Included" if context["included_in_plan"] else "⚠ Outside Financial Plan"
        summary_cols = st.columns(3)
        summary_cols[0].metric("Financial Plan Status", plan_status)
        summary_cols[1].metric("Deal Type", str(deal.get("Deal Type", "")) or "Not specified")
        summary_cols[2].metric("Risk Assessment", str(deal.get("KAM Risk Assessment", deal.get("Intake Risk", ""))) or "Not rated")
        st.subheader("Business Case")
        st.write(short_business_text(deal.get("Strategic Rationale", ""), "Commercial rationale is not available.", 320))
        if customer:
            render_customer_risk_strip(customer, data)

    with tabs[1]:
        st.subheader("Commercial Pricing")
        st.dataframe(commercial_pricing_view(calc_lines), use_container_width=True, hide_index=True)
        st.subheader("Plan Comparison")
        if context["included_in_plan"]:
            st.dataframe(mask_sensitive_dataframe(context["plan_df"]), use_container_width=True, hide_index=True)
        else:
            st.info("This request is outside the latest financial plan. Planned price comparison is not available; treat the volume as incremental.")
        st.subheader("Financial Projection")
        projection = financial_projection_values(deal, calc_lines, summary)
        projection_cols = st.columns(5)
        for index, (label, value) in enumerate(projection.items()):
            projection_cols[index].metric(label, value)

    with tabs[2]:
        customer_name = str(deal.get("End Account Name", deal.get("Customer Name", "")))
        tender_df, signal_df = tender_competitor_summary(data, calc_lines, customer_name, str(deal.get("Region", "")))
        st.subheader("Commercial Rationale")
        st.write(short_business_text(deal.get("Strategic Rationale", ""), "Commercial rationale is not available.", 420))
        st.subheader("Market Intelligence")
        render_insight_cards(market_intelligence_insights(signal_df, context["competitor_df"]))
        st.subheader("Supply & Inventory")
        render_insight_cards(supply_inventory_insights(context["inventory_df"], context["aging_df"]))
        with st.expander("Supporting supply detail", expanded=False):
            evidence_cols = st.columns(2)
            evidence_cols[0].dataframe(mask_sensitive_dataframe(context["inventory_df"]), use_container_width=True, hide_index=True)
            evidence_cols[1].dataframe(mask_sensitive_dataframe(context["aging_df"]), use_container_width=True, hide_index=True)
        st.subheader("Tender Intelligence")
        render_insight_cards(tender_intelligence_insights(tender_df))
        with st.expander("Supporting market and tender detail", expanded=False):
            detail_cols = st.columns(2)
            detail_cols[0].dataframe(mask_sensitive_dataframe(tender_df), use_container_width=True, hide_index=True)
            detail_cols[1].dataframe(mask_sensitive_dataframe(signal_df), use_container_width=True, hide_index=True)

    with tabs[3]:
        render_technical_route_details(context)
        st.subheader("Audit Trail")
        audit = pd.DataFrame(st.session_state.audit_events)
        if not audit.empty:
            audit = audit[audit["Deal ID"].astype(str).eq(selected)]
        if audit.empty:
            st.info("No session audit events are recorded for this deal.")
        else:
            st.dataframe(audit.sort_values("Timestamp", ascending=False), use_container_width=True, hide_index=True)


def render_analysis_blocks(data: dict[str, pd.DataFrame], deal: dict, lines: pd.DataFrame) -> None:
    region = deal.get("Region", "")
    customer = deal.get("Customer Name", "")
    segment = deal_customer_type(deal)
    account = customer_lookup(data).get(customer, {})
    channel = deal.get("Channel", customer_type(account))
    summary = summarize_lines(lines)
    included_value = str(deal.get("Included In Latest Financial Plan", deal.get("Included_In_Latest_Financial_Plan", "Yes"))).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, lines, region, segment, customer)
    incremental_df = incremental_opportunity_analysis(data, lines, customer, channel)
    inventory_df = enhanced_inventory_analysis(data, lines, region)
    aging_df = enhanced_aging_analysis(data, lines, region)
    competitor_df = enhanced_competitor_intelligence(data, lines, customer, region)
    gp_impact = gross_profit_impact(lines, plan_df, incremental_df, included_in_plan)
    header = build_route_header(deal, data)
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
    sensitive_data_note()
    st.write(
        f"**{recommendation}** for {deal.get('Deal Title', 'selected deal')}. "
        f"The deal is classified as **{'included in latest financial plan' if included_in_plan else 'incremental opportunity'}** "
        f"with proposed revenue of **{sensitive_money('Proposed Revenue', gp_impact['Proposed Revenue'])}**, gross profit impact of "
        f"**{sensitive_money('Gross Profit Variance', gp_impact['Gross Profit Variance'])}**, and a decision score of **{total_score}/100**."
    )
    st.caption(rationale)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision Score", f"{total_score}/100")
    c2.metric("Recommendation", recommendation)
    c3.metric("Plan Inclusion Flag", included_value)
    c4.metric("Gross Profit Impact", sensitive_money("Gross Profit Variance", gp_impact["Gross Profit Variance"]))

    st.subheader("Score Breakdown")
    st.dataframe(score_df, use_container_width=True, hide_index=True)
    st.progress(total_score / 100, text=f"Total Decision Score: {total_score}/100")

    st.subheader("Plan Inclusion Flag")
    flag_message = (
        "Deal is evaluated against planned price, planned quantity, net revenue variance, and gross profit variance."
        if included_in_plan
        else "Deal is evaluated as incremental revenue using historical price and margin benchmarks."
    )
    st.info(f"Included In Latest Financial Plan = {included_value}. {flag_message}")

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
        st.dataframe(mask_sensitive_dataframe(plan_df), use_container_width=True, hide_index=True)
    else:
        st.subheader("Incremental Opportunity Analysis")
        st.dataframe(mask_sensitive_dataframe(incremental_df), use_container_width=True, hide_index=True)

    st.subheader("Gross Profit Impact")
    gp_cols = st.columns(5)
    gp_cols[0].metric("Context", gp_impact["Context"])
    gp_cols[1].metric("Planned Revenue", sensitive_money("Planned Revenue", gp_impact["Planned Revenue"]))
    gp_cols[2].metric("Proposed Revenue", sensitive_money("Proposed Revenue", gp_impact["Proposed Revenue"]))
    gp_cols[3].metric("Net Revenue Variance", sensitive_money("Net Revenue Variance", gp_impact["Net Revenue Variance"]))
    gp_cols[4].metric("Proposed Margin", margin_value_display(gp_impact["Proposed Margin %"], summary["weighted_target_margin"]))

    st.subheader("Price-Volume Benchmark")
    st.dataframe(mask_sensitive_dataframe(price_volume_summary(data, lines, customer, channel)), use_container_width=True, hide_index=True)

    st.subheader("Inventory Analysis")
    st.info(inventory_aging_recommendation(inventory_df, aging_df))
    st.dataframe(mask_sensitive_dataframe(inventory_df), use_container_width=True, hide_index=True)

    st.subheader("Aging Analysis")
    st.dataframe(mask_sensitive_dataframe(aging_df), use_container_width=True, hide_index=True)

    tender_df, intel_df = tender_competitor_summary(data, lines, customer, region)
    st.subheader("Tender History")
    st.dataframe(mask_sensitive_dataframe(tender_df), use_container_width=True, hide_index=True)

    st.subheader("External Market Signals")
    st.info(competitor_summary(competitor_df))
    st.dataframe(mask_sensitive_dataframe(competitor_df), use_container_width=True, hide_index=True)
    with st.expander("Raw external market signals"):
        st.dataframe(mask_sensitive_dataframe(intel_df), use_container_width=True, hide_index=True)

    st.subheader("Approval Route with Trigger Reasons")
    st.dataframe(mask_sensitive_dataframe(route_triggers), use_container_width=True, hide_index=True)


def page_approval_queue(data: dict[str, pd.DataFrame]) -> None:
    render_header("Review Queue", "Role-based review queue for submitted commercial deal requests.")
    st.info("Select a deal from the review queue to review details and capture a decision.")
    deals = visible_deals_for_current_role(combined_deals(data), data)
    sensitive_data_note()
    confirmation = st.session_state.get("approval_confirmation", "")
    if confirmation:
        st.success(confirmation)
        st.session_state.approval_confirmation = ""
    submitted = deals[deals["Status"].astype(str).str.strip().isin(ACTIVE_APPROVAL_STATUSES - {"Changes Requested"})].copy()
    if submitted.empty:
        st.info("No submitted deals available.")
        return
    delegated_roles = delegated_roles_for_persona(data, current_persona())
    selectable_roles = ACTIONABLE_APPROVAL_ROLES if can_configure_system() else list(dict.fromkeys(([current_role()] if current_role() in ACTIONABLE_APPROVAL_ROLES else []) + delegated_roles))
    if not selectable_roles:
        selectable_roles = ROLE_ORDER
    role = st.selectbox("Queue Role", selectable_roles, index=0)
    lines = combined_lines(data)
    rows = []
    for _, deal in submitted.iterrows():
        calc_lines = normalize_lines(lines[lines["Deal ID"].astype(str).eq(str(deal["Deal ID"]))], data)
        summary = summarize_lines(calc_lines)
        header = build_route_header(deal.to_dict(), data)
        route = route_preview(header, calc_lines, summary, data)
        ensure_approval_assignments(str(deal["Deal ID"]), route, data)
        required_roles = current_required_approval_roles(str(deal["Deal ID"]), str(deal.get("Status", "")).strip(), route)
        if role in required_roles:
            update_sla_breach_audit(str(deal["Deal ID"]), role, data)
            sla_status = assignment_status(str(deal["Deal ID"]), role)
            reason = route[route["Role"].eq(role)].iloc[0]["Reason"] if role in set(route["Role"]) else "Current required approval step."
            route_row = route[route["Role"].eq(role)].iloc[0].to_dict() if role in set(route["Role"]) else {}
            rows.append(
                {
                    "Deal ID": deal["Deal ID"],
                    "Customer": deal.get("Sold-To Customer Name", deal.get("Customer Name", "")),
                    "Deal Title": deal["Deal Title"],
                    "Value": summary["total_proposed"],
                    "Discount %": summary["discount_pct"],
                    "Risk": deal.get("KAM Risk Assessment", deal.get("Intake Risk", "")),
                    "Role": role_display_label(data, role),
                    "Route Role": role,
                    "Active Approver": route_row.get("Active Approver", ""),
                    "Target Response": f"{int(sla_status.get('SLA Hours', route_row.get('SLA Hours', 0)))}h",
                    "SLA Status": "Breached" if sla_status.get("Is Breached") else "On Track",
                    "Current Status": deal.get("Status", ""),
                    "Trigger Reason": reason,
                }
            )
    queue = pd.DataFrame(rows)
    if queue.empty:
        st.info(f"No deals currently require {role}.")
        return
    queue_display = mask_sensitive_dataframe(queue.drop(columns=["Route Role"], errors="ignore"))
    table_event = st.dataframe(
        queue_display,
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
    required_roles = current_required_approval_roles(selected, previous_status, context["route_df"])
    required_role = role if role in required_roles else (required_roles[0] if required_roles else "")
    required_role_label = role_display_label(data, required_role) if required_role else "None"
    update_sla_breach_audit(selected, required_role, data)
    sla_status = assignment_status(selected, required_role)
    user_role = st.session_state.get("role", "Demo Role")
    allowed_decisions = allowed_decisions_for_role(user_role)
    can_act_on_step = bool(required_role) and user_can_act_for_role(data, required_role, current_persona(), user_role) and bool(allowed_decisions)
    role_cols = st.columns(3)
    role_cols[0].metric("Current Required Role", required_role_label)
    role_cols[1].metric("Current User Role", user_role)
    role_cols[2].metric("Can Approve", "Yes" if can_act_on_step else "No")
    if not can_act_on_step:
        st.warning(f"{user_role} cannot capture a decision for this step. Required role: {required_role_label}.")

    if sla_status:
        sla_cols = st.columns(4)
        sla_cols[0].metric("Assigned", str(sla_status.get("Assigned At", "")))
        sla_cols[1].metric("Due", str(sla_status.get("Due At", "")))
        sla_cols[2].metric("Target Response", f"{int(sla_status.get('SLA Hours', 0))}h")
        sla_cols[3].metric("SLA", "Breached" if sla_status.get("Is Breached") else "On Track")

    st.subheader("SLA Actions")
    action_cols = st.columns(3)
    if action_cols[0].button("Send Reminder", type="secondary", key=f"reminder_{selected}_{required_role}", disabled=not bool(required_role)):
        workflow_audit_once(
            f"{assignment_key(selected, required_role)}::reminder::{len(st.session_state.audit_events)}",
            selected,
            "Reminder Sent",
            entity="Approval SLA",
            details=f"Reminder recorded for {required_role_label}. No email was sent.",
            approval_step=required_role,
        )
        st.session_state.approval_confirmation = f"Reminder recorded for {required_role_label}."
        st.rerun()
    if action_cols[1].button("Mark SLA Breached", type="secondary", key=f"breach_{selected}_{required_role}", disabled=not bool(required_role)):
        workflow_audit_once(
            f"{assignment_key(selected, required_role)}::breached",
            selected,
            "SLA Breached",
            entity="Approval SLA",
            details=f"SLA breach recorded for {required_role_label}.",
            approval_step=required_role,
        )
        st.session_state.approval_confirmation = f"SLA breach recorded for {required_role_label}."
        st.rerun()
    if action_cols[2].button("Escalate", type="secondary", key=f"escalate_{selected}_{required_role}", disabled=not bool(required_role)):
        workflow_audit_once(
            f"{assignment_key(selected, required_role)}::escalated::{len(st.session_state.audit_events)}",
            selected,
            "Escalated",
            entity="Approval SLA",
            details=f"{required_role_label} escalated to General Manager.",
            approval_step=required_role,
            previous_status=previous_status,
            new_status="Pending General Manager",
        )
        update_deal_status(selected, "Pending General Manager", "Escalate", "SLA escalation", approval_step=required_role, previous_status=previous_status)
        st.session_state.approval_confirmation = f"{required_role_label} escalated to General Manager."
        st.rerun()

    st.subheader("Decision")
    decision = st.radio("Decision", DECISIONS, horizontal=True, key=f"decision_{selected}")
    comment = st.text_area("Decision comment", key=f"decision_comment_{selected}")
    can_capture = can_act_on_step and decision in allowed_decisions
    if decision not in allowed_decisions:
        st.warning(f"{user_role} is not permitted to capture `{decision}`.")
    if st.button("Capture Decision", type="primary", disabled=not can_capture):
        success, message = process_approval_decision(selected, decision, comment, context["route_df"], previous_status, data)
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
            approval_step=required_role,
            previous_status=previous_status,
            new_status=previous_status,
        )
        st.session_state.approval_confirmation = f"Comment added for {selected}. Status remains {previous_status}."
        st.rerun()

    if st.button("Open Full Deal Detail", type="secondary"):
        navigate_to_deal_detail(selected, "approval queue preview")


def page_reference_data(data: dict[str, pd.DataFrame]) -> None:
    render_header("Reference Data", "Inspect source datasets powering the MVP.")
    if not can_view_reference_data():
        st.warning("Reference Data is available to Finance, Pricing Governance, Market Access, General Manager, and System Administrator roles.")
        return
    sensitive_data_note()
    labels = {
        "customers": "Customers",
        "products": "Products",
        "price_book": "Price Book",
        "deal_summary": "Deal Summary",
        "commercial_plan": "Commercial Plan",
        "price_volume": "Price-Volume History",
        "inventory_coverage": "Inventory Coverage",
        "expiry_aging": "Expiry Aging",
        "tender_history": "Tender History",
        "competitor_intel": "External Market Signals",
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
    st.dataframe(mask_sensitive_dataframe(view), use_container_width=True, hide_index=True)


def readable_condition_for_rule(rule: pd.Series) -> str:
    rule_type = str(rule.get("Rule Type", ""))
    if rule_type == "DISC":
        return f"Discount {rule.get('Discount Trigger', '')}"
    if rule_type == "MARGIN":
        role = str(rule.get("Required Role", ""))
        if role == "Finance Director":
            return "Margin < Product Target - 10%"
        if role == "General Manager":
            return "Margin < Product Target - 20%"
        return "Product Target Margin Trigger"
    if rule_type == "PUBLIC":
        return "Public Price Impact"
    if rule_type == "CREDIT":
        return "Overdue Receivables"
    if rule_type == "SUPPLY":
        return "Inventory Shortage"
    return str(rule.get("Policy Name", rule.get("Condition", "")))


def approval_matrix_summary(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rules = approval_rule_rows(data)
    if rules.empty:
        return pd.DataFrame(columns=["Rule", "Required Roles"])
    rows = []
    rules = rules.copy()
    rules["Readable Rule"] = rules.apply(readable_condition_for_rule, axis=1)
    for rule, part in rules.sort_values(["Sequence", "Required Role"]).groupby("Readable Rule", sort=False):
        roles = part.sort_values(["Sequence", "Required Role"])["Required Role"].astype(str).tolist()
        rows.append({"Rule": rule, "Required Roles": "\n".join(dict.fromkeys(roles))})
    return pd.DataFrame(rows)


def product_margin_thresholds(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    products = data.get("products", pd.DataFrame())
    if products.empty:
        return pd.DataFrame()
    rows = []
    for _, product in products.iterrows():
        item = product.to_dict()
        target = product_target_margin(item)
        rows.append(
            {
                "SKU": item.get("SKU", ""),
                "Product Name": item.get("Product Name", ""),
                "Product Category": item.get("Product Category", item.get("Product Type", "")),
                "List Price": product_list_price(item),
                "Gross Price": product_gross_price(item),
                "Base Rebate %": safe_float(item.get("Base Rebate %", 0)),
                "Standard Cost": safe_float(item.get("Standard Cost", 0)),
                "Target Margin": target,
                "FD Trigger Margin": finance_trigger_margin(target),
                "GM Trigger Margin": gm_trigger_margin(target),
            }
        )
    return pd.DataFrame(rows)


def can_view_margin_trigger_reference(role: str | None = None) -> bool:
    return (role or current_role()) in {
        "Pricing Governance Owner",
        "Finance Director",
        "General Manager",
        "System Administrator",
    }


def page_approval_matrix(data: dict[str, pd.DataFrame]) -> None:
    render_header("Approval Rules & Matrix", "Business-readable approval stages and the configurable rules that activate them.")
    stage_summary = pd.DataFrame(
        [
            {
                "Stage": "1. Commercial Review",
                "Required Review": "Sales Manager",
                "How It Works": "Every submitted deal starts with the assigned Sales Manager.",
            },
            {
                "Stage": "2. Specialist Review",
                "Required Review": "Pricing Governance Owner + Finance Director + Operations Manager when triggered",
                "How It Works": "Required specialist reviews run in parallel after Sales Manager approval.",
            },
            {
                "Stage": "3. Executive Review",
                "Required Review": "General Manager when triggered",
                "How It Works": "General Manager review starts only after all required specialist reviews are complete.",
            },
        ]
    )
    st.dataframe(stage_summary, use_container_width=True, hide_index=True)
    st.subheader("Routing Rules")
    summary = approval_matrix_summary(data)
    if summary.empty:
        st.info("No approval routing rules are configured.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)

    if can_view_margin_trigger_reference():
        st.subheader("Product Margin Trigger Reference")
        product_thresholds = product_margin_thresholds(data)
        if product_thresholds.empty:
            st.info("No product margin targets are configured.")
        else:
            st.dataframe(product_thresholds, use_container_width=True, hide_index=True)

    with st.expander("Rule Reference Data", expanded=False):
        rules = approval_rule_rows(data)
        display_cols = [
            "Policy ID",
            "Policy Name",
            "Discount Trigger",
            "Value / Margin Trigger",
            "Required Role",
            "Sequence",
            "SLA Hours",
            "Notes",
        ]
        st.dataframe(rules[[col for col in display_cols if col in rules]], use_container_width=True, hide_index=True)
def page_approver_roster(data: dict[str, pd.DataFrame]) -> None:
    render_header("Approver Roster", "Primary and delegate approver assignments by role.")
    if not can_configure_system():
        st.warning("Approver roster access is available to System Administrator.")
        return
    roster = delegate_config(data).copy()
    roster = roster.rename(columns={"Target Response Hours": "Target Response Time (Hours)"})
    display_cols = ["Role", "Primary Approver", "Delegate Approver", "Target Response Time (Hours)"]
    st.dataframe(roster[display_cols], use_container_width=True, hide_index=True)


def page_system_administrator_settings(data: dict[str, pd.DataFrame]) -> None:
    render_header("Reference & Governance", "Configure thresholds, SLA values, delegates, and role permissions.")
    if not can_configure_system():
        st.warning("System administrator settings are available to System Administrator.")
        return

    tabs = st.tabs(["Approval Thresholds", "SLA Values", "Delegates", "Role Permissions"])

    with tabs[0]:
        rules = approval_rule_rows(data)
        threshold_cols = ["Policy ID", "Policy Name", "Discount Trigger", "Value / Margin Trigger", "Required Role", "Sequence", "SLA Hours", "Notes"]
        edited_rules = st.data_editor(
            rules[[col for col in threshold_cols if col in rules]],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Required Role": st.column_config.SelectboxColumn("Required Role", options=ACTIONABLE_APPROVAL_ROLES, required=True),
                "Sequence": st.column_config.NumberColumn("Sequence", min_value=1, max_value=10, step=1),
                "SLA Hours": st.column_config.NumberColumn("SLA Hours", min_value=1, max_value=168, step=1),
            },
            key="approval_threshold_editor",
        )
        if st.button("Save Approval Thresholds", type="primary"):
            st.session_state.approval_matrix_overrides = edited_rules.to_dict("records")
            add_audit("SYSTEM", "Approval Thresholds Updated", entity="Administration", details="Approval matrix thresholds updated for this session.")
            st.success("Approval thresholds saved for this session.")

    with tabs[1]:
        config = delegate_config(data).copy()
        sla_edit = st.data_editor(
            config[["Role", "Target Response Hours"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Role": st.column_config.SelectboxColumn("Role", options=ACTIONABLE_APPROVAL_ROLES, required=True),
                "Target Response Hours": st.column_config.NumberColumn("Target Response Time (Hours)", min_value=1, max_value=168, step=1),
            },
            key="sla_value_editor",
        )
        if st.button("Save SLA Values", type="primary"):
            saved = config.copy()
            for _, row in sla_edit.iterrows():
                saved.loc[saved["Role"].astype(str).eq(str(row["Role"])), "Target Response Hours"] = int(row["Target Response Hours"])
            st.session_state.delegate_overrides = saved.to_dict("records")
            add_audit("SYSTEM", "SLA Values Updated", entity="Administration", details="Target response times updated for this session.")
            st.success("SLA values saved for this session.")

    with tabs[2]:
        render_delegate_editor(data, key_prefix="settings")

    with tabs[3]:
        permission_config = role_permission_config()
        edited_permissions = st.data_editor(
            permission_config,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Role": st.column_config.SelectboxColumn("Role", options=ROLE_ORDER, required=True),
                "Sensitive Visibility": st.column_config.SelectboxColumn("Sensitive Visibility", options=["Restricted", "Full"], required=True),
                "Margin Visibility": st.column_config.SelectboxColumn("Margin Visibility", options=["Hidden", "Status Only", "Exact"], required=True),
                "Configuration Rights": st.column_config.CheckboxColumn("Configuration Rights"),
            },
            key="role_permission_editor",
        )
        if st.button("Save Role Permissions", type="primary"):
            st.session_state.role_permission_overrides = edited_permissions.to_dict("records")
            add_audit("SYSTEM", "Role Permissions Updated", entity="Administration", details="Role permission settings updated for this session.")
            st.success("Role permissions saved for this session.")


def render_delegate_editor(data: dict[str, pd.DataFrame], key_prefix: str = "delegate_admin") -> None:
    config = delegate_config(data)
    persona_options = list(PERSONAS.keys())
    edited = st.data_editor(
        config,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Role": st.column_config.SelectboxColumn("Role", options=ACTIONABLE_APPROVAL_ROLES, required=True),
            "Primary Approver": st.column_config.SelectboxColumn("Primary Approver", options=persona_options, required=True),
            "Delegate Approver": st.column_config.SelectboxColumn("Delegate Approver", options=persona_options, required=False),
            "Delegation Enabled": st.column_config.CheckboxColumn("Delegation Enabled"),
            "Target Response Hours": st.column_config.NumberColumn("Target Response Hours", min_value=1, max_value=168, step=1),
        },
        key=f"{key_prefix}_editor",
    )
    actions = st.columns(2)
    if actions[0].button("Save Delegate Settings", type="primary", key=f"{key_prefix}_save"):
        saved = edited.copy()
        saved["Delegation Enabled"] = saved["Delegation Enabled"].astype(bool)
        saved["Target Response Hours"] = pd.to_numeric(saved["Target Response Hours"], errors="coerce").fillna(24).astype(int)
        st.session_state.delegate_overrides = saved.to_dict("records")
        add_audit("SYSTEM", "Delegate Settings Updated", entity="Administration", details="Primary/delegate approver settings updated for this session.")
        st.success("Delegate settings saved for this session.")
    if actions[1].button("Reset Delegate Settings", type="secondary", key=f"{key_prefix}_reset"):
        st.session_state.delegate_overrides = default_delegate_config(data)
        add_audit("SYSTEM", "Delegate Settings Reset", entity="Administration", details="Delegate settings reset from reference data.")
        st.rerun()

    st.subheader("Current Route Display")
    preview = delegate_config(data).copy()
    preview["Route Label"] = preview.apply(lambda row: f"{row['Role']} (Delegated)" if row["Delegation Enabled"] else row["Role"], axis=1)
    preview["Active Approver"] = preview.apply(lambda row: row["Delegate Approver"] if row["Delegation Enabled"] else row["Primary Approver"], axis=1)
    st.dataframe(preview[["Role", "Route Label", "Primary Approver", "Delegate Approver", "Delegation Enabled", "Active Approver", "Target Response Hours"]], use_container_width=True, hide_index=True)


def page_delegate_administration(data: dict[str, pd.DataFrame]) -> None:
    render_header("Delegation", "Primary and delegate approvers for each approval role.")
    if not can_configure_system():
        preview = delegate_config(data).copy()
        preview["Route Label"] = preview.apply(lambda row: f"{row['Role']} (Delegated)" if row["Delegation Enabled"] else row["Role"], axis=1)
        preview["Active Approver"] = preview.apply(lambda row: row["Delegate Approver"] if row["Delegation Enabled"] else row["Primary Approver"], axis=1)
        st.dataframe(
            preview[["Role", "Route Label", "Primary Approver", "Delegate Approver", "Active Approver", "Target Response Hours"]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Delegate configuration is maintained by the System Administrator.")
        return
    render_delegate_editor(data)


def page_audit_log(data: dict[str, pd.DataFrame]) -> None:
    render_header("Audit Trail", "Approval, SLA, reminder, delegation, and decision events.")
    audit = pd.DataFrame(st.session_state.audit_events)
    if audit.empty:
        st.info("No audit events in this session yet.")
        return
    if not can_configure_system() and "Deal ID" in audit:
        visible_ids = set(visible_deals_for_current_role(combined_deals(data), data)["Deal ID"].astype(str))
        audit = audit[audit["Deal ID"].astype(str).isin(visible_ids)]
    if audit.empty:
        st.info("No audit events are available for the deals visible to the current user.")
        return
    st.dataframe(audit.sort_values("Timestamp", ascending=False), use_container_width=True, hide_index=True)


def reset_demo_session() -> None:
    st.session_state.runtime_deals = []
    st.session_state.runtime_lines = []
    st.session_state.audit_events = []
    st.session_state.deal_status_overrides = {}
    st.session_state.deal_approval_steps = {}
    st.session_state.approval_assignments = {}
    st.session_state.workflow_audit_keys = []
    st.session_state.requestor_followups = []
    st.session_state.delegate_overrides = None
    st.session_state.approval_matrix_overrides = None
    st.session_state.role_permission_overrides = None
    st.session_state.approval_confirmation = ""
    st.session_state.deal_detail_confirmation = ""
    st.session_state.deal_list_selected_deal_id = None
    st.session_state.approval_queue_selected_deal_id = None
    st.session_state.selected_deal_id = None
    st.session_state.deal_detail_parent = "Deal Requests"
    st.session_state.draft_lines = None
    st.session_state.line_editor_rows = None
    st.session_state.line_editor_revision += 1
    st.session_state.editing_deal_id = None
    st.session_state.deal_edit_active = False
    st.session_state.current_draft_snapshot = None
    st.session_state.pending_role_switch = None
    st.session_state.current_page = "Deal Request List"
    st.rerun()


def complete_role_switch(target_persona: str) -> None:
    clear_deal_editor_state()
    st.session_state.persona = target_persona
    st.session_state.role = PERSONAS[target_persona]
    st.session_state.role_selector_version += 1
    st.session_state.pending_role_switch = None
    st.session_state.selected_deal_id = None
    st.session_state.deal_list_selected_deal_id = None
    st.session_state.approval_queue_selected_deal_id = None
    st.session_state.deal_list_view_mode = "Active"
    st.session_state.deal_list_table_revision += 1
    st.session_state.current_page = "Deal Request List"


def render_role_switch_confirmation(data: dict[str, pd.DataFrame]) -> None:
    target = str(st.session_state.get("pending_role_switch") or "")
    st.warning("Do you want to save this deal as Draft before switching role?")
    actions = st.columns(3)
    snapshot = st.session_state.get("current_draft_snapshot")
    if actions[0].button("Save Draft and Switch", type="primary", disabled=not bool(snapshot)):
        save_runtime_deal(
            snapshot["header"],
            snapshot["lines"],
            snapshot["summary"],
            snapshot["route_df"],
            status="Draft",
            recommendation="Draft",
        )
        complete_role_switch(target)
        st.rerun()
    if actions[1].button("Discard and Switch"):
        complete_role_switch(target)
        st.rerun()
    if actions[2].button("Cancel"):
        st.session_state.role_selector_version += 1
        st.session_state.pending_role_switch = None
        st.rerun()


def top_navigation(data: dict[str, pd.DataFrame]) -> str:
    valid_pages = {
        "Deal Request List",
        "New Deal Intake",
        "Approval Queue Preview",
        "Deal Detail",
        "Reference Data",
        "Approval Matrix",
        "Approver Roster",
        "System Administrator Settings",
        "Delegate Administration",
        "Audit Log",
    }
    if st.session_state.get("current_page") not in valid_pages:
        st.session_state.current_page = "Deal Request List"

    with st.container():
        nav_cols = st.columns([0.55, 0.95, 1.75, 1.35, 1.05])
        nav_cols[0].markdown("<span class='nav-marker nav-title-marker'></span>", unsafe_allow_html=True)
        if nav_cols[0].button("Home", key="top_navigation_home"):
            clear_deal_editor_state()
            st.session_state.selected_deal_id = None
            st.session_state.current_page = "Deal Request List"
            st.rerun()
        nav_cols[2].markdown("<span class='nav-marker nav-user-marker'></span>", unsafe_allow_html=True)
        persona_options = list(PERSONAS.keys())
        selected_persona = nav_cols[2].selectbox(
            "Current User",
            persona_options,
            index=persona_options.index(current_persona()),
            key=f"role_selector_{st.session_state.role_selector_version}",
            format_func=lambda name: f"{name} | {PERSONAS[name]}",
        )
        if selected_persona != current_persona() and not st.session_state.get("pending_role_switch"):
            if st.session_state.get("deal_edit_active") and st.session_state.get("current_page") == "New Deal Intake":
                st.session_state.pending_role_switch = selected_persona
            else:
                complete_role_switch(selected_persona)
                st.rerun()
        if st.session_state.get("pending_role_switch"):
            render_role_switch_confirmation(data)

        new_disabled = not is_kam_role(st.session_state.role)
        nav_cols[1].markdown("<span class='nav-marker nav-new-marker'></span>", unsafe_allow_html=True)
        if nav_cols[1].button("New Request", disabled=new_disabled):
            clear_deal_editor_state()
            st.session_state.deal_edit_active = True
            st.session_state.current_page = "New Deal Intake"
            st.rerun()

        nav_cols[3].markdown("<span class='nav-marker nav-governance-marker'></span>", unsafe_allow_html=True)
        with nav_cols[3].popover("Reference & Governance", use_container_width=True):
            st.markdown("**Governance**")
            if st.button("Approval Rules & Matrix", key="nav_approval_matrix", use_container_width=True):
                st.session_state.current_page = "Approval Matrix"
                st.rerun()
            if st.button("Delegation", key="nav_delegation", use_container_width=True):
                st.session_state.current_page = "Delegate Administration"
                st.rerun()
            if st.button("Audit Trail", key="nav_audit_trail", use_container_width=True):
                st.session_state.current_page = "Audit Log"
                st.rerun()
            if can_view_reference_data():
                if st.button("Reference Data", key="nav_reference_data", use_container_width=True):
                    st.session_state.current_page = "Reference Data"
                    st.rerun()
            if can_configure_system():
                st.markdown("**Administration**")
                if st.button("Configuration Tools", key="admin_system_settings", use_container_width=True):
                    st.session_state.current_page = "System Administrator Settings"
                    st.rerun()
                if st.button("Approver Roster", key="admin_approver_roster", use_container_width=True):
                    st.session_state.current_page = "Approver Roster"
                    st.rerun()
                st.divider()
                st.warning("Reset clears session-created deals, status overrides, and session audit events.")
                confirm_reset = st.checkbox("I understand and want to reset this demo session.", key="admin_confirm_reset")
                if st.button("Reset Demo Session", key="admin_reset_demo", use_container_width=True, disabled=not confirm_reset):
                    reset_demo_session()
    return st.session_state.current_page


def main() -> None:
    inject_css()
    init_state()
    data = load_demo_data()
    page = top_navigation(data)
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
    elif page == "Approval Matrix":
        page_approval_matrix(data)
    elif page == "Approver Roster":
        page_approver_roster(data)
    elif page == "System Administrator Settings":
        page_system_administrator_settings(data)
    elif page == "Delegate Administration":
        page_delegate_administration(data)
    elif page == "Audit Log":
        page_audit_log(data)


if __name__ == "__main__":
    main()
