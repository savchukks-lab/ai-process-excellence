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
    "Market Access Director",
    "Finance Director",
    "Supply Chain Manager",
    "General Manager",
    "System Administrator",
]

PERSONAS = {
    "Maya Chen": "KAM North",
    "Ethan Brooks": "KAM South",
    "Jordan Blake": "Sales Manager",
    "Priya Nair": "Pricing Governance Owner",
    "Marcus Reed": "Market Access Director",
    "Daniel Ortiz": "Finance Director",
    "Elena Rossi": "Supply Chain Manager",
    "Sarah Morgan": "General Manager",
    "Admin User": "System Administrator",
}

SALES_MANAGER_TEAMS = {
    "Jordan Blake": ["Maya Chen", "Ethan Brooks"],
}

APPROVAL_STEP_STATUS = {
    "Sales Manager": "Pending Sales Manager",
    "Pricing Governance Owner": "Pending Pricing Governance",
    "Market Access Director": "Pending Market Access",
    "Finance Director": "Pending Finance",
    "Supply Chain Manager": "Pending Supply Chain",
    "General Manager": "Pending General Manager",
}

STATUS_APPROVAL_STEP = {status: role for role, status in APPROVAL_STEP_STATUS.items()}

ACTIONABLE_APPROVAL_ROLES = [
    "Sales Manager",
    "Pricing Governance Owner",
    "Market Access Director",
    "Finance Director",
    "Supply Chain Manager",
    "General Manager",
]

ACTIVE_APPROVAL_STATUSES = {
    "Submitted",
    "Pending Sales Manager",
    "Pending Pricing Governance",
    "Pending Market Access",
    "Pending Finance",
    "Pending Supply Chain",
    "Pending General Manager",
    "Changes Requested",
}

DECISIONS = ["Approve", "Request Changes", "Escalate", "Reject"]

