# src/ui_sidebar.py
"""Functions for rendering the Streamlit sidebar UI."""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import altair as alt
import os

# Import project modules
from src.utils import (
    get_base64_of_bin_file, get_icon_data_uri, format_percent, format_value,
    get_delta, get_delta_percent, get_delta_points, get_delta_percentage_formatted
)
from src.config import SPARKLINE_YEARS, GAME_END_YEAR
from characters import CHARACTERS # Assuming characters.py is in the root

# --- Helper function to create sparkline data ---
def get_sparkline_data(metric_key, num_years, fetch_full_history=False):
    """Fetches and prepares data for sparkline/KPI plots from model solutions."""
    if not hasattr(st.session_state, 'sfc_model_object') or not st.session_state.sfc_model_object.solutions:
        return None
    solutions = st.session_state.sfc_model_object.solutions
    # Allow processing even if only one solution exists (for single point display)
    if not solutions: # Check if solutions list is empty
        return None

    # Determine start index based on flag
    if fetch_full_history:
        # Fetch from Year 1 (index 1) onwards for full history plots
        start_index = 1
    else:
        # Fetch last num_years for sparklines (including year 0 if within window)
        start_index = max(1, len(solutions) - num_years) # Ensure sparklines start from Year 1

    # Ensure start_index is valid (e.g., don't try to fetch index 1 if only index 0 exists)
    if start_index >= len(solutions):
         logging.warning(f"SPARKLINE {metric_key} - start_index {start_index} out of bounds for solutions length {len(solutions)}. Returning None.")
         return None # Avoid slicing error if start_index is too large

    history_slice = solutions[start_index:]

    # Extract data, handling potential missing keys or non-numeric values gracefully
    data = []
    years = []
    # Assuming solutions[0] corresponds to year 0, solutions[1] to year 1 etc.
    start_actual_year = start_index # Year number corresponds to the index in solutions list (0=Year 0, 1=Year 1, etc.)

    for i, sol in enumerate(history_slice):
        # Get the raw value first, default to NaN
        val = np.nan
        current_year_in_slice = start_actual_year + i

        # Handle specific metric calculations
        if metric_key == 'Unemployment':
            er_val = sol.get('ER')
            val = (1 - er_val) * 100 if er_val is not None and np.isfinite(er_val) else np.nan
        elif metric_key == 'Yk_Index':
            # Store raw Yk, calculation happens after loop
            val = sol.get('Yk') # Get raw Yk
        elif metric_key == 'GD_GDP':
            gd_val = sol.get('GD')
            y_val = sol.get('Y')
            if gd_val is not None and y_val is not None and np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                val = (gd_val / y_val) * 100 # Calculate ratio and scale to percentage
            else:
                val = np.nan # Cannot calculate
        elif metric_key == 'GovBalance_GDP': # New metric calculation
            psbr_val = sol.get('PSBR')
            y_val = sol.get('Y')
            if psbr_val is not None and y_val is not None and np.isfinite(psbr_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                # Calculate balance (-PSBR) as % of GDP
                val = (-psbr_val / y_val) * 100
            else:
                val = np.nan # Cannot calculate
        elif metric_key in ['PI', 'GRk', 'Rb', 'Rl', 'Rm', 'BUR', 'CAR']: # Rates/Ratios need scaling (excluding GD_GDP as it's handled above)
             raw_val = sol.get(metric_key)
             val = raw_val * 100 if raw_val is not None and np.isfinite(raw_val) else np.nan
        else: # For other metrics, just get the value
             val = sol.get(metric_key)

        # Append the calculated/retrieved value and year
        # Ensure only valid numbers or NaN are added
        data.append(val if (val is not None and np.isfinite(val)) else np.nan)
        years.append(current_year_in_slice)

    # Create DataFrame
    df = pd.DataFrame({'Year': years, metric_key: data})

    # --- Post-loop calculations for specific metrics ---
    if metric_key == 'Yk_Index':
        base_yk = st.session_state.get('base_yk')
        if base_yk and not np.isclose(base_yk, 0):
            # Calculate index relative to base_yk, set Year 1 index explicitly to 100
            # Apply calculation only where Yk value is not NaN
            df[metric_key] = df[metric_key].apply(lambda yk: (yk / base_yk) * 100 if pd.notna(yk) else np.nan)
            if 1 in df['Year'].values:
                 # Find the index corresponding to Year 1 and set its value
                 year1_index = df[df['Year'] == 1].index
                 if not year1_index.empty:
                     # Use .loc with the index label to set the value
                     df.loc[year1_index[0], metric_key] = 100.0 # Ensure Year 1 is exactly 100
        else:
            # If base_yk isn't set (should only happen before Year 2), set all to NaN
            df[metric_key] = np.nan
        logging.debug(f"SPARKLINE Yk_Index - Calculated Index DF:\n{df}")

    # Filter out rows where the metric value is exactly zero for sparklines
    if not fetch_full_history:
        logging.debug(f"SPARKLINE({metric_key}) DF before zero filter:\n{df}")
        # Do this *before* dropping NaNs to handle cases where zero might be valid but unwanted
        df = df[~np.isclose(df[metric_key], 0.0)]
        logging.debug(f"SPARKLINE({metric_key}) DF after zero filter:\n{df}")

    # Explicitly drop rows where the metric value is NaN BEFORE setting index
    df.dropna(subset=[metric_key], inplace=True)

    # Check again if enough points remain after dropping NaNs
    if df.empty:
        logging.debug(f"SPARKLINE {metric_key} - Not enough valid points after dropna.")
        return None

    # Set index after cleaning
    df.set_index('Year', inplace=True)
    return df

# --- Function to create Vega-Lite spec for sidebar (minimalist) ---
def create_sparkline_spec(data_df, metric_key):
    """Creates a Vega-Lite spec for a minimalist sparkline chart."""
    if data_df is None or data_df.empty:
        return None
    # Prepare data in list-of-dicts format
    chart_data = data_df.reset_index().to_dict('records')
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": chart_data},
        "mark": {"type": "line", "point": True}, # Show points
        "encoding": {
            "x": {"field": "Year", "type": "ordinal", "axis": None}, # Hide X axis
            "y": {
                "field": metric_key,
                "type": "quantitative",
                "axis": None,
                "scale": {"zero": True} # Ensure zero is included in the scale
            }, # Hide Y axis
            "tooltip": [ # Enable tooltips
                {"field": "Year", "type": "ordinal"},
                {"field": metric_key, "type": "quantitative", "format": ".2f"} # Format tooltip value
            ]
        },
        "height": 50,
        "width": "container", # Use container width
         # Attempt to set theme config
        "config": {
             "background": None, # Try transparent background
             "view": {"stroke": None}, # Remove view border
             "theme": "none" # Attempt to force theme inheritance
         }
    }

