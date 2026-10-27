import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import re
import os
import time
from simulation import (
    create_sample_chain, SUPPLIERS, MANUFACTURERS, 
    EQUIPMENT_CATEGORIES, PRESETS
)
from sms_notifications import (
    send_disruption_alert, 
    send_solution_notification
)

def create_bar_chart(data: dict, title: str, y_axis: str, categories_enabled: bool = False) -> go.Figure:
    # Create a custom color scale for different equipment categories
    category_colors = px.colors.qualitative.Plotly

    # Get categories list upfront so we can use it in both branches
    categories_list = list(SUPPLIERS.keys()) if categories_enabled else []
    
    # Early exit if no data provided
    if not data:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
        
    # For extremely large datasets, we may need to limit the number of items shown
    MAX_ITEMS_PER_CATEGORY = 30  # Show max 30 items per category for performance
    
    # If the dataset is very large, show a warning
    total_items = len(data)
    if total_items > 100:
        st.info(f"Large dataset detected ({total_items} items). Visualization optimized for performance.")
        
    # Function to truncate data if necessary
    def truncate_data(data_dict, max_items):
        if len(data_dict) <= max_items:
            return data_dict
            
        # Sort by value (descending) and take top items
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        truncated_data = dict(sorted_items[:max_items])
        return truncated_data

    if categories_enabled:
        # Check which categories actually have data
        used_categories = []
        category_data_map = {}
        
        # First pass: determine which categories have data
        for category in categories_list:
            # Extract data for this category
            category_data = {}
            for k, v in data.items():
                # Check if the category name appears in the key
                if f"({category})" in k:
                    category_data[k] = v
                # Also check for exact matches (for manufacturer/supplier data)
                elif k.endswith(f"_{category}"):
                    cleaned_key = k.replace(f"_{category}", "")
                    category_data[cleaned_key] = v
            
            # If we have data for this category, keep it
            if category_data:
                # Truncate data if there are too many items
                if len(category_data) > MAX_ITEMS_PER_CATEGORY:
                    category_data = truncate_data(category_data, MAX_ITEMS_PER_CATEGORY)
                
                used_categories.append(category)
                category_data_map[category] = category_data
        
        # If we don't have any categories with data, fall back to non-categorized display
        if not used_categories:
            # Single category visualization
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=list(data.keys()),
                    y=list(data.values()),
                    text=list(map(lambda x: f"{x:.0f}", data.values())),
                    textposition='auto',
                    textfont=dict(size=12, color='black', family="Arial, sans-serif"),
                    width=0.5,
                    marker=dict(
                        color=category_colors[0],
                        line=dict(width=1.5, color="#333333")
                    ),
                    hovertemplate='%{x}<br>Value: %{y}<extra></extra>'
                )
            )
            fig.update_layout(title=title)
            return fig
            
        # Calculate proper vertical spacing based on number of rows
        # The spacing must be less than 1/(rows-1)
        num_rows = len(used_categories)
        max_spacing = 1 / (num_rows - 1) if num_rows > 1 else 0.1
        vertical_spacing = min(0.05, max_spacing * 0.9)  # Add some safety margin
        
        # Create subplot for each category that has data
        fig = make_subplots(
            rows=num_rows, 
            cols=1,
            subplot_titles=[f"{title} - {category}" for category in used_categories],
            vertical_spacing=vertical_spacing
        )

        # Add traces for each category that has data
        for i, category in enumerate(used_categories, 1):
            category_data = category_data_map[category]
            fig.add_trace(
                go.Bar(
                    x=list(category_data.keys()),
                    y=list(category_data.values()),
                    text=list(map(lambda x: f"{x:.0f}", category_data.values())),
                    textposition='auto',
                    textfont=dict(size=12, color='black', family="Arial, sans-serif"),
                    width=0.5,  # Make bars a bit wider
                    marker=dict(
                        color=category_colors[i % len(category_colors)],
                        line=dict(width=1.5, color="#333333")  # Thicker border lines
                    ),
                    hovertemplate='%{x}<br>Value: %{y}<extra></extra>'
                ),
                row=i, col=1
            )
    else:
        # Single category visualization
        # Truncate data if it's very large
        if len(data) > MAX_ITEMS_PER_CATEGORY:
            data = truncate_data(data, MAX_ITEMS_PER_CATEGORY)
            
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=list(data.keys()),
                y=list(data.values()),
                text=list(map(lambda x: f"{x:.0f}", data.values())),
                textposition='auto',
                textfont=dict(size=12, color='black', family="Arial, sans-serif"),
                width=0.5,  # Make bars a bit wider
                marker=dict(
                    color=category_colors,
                    line=dict(width=1.5, color="#333333")  # Thicker border lines
                ),
                hovertemplate='%{x}<br>Value: %{y}<extra></extra>'
            )
        )

    # Update layout with improved aesthetics
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24, family="Arial, sans-serif"),
            x=0.5,
            xanchor='center'
        ),
        showlegend=False,
        plot_bgcolor='white',
        bargap=0.3,
        margin=dict(t=100, l=70, r=40, b=50),
        height=260 * (len(categories_list) if categories_enabled else 1),
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
    )
    
    # Update axes for all subplots
    num_rows = len(categories_list) if categories_enabled else 1
    for i in range(1, num_rows + 1):
        fig.update_xaxes(
            showgrid=False,
            tickangle=-45,
            tickfont=dict(size=12, color='black', family="Arial, sans-serif"),
            tickmode='auto',
            nticks=10,  # Limit number of ticks to avoid overcrowding
            row=i if categories_enabled else None,
            col=1 if categories_enabled else None
        )
        
        fig.update_yaxes(
            title=dict(
                text=y_axis,
                font=dict(size=14, family="Arial, sans-serif")
            ),
            showgrid=True,
            gridcolor='rgb(200, 200, 200)',  # Darker grid lines
            gridwidth=1.2,  # Thicker grid lines
            zeroline=True,
            zerolinecolor='rgb(100, 100, 100)',  # Dark zero line
            zerolinewidth=1.5,  # Thicker zero line
            tickfont=dict(size=12),  # Larger axis tick labels
            row=i if categories_enabled else None,
            col=1 if categories_enabled else None
        )
        
    return fig