ROLE_ALLOWED_DECISIONS = {
    "KAM North": [],
    "KAM South": [],
    "Sales Manager": ["Approve", "Request Changes"],
    "Pricing Governance Owner": ["Approve", "Request Changes"],
    "Market Access Director": ["Approve", "Request Changes"],
    "Finance Director": ["Approve", "Request Changes"],
    "Supply Chain Manager": ["Approve", "Request Changes"],
    "General Manager": ["Approve", "Request Changes", "Escalate", "Reject"],
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
    "Market Access Director": SENSITIVE_FIELD_PATTERNS,
    "Finance Director": SENSITIVE_FIELD_PATTERNS,
    "Supply Chain Manager": [],
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
            padding-top: 0.6rem;
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
            margin-top: 0.15rem;
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
        @media (max-width: 760px) {
            .block-container {
                padding-left: 0.65rem;
                padding-right: 0.65rem;
                padding-top: 0.45rem;
            }
            h1 {
                font-size: 1.32rem !important;
            }
            [data-testid="stMetric"] {
                padding: 6px 8px;
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
    st.session_state.setdefault("approval_assignments", {})
    st.session_state.setdefault("workflow_audit_keys", [])
    st.session_state.setdefault("delegate_overrides", None)
    st.session_state.setdefault("approval_matrix_overrides", None)
    st.session_state.setdefault("role_permission_overrides", None)
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
        {"Role": "Market Access Director", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": False},
        {"Role": "Finance Director", "Sensitive Visibility": "Full", "Margin Visibility": "Exact", "Configuration Rights": False},
        {"Role": "Supply Chain Manager", "Sensitive Visibility": "Restricted", "Margin Visibility": "Hidden", "Configuration Rights": False},
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
        "Market Access Director",
        "Finance Director",
        "General Manager",
        "System Administrator",
    }


def can_configure_system(role: str | None = None) -> bool:
    profile = role_permission_profile(role)
    if profile:
        return bool(profile.get("Configuration Rights"))
    return (role or current_role()) == "System Administrator"


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
    return pd.DataFrame(grouped).sort_values(["Sequence", "Role"])


def build_route_header(deal: dict, data: dict[str, pd.DataFrame]) -> dict:
    customer_name = deal.get("Customer Name")
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
                "Target Response Hours": int(safe_float(item.get("Target Response Hours", item.get("SLA Hours", 24)), 24)),
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


def visible_deals_for_current_role(deals: pd.DataFrame, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if deals.empty:
        return deals
    role = current_role()
    persona = current_persona()
    delegated_ids = route_visible_deal_ids_for_roles(deals, data, delegated_roles_for_persona(data, persona))
    if role == "System Administrator":
        return deals
    if is_kam_role(role):
        own_mask = deals.get("Sales Owner", pd.Series(dtype=str)).astype(str).eq(persona)
        delegate_mask = deals["Deal ID"].astype(str).isin(delegated_ids)
        return deals[own_mask | delegate_mask].copy()
    if role == "Sales Manager":
        team = SALES_MANAGER_TEAMS.get(persona, SALES_MANAGER_TEAMS.get("Jordan Blake", []))
        return deals[
            deals.get("Sales Owner", pd.Series(dtype=str)).astype(str).isin(team)
            | deals.get("Sales Manager", pd.Series(dtype=str)).astype(str).eq(persona)
            | deals["Deal ID"].astype(str).isin(delegated_ids)
        ].copy()
    if has_full_visibility(role):
        return deals
    if role == "Supply Chain Manager":
        visible_ids = route_visible_deal_ids_for_roles(deals, data, [role]).union(delegated_ids)
        return deals[deals["Deal ID"].astype(str).isin(visible_ids)].copy()
    return deals.iloc[0:0].copy()


def demo_commercial_price_defaults(data: dict[str, pd.DataFrame], sku: str) -> dict[str, float]:
    prod = product_lookup(data).get(str(sku), {})
    list_price = product_list_price(prod)
    gross_price = product_gross_price(prod)
    return {
        "Unit List Price": round(list_price, 2),
        "Gross Price": round(gross_price, 2),
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
    st.session_state.deal_detail_parent = "Review Queue" if "approval" in source.lower() else "Deal Requests"
    add_audit(deal_id, "Deal viewed", details=f"Opened from {source}.")
    if sensitive_fields_visible_for_role(current_role()) == "Yes":
        add_audit(deal_id, "Sensitive deal data accessed", details=f"Opened from {source}.", sensitive_fields_visible="Yes")
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
        return "KAM North"
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
    if current_role == "General Manager" and current_role not in roles:
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


def process_approval_decision(deal_id: str, decision: str, comment: str, route_df: pd.DataFrame, previous_status: str, data: dict[str, pd.DataFrame]) -> tuple[bool, str]:
    current_role = current_required_approval_role(deal_id, previous_status, route_df)
    persona = st.session_state.get("persona", "Demo User")
    user_role = st.session_state.get("role", "Demo Role")
    allowed = allowed_decisions_for_role(user_role)
    if not user_can_act_for_role(data, current_role, persona, user_role) or decision not in allowed:
        return False, f"{user_role} cannot capture `{decision}` for this step. Current required role is {role_display_label(data, current_role) if current_role else 'none'}."

    if decision == "Approve":
        new_status = next_approval_status(deal_id, current_role, route_df)
    elif decision == "Request Changes":
        new_status = "Changes Requested"
    elif decision == "Reject":
        new_status = "Rejected"
    else:
        new_status = "Pending General Manager"

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
        gross_price = float(row.get("Gross Price", product_gross_price(prod)) or 0)
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
                "Product Category": prod.get("Product Category", prod.get("Product Type", "")),
                "Therapeutic Area": prod.get("Therapeutic Area", ""),
                "Product Type": prod.get("Product Type", prod.get("Product Category", "")),
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
                "Base Rebate %": prod.get("Base Rebate %", 0),
                "Target Margin %": product_target_margin(prod),
                "Target Gross Margin %": product_target_margin(prod),
                "Finance Director Trigger Margin": finance_trigger_margin(product_target_margin(prod)),
                "General Manager Trigger Margin": gm_trigger_margin(product_target_margin(prod)),
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
        if role == "Pricing Governance Owner" and aggressive_pricing:
            trigger += " Competitor pricing signals require guardrail review."
        if role == "Market Access Director" and incumbent:
            trigger += " Incumbent competitor or access defense is present."
        if role == "Finance Director":
            trigger += " Gross profit variance requires finance review."
        if role == "Supply Chain Manager" and shortage > 0:
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
        if role in {"Market Access Director", "General Manager"} and purpose == "Strategic account":
            reason += " Strategic account."
        if role == "Supply Chain Manager" and shortage > 0:
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
    customer = deal.get("Customer Name", "")
    region = deal.get("Region", "")
    segment = deal_customer_type(deal)
    account = customer_lookup(data).get(customer, {})
    channel = customer_type(account)
    included_value = str(deal.get("Included_In_Latest_Financial_Plan", "Yes")).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, calc_lines, region, segment)
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
        f"**{deal.get('Deal Title', '')}** | {deal.get('Customer Name', '')} | "
        f"Status: **{deal.get('Status', '')}** | Plan flag: **{context['included_value']}**"
    )
    metrics = st.columns(4)
    metrics[0].metric("Proposed Value", money(gp_impact["Proposed Revenue"]))
    metrics[1].metric("Decision Score", f"{context['total_score']}/100")
    metrics[2].metric("Recommendation", context["recommendation"])
    metrics[3].metric("Gross Profit Impact", sensitive_money("Gross Profit Variance", gp_impact["Gross Profit Variance"]))
    st.caption(context["rationale"])
    if compact:
        st.info(inventory_aging_recommendation(context["inventory_df"], context["aging_df"]))
        st.info(competitor_summary(context["competitor_df"]))
        return
    left, right = st.columns(2)
    with left:
        st.markdown("**Inventory / Aging Summary**")
        st.info(inventory_aging_recommendation(context["inventory_df"], context["aging_df"]))
        st.dataframe(mask_sensitive_dataframe(context["inventory_df"]), use_container_width=True, hide_index=True)
        st.dataframe(mask_sensitive_dataframe(context["aging_df"]), use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Competitor Summary**")
        st.info(competitor_summary(context["competitor_df"]))
        st.dataframe(mask_sensitive_dataframe(context["competitor_df"]), use_container_width=True, hide_index=True)
    st.markdown("**Approval Route Trigger Reasons**")
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
        required_condition = "Use FEFO and confirm aging or near-expiry stock allocation before approval."
    elif not inventory_df.empty and (inventory_df["Allocation Risk"] == "High").any():
        required_condition = "Supply chain must confirm allocation feasibility and supply continuity."
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
    top[4].metric("Est. Margin", margin_display(summary))

    st.write(f"Customer: **{deal.get('Customer Name', '')}**")
    st.write(f"Deal title: **{deal.get('Deal Title', '')}**")

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
    required = ["Deal Title", "Customer Name", "Deal Type", "Region", "Currency", "Target Close Date", "Requested Effective Date", "Payment Terms"]
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
    if header.get("Special Terms Requested") and not header.get("Special Terms Description"):
        errors.append("Special terms description is required.")
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
        return "System Administration > Reference Data"
    if page == "Approval Matrix":
        return "System Administration > Approval Matrix"
    if page == "Approver Roster":
        return "System Administration > Approver Roster"
    if page == "System Administrator Settings":
        return "System Administration > Settings"
    if page == "Delegate Administration":
        return "System Administration > Delegates"
    if page == "Audit Log":
        return "System Administration > Audit Log"
    return str(page)


def render_header(title: str, subtitle: str = "") -> None:
    breadcrumb = breadcrumb_for_current_page()
    if breadcrumb and breadcrumb != title:
        st.markdown(f"<div class='page-breadcrumb'>{breadcrumb}</div>", unsafe_allow_html=True)
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='section-note'>{subtitle}</div>", unsafe_allow_html=True)


def page_deal_list(data: dict[str, pd.DataFrame]) -> None:
    render_header("Deal Requests", "Seeded and session-created commercial deal requests.")
    deals = visible_deals_for_current_role(combined_deals(data), data)
    sensitive_data_note()
    if deals.empty:
        st.info("No deal requests are visible for the selected persona and role.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Deals", len(deals))
    c2.metric("Draft", int((deals["Status"] == "Draft").sum()) if "Status" in deals else 0)
    c3.metric("Submitted", int((deals["Status"] == "Submitted").sum()) if "Status" in deals else 0)
    c4.metric("Changes Requested", int((deals["Status"] == "Changes Requested").sum()) if "Status" in deals else 0)
    c5.metric("High Risk", int((deals.get("Intake Risk", pd.Series(dtype=str)) == "High").sum()))

    filters = st.columns([1, 1, 1, 1, 1])
    status = filters[0].multiselect("Status", sorted(deals["Status"].dropna().unique()), default=[])
    region = filters[1].multiselect("Region", sorted(deals["Region"].dropna().unique()), default=[])
    customer_type_col = "Customer Type" if "Customer Type" in deals else "Segment"
    segment = filters[2].multiselect("Customer Type", sorted(deals[customer_type_col].dropna().unique()), default=[])
    owner = filters[3].multiselect("Sales Owner", sorted(deals["Sales Owner"].dropna().unique()), default=[])
    risk_options = sorted(deals.get("Intake Risk", pd.Series(dtype=str)).dropna().unique())
    risk = filters[4].multiselect("Risk", risk_options, default=[])

    filtered = deals.copy()
    for col, selected in [("Status", status), ("Region", region), (customer_type_col, segment), ("Sales Owner", owner), ("Intake Risk", risk)]:
        if selected and col in filtered:
            filtered = filtered[filtered[col].isin(selected)]

    if st.button("Create New Deal", type="secondary"):
        set_current_page("New Deal Intake")
    if filtered.empty:
        st.info("No deals match the current filters.")
        return

    display_cols = [col for col in ["Deal ID", "Deal Title", "Customer Name", "Deal Type", "Region", customer_type_col, "Status", "Target Close Date", "Payment Terms", "Intake Risk", "Expected Route"] if col in filtered]
    display_df = mask_sensitive_dataframe(filtered[display_cols].reset_index(drop=True))
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
    prod_dict = prod.to_dict()
    list_price = product_list_price(prod_dict)
    target = list_price * 0.9
    return {
        "SKU": prod["SKU"],
        "Quantity": 1,
        "Unit List Price": round(list_price, 2),
        "Gross Price": round(product_gross_price(prod_dict), 2),
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
        kam_users = [name for name, role in PERSONAS.items() if is_kam_role(role)]
        default_owner = current_persona() if current_persona() in kam_users else kam_users[0]
        sales_owner = owner_cols[0].selectbox("Sales Owner", kam_users, index=kam_users.index(default_owner), key="form_owner")
        sales_manager = owner_cols[1].selectbox("Sales Manager", list(SALES_MANAGER_TEAMS.keys()), key="form_manager")
        target_close = owner_cols[2].date_input("Target Close Date", value=date.today() + timedelta(days=45), key="form_close")
        effective_date = owner_cols[3].date_input("Requested Effective Date", value=date.today() + timedelta(days=60), key="form_effective")
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
            "Requested Net Price": st.column_config.NumberColumn("Requested Net Price", min_value=-1_000_000.0, step=1.0, format="$%.2f"),
            "Requested Delivery Date": st.column_config.DateColumn("Requested Delivery Date"),
            "Notes": st.column_config.TextColumn("Notes"),
        }
        editable_line_cols = [
            "SKU",
            "Quantity",
            "Requested Net Price",
            "Requested Delivery Date",
            "Notes",
        ]
        st.session_state.draft_lines = st.data_editor(
            st.session_state.draft_lines[[col for col in editable_line_cols if col in st.session_state.draft_lines]],
            num_rows="dynamic",
            use_container_width=True,
            column_config=editor_config,
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
        metric_cols[4].metric("Estimated Gross Margin %", margin_display(summary))
        if not calc_lines.empty:
            view_cols = [
                "SKU",
                "Product Name",
                "Product Category",
                "Quantity",
                "List Price",
                "Gross Price",
                "Base Rebate %",
                "Requested Net Price",
                "Requested Discount %",
                "Floor Price",
                "Guidance Price",
                "Walk-away Price",
                "Extended Requested Net",
                "Target Gross Margin %",
                "Finance Director Trigger Margin",
                "General Manager Trigger Margin",
            ]
            view = calc_lines[[col for col in view_cols if col in calc_lines]].copy()
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
        "Segment": customer_type(customer),
        "Customer Type": customer_type(customer),
        "Account Type": customer_type(customer),
        "Channel": customer_type(customer),
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
        sensitive_data_note()
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
            kpis[0].metric("Planned Revenue", sensitive_money("Planned Revenue", planned_revenue))
            kpis[1].metric("Proposed Revenue", sensitive_money("Proposed Revenue", proposed_revenue), delta=sensitive_money("Revenue Variance", revenue_variance))
            kpis[2].metric("Planned Gross Profit", sensitive_money("Planned Gross Profit", planned_gp))
            kpis[3].metric("Proposed Gross Profit", sensitive_money("Proposed Gross Profit", proposed_gp))
            kpis[4].metric("Gross Profit Variance", sensitive_money("Gross Profit Variance", gp_variance))
            margin_cols = st.columns(4)
            margin_cols[0].metric("Planned Net Price", sensitive_money("Planned Net Price", planned_net))
            margin_cols[1].metric("Proposed Net Price", money(proposed_net))
            margin_cols[2].metric("Planned Margin %", margin_value_display(planned_margin, summary["weighted_target_margin"]))
            margin_cols[3].metric("Proposed Margin %", margin_value_display(proposed_margin, summary["weighted_target_margin"]))

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

            st.info("Classified as Incremental Opportunity because it is not included in the latest financial plan.")
            kpis = st.columns(4)
            kpis[0].metric("Incremental Revenue", money(incremental_revenue))
            kpis[1].metric("Incremental Gross Profit", sensitive_money("Gross Profit", incremental_gp))
            kpis[2].metric("Proposed Margin %", margin_value_display(proposed_margin, summary["weighted_target_margin"]))
            kpis[3].metric("Historical Average Net Price", money(hist_price))
            benchmark_cols = st.columns(3)
            benchmark_cols[0].metric("Price Difference vs Historical Average %", pct(price_vs_hist))
            benchmark_cols[1].metric("Historical Margin %", sensitive_pct("Historical Margin %", hist_margin))
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
                "Incremental Revenue",
                "Incremental Gross Profit",
                "Historical Average Net Price",
                "Price vs Historical Price %",
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
            st.dataframe(mask_sensitive_dataframe(calc_lines), use_container_width=True, hide_index=True)

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
            "Target Close Date": str(header["Target Close Date"]),
            "Payment Terms": header["Payment Terms"],
            "Contract Months": header["Contract Months"],
            "Strategic Rationale": header["Business Justification"],
            "Intake Risk": "High" if "General Manager" in set(route_df["Role"]) else "Medium" if len(route_df) > 2 else "Low",
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
    if status == "Submitted":
        ensure_approval_assignments(deal_id, route_df, load_demo_data())
    return deal_id


def page_deal_detail(data: dict[str, pd.DataFrame]) -> None:
    render_header("Deal Detail", "Review intake, analysis context, route preview, and audit trail.")
    all_deals = combined_deals(data)
    deals = visible_deals_for_current_role(all_deals, data)
    sensitive_data_note()
    if deals.empty:
        st.info("No deal details are visible for the selected persona and role.")
        return
    default = st.session_state.selected_deal_id if st.session_state.selected_deal_id in set(deals["Deal ID"]) else deals.iloc[0]["Deal ID"]
    selected = st.selectbox("Deal", deals["Deal ID"].tolist(), index=deals["Deal ID"].tolist().index(default))
    st.session_state.selected_deal_id = selected
    deal = deals[deals["Deal ID"].eq(selected)].iloc[0].to_dict()
    lines = combined_lines(data)
    deal_lines = lines[lines["Deal ID"].astype(str).eq(str(selected))]
    calc_lines = normalize_lines(deal_lines, data)
    summary = summarize_lines(calc_lines)
    header = build_route_header(deal, data)
    route_df = route_preview(header, calc_lines, summary, data)
    deal_status = str(deal.get("Status", "")).strip()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", deal_status)
    c2.metric("Total Proposed", money(summary["total_proposed"]))
    c3.metric("Discount", pct(summary["discount_pct"]))
    c4.metric("Est. Margin", margin_display(summary))
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
            route_summary_col = "Approver" if "Approver" in context["route_triggers"] else "Role"
            route_summary = " -> ".join(context["route_triggers"][route_summary_col].astype(str).tolist()) if not context["route_triggers"].empty else "No route available"
            current_role = current_required_approval_role(selected, deal_status, context["route_df"])
            current_role_label = role_display_label(data, current_role) if current_role else "None"
            user_role = st.session_state.get("role", "Demo Role")
            allowed_decisions = allowed_decisions_for_role(user_role)
            st.write(f"**Recommendation:** {context['recommendation']}")
            panel_cols = st.columns(4)
            panel_cols[0].metric("Decision Score", f"{context['total_score']}/100")
            panel_cols[1].metric("Approval Route Summary", route_summary)
            panel_cols[2].metric("Current Required Role", current_role_label)
            panel_cols[3].metric("Current User Role", user_role)
            can_act_on_step = bool(current_role) and user_can_act_for_role(data, current_role, current_persona(), user_role) and bool(allowed_decisions)
            if can_act_on_step:
                st.success("Current user can capture a decision for this approval step.")
            else:
                st.warning(f"{user_role} cannot approve this step. Required role: {current_role_label}.")
            with st.expander("Approval route trigger reasons", expanded=False):
                st.dataframe(mask_sensitive_dataframe(context["route_triggers"]), use_container_width=True, hide_index=True)

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
                success, message = process_approval_decision(selected, detail_decision, detail_comment, context["route_df"], deal_status, data)
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
        st.dataframe(mask_sensitive_dataframe(pd.DataFrame([deal])), use_container_width=True, hide_index=True)
    with tabs[1]:
        st.dataframe(mask_sensitive_dataframe(calc_lines), use_container_width=True, hide_index=True)
    with tabs[2]:
        render_analysis_blocks(data, deal, calc_lines)
    with tabs[3]:
        st.dataframe(mask_sensitive_dataframe(route_df), use_container_width=True, hide_index=True)
    with tabs[4]:
        audit = pd.DataFrame(st.session_state.audit_events)
        if not audit.empty:
            audit = audit[audit["Deal ID"].astype(str).eq(str(selected))]
        st.dataframe(audit, use_container_width=True, hide_index=True)


def render_analysis_blocks(data: dict[str, pd.DataFrame], deal: dict, lines: pd.DataFrame) -> None:
    region = deal.get("Region", "")
    customer = deal.get("Customer Name", "")
    segment = deal_customer_type(deal)
    account = customer_lookup(data).get(customer, {})
    channel = deal.get("Channel", customer_type(account))
    summary = summarize_lines(lines)
    included_value = str(deal.get("Included_In_Latest_Financial_Plan", "Yes")).strip() or "Yes"
    included_in_plan = included_value.lower() == "yes"
    plan_df = plan_impact_analysis(data, lines, region, segment)
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

    st.subheader("Competitor Intelligence")
    st.info(competitor_summary(competitor_df))
    st.dataframe(mask_sensitive_dataframe(competitor_df), use_container_width=True, hide_index=True)
    with st.expander("Raw competitor signals"):
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
    selectable_roles = ROLE_ORDER if can_configure_system() else list(dict.fromkeys(([current_role()] if current_role() in ROLE_ORDER else []) + delegated_roles))
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
        required_role = current_required_approval_role(str(deal["Deal ID"]), str(deal.get("Status", "")).strip(), route)
        if role == required_role:
            update_sla_breach_audit(str(deal["Deal ID"]), required_role, data)
            sla_status = assignment_status(str(deal["Deal ID"]), required_role)
            reason = route[route["Role"].eq(role)].iloc[0]["Reason"] if role in set(route["Role"]) else "Current required approval step."
            route_row = route[route["Role"].eq(role)].iloc[0].to_dict() if role in set(route["Role"]) else {}
            rows.append(
                {
                    "Deal ID": deal["Deal ID"],
                    "Customer": deal["Customer Name"],
                    "Deal Title": deal["Deal Title"],
                    "Value": summary["total_proposed"],
                    "Discount %": summary["discount_pct"],
                    "Risk": deal.get("Intake Risk", ""),
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
    required_role = current_required_approval_role(selected, previous_status, context["route_df"])
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
    if not can_configure_system():
        st.warning("Reference data configuration is available to System Administrator.")
        return
    sensitive_data_note()
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


def page_approval_matrix(data: dict[str, pd.DataFrame]) -> None:
    render_header("Approval Matrix", "Human-readable routing rules used by approval workflow.")
    if not can_configure_system():
        st.warning("Approval matrix access is available to System Administrator.")
        return
    summary = approval_matrix_summary(data)
    if summary.empty:
        st.info("No approval routing rules are configured.")
    else:
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("Product Margin Trigger Reference")
    product_thresholds = product_margin_thresholds(data)
    if product_thresholds.empty:
        st.info("No product margin targets are configured.")
    else:
        st.dataframe(mask_sensitive_dataframe(product_thresholds), use_container_width=True, hide_index=True)

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
    render_header("System Administrator Settings", "Configure thresholds, SLA values, delegates, and role permissions.")
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
    render_header("Delegate Administration", "Maintain primary and delegate approvers for each approval role.")
    if not can_configure_system():
        st.warning("Delegate administration is available to System Administrator.")
        return
    render_delegate_editor(data)


def page_audit_log() -> None:
    render_header("Audit Log", "Session-level audit events for the Streamlit MVP.")
    if not can_configure_system():
        st.warning("Global audit log access is available to System Administrator.")
        return
    audit = pd.DataFrame(st.session_state.audit_events)
    if audit.empty:
        st.info("No audit events in this session yet.")
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
    st.session_state.current_page = "Deal Request List"
    st.rerun()


def top_navigation() -> str:
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

    current_page = st.session_state.get("current_page", "Deal Request List")
    submit_active = current_page in {"Deal Request List", "New Deal Intake"} or (
        current_page == "Deal Detail" and st.session_state.get("deal_detail_parent") == "Deal Requests"
    )
    review_active = current_page == "Approval Queue Preview" or (
        current_page == "Deal Detail" and st.session_state.get("deal_detail_parent") == "Review Queue"
    )

    with st.container():
        st.markdown("### Deal Desk Copilot")
        nav_cols = st.columns([1.05, 1.05, 0.25, 1.7, 0.9])
        if nav_cols[0].button("Submit Deal", type="primary" if submit_active else "secondary", use_container_width=True):
            st.session_state.current_page = "Deal Request List"
            st.rerun()
        if nav_cols[1].button("Review Queue", type="primary" if review_active else "secondary", use_container_width=True):
            st.session_state.current_page = "Approval Queue Preview"
            st.rerun()

        persona = nav_cols[3].selectbox("Persona", list(PERSONAS.keys()), key="persona")
        st.session_state.role = PERSONAS[persona]
        nav_cols[3].caption(st.session_state.role)

        with nav_cols[4].popover("System Settings"):
            st.metric("Session Deals", len(st.session_state.runtime_deals))
            st.metric("Audit Events", len(st.session_state.audit_events))
            if can_configure_system():
                if st.button("Reference Data", key="admin_reference_data", use_container_width=True):
                    st.session_state.current_page = "Reference Data"
                    st.rerun()
                if st.button("Approval Matrix", key="admin_approval_matrix", use_container_width=True):
                    st.session_state.current_page = "Approval Matrix"
                    st.rerun()
                if st.button("Approver Roster", key="admin_approver_roster", use_container_width=True):
                    st.session_state.current_page = "Approver Roster"
                    st.rerun()
                if st.button("System Administrator Settings", key="admin_system_settings", use_container_width=True):
                    st.session_state.current_page = "System Administrator Settings"
                    st.rerun()
                if st.button("Delegate Administration", key="admin_delegate_admin", use_container_width=True):
                    st.session_state.current_page = "Delegate Administration"
                    st.rerun()
                if st.button("Global Audit Log", key="admin_audit_log", use_container_width=True):
                    st.session_state.current_page = "Audit Log"
                    st.rerun()
                st.divider()
                st.warning("Reset clears session-created deals, status overrides, and session audit events.")
                confirm_reset = st.checkbox("I understand and want to reset this demo session.", key="admin_confirm_reset")
                if st.button("Reset Demo Session", key="admin_reset_demo", use_container_width=True, disabled=not confirm_reset):
                    reset_demo_session()
            else:
                st.caption("Configuration controls are available to System Administrator.")

    st.divider()
    return st.session_state.current_page


def main() -> None:
    inject_css()
    init_state()
    data = load_demo_data()
    page = top_navigation()
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
        page_audit_log()


if __name__ == "__main__":
    main()