# --- Function to display metric and sparkline (NO EXPANDER) ---
def display_metric_sparkline(metric_key, label, icon_key, format_func, delta_val, latest_history_entry):
    """Displays a single metric with its value, delta, icon, and sparkline."""
    spark_df = get_sparkline_data(metric_key, SPARKLINE_YEARS)
    current_val = latest_history_entry.get(metric_key, np.nan)

    # Special handling for specific metrics
    if metric_key == 'Unemployment':
        er_val = latest_history_entry.get('ER', np.nan)
        current_val = max(0.005, (1 - er_val)) if np.isfinite(er_val) else np.nan
        icon_key = "ER" # Use ER icon
    elif metric_key == 'Yk_Index':
        yk_val = latest_history_entry.get('Yk', np.nan)
        base_yk = st.session_state.get('base_yk')
        is_first_result_year = (len(st.session_state.sfc_model_object.solutions) == 2) # Check if it's Year 1 result
        if is_first_result_year and np.isfinite(yk_val):
            current_val = 100.0
        elif base_yk and np.isfinite(yk_val) and not np.isclose(base_yk, 0):
            current_val = (yk_val / base_yk) * 100
        else:
            current_val = np.nan
        icon_key = "Yk"
        format_func = lambda x: f"{x:.1f}" if np.isfinite(x) else "N/A"
    elif metric_key == 'GD_GDP':
        gd_val = latest_history_entry.get('GD', np.nan)
        y_val = latest_history_entry.get('Y', np.nan)
        if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
            current_val = gd_val / y_val
        else:
            current_val = np.nan
        icon_key = "GD_GDP"
        format_func = format_percent
    elif metric_key == 'GovBalance_GDP':
        psbr_val = latest_history_entry.get('PSBR', np.nan)
        y_val = latest_history_entry.get('Y', np.nan)
        if np.isfinite(psbr_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
            current_val = -psbr_val / y_val
        else:
            current_val = np.nan
        icon_key = "PSBR"
        format_func = format_percent

    icon_data_uri = get_icon_data_uri(icon_key)
    cols = st.sidebar.columns([1, 5, 2])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label=label, value=format_func(current_val), delta=delta_val)
    with cols[2]:
        if spark_df is not None and not spark_df.empty:
            try:
                spec = create_sparkline_spec(spark_df, metric_key)
                if spec:
                    st.vega_lite_chart(spec, use_container_width=True, theme="streamlit")
            except Exception as e:
                logging.error(f"Error creating st.vega_lite_chart for {metric_key}: {e}")

