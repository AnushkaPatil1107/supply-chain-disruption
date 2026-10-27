import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import os
from simulation import (
    add_catalog_brand, build_equipment_maps, calculate_customer_order_impact,
    create_sample_chain, load_company_equipment, parse_equipment_types, PRESETS,
    remove_catalog_brand, save_company_equipment, update_catalog_brand
)
from sms_notifications import (
    send_disruption_alert,
    send_solution_notification
)

DISRUPTION_TYPES = [
    "Supply chain delay",
    "Production facility shutdown",
    "Materials shortage",
    "Transportation issues",
    "Quality control failure",
    "Labor shortage",
    "Natural disaster",
    "Weather-related delays",
    "Customs or import delay",
    "Component shortage"
]

DEFAULT_SOLUTION = "Find alternative supplier"


def create_bar_chart(
    data: dict,
    title: str,
    y_axis: str,
    categories_enabled: bool = False,
    category_names=None,
) -> go.Figure:
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#64748B")
        )
        return fig

    visible_data = sorted(data.items(), key=lambda item: item[1], reverse=True)[:18]
    labels = [str(label) for label, _ in visible_data]
    values = [value for _, value in visible_data]
    palette = px.colors.qualitative.Bold

    def category_for(label: str) -> str:
        if categories_enabled:
            for category in category_names or ():
                if label.endswith(f" ({category})"):
                    return category
        return "Equipment"

    category_colors = {
        category: palette[index % len(palette)]
        for index, category in enumerate(dict.fromkeys(category_for(label) for label in labels))
    }
    colors = [category_colors[category_for(label)] for label in labels]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        customdata=[category_for(label) for label in labels],
        hovertemplate="%{y}<br>%{customdata}<br>%{x:,.0f} units<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#142B3B"), x=0, xanchor="left"),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.38,
        margin=dict(t=54, l=12, r=22, b=28),
        height=max(310, 38 * len(labels) + 100),
        font=dict(family="Inter, sans-serif", color="#536273"),
        xaxis=dict(title=y_axis, showgrid=True, gridcolor="#E8EDF1", zeroline=False),
        yaxis=dict(autorange="reversed", showgrid=False, tickfont=dict(size=12))
    )
    return fig


def get_or_create_simulation(
    num_suppliers, num_manufacturers, num_customers,
    base_inventory, disruption_probability, company_equipment=None,
    target_equipment_type=None, target_brand=None
):
    if company_equipment is None:
        company_equipment = load_company_equipment()
    sim_key = (num_suppliers, num_manufacturers, num_customers,
               base_inventory, disruption_probability,
               tuple((brand, tuple(types)) for brand, types in company_equipment.items()),
               target_equipment_type, target_brand)

    if st.session_state.get('sim_params') != sim_key:
        st.session_state.sim_params = sim_key
        st.session_state.simulation = create_sample_chain(
            num_suppliers=num_suppliers,
            num_manufacturers=num_manufacturers,
            num_customers=num_customers,
            base_inventory=base_inventory,
            disruption_probability=disruption_probability,
            company_equipment=company_equipment,
            target_equipment_type=target_equipment_type,
            target_brand=target_brand,
        )
        st.session_state.applied_disruptions = {}
        st.session_state.applied_solutions = {}
        for result_key in ('normal_results', 'disrupted_results', 'solution_results',
                           'disruptions', 'notification_results'):
            st.session_state.pop(result_key, None)

    return st.session_state.simulation


def persist_catalog_change(updated_catalog, success_message):
    try:
        save_company_equipment(updated_catalog)
    except (OSError, ValueError) as error:
        st.error(f"Catalog was not saved: {error}")
        return

    st.session_state["catalog_notice"] = success_message
    st.rerun()


