import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"
os.chdir(APP_PATH.parent)
sys.path.insert(0, str(APP_PATH.parent))


def assert_clean(app: AppTest, label: str) -> None:
    exceptions = list(app.exception)
    if exceptions:
        raise AssertionError(f"{label}: {exceptions[0].message}")


def widget_by_key(widgets, key: str):
    return next(widget for widget in widgets if widget.key == key)


for case_id in ("LAUNCH-1001", "LAUNCH-1002"):
    app = AppTest.from_file(str(APP_PATH), default_timeout=90)
    app.session_state["current_module"] = "launch"
    app.session_state["launch_page"] = "Launch Case"
    app.session_state["selected_launch_case_id"] = case_id
    app.session_state["launch_current_role"] = "Marketing · Launch Coordinator"
    app.session_state[f"launch_case_section_{case_id}"] = "Overview"
    app.run()
    assert_clean(app, f"{case_id} Overview")

    metric_labels = {metric.label for metric in app.metric}
    required_metrics = {
        "Commercial Stock Available Date",
        "5Y NPV",
        "Payback Period",
        "Y5 Net Revenue",
        "Y5 Operating Margin %",
    }
    assert required_metrics.issubset(metric_labels), f"{case_id}: missing Overview KPI {required_metrics - metric_labels}"
    assert "Y5 Patients on Product" not in metric_labels
    assert "Y5 Operating Profit" not in metric_labels

    page_text = "\n".join(str(item.value) for item in app.markdown)
    for text in (
        "Gross Margin %",
        "Operating Margin %",
        "Regulatory Dossier Submission Date",
        "Regulatory Approval Date",
        "Commercial Stock Available Date",
        "50% Market Access Reached",
        "Peak Planned Market Share Reached",
        "Current Case vs Benchmark",
    ):
        assert text in page_text, f"{case_id}: missing Overview content {text}"
    assert "First Access Start Date" not in page_text

    benchmark_widget = widget_by_key(app.selectbox, f"launch_overview_benchmark_metric_{case_id}")
    assert benchmark_widget.value == "Revenue"

    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    discount = next(row for row in records if row.get("Assumption Name") == "Discount Rate")
    assert discount["Owner"] == "Finance"
    assert discount["Source"] == "Central Reference Data"
    if case_id == "LAUNCH-1001":
        def package_status(owner: str) -> str:
            statuses = [
                str(row.get("Validation Status", "Draft"))
                for row in records
                if row.get("Owner") == owner and str(row.get("Validators", "")).strip() and not bool(row.get("Calculated", False))
            ]
            if "Alignment Required" in statuses:
                return "Alignment Required"
            if any(status in {"Draft", "Not Started"} for status in statuses):
                return "Draft"
            if statuses and all(status == "Aligned" for status in statuses):
                return "Aligned"
            return "Shared for Alignment"

        expected_statuses = {
            "Marketing": "Aligned",
            "Sales": "Shared for Alignment",
            "Medical": "Alignment Required",
            "Market Access": "Aligned",
            "Regulatory": "Shared for Alignment",
            "Supply / Operations": "Draft",
            "Finance": "Aligned",
        }
        assert {owner: package_status(owner) for owner in expected_statuses} == expected_statuses
        warnings = "\n".join(str(item.value) for item in app.warning)
        for prefix in ("REGULATORY ·", "SUPPLY ·", "CLINICAL ·", "ALIGNMENT ·"):
            assert prefix in warnings, f"Missing risk prefix: {prefix}"

    app.session_state["launch_current_role"] = "Finance"
    app.session_state[f"launch_case_section_{case_id}"] = "Workstreams"
    app.run()
    assert_clean(app, f"{case_id} Finance reference")
    basis_key = f"launch_discount_rate_basis_{case_id}"
    widget_by_key(app.radio, basis_key).set_value("Override for This Case").run()
    assert_clean(app, f"{case_id} Discount Rate override mode")
    widget_by_key(app.number_input, f"launch_discount_rate_override_{case_id}").set_value(11.5).run()
    widget_by_key(app.text_input, f"launch_discount_rate_rationale_{case_id}").set_value("Management valuation reference.").run()
    assert_clean(app, f"{case_id} Discount Rate override")
    records = app.session_state[f"launch_case_assumptions_{case_id}"]
    discount = next(row for row in records if row.get("Assumption Name") == "Discount Rate")
    assert abs(float(discount["Value"]) - 0.115) < 1e-9
    assert bool(discount["Override Enabled"])
    assert discount["Override Rationale"] == "Management valuation reference."

print("launch overview management smoke test complete")