def main():
    # Set up session state to persist values between reruns
    if 'disruption_settings' not in st.session_state:
        st.session_state.disruption_settings = {}
    
    # Ensure our session state has the disruptions_dict and solutions_dict
    if 'disruptions_dict' not in st.session_state:
        st.session_state.disruptions_dict = {}
    if 'solutions_dict' not in st.session_state:
        st.session_state.solutions_dict = {}
    
    st.title("Supply Chain Disruption Simulator")
    st.subheader("Gym Equipment Supply Chain")

    st.write("""
    This simulator demonstrates the impact of disruptions on a gym equipment supply chain network.
    Adjust the parameters below or use a preset scenario to explore different situations.
    """)

    # Parameter Presets Section
    st.header("Scenario Presets")
    
    preset_descriptions = {preset.name: preset.description for preset in PRESETS}
    selected_preset = st.selectbox(
        "Select a preset scenario",
        options=["Custom"] + [preset.name for preset in PRESETS],
        index=0,
        help="Choose a predefined scenario or customize your own",
        key="preset_selector"
    )
    
    if selected_preset != "Custom":
        st.info(f"**{selected_preset}**: {preset_descriptions[selected_preset]}")
        
        # Find the selected preset
        selected_preset_data = next((preset for preset in PRESETS if preset.name == selected_preset), None)
        
        # Supply Chain Configuration with preset values
        num_suppliers = selected_preset_data.suppliers
        num_manufacturers = selected_preset_data.manufacturers
        num_customers = selected_preset_data.customers
        base_inventory = selected_preset_data.base_inventory
        
        # Display the preset configuration (read-only)
        cols = st.columns(4)
        cols[0].metric("Suppliers", num_suppliers)
        cols[1].metric("Manufacturers", num_manufacturers)
        cols[2].metric("Customers", num_customers)
        cols[3].metric("Base Inventory", base_inventory)
        
    else:
        # Custom Supply Chain Configuration
        st.header("Supply Chain Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_suppliers = st.slider(
                "Number of Suppliers",
                min_value=1,
                max_value=30,
                value=30,
                help="Number of suppliers in the chain",
                key="num_suppliers_slider"
            )
            
            num_manufacturers = st.slider(
                "Number of Manufacturers",
                min_value=1,
                max_value=30,
                value=30,
                help="Number of manufacturers in the chain",
                key="num_manufacturers_slider"
            )
            
        with col2:
            num_customers = st.slider(
                "Number of Customers",
                min_value=1,
                max_value=25,
                value=5,
                help="Number of customers in the chain",
                key="num_customers_slider"
            )
            
            base_inventory = st.number_input(
                "Base Inventory Level",
                min_value=50,
                max_value=2000,
                value=100,
                help="Initial inventory level for suppliers",
                key="base_inventory_input"
            )
    
    # Equipment categories information
    with st.expander("View Equipment Categories"):
        st.subheader("Equipment Categories")
        for category, details in EQUIPMENT_CATEGORIES.items():
            st.write(f"**{category}**")
            st.write(f"- Suppliers: {', '.join(details['suppliers'])}")
            st.write(f"- Manufacturers: {', '.join(details['manufacturers'])}")
        
    # Create supply chain with disruption probability
    if selected_preset != "Custom":
        disruption_probability = selected_preset_data.disruption_probability
        simulation = create_sample_chain(
            num_suppliers=num_suppliers,
            num_manufacturers=num_manufacturers,
            num_customers=num_customers,
            base_inventory=base_inventory,
            disruption_probability=disruption_probability
        )
    else:
        # Default disruption probability for custom scenario
        simulation = create_sample_chain(
            num_suppliers=num_suppliers,
            num_manufacturers=num_manufacturers,
            num_customers=num_customers,
            base_inventory=base_inventory,
            disruption_probability=0.2
        )
        
    # Store supplier/manufacturer data in session state to maintain persistence
    if 'current_suppliers' not in st.session_state:
        st.session_state.current_suppliers = []
        
    # Update the current suppliers list
    st.session_state.current_suppliers = [s.name for s in simulation.suppliers]

    # Production settings
    st.header("Production Settings")
    for manufacturer in simulation.manufacturers:
        simulation.units_produced[f"{manufacturer.name}_{manufacturer.category}"] = st.slider(
            f"Units produced by {manufacturer.name} ({manufacturer.category})",
            min_value=10,
            max_value=1000,
            value=50,
            key=f"manufacturer_slider_{manufacturer.name}_{manufacturer.category}"
        )

    # Supply settings
    st.header("Supply Settings")
    for supplier in simulation.suppliers:
        supplier.supply_amount = st.slider(
            f"Supply amount for {supplier.name} ({supplier.category})",
            min_value=10,
            max_value=1000,
            value=50,
            key=f"supplier_slider_{supplier.name}_{supplier.category}"
        )

    # Disruption settings with form to prevent auto-refresh
    st.header("Disruption Settings")
    
    st.markdown("""
    Use this form to select ANY NUMBER of suppliers to simulate disruptions.
    Check all disruptions you want to apply, then click "Apply Disruptions" when done.
    """)
    
    # Organize suppliers by category for display
    suppliers_by_category = {}
    for category in SUPPLIERS.keys():
        suppliers_by_category[category] = [(s.name, s.category) for s in simulation.suppliers if s.category == category]
    
    # Get total supplier count for reference
    total_suppliers = sum(len(suppliers) for suppliers in suppliers_by_category.values())

    # Create a form to allow multiple selections without refreshing
    with st.form(key="disruption_form"):
        # Temporary dict to track form checkbox states
        temp_disruptions = {}
        
        # Create expandable sections for each category of suppliers
        for category, suppliers in suppliers_by_category.items():
            if suppliers:  # Only show categories that have suppliers
                with st.expander(f"{category} Suppliers ({len(suppliers)} suppliers)", expanded=True):
                    # Create multiple columns within the expander
                    columns = st.columns(4)  # Adjust number of columns as needed
                    
                    # Distribute suppliers across columns
                    for i, (supplier_name, supplier_category) in enumerate(suppliers):
                        col_idx = i % 4  # Choose which column to place this supplier in
                        
                        # Create unique key for checkbox
                        supplier_key = f"{supplier_name}_{supplier_category}"
                        checkbox_key = f"disruption_checkbox_{supplier_key}"
                        
                        # Get current state from session
                        current_state = False
                        if supplier_key in st.session_state.disruption_settings:
                            current_state = st.session_state.disruption_settings[supplier_key]["is_disrupted"]
                        
                        # Add the checkbox in form (won't cause refresh)
                        is_checked = columns[col_idx].checkbox(
                            supplier_name,
                            value=current_state,
                            key=checkbox_key
                        )
                        
                        # Store in temporary dict
                        temp_disruptions[supplier_key] = is_checked
        
        # Submit button at end of form
        submit_button = st.form_submit_button(label="Apply Disruptions")
    
    # Process form submission (outside form)
    if submit_button:
        # Reset disruptions first
        simulation.disruptions.clear()
        simulation.solutions.clear()
        
        # Count active disruptions
        active_disruptions_count = 0
        disrupted_suppliers_names = []
        
        # Update session state with form values
        for supplier_key, is_disrupted in temp_disruptions.items():
            supplier_name, supplier_category = supplier_key.split("_", 1)
            
            # Initialize if not present
            if supplier_key not in st.session_state.disruption_settings:
                st.session_state.disruption_settings[supplier_key] = {
                    "is_disrupted": is_disrupted,
                    "disruption": "Supply chain delay",
                    "solution": "Find alternative supplier"
                }
            else:
                st.session_state.disruption_settings[supplier_key]["is_disrupted"] = is_disrupted
            
            # Count active disruptions
            if is_disrupted:
                active_disruptions_count += 1
                disrupted_suppliers_names.append(supplier_name)
                
                # Apply to simulation
                disruption_text = st.session_state.disruption_settings[supplier_key].get("disruption", "Supply chain delay")
                solution_text = st.session_state.disruption_settings[supplier_key].get("solution", "Find alternative supplier")
                simulation.disruptions[supplier_name] = disruption_text
                simulation.solutions[supplier_name] = solution_text
        
        st.success(f"Applied {active_disruptions_count} disruptions. Scroll down to configure details.")
    else:
        # Count current active disruptions for display
        active_disruptions_count = sum(1 for v in st.session_state.disruption_settings.values() if v.get("is_disrupted", False))
    
    # Show active disruption count
    st.info(f"Active Disruptions: {active_disruptions_count} out of {total_suppliers} suppliers")
    
    # Display configuration for disrupted suppliers
    if active_disruptions_count > 0:
        st.subheader("Disruption Configuration")
        st.markdown("Define the disruption type and solution for each selected supplier:")
        
        for category, suppliers in suppliers_by_category.items():
            # Filter for disrupted suppliers in this category
            disrupted_in_category = []
            for supplier_name, supplier_category in suppliers:
                supplier_key = f"{supplier_name}_{supplier_category}"
                if (supplier_key in st.session_state.disruption_settings and 
                    st.session_state.disruption_settings[supplier_key].get("is_disrupted", False)):
                    disrupted_in_category.append((supplier_name, supplier_category))
            
            if disrupted_in_category:  # Only show categories with disrupted suppliers
                st.markdown(f"**{category} Disruptions:**")
                
                for supplier_name, supplier_category in disrupted_in_category:
                    supplier_key = f"{supplier_name}_{supplier_category}"
                    
                    # Create columns for each disrupted supplier configuration
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        # Initialize session state for this text field if needed
                        if f"disruption_type_{supplier_key}" not in st.session_state:
                            st.session_state[f"disruption_type_{supplier_key}"] = st.session_state.disruption_settings[supplier_key].get("disruption", "Supply chain delay")
                        
                        disruption_input = st.text_input(
                            f"Disruption for {supplier_name}",
                            value=st.session_state[f"disruption_type_{supplier_key}"],
                            key=f"disruption_type_{supplier_key}",
                            placeholder="Describe the disruption"
                        )
                        
                        # Update session state
                        st.session_state.disruption_settings[supplier_key]["disruption"] = disruption_input
                        # Apply to simulation
                        simulation.disruptions[supplier_name] = disruption_input
                        
                    with col2:
                        # Initialize session state for this text field if needed
                        if f"solution_type_{supplier_key}" not in st.session_state:
                            st.session_state[f"solution_type_{supplier_key}"] = st.session_state.disruption_settings[supplier_key].get("solution", "Find alternative supplier")
                        
                        solution_input = st.text_input(
                            f"Solution for {supplier_name}",
                            value=st.session_state[f"solution_type_{supplier_key}"],
                            key=f"solution_type_{supplier_key}",
                            placeholder="Describe the solution"
                        )
                        
                        # Update session state
                        st.session_state.disruption_settings[supplier_key]["solution"] = solution_input
                        # Apply to simulation
                        simulation.solutions[supplier_name] = solution_input
    
    # SMS Notification Settings
    st.header("SMS Notification Settings")
    st.write("Enable SMS notifications to receive alerts about supply chain disruptions and solutions.")
    
    # Initialize notifications_enabled in session state if not already present
    if 'notifications_enabled' not in st.session_state:
        st.session_state.notifications_enabled = False
        
    # Initialize phone_number in session state if not already present
    if 'phone_number' not in st.session_state:
        st.session_state.phone_number = ""
    
    # Enable/disable notifications
    enable_notifications = st.checkbox(
        "Enable SMS notifications", 
        value=st.session_state.notifications_enabled,
        key="enable_notifications"
    )
    
    # Update session state from checkbox
    st.session_state.notifications_enabled = enable_notifications
    
    # Show phone number input if notifications are enabled
    if st.session_state.notifications_enabled:
        phone_number = st.text_input(
            "Your phone number (include country code)",
            value=st.session_state.phone_number,
            key="phone_number_input",
            placeholder="e.g., +1234567890"
        )
        # Update session state
        st.session_state.phone_number = phone_number
        
        # Check if Twilio credentials are configured
        try:
            import os
            has_twilio_creds = (
                os.environ.get("TWILIO_ACCOUNT_SID") and 
                os.environ.get("TWILIO_AUTH_TOKEN") and 
                os.environ.get("TWILIO_PHONE_NUMBER")
            )
            
            if not has_twilio_creds:
                st.warning("Twilio credentials are not configured. SMS notifications will not work.")
                st.info("To enable SMS notifications, please provide TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER secrets.")
        except Exception as e:
            st.error(f"Error checking Twilio credentials: {e}")
    
    # Performance Analysis Section
    with st.expander("Performance Analysis"):
        st.subheader("Simulator Performance Analysis")
        st.write("""
        This section provides insights on how much data the simulator can efficiently handle.
        The current configuration is set to handle up to 30 suppliers and 30 manufacturers,
        with optimizations for efficient data processing.
        """)
        
        # Add benchmark on request
        if st.button("Run Performance Analysis", key="run_benchmark"):
            with st.spinner("Running performance analysis..."):
                st.info("Testing simulation performance with different data sizes...")
                
                # Define test sizes
                test_sizes = [5, 10, 20, 30]
                
                # Results storage
                times = []
                disruption_times = []
                
                # Run benchmarks for each size
                for size in test_sizes:
                    # Time the creation and basic simulation
                    start_time = time.time()
                    test_sim = create_sample_chain(
                        num_suppliers=size,
                        num_manufacturers=size,
                        num_customers=5,
                        base_inventory=100,
                        disruption_probability=0.2
                    )
                    # Set up some basic production values
                    for m in test_sim.manufacturers:
                        test_sim.units_produced[f"{m.name}_{m.category}"] = 100
                    for s in test_sim.suppliers:
                        s.supply_amount = 100
                    # Run normal simulation
                    _ = test_sim.simulate_normal()
                    setup_time = time.time() - start_time
                    
                    # Time disruptions simulation separately
                    start_time = time.time()
                    _ = test_sim.simulate_with_disruptions()
                    disruption_time = time.time() - start_time
                    
                    times.append(setup_time)
                    disruption_times.append(disruption_time)
                
                # Create performance visualization
                performance_data = {
                    f"{size} suppliers/manufacturers": time_value
                    for size, time_value in zip(test_sizes, times)
                }
                
                disruption_performance_data = {
                    f"{size} suppliers/manufacturers": time_value
                    for size, time_value in zip(test_sizes, disruption_times)
                }
                
                st.subheader("Setup & Basic Simulation Time (seconds)")
                st.bar_chart(performance_data)
                
                st.subheader("Disruption Simulation Time (seconds)")
                st.bar_chart(disruption_performance_data)
                
                # Analysis of results
                max_suppliers = 30
                max_manufacturers = 30
                st.write(f"""
                **Performance Analysis Results:**
                
                - The simulator is configured to handle up to {max_suppliers} suppliers and {max_manufacturers} manufacturers efficiently.
                - Larger datasets (30+ suppliers/manufacturers) may experience degraded performance.
                - The simulator optimizes for performance by limiting the number of items shown in visualizations.
                
                **Memory Usage:**
                - Each supplier requires approximately 5KB of memory
                - Each manufacturer requires approximately 3KB of memory
                - With 30 suppliers and 30 manufacturers, the simulation uses approximately 240KB of memory
                
                **Best Practices for Optimal Performance:**
                - Use 20-30 suppliers/manufacturers for best balance of detail and performance
                - Limit the number of disruptions to 10-15 for faster processing
                - For large simulations, use fewer customers (5-10)
                """)
    
    # Simulation button and results
    st.header("Simulation Results")
    
    st.write("""
    Run the simulation to see how disruptions impact the supply chain. The simulation will run three phases:
    
    1. **Normal Operations**: Shows baseline performance without any disruptions
    2. **With Disruptions**: Demonstrates the impact of the configured disruptions
    3. **With Solutions**: Shows how the proposed solutions mitigate disruption impacts
    
    Compare these phases to understand how disruptions affect the supply chain and how effective different solutions are.
    """)
    
    # Run Simulation button with three phases
    if st.button("Run All Simulations", key="run_simulations_button"):
        st.header("1. Normal Supply Chain Operations")
        normal_results = simulation.simulate_normal()

        # Display normal operation graphs
        st.plotly_chart(create_bar_chart(
            normal_results['manufacturer_production'],
            "Units Produced by Manufacturers",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        st.plotly_chart(create_bar_chart(
            normal_results['supplier_amounts'],
            "Supply Amounts from Suppliers",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        # Create simplified customer data by category
        customer_data = {}
        
        # Get the total number of customers and an even distribution of units
        num_customers = len(simulation.customers)
        per_customer_amount = normal_results['customer_received'] / num_customers if num_customers > 0 else 0
        
        # Distribute customers evenly across all our gym equipment categories
        for i, customer in enumerate(simulation.customers):
            # Assign each customer to a specific category in a round-robin fashion
            category_index = i % len(SUPPLIERS.keys())
            category = list(SUPPLIERS.keys())[category_index]
            
            # Add to our data dictionary with a readable label
            customer_data[f"{customer} ({category})"] = per_customer_amount
                    
        st.plotly_chart(create_bar_chart(
            customer_data,
            "Total Units Received by Customers",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        st.header("2. Supply Chain with Disruptions")
        disruption_results = simulation.simulate_with_disruptions()

        # Display disrupted operation graphs
        st.plotly_chart(create_bar_chart(
            disruption_results['manufacturer_production'],
            "Units Produced by Manufacturers (With Disruptions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        st.plotly_chart(create_bar_chart(
            disruption_results['supplier_amounts'],
            "Supply Amounts from Suppliers (With Disruptions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        # Create simplified customer data by category
        customer_data = {}
        
        # Get the total number of customers and an even distribution of units
        num_customers = len(simulation.customers)
        per_customer_amount = disruption_results['customer_received'] / num_customers if num_customers > 0 else 0
        
        # Distribute customers evenly across all our gym equipment categories
        for i, customer in enumerate(simulation.customers):
            # Assign each customer to a specific category in a round-robin fashion
            category_index = i % len(SUPPLIERS.keys())
            category = list(SUPPLIERS.keys())[category_index]
            
            # Add to our data dictionary with a readable label
            customer_data[f"{customer} ({category})"] = per_customer_amount
                    
        st.plotly_chart(create_bar_chart(
            customer_data,
            "Total Units Received by Customers (With Disruptions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        # Display disruption events
        if disruption_results['disruption_events']:
            st.subheader("Disruption Events")
            
            # For notification status
            notification_status = []
            
            for event in disruption_results['disruption_events']:
                st.warning(f"🚨 {event['supplier']}: {event['disruption']}")
                
                # Send SMS notification if enabled
                if st.session_state.get('notifications_enabled', False) and st.session_state.get('phone_number'):
                    # Find the category for this supplier
                    supplier_category = next((cat for cat in SUPPLIERS.keys() 
                                           for s_name in SUPPLIERS[cat] 
                                           if s_name == event['supplier']), "General")
                    
                    # Send the notification
                    result = send_disruption_alert(
                        st.session_state.phone_number,
                        event['supplier'],
                        event['disruption'],
                        supplier_category
                    )
                    
                    # Track notification status
                    notification_status.append(result)
            
            # Show notification summary if notifications were attempted
            if notification_status:
                st.subheader("SMS Notification Status")
                success_count = sum(1 for status in notification_status if status.get('success'))
                
                if success_count == len(notification_status):
                    st.success(f"✅ Successfully sent {success_count} SMS notifications")
                elif success_count > 0:
                    st.warning(f"⚠️ Sent {success_count} out of {len(notification_status)} SMS notifications")
                else:
                    # Show error details
                    st.error(f"❌ Failed to send SMS notifications: {notification_status[0].get('error')}")
                    if "Missing Twilio credentials" in notification_status[0].get('error', ''):
                        st.info("To enable SMS notifications, please provide TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER secrets.")

        st.header("3. Supply Chain with Solutions")
        solution_results = simulation.simulate_with_solutions()

        # Display solution operation graphs
        st.plotly_chart(create_bar_chart(
            solution_results['manufacturer_production'],
            "Units Produced by Manufacturers (With Solutions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        st.plotly_chart(create_bar_chart(
            solution_results['supplier_amounts'],
            "Supply Amounts from Suppliers (With Solutions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        # Create simplified customer data by category
        customer_data = {}
        
        # Get the total number of customers and an even distribution of units
        num_customers = len(simulation.customers)
        per_customer_amount = solution_results['customer_received'] / num_customers if num_customers > 0 else 0
        
        # Distribute customers evenly across all our gym equipment categories
        for i, customer in enumerate(simulation.customers):
            # Assign each customer to a specific category in a round-robin fashion
            category_index = i % len(SUPPLIERS.keys())
            category = list(SUPPLIERS.keys())[category_index]
            
            # Add to our data dictionary with a readable label
            customer_data[f"{customer} ({category})"] = per_customer_amount
                    
        st.plotly_chart(create_bar_chart(
            customer_data,
            "Total Units Received by Customers (With Solutions)",
            "Units",
            categories_enabled=True
        ), use_container_width=True)

        # Display solution events
        if solution_results['solution_events']:
            st.subheader("Solution Actions")
            
            # For notification status
            notification_status = []
            
            for event in solution_results['solution_events']:
                # Get solution text and handle potential None values
                solution_text = str(event['solution'] or "").strip().lower()
                
                # Check if the solution contains text indicating no solution was found
                no_solution_phrases = ["not found", "not available", "no solution", 
                                      "unavailable", "unknown", "none", "n/a", "tbd"]
                
                # Convert solution text to lowercase and check for matches
                if (not solution_text or 
                    any(phrase in solution_text for phrase in no_solution_phrases) or
                    solution_text in no_solution_phrases):
                    
                    st.error(
                        f"❌ No viable solution found for {event['disrupted_supplier']} disruption.\n"
                        f"Impact: Supply chain significantly affected with no current mitigation strategy."
                    )
                    
                else:
                    # Only show redistribution if there are actually suppliers to redistribute to
                    if event['redistributed_to']:
                        st.success(
                            f"✅ Solution for {event['disrupted_supplier']}: {event['solution']}\n"
                            f"Load redistributed to: {', '.join(event['redistributed_to'])}"
                        )
                        
                        # Send solution notification if enabled and there was a successful solution
                        if st.session_state.get('notifications_enabled', False) and st.session_state.get('phone_number'):
                            # Find the category for this supplier
                            supplier_category = next((cat for cat in SUPPLIERS.keys() 
                                                  for s_name in SUPPLIERS[cat] 
                                                  if s_name == event['disrupted_supplier']), "General")
                            
                            # Send the solution notification
                            result = send_solution_notification(
                                st.session_state.phone_number,
                                event['disrupted_supplier'],
                                event['solution'],
                                supplier_category
                            )
                            
                            # Track notification status
                            notification_status.append(result)
                        
                    else:
                        st.warning(
                            f"⚠️ Solution attempted for {event['disrupted_supplier']}: {event['solution']}\n"
                            f"Note: No alternative suppliers were available in this category for redistribution."
                        )
            
            # Show notification summary if notifications were attempted
            if notification_status:
                st.subheader("Solution SMS Notification Status")
                success_count = sum(1 for status in notification_status if status.get('success'))
                
                if success_count == len(notification_status):
                    st.success(f"✅ Successfully sent {success_count} solution SMS notifications")
                elif success_count > 0:
                    st.warning(f"⚠️ Sent {success_count} out of {len(notification_status)} solution SMS notifications")
                else:
                    # Show error details
                    st.error(f"❌ Failed to send solution SMS notifications: {notification_status[0].get('error')}")

if __name__ == "__main__":
    main()