def render_catalog_editor(company_equipment):
    notice = st.session_state.pop("catalog_notice", None)
    if notice:
        st.success(notice)

    with st.expander("Equipment catalog", expanded=False):
        st.caption("Changes are saved for this workspace and used in new scenario runs.")
        action = st.radio(
            "Catalog action", ["Edit a brand", "Add a brand"],
            horizontal=True, key="catalog_action"
        )

        if action == "Add a brand":
            form_key = f"catalog_add_form_{len(company_equipment)}"
            with st.form(form_key):
                brand_name = st.text_input(
                    "Brand name", max_chars=100, key=f"{form_key}_brand"
                )
                types_text = st.text_area(
                    "Equipment types",
                    placeholder="Enter one type per line or separate types with commas",
                    key=f"{form_key}_types",
                )
                add_submitted = st.form_submit_button("Add brand", type="primary")

            if add_submitted:
                normalized_brand = brand_name.strip()
                try:
                    updated_catalog = add_catalog_brand(
                        company_equipment, normalized_brand, parse_equipment_types(types_text)
                    )
                except ValueError as error:
                    st.error(str(error))
                else:
                    persist_catalog_change(
                        updated_catalog,
                        f"Added {normalized_brand} to the equipment catalog.",
                    )
        else:
            selection_key = f"catalog_edit_selection_{abs(hash(tuple(company_equipment)))}"
            selected_brand = st.selectbox(
                "Brand to edit", list(company_equipment), key=selection_key
            )
            form_key = f"catalog_edit_form_{selected_brand}"
            with st.form(form_key):
                edited_brand = st.text_input(
                    "Brand name",
                    value=selected_brand,
                    max_chars=100,
                    key=f"{form_key}_brand",
                )
                types_text = st.text_area(
                    "Equipment types",
                    value="\n".join(company_equipment[selected_brand]),
                    help="Enter one type per line or separate types with commas.",
                    key=f"{form_key}_types",
                )
                edit_submitted = st.form_submit_button("Save changes", type="primary")

            if edit_submitted:
                normalized_brand = edited_brand.strip()
                try:
                    updated_catalog = update_catalog_brand(
                        company_equipment,
                        selected_brand,
                        normalized_brand,
                        parse_equipment_types(types_text),
                    )
                except ValueError as error:
                    st.error(str(error))
                else:
                    persist_catalog_change(
                        updated_catalog, f"Saved changes to {normalized_brand}."
                    )

            confirmed = st.checkbox(
                f"Confirm removal of {selected_brand}",
                key=f"catalog_confirm_delete_{selected_brand}",
            )
            if st.button(
                "Remove brand and its equipment types",
                disabled=not confirmed,
                key=f"catalog_delete_{selected_brand}",
            ):
                try:
                    updated_catalog = remove_catalog_brand(company_equipment, selected_brand)
                except ValueError as error:
                    st.error(str(error))
                else:
                    persist_catalog_change(
                        updated_catalog, f"Removed {selected_brand} from the equipment catalog."
                    )


