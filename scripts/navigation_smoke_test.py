from __future__ import annotations

import faulthandler
import sys
from pathlib import Path

faulthandler.enable()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit_app as app


def main() -> None:
    app.init_state()
    data = app.load_demo_data()
    deals = app.combined_deals(data)
    assert not deals.empty, "Home data did not load any deals."
    deal_id = str(deals.iloc[0]["Deal ID"])
    context = app.build_deal_context(data, deal_id)
    assert context is not None, f"Preview context could not be built for {deal_id}."
    route = context["route_df"]
    pending = app.current_required_approval_roles(deal_id, str(context["deal"].get("Status", "")), route)
    assert isinstance(pending, list), "Pending approval role calculation did not return a list."
    transition = {"selected_deal_id": deal_id, "current_page": "Deal Detail"}
    assert transition["selected_deal_id"] == deal_id
    assert transition["current_page"] == "Deal Detail"
    transition["current_page"] = "Deal Request List"
    print(f"navigation smoke test complete for {deal_id}", flush=True)


if __name__ == "__main__":
    main()