# --- Sector Summary Display ---
def display_sector_summary(latest_solution):
    """Displays key summary data for each economic sector in the sidebar."""
    st.sidebar.markdown("---") # Add a divider
    st.sidebar.markdown("##### Sector Summaries")

    # Households
    with st.sidebar.expander("Households", expanded=False):
        hh_v = latest_solution.get('V', np.nan)
        hh_ydr = latest_solution.get('YDr', np.nan)
        hh_c = latest_solution.get('CONS', np.nan)
        st.metric(label="Wealth (V)", value=format_value(hh_v))
        st.metric(label="Disposable Income (YDr)", value=format_value(hh_ydr))
        st.metric(label="Consumption (C)", value=format_value(hh_c))

    # Firms
    with st.sidebar.expander("Firms", expanded=False):
        f_k = latest_solution.get('K', np.nan)
        f_i = latest_solution.get('INV', np.nan)
        f_fu = latest_solution.get('FUf', np.nan)
        f_grk = latest_solution.get('GRk', np.nan)
        st.metric(label="Capital Stock (K)", value=format_value(f_k))
        st.metric(label="Investment (I)", value=format_value(f_i))
        st.metric(label="Retained Earnings (FUf)", value=format_value(f_fu))
        st.metric(label="Capital Growth (GRk)", value=format_percent(f_grk))

    # Government
    with st.sidebar.expander("Government", expanded=False):
        g_gd = latest_solution.get('GD', np.nan)
        g_psbr = latest_solution.get('PSBR', np.nan)
        g_t = latest_solution.get('T', np.nan)
        g_g = latest_solution.get('G', np.nan)
        st.metric(label="Total Debt (GD)", value=format_value(g_gd))
        st.metric(label="Deficit (PSBR)", value=format_value(g_psbr))
        st.metric(label="Taxes (T)", value=format_value(g_t))
        st.metric(label="Spending (G)", value=format_value(g_g))

    # Banks
    with st.sidebar.expander("Banks", expanded=False):
        b_lfs = latest_solution.get('Lfs', np.nan)
        b_lhs = latest_solution.get('Lhs', np.nan)
        b_m = latest_solution.get('Ms', np.nan)
        b_ofb = latest_solution.get('OFb', np.nan)
        b_car = latest_solution.get('CAR', np.nan)
        st.metric(label="Loans to Firms (Lfs)", value=format_value(b_lfs))
        st.metric(label="Loans to Households (Lhs)", value=format_value(b_lhs))
        st.metric(label="Deposits (Ms)", value=format_value(b_m))
        st.metric(label="Own Funds (OFb)", value=format_value(b_ofb))
        st.metric(label="Capital Adequacy (CAR)", value=format_percent(b_car))

    # Central Bank
    with st.sidebar.expander("Central Bank", expanded=False):
        cb_bcb = latest_solution.get('Bcbd', np.nan)
        st.metric(label="Bills Held (Bcb)", value=format_value(cb_bcb))