def display_ai_insights(tab, simulation_data):
    tab.header("Supply network analysis")

    if not simulation_data:
        tab.info("Estimate the order impact first to generate network insights.")
        return

    from advanced_agent import get_agent_recommendations
    agent_insights = get_agent_recommendations(simulation_data)

    summary = agent_insights.get("summary", {})
    tab.subheader("Network summary")
    tab.write(summary.get("headline", "Supply Chain Analysis"))

    key_metrics = summary.get("key_metrics", {})
    cols = tab.columns(4)
    if key_metrics:
        cols[0].metric("Disruption rate", key_metrics.get("disruption_rate", "N/A"))
        cols[1].metric("Risk severity", key_metrics.get("severity", "N/A"))
        cols[2].metric("Bottlenecks", key_metrics.get("critical_bottlenecks", "N/A"))
        cols[3].metric("Network resilience", summary.get("resilience_score", "N/A"))

    tab.subheader("Key Findings")
    for insight in summary.get("top_insights", []):
        tab.markdown(f"- {insight}")

    with tab.expander("Detailed Disruption Analysis", expanded=False):
        disruption_analysis = agent_insights.get("disruption_analysis", {})
        st.subheader("Disruption Summary")
        disruption_summary = disruption_analysis.get("disruption_summary", {})
        st.write(f"- Total Suppliers: {disruption_summary.get('total_suppliers', 0)}")
        st.write(f"- Disrupted Suppliers: {disruption_summary.get('disrupted_suppliers', 0)}")
        st.write(f"- Most Common Disruption: {disruption_summary.get('most_common_disruption', 'N/A')}")
        st.write(f"- Highest Risk Categories: {', '.join(disruption_summary.get('highest_risk_categories', ['N/A']))}")

        st.subheader("Category Impact Analysis")
        for impact in disruption_analysis.get("category_impacts", []):
            st.write(f"**{impact.get('category')}**: {impact.get('impact_percentage', 0):.1f}% impact, "
                     f"{impact.get('severity', 'Unknown')} severity")

        st.subheader("Recommended Actions")
        for rec in disruption_analysis.get("recommendations", [])[:5]:
            st.markdown(f"- **{rec.get('type')}**: {rec.get('action')} for {rec.get('target')} "
                        f"({rec.get('priority')} priority)")

    with tab.expander("What-If Scenario Analysis", expanded=False):
        what_if = agent_insights.get("what_if_scenarios", {})

        st.subheader("Increased Disruption Scenario")
        for scenario in what_if.get("increased_disruption", {}).get("projected_scenarios", []):
            st.write(f"- At {scenario.get('disruption_probability', 0):.1%} probability: "
                     f"{scenario.get('estimated_impact_factor', 0):.1%} impact, "
                     f"production down {scenario.get('production_decrease', 0):.0f} units")

        st.subheader("Improved Resilience Scenario")
        for improvement in what_if.get("improved_resilience", {}).get("projected_improvements", []):
            st.write(f"- With {improvement.get('resilience_improvement', '0%')} improvement: "
                     f"{improvement.get('production_increase', 0):.0f} additional units produced")

        st.subheader("Category Failure Scenario")
        for failure in what_if.get("category_failure", {}).get("failure_scenarios", []):
            st.write(f"- {failure.get('category', 'Unknown')}: {failure.get('business_impact', 'Unknown')} "
                     f"impact, recovery time {failure.get('estimated_recovery_time', 'Unknown')}")

    with tab.expander("Supplier Cluster Analysis", expanded=False):
        for cluster in agent_insights.get("cluster_analysis", {}).get("clusters", []):
            st.write(f"**Cluster {cluster.get('cluster_id', 0)+1}**: {cluster.get('size', 0)} suppliers, "
                     f"{cluster.get('risk_level', 'Unknown')} risk")
            st.write(f"- Dominant Category: {cluster.get('dominant_category', 'Mixed')}")
            st.write(f"- Characteristics: {cluster.get('characteristics', 'Unknown')}")
            st.write(f"- Average Supply Ratio: {cluster.get('avg_supply_ratio', 0):.2f}")

    with tab.expander("Recovery Forecast", expanded=False):
        recovery = agent_insights.get("disruption_analysis", {}).get("recovery_forecast", {})
        if recovery:
            st.write(f"Expected recovery time: **{recovery.get('estimated_recovery_time', 'Unknown')}**")
            st.write(f"Confidence: **{recovery.get('confidence', 'Unknown')}**")
            for phase in recovery.get("recovery_phases", []):
                st.write(f"**{phase.get('phase', 'Unknown')}** ({phase.get('timeline', 'Unknown')})")
                for activity in phase.get('activities', []):
                    st.write(f"- {activity}")