# --- Main Sidebar Function ---
def display_sidebar():
    """Renders the entire sidebar based on the current game state."""

    # Display Character Image and Objectives side-by-side if character selected
    if st.session_state.get('selected_character_id'):
        char_id = st.session_state.selected_character_id
        char_data = CHARACTERS.get(char_id)

        if char_data: # Check if character data was found
            st.sidebar.header(f"Advisor: {char_data['name']}") # Display the name

        # Create two columns in the sidebar
        col1, col2 = st.sidebar.columns([1, 2]) # Adjust ratio if needed

        # --- Column 1: Character Image ---
        with col1:
            if char_data:
                img_path = char_data.get('image_path')
                if img_path:
                    try:
                        # Use relative path assuming assets/ is accessible
                        full_img_path = os.path.join("assets", "characters", os.path.basename(img_path))
                        img_data_uri = get_base64_of_bin_file(full_img_path)
                        if img_data_uri:
                            st.image(f"data:image/png;base64,{img_data_uri}", width=70, use_container_width=False)
                        else:
                            logging.warning(f"Could not encode image for character {char_id} at path: {full_img_path}")
                    except Exception as e:
                        logging.error(f"Error loading/displaying character image {full_img_path}: {e}")

        # --- Column 2: Objectives ---
        with col2:
            st.markdown(f"**Objectives (Y{GAME_END_YEAR})**")
            objectives = st.session_state.get('game_objectives', {})
            if objectives:
                for obj_key, details in objectives.items():
                    target_str = ""
                    if details['target_type'] == 'percent':
                        target_str = f"{details['target_value']:.0f}%"
                    elif details['target_type'] == 'index':
                         target_str = f"{details['target_value']:.0f}"
                    else:
                         target_str = f"{details['target_value']}"
                    st.markdown(f"<small>- {details['label']}: {details['condition']} {target_str}</small>", unsafe_allow_html=True)
            else:
                st.caption("Objectives not set.")

        st.sidebar.divider()

    # --- Dashboard Metrics Display ---
    if st.session_state.current_year == 0 or not st.session_state.history:
         st.sidebar.caption("Waiting for first year results...")
    else:
        # Get data directly from model object solutions
        model_state = st.session_state.sfc_model_object
        if not model_state.solutions or len(model_state.solutions) < 2:
            st.sidebar.caption("Simulation results not yet available.")
            latest_history_entry = st.session_state.initial_state_dict # Fallback
            prev_year_data = None
            is_first_result_year = True
        else:
            latest_history_entry = model_state.solutions[-1] # Latest solved state
            prev_year_data = model_state.solutions[-2]       # Previous solved state
            is_first_result_year = (len(model_state.solutions) == 2)

        # --- Core Metrics Display ---
        st.sidebar.markdown("##### Core Economic Indicators")

        # Fetch current and previous values for delta calculation
        yk_val = latest_history_entry.get('Yk', np.nan)
        pi_val = latest_history_entry.get('PI', np.nan)
        er_val = latest_history_entry.get('ER', np.nan)
        gd_val = latest_history_entry.get('GD', np.nan)
        y_val = latest_history_entry.get('Y', np.nan)

        yk_prev = prev_year_data.get('Yk') if prev_year_data else np.nan
        pi_prev = prev_year_data.get('PI') if prev_year_data else np.nan
        er_prev = prev_year_data.get('ER') if prev_year_data else np.nan
        gd_prev = prev_year_data.get('GD') if prev_year_data else np.nan
        y_prev = prev_year_data.get('Y') if prev_year_data else np.nan

        # Calculate deltas
        delta_pi = None if is_first_result_year else get_delta_percent(pi_val, pi_prev)
        delta_unemp = None if is_first_result_year else get_delta_percent((1-er_val), (1-er_prev))

        # Calculate current and previous GD/GDP ratio
        gd_gdp_curr = (gd_val / y_val) if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0) else np.nan
        gd_gdp_prev = (gd_prev / y_prev) if np.isfinite(gd_prev) and np.isfinite(y_prev) and not np.isclose(float(y_prev), 0) else np.nan
        delta_gd_gdp = None if is_first_result_year else get_delta_percent(gd_gdp_curr, gd_gdp_prev)

        # Calculate Real GDP Index Delta
        current_gdp_index = np.nan
        previous_gdp_index = np.nan
        base_yk = st.session_state.get('base_yk')
        if is_first_result_year and np.isfinite(yk_val):
            current_gdp_index = 100.0
        elif base_yk and np.isfinite(yk_val) and not np.isclose(base_yk, 0):
            current_gdp_index = (yk_val / base_yk) * 100
        if not is_first_result_year and prev_year_data:
            yk_prev_val = prev_year_data.get('Yk')
            if len(model_state.solutions) == 3: # Prev is Year 1
                 previous_gdp_index = 100.0
            elif base_yk and np.isfinite(yk_prev_val) and not np.isclose(base_yk, 0):
                 previous_gdp_index = (yk_prev_val / base_yk) * 100
        delta_yk_index_formatted = None if is_first_result_year else get_delta_percentage_formatted(current_gdp_index, previous_gdp_index)

        # Display core metrics
        display_metric_sparkline('Yk_Index', 'Real GDP Index (Y1=100)', 'Yk', lambda x: f"{x:.1f}", delta_yk_index_formatted, latest_history_entry)
        display_metric_sparkline('PI', 'Inflation Rate', 'PI', format_percent, delta_pi, latest_history_entry)
        display_metric_sparkline('Unemployment', 'Unemployment Rate', 'ER', format_percent, delta_unemp, latest_history_entry)
        display_metric_sparkline("GD_GDP", "Gov Debt / GDP", "GD_GDP", format_percent, delta_gd_gdp, latest_history_entry)

        st.sidebar.divider()

        # --- Financial & Banking Metrics ---
        st.sidebar.markdown("##### Financial & Banking")
        rb_val = latest_history_entry.get('Rb', np.nan)
        rl_val = latest_history_entry.get('Rl', np.nan)
        rm_val = latest_history_entry.get('Rm', np.nan)
        q_val = latest_history_entry.get('Q', np.nan)
        bur_val = latest_history_entry.get('BUR', np.nan)
        car_val = latest_history_entry.get('CAR', np.nan)
        rb_prev = prev_year_data.get('Rb') if prev_year_data else np.nan
        rl_prev = prev_year_data.get('Rl') if prev_year_data else np.nan
        rm_prev = prev_year_data.get('Rm') if prev_year_data else np.nan
        q_prev = prev_year_data.get('Q') if prev_year_data else np.nan
        bur_prev = prev_year_data.get('BUR') if prev_year_data else np.nan
        car_prev = prev_year_data.get('CAR') if prev_year_data else np.nan
        delta_rb = None if is_first_result_year else get_delta_percent(rb_val, rb_prev)
        delta_rl = None if is_first_result_year else get_delta_percent(rl_val, rl_prev)
        delta_rm = None if is_first_result_year else get_delta_percent(rm_val, rm_prev)
        delta_q = None if is_first_result_year else get_delta(q_val, q_prev)
        delta_bur = None if is_first_result_year else get_delta_percent(bur_val, bur_prev)
        delta_car = None if is_first_result_year else get_delta_percent(car_val, car_prev)

        display_metric_sparkline("Rb", "Bill Rate (Rb)", "Rb", format_percent, delta_rb, latest_history_entry)
        display_metric_sparkline("Rl", "Loan Rate (Rl)", "Rl", format_percent, delta_rl, latest_history_entry)
        display_metric_sparkline("Rm", "Deposit Rate (Rm)", "Rm", format_percent, delta_rm, latest_history_entry)
        display_metric_sparkline("Q", "Tobin's Q", "Q", format_value, delta_q, latest_history_entry)
        display_metric_sparkline("BUR", "Debt Burden (BUR)", "BUR", format_percent, delta_bur, latest_history_entry)
        display_metric_sparkline("CAR", "Capital Adequacy (CAR)", "CAR", format_percent, delta_car, latest_history_entry)

        # --- Government Metrics ---
        psbr_val = latest_history_entry.get('PSBR', np.nan)
        psbr_prev = prev_year_data.get('PSBR') if prev_year_data else np.nan
        gov_bal_gdp_curr = (-psbr_val / y_val) if np.isfinite(psbr_val) and np.isfinite(y_val) and y_val != 0 else np.nan
        gov_bal_gdp_prev = (-psbr_prev / y_prev) if np.isfinite(psbr_prev) and np.isfinite(y_prev) and y_prev != 0 else np.nan
        delta_gov_bal_gdp = None if is_first_result_year else get_delta_percent(gov_bal_gdp_curr, gov_bal_gdp_prev)

        display_metric_sparkline("GovBalance_GDP", "Gov Balance / GDP", "PSBR", format_percent, delta_gov_bal_gdp, latest_history_entry)

        # --- Sector Summaries ---
        display_sector_summary(latest_history_entry)