def main():
    st.set_page_config(
        page_title="Groundwork | Order Impact",
        page_icon="G",
        layout="wide",
        initial_sidebar_state="auto"
    )

    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
      :root { --ink:#142b3b; --muted:#64748b; --orange:#ee792f; --line:#e2e9ed; --paper:#f5f7f8; }
      .stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
      [data-testid="stHeader"] { background:rgba(245,247,248,.88); }
      [data-testid="stMainBlockContainer"] { max-width:1440px; padding-top:2.1rem; padding-bottom:4rem; }
      [data-testid="stSidebar"] { background:#122b3a; border-right:1px solid #274453; }
      [data-testid="stSidebar"] * { color:#eaf1f3; }
      [data-testid="stSidebar"] [data-baseweb="select"] div,
      [data-testid="stSidebar"] input { color:#172b3a; }
      [data-testid="stSidebar"] [data-testid="stExpander"] { border-color:#31505d; }
      [data-testid="stSidebar"] hr { border-color:#31505d; }
      h1,h2,h3,h4 { color:var(--ink); font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
      [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4 { color:#f3f7f8; }
      .hero {
        position:relative; overflow:hidden; border-radius:24px; padding:34px 38px;
        color:#fff; background:linear-gradient(112deg,#142f40 0%,#1c4353 64%,#275262 100%);
        box-shadow:0 18px 45px rgba(20,43,59,.13); margin:0 0 24px;
      }
      .hero:after { content:""; position:absolute; width:330px; height:330px; right:-82px; top:-140px;
        border:1px solid rgba(255,255,255,.13); border-radius:50%;
        box-shadow:0 0 0 32px rgba(255,255,255,.035),0 0 0 68px rgba(255,255,255,.025); }
      .hero-kicker { font-size:11px; font-weight:700; letter-spacing:.17em; text-transform:uppercase;
        color:#f6ad71; margin-bottom:12px; }
      .hero h1 { color:white; font-size:clamp(30px,4vw,48px); line-height:1.08; margin:0 0 12px; }
      .hero p { position:relative; z-index:1; max-width:740px; color:#d2e0e4;
        font-size:15px; line-height:1.65; margin:0; }
      .section-kicker { color:#e27631; font-size:11px; font-weight:700; letter-spacing:.13em;
        text-transform:uppercase; margin:30px 0 5px; }
      .stButton > button { border-radius:10px; font-weight:700; transition:all .18s ease; }
      .stButton > button[kind="primary"] { background:#ed792f; border-color:#ed792f; color:#fff; }
      .stButton > button[kind="primary"]:hover { background:#d96522; border-color:#d96522;
        transform:translateY(-1px); box-shadow:0 7px 18px rgba(237,121,47,.24); }
      [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:15px;
        padding:17px 19px; box-shadow:0 4px 15px rgba(20,43,59,.035); }
      [data-testid="stMetricLabel"] { color:#64748b; font-size:12px; }
      [data-testid="stMetricValue"] { color:var(--ink); font-family:'Manrope',sans-serif;
        font-size:clamp(18px,1.7vw,24px); }
      [data-testid="stMetricValue"] > div { white-space:normal; overflow-wrap:anywhere; line-height:1.2; }
      [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:7px; border-bottom:1px solid var(--line); }
      [data-testid="stTabs"] button[role="tab"] { background:transparent; border-radius:9px 9px 0 0;
        padding:12px 17px; color:#627180; font-weight:600; }
      [data-testid="stTabs"] button[aria-selected="true"] { color:#de6c28; border-bottom:2px solid #ed792f; }
      [data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:13px; }
      [data-testid="stSidebar"] [data-testid="stExpander"] {
        background:#122b3a; border-color:#31505d;
      }
      [data-testid="stSidebar"] .stButton > button { color:#142b3b; }
      [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background:#ed792f; border-color:#ed792f; color:#fff;
      }
      [data-testid="stPlotlyChart"] { background:#fff; border:1px solid var(--line);
        border-radius:15px; padding:8px; }
      .dataset-note { font-size:12px; color:#71808d; padding:2px 0 5px; }
      .brand-mark { width:36px;height:36px;border-radius:10px;background:#ed792f;color:white;
        display:flex;align-items:center;justify-content:center;font:800 16px 'Manrope',sans-serif;
        margin-bottom:12px; }
      .sidebar-brand { font:800 18px 'Manrope',sans-serif; letter-spacing:-.04em; color:white; }
      .sidebar-caption { font-size:10px; letter-spacing:.14em; text-transform:uppercase;
        color:#9bb2bb; margin:2px 0 22px; }
      @media (max-width:700px) {
        [data-testid="stMainBlockContainer"] { padding:1rem 1rem 3rem; }
        .hero { padding:26px 24px; border-radius:18px; }
      }
    </style>
    """, unsafe_allow_html=True)

    for key, default in {
        "disruption_settings": {},
        "applied_disruptions": {},
        "applied_solutions": {},
        "notifications_enabled": False,
        "phone_number": "",
        "sim_params": None,
    }.items():
        st.session_state.setdefault(key, default)

    try:
        company_equipment = load_company_equipment()
        equipment_categories, dynamic_suppliers, _ = build_equipment_maps(company_equipment)
    except (OSError, ValueError) as error:
        st.error(f"The equipment catalog could not be loaded: {error}")
        st.stop()

    with st.sidebar:
        st.markdown('<div class="brand-mark">G</div><div class="sidebar-brand">GROUNDWORK</div>'
                    '<div class="sidebar-caption">Order disruption impact</div>',
                    unsafe_allow_html=True)
        render_catalog_editor(company_equipment)

        st.markdown("### Your order")
        equipment_types = sorted(equipment_categories)
        if st.session_state.get("order_equipment_type") not in equipment_types:
            st.session_state["order_equipment_type"] = (
                "Excavators" if "Excavators" in equipment_types else equipment_types[0]
            )
        order_equipment_type = st.selectbox(
            "Equipment type", equipment_types, key="order_equipment_type"
        )
        listed_brands = sorted(
            equipment_categories[order_equipment_type]["manufacturers"]
        )
        brand_options = ["Any compatible brand"] + listed_brands
        if st.session_state.get("order_brand") not in brand_options:
            st.session_state["order_brand"] = "Any compatible brand"
        order_brand = st.selectbox(
            "Brand requirement", brand_options, key="order_brand"
        )
        target_brand = None if order_brand == "Any compatible brand" else order_brand
        order_quantity = st.number_input(
            "Units on order", min_value=1, max_value=10000, value=100,
            step=1, key="order_quantity"
        )
        on_hand_units = st.number_input(
            "Usable stock on hand", min_value=0, max_value=10000, value=0,
            step=1, key="on_hand_units"
        )
        st.caption("Estimates cover equipment units only, not price or delivery dates.")

        st.markdown("### Disruption scenario")
        selected_preset = st.selectbox(
            "Supply scenario", ["Custom"] + [preset.name for preset in PRESETS],
            key="preset_selector"
        )

        if selected_preset != "Custom":
            preset = next(preset for preset in PRESETS if preset.name == selected_preset)
            num_suppliers = min(preset.suppliers, len(dynamic_suppliers[order_equipment_type]))
            manufacturer_limit = 1 if target_brand else len(listed_brands)
            num_manufacturers = min(preset.manufacturers, manufacturer_limit)
            num_customers = 1
            base_inventory = preset.base_inventory
            disruption_probability = preset.disruption_probability
            st.caption(preset.description)
            st.caption(
                f"{num_suppliers} modeled suppliers · {num_manufacturers} production source"
                f"{'' if num_manufacturers == 1 else 's'} · "
                f"{disruption_probability:.0%} disruption likelihood"
            )
        else:
            with st.expander("Scenario assumptions", expanded=False):
                st.caption("Adjust the modeled supply network for this equipment type.")
                available_pair_count = len(dynamic_suppliers[order_equipment_type])
                supplier_limit = max(1, available_pair_count)
                manufacturer_limit = 1 if target_brand else len(listed_brands)
                if st.session_state.get("num_suppliers_slider", 8) > supplier_limit:
                    st.session_state["num_suppliers_slider"] = supplier_limit
                if st.session_state.get("num_manufacturers_slider", 5) > manufacturer_limit:
                    st.session_state["num_manufacturers_slider"] = manufacturer_limit
                num_suppliers = st.slider(
                    "Modeled suppliers", 1, supplier_limit, min(8, supplier_limit),
                    key="num_suppliers_slider"
                )
                num_manufacturers = st.slider(
                    "Production sources", 1, manufacturer_limit, min(5, manufacturer_limit),
                    key="num_manufacturers_slider"
                )
                disruption_probability = st.slider(
                    "Disruption likelihood", 5, 95, 20, 5,
                    format="%d%%", key="disruption_probability_slider"
                ) / 100
            num_customers = 1
            base_inventory = 250

    simulation = get_or_create_simulation(
        num_suppliers, num_manufacturers, num_customers,
        base_inventory, disruption_probability, company_equipment,
        order_equipment_type, target_brand
    )
    st.session_state["simulation"] = simulation
    st.session_state["suppliers"] = simulation.suppliers
    st.session_state["manufacturers"] = simulation.manufacturers

    with st.sidebar:
        with st.expander("Equipment capacity assumptions", expanded=False):
            for manufacturer in simulation.manufacturers:
                key = f"{manufacturer.name}_{manufacturer.category}"
                simulation.units_produced[key] = st.slider(
                    manufacturer.display_name, 10, 1000, 100,
                    key=f"mfr_slider_{key}"
                )
        with st.expander("Supplier availability assumptions", expanded=False):
            for supplier in simulation.suppliers:
                supplier.supply_amount = st.slider(
                    supplier.display_name, 10, 1000, 100,
                    key=f"sup_slider_{supplier.name}_{supplier.category}"
                )
        with st.expander("SMS notifications", expanded=False):
            st.checkbox("Enable SMS alerts", key="notifications_enabled")
            if st.session_state.notifications_enabled:
                st.session_state.phone_number = st.text_input(
                    "Phone number with country code",
                    value=st.session_state.phone_number,
                    key="phone_number_input",
                    placeholder="+1 555 000 0000"
                )
                has_twilio_creds = all(os.environ.get(name) for name in (
                    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"
                ))
                if not has_twilio_creds:
                    st.caption("SMS delivery is unavailable until Twilio is configured.")

    st.markdown(
        '<div class="hero"><div class="hero-kicker">Groundwork / Customer order protection</div>'
        '<h1>Know what a supply disruption could mean for your order.</h1>'
        '<p>Choose the construction equipment you ordered, set your order quantity and available stock, '
        'then see how a supply interruption could change the units available to your project.</p></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="dataset-note">Market map: {len(company_equipment)} equipment brands · '
        f'{len(equipment_categories)} equipment types. Select an order in the sidebar. '
        'Results are scenario estimates based on listed equipment brands, not confirmed delivery dates or prices.</div>',
        unsafe_allow_html=True
    )

    top_cols = st.columns([1.6, 1.25, 1, 1])
    brand_summary = "Flexible" if target_brand is None else order_brand
    top_cols[0].metric("Equipment on order", order_equipment_type)
    top_cols[1].metric("Brand rule", brand_summary)
    top_cols[2].metric("Order quantity", f"{order_quantity:,} units")
    top_cols[3].metric("Usable stock", f"{on_hand_units:,} units")

    st.markdown('<div class="section-kicker">Customer impact check</div>', unsafe_allow_html=True)
    st.subheader("Stress-test your order")
    st.write(
        "Choose possible supply disruptions and recovery actions, then estimate how much of your "
        "order could be covered."
    )

    with st.expander("Disruption planner", expanded=False):
        st.caption(
            "Choose modeled suppliers of this equipment type. Leave all unchecked to use the "
            "scenario's random disruption likelihood."
        )
        suppliers_by_category = {}
        for supplier in simulation.suppliers:
            suppliers_by_category.setdefault(supplier.category, []).append(supplier)
        total_suppliers = len(simulation.suppliers)

        with st.form("disruption_form", clear_on_submit=False):
            form_data = {}
            for category, suppliers in suppliers_by_category.items():
                st.markdown(f"**{category}**")
                for supplier in suppliers:
                    uid = f"{supplier.name}__{supplier.category}"
                    prev = st.session_state.applied_disruptions.get(supplier.name)
                    prev_solution = st.session_state.applied_solutions.get(
                        supplier.name, DEFAULT_SOLUTION
                    )
                    col1, col2, col3 = st.columns([1.3, 1.3, 2])
                    with col1:
                        checked = st.checkbox(
                            supplier.name.removesuffix(f" ({supplier.category})"),
                            value=prev is not None, key=f"fcb_{uid}"
                        )
                    with col2:
                        disruption_index = (
                            DISRUPTION_TYPES.index(prev) if prev in DISRUPTION_TYPES else 0
                        )
                        disruption = st.selectbox(
                            "Disruption type", DISRUPTION_TYPES, index=disruption_index,
                            key=f"fdt_{uid}", label_visibility="collapsed"
                        )
                    with col3:
                        solution = st.text_input(
                            "Recovery action", value=prev_solution, key=f"fsol_{uid}",
                            label_visibility="collapsed", placeholder="Recovery action"
                        )
                    form_data[supplier.name] = {
                        "checked": checked,
                        "disruption": disruption,
                        "solution": solution
                    }

            submitted = st.form_submit_button("Apply disruption plan", type="primary")

        if submitted:
            st.session_state.applied_disruptions = {
                name: data["disruption"] for name, data in form_data.items()
                if data["checked"]
            }
            st.session_state.applied_solutions = {
                name: data["solution"] for name, data in form_data.items()
                if data["checked"]
            }
            if st.session_state.applied_disruptions:
                st.success(
                    f"Plan saved with {len(st.session_state.applied_disruptions)} "
                    f"disruption{'s' if len(st.session_state.applied_disruptions) != 1 else ''}."
                )
            else:
                st.info("Plan cleared. Random scenario disruptions may occur during the run.")

        st.caption(
            f"{len(st.session_state.applied_disruptions)} of {total_suppliers} "
            "supply partners selected for disruption."
        )

    with st.expander(f"Browse equipment map · {len(equipment_categories)} types", expanded=False):
        category_columns = st.columns(3)
        for index, (category, details) in enumerate(equipment_categories.items()):
            with category_columns[index % 3]:
                st.markdown(f"**{category}**")
                st.caption(", ".join(details["manufacturers"]))

    run_col, guidance_col = st.columns([1, 2.8], vertical_alignment="center")
    with run_col:
        run_simulation = st.button(
            "Estimate order impact", type="primary", key="run_simulations_button",
            use_container_width=True
        )
    with guidance_col:
        st.caption("Compare your order before disruption, during disruption, and after a response.")

    if run_simulation:
        simulation.disruptions.clear()
        simulation.solutions.clear()
        simulation.disruptions.update(st.session_state.applied_disruptions)
        simulation.solutions.update(st.session_state.applied_solutions)
        normal_results = simulation.simulate_normal()
        disruption_results = simulation.simulate_with_disruptions()
        solution_results = simulation.simulate_with_solutions()
        st.session_state["normal_results"] = normal_results
        st.session_state["disrupted_results"] = disruption_results
        st.session_state["solution_results"] = solution_results
        st.session_state["disruptions"] = dict(simulation.disruptions)

        notification_results = []
        if st.session_state.notifications_enabled and st.session_state.phone_number:
            for event in disruption_results.get("disruption_events", []):
                notification_results.append(send_disruption_alert(
                    st.session_state.phone_number, event["supplier"],
                    event["disruption"], event["category"]
                ))
            for event in solution_results.get("solution_events", []):
                notification_results.append(send_solution_notification(
                    st.session_state.phone_number, event["disrupted_supplier"],
                    event["solution"], event["category"]
                ))
        st.session_state["notification_results"] = notification_results
        st.toast("Order impact estimate complete")

    if "normal_results" not in st.session_state:
        st.markdown(
            '<div style="margin-top:26px;padding:24px;border:1px solid #e2e9ed;'
            'border-radius:16px;background:#fff;color:#64748b;">'
            '<strong style="color:#142b3b">Your order impact estimate is ready.</strong><br>'
            'Set a disruption plan above or keep the scenario probabilistic, then estimate how much '
            'of your order supply and current stock could cover.</div>',
            unsafe_allow_html=True
        )
        return

    normal_results = st.session_state["normal_results"]
    disruption_results = st.session_state["disrupted_results"]
    solution_results = st.session_state["solution_results"]
    order_impacts = {
        "Before disruption": calculate_customer_order_impact(
            normal_results, order_equipment_type, order_quantity, on_hand_units, target_brand
        ),
        "During disruption": calculate_customer_order_impact(
            disruption_results, order_equipment_type, order_quantity, on_hand_units, target_brand
        ),
        "After response": calculate_customer_order_impact(
            solution_results, order_equipment_type, order_quantity, on_hand_units, target_brand
        ),
    }
    st.markdown('<div class="section-kicker">Analysis workspace</div>', unsafe_allow_html=True)
    st.subheader("What this means for your order")
    disrupted_impact = order_impacts["During disruption"]
    baseline_impact = order_impacts["Before disruption"]
    recovery_impact = order_impacts["After response"]
    supply_reduction = max(
        0, baseline_impact["available_units"] - disrupted_impact["available_units"]
    )
    metric_cols = st.columns(4)
    metric_cols[0].metric(
        "Order quantity", f"{order_quantity:,} units"
    )
    metric_cols[1].metric(
        "Supply during disruption", f"{disrupted_impact['available_units']:,} units",
        delta=f"{supply_reduction:,} units lost vs. baseline", delta_color="inverse"
    )
    metric_cols[2].metric(
        "Still uncovered after stock", f"{disrupted_impact['uncovered_units']:,} units"
    )
    metric_cols[3].metric(
        "Covered after response",
        f"{recovery_impact['covered_units']:,} / {order_quantity:,} units",
        delta=f"{recovery_impact['coverage_percentage']:.0f}% covered"
    )

    if disrupted_impact["uncovered_units"]:
        st.warning(
            f"Estimated shortfall: {disrupted_impact['uncovered_units']:,} of "
            f"{order_quantity:,} units remain uncovered after using "
            f"{disrupted_impact['inventory_used']:,} units of your stock buffer."
        )
    elif supply_reduction:
        st.info(
            f"Modeled supply falls by {supply_reduction:,} units, but your selected order "
            "remains covered by available supply and stock."
        )
    else:
        st.success("The selected disruption does not create an uncovered order in this scenario.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Your order", "Modeled supply", "Disruption details", "Recovery options", "Risk insights"
    ])
    with tab1:
        st.markdown("#### Order coverage across scenarios")
        phase_names = list(order_impacts)
        phase_impacts = [order_impacts[phase] for phase in phase_names]
        comparison_fig = go.Figure(go.Bar(
            x=phase_names,
            y=[impact["covered_units"] for impact in phase_impacts],
            marker_color="#ed792f",
            text=[f"{impact['covered_units']:,} / {order_quantity:,}" for impact in phase_impacts],
            textposition="outside",
            customdata=[
                [impact["available_units"], impact["uncovered_units"]]
                for impact in phase_impacts
            ],
            hovertemplate=(
                "%{x}<br>Order covered: %{y:,.0f} units"
                "<br>Supply available: %{customdata[0]:,.0f} units"
                "<br>Still uncovered: %{customdata[1]:,.0f} units<extra></extra>"
            ),
        ))
        comparison_fig.update_layout(
            height=360, plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=28, l=20, r=20, b=35),
            showlegend=False, font=dict(color="#536273"),
            xaxis_title=None, yaxis_title="Order units covered",
            yaxis=dict(range=[0, max(order_quantity * 1.16, 1)], gridcolor="#E8EDF1")
        )
        st.plotly_chart(comparison_fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            "Coverage includes your usable stock. Supply availability is a scenario estimate; "
            "the model does not predict a specific delivery date or order cost."
        )

    with tab2:
        st.markdown("#### Modeled supply by equipment brand")
        supply_view = st.radio(
            "Operating phase", ["Baseline", "Disrupted", "Recovered"],
            horizontal=True, label_visibility="collapsed", key="supply_phase"
        )
        supply_results = {
            "Baseline": normal_results,
            "Disrupted": disruption_results,
            "Recovered": solution_results
        }[supply_view]
        st.plotly_chart(create_bar_chart(
            supply_results["supplier_amounts"],
            f"{supply_view} supply volume", "Units", categories_enabled=True,
            category_names=equipment_categories.keys(),
        ), use_container_width=True, config={"displayModeBar": False})

    with tab3:
        events = disruption_results.get("disruption_events", [])
        st.markdown(f"#### {len(events)} disruption{'s' if len(events) != 1 else ''} detected")
        if not events:
            st.success("No disruption events occurred in this run.")
        else:
            for event in events:
                with st.container(border=True):
                    st.markdown(f"**{event['supplier']}** · {event['category']}")
                    st.caption(event["disruption"])
        notifications = st.session_state.get("notification_results", [])
        if notifications:
            successes = sum(result.get("success", False) for result in notifications)
            st.caption(f"SMS status: {successes} of {len(notifications)} notifications sent.")

    with tab4:
        solution_events = solution_results.get("solution_events", [])
        st.markdown(f"#### {len(solution_events)} recovery action{'s' if len(solution_events) != 1 else ''}")
        if not solution_events:
            st.info("No recovery actions were needed. Apply a disruption plan to compare responses.")
        else:
            for event in solution_events:
                with st.container(border=True):
                    st.markdown(f"**{event['disrupted_supplier']}** · {event['category']}")
                    st.write(event["solution"])
                    if event.get("redistributed_to"):
                        st.caption("Load shared with: " + ", ".join(event["redistributed_to"]))
                    else:
                        st.caption("No unaffected alternative was available in this equipment category.")

    with tab5:
        tab5.subheader("Order coverage by scenario")
        coverage_cols = tab5.columns(3)
        for column, phase in zip(coverage_cols, order_impacts):
            impact = order_impacts[phase]
            column.metric(
                phase,
                f"{impact['covered_units']:,} / {order_quantity:,} units",
                delta=f"{impact['uncovered_units']:,} units uncovered",
                delta_color="inverse",
            )
        tab5.caption(
            "Coverage includes modeled supply plus usable stock. Network insights below explain "
            "which modeled suppliers and equipment types contributed to the result."
        )
        tab5.divider()
        simulation_data = {
            "suppliers": st.session_state.get("suppliers", []),
            "manufacturers": st.session_state.get("manufacturers", []),
            "disruptions": st.session_state.get("disruptions", {}),
            "normal_results": normal_results,
            "disrupted_results": disruption_results,
            "solution_results": solution_results,
            "simulation": simulation
        }
        display_ai_insights(tab5, simulation_data)


if __name__ == "__main__":
    main()
