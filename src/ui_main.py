# src/ui_main.py
"""Functions for rendering the main Streamlit UI content area."""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import altair as alt
from urllib.parse import quote
import os

# Import project modules
from src.utils import (
    get_logo_data_uri, get_base64_of_bin_file, get_icon_data_uri, format_effect
)
from src.config import MAX_CARDS_PER_ROW, PARAM_DESCRIPTIONS, GAME_END_YEAR
from characters import CHARACTERS # Assuming characters.py is in the root
from cards import POLICY_CARDS # Assuming cards.py is in the root
from events import ECONOMIC_EVENTS # Assuming events.py is in the root
from matrix_display import ( # Assuming matrix_display.py is in the root
    display_balance_sheet_matrix, display_revaluation_matrix,
    display_transaction_flow_matrix
)
# Import the specific plot function from ui_sidebar (or move it to utils if more appropriate)
# For now, let's assume it's needed here too, or we pass the charts as arguments.
# Re-evaluating: KPI plots are generated *within* the YEAR_START logic, so the function needs to be accessible there.
# Let's define it here for now, potentially moving it later if needed elsewhere.

# --- Helper function to create KPI plots ---
# (Copied from original script, potentially move to a shared plotting module later)
def create_kpi_plot(metric_key, y_axis_title):
    """Creates an Altair chart for a Key Performance Indicator."""
    logging.debug(f"Entering create_kpi_plot for metric: {metric_key}")
    # Import get_sparkline_data locally to avoid circular dependency if moved later
    from src.ui_sidebar import get_sparkline_data
    # Fetch full history starting from Year 1 for KPI plots
    plot_df = get_sparkline_data(metric_key, st.session_state.current_year, fetch_full_history=True)
    logging.debug(f"create_kpi_plot({metric_key}) - plot_df from get_sparkline_data:\n{plot_df}")
    if plot_df is not None and not plot_df.empty:
        # Define colors based on metric_key
        if metric_key == 'Yk_Index': plot_color = "#1FB25A" # Green
        elif metric_key == 'PI': plot_color = "#000000" # Black
        elif metric_key == 'Unemployment': plot_color = "#0072BB" # Blue
        elif metric_key == 'GD_GDP': plot_color = "#555555" # Dark Grey
        else: plot_color = "#1FB25A" # Default Green

        # Determine axis format
        y_axis_format = ".1f" # Default format for index
        if metric_key in ['PI', 'Unemployment', 'GD_GDP']:
            y_axis_format = ".1%" # Percentage format

        # Correct data for percentage scaling in Altair
        plot_df_corrected = plot_df.copy()
        if y_axis_format.endswith('%'):
            plot_df_corrected[metric_key] = plot_df_corrected[metric_key] / 100.0

        # Base chart
        base = alt.Chart(plot_df_corrected.reset_index()).encode(
            x=alt.X('Year:Q',
                    axis=alt.Axis(orient='bottom', title='Year', format='d', labelAngle=-45, grid=False),
                    scale=alt.Scale(domain=[plot_df.index.min(), plot_df.index.max()], paddingOuter=0.1)
                   ),
            tooltip=[
                alt.Tooltip('Year:O', title='Simulation Year'),
                alt.Tooltip(f'{metric_key}:Q', format=y_axis_format, title=y_axis_title)
            ]
        )

        # Handle single data point or line chart
        if len(plot_df_corrected) == 1:
            single_value = plot_df_corrected[metric_key].iloc[0]
            padding = abs(single_value) * 0.15 if not np.isclose(single_value, 0) else 0.01
            y_domain = [single_value - padding, single_value + padding]
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']:
                 y_domain[0] = max(0, y_domain[0])
            y_axis_scale = alt.Scale(domain=y_domain, zero=False)
            chart = base.mark_point(size=100, filled=True, color=plot_color).encode(
                 y=alt.Y(f'{metric_key}:Q',
                         axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                         scale=y_axis_scale)
            )
        else:
            min_val = plot_df_corrected[metric_key].min()
            max_val = plot_df_corrected[metric_key].max()
            data_range = max_val - min_val
            padding = data_range * 0.15 if not np.isclose(data_range, 0) else (abs(max_val) * 0.15 if not np.isclose(max_val, 0) else 0.01)
            y_domain = [min_val - padding, max_val + padding]
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']:
                 y_domain[0] = max(0, y_domain[0])
            y_axis_scale = alt.Scale(domain=y_domain, zero=False)

            line = base.mark_line(
                point=alt.OverlayMarkDef(color=plot_color), color=plot_color, strokeWidth=2
            ).encode(
                y=alt.Y(f'{metric_key}:Q',
                        axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                        scale=y_axis_scale)
            )
            last_point_df_corrected = plot_df_corrected.reset_index().iloc[[-1]]
            labels = alt.Chart(last_point_df_corrected).mark_text(
                align='left', baseline='middle', dx=7, fontSize=11
            ).encode(
                x=alt.X('Year:O'), y=alt.Y(f'{metric_key}:Q'),
                text=alt.Text(f'{metric_key}:Q', format=y_axis_format),
                color=alt.value(plot_color)
            )
            chart_layers = [line, labels]
            if y_domain[0] <= 0 <= y_domain[1]:
                 zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                     color='grey', strokeDash=[2,2], size=1
                 ).encode(y='y')
                 chart_layers.append(zero_line)
            chart = alt.layer(*chart_layers)

        # Common Chart Configuration
        chart = chart.properties(
            height=200,
            padding={"top": 10, "right": 20, "bottom": 10, "left": 20}
        ).configure_view(
            fill=None, stroke='#cccccc'
        ).configure_axis(
            labelFont='Lato', titleFont='Oswald', titleFontSize=12, labelFontSize=11
        ).interactive()
        return chart
    else:
        logging.warning(f"create_kpi_plot({metric_key}) - Returning None because plot_df is None or empty.")
        return None

# --- UI Rendering Functions ---

def display_css():
    """Injects custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* --- Monopoly Theme --- */
        /* --- Fonts --- */
        @import url('https://fonts.googleapis.com/css2?family=Passion+One:wght@700&family=Oswald:wght@700&family=Lato&display=swap');
        /* --- Base Styles --- */
        html, body, [class*="st-"], button, input, textarea, select {
            font-family: 'Lato', sans-serif !important;
            color: #000000 !important; /* Black text */
        }
        .stApp {
            background-color: #F7F1E3 !important; /* Cream background */
        }
        [data-testid="stSidebar"] {
            background-color: #e9e4d9 !important; /* Slightly darker cream for sidebar */
            border-right: 2px solid #000000 !important;
        }
        /* Hide default Streamlit header */
        [data-testid="stHeader"] {
            background-color: #F7F1E3 !important; /* Match background */
            box-shadow: none !important;
            border-bottom: none !important;
            height: 0px !important; /* Attempt to hide */
            visibility: hidden !important;
        }
        /* --- Title Area --- */
        .title-container {
            padding: 0.2rem 1rem; /* Reduced vertical padding */
            margin-bottom: 2rem;
            border-radius: 5px;
            display: inline-block; /* Fit content width */
            margin-left: auto; /* Center align block */
            margin-right: auto; /* Center align block */
            text-align: center; /* Center text inside */
        }
        .title-container h1 {
            font-family: 'Passion One', sans-serif !important; /* Monopoly-like font */
            color: #FFFFFF !important; /* White text */
            text-align: center;
            margin-bottom: 0 !important;
            font-size: 2.5em !important; /* Adjust size as needed */
            line-height: 1.2 !important; /* Adjust line height */
        }
        /* --- Other Headers --- */
        h2, h3 {
            font-family: 'Oswald', sans-serif !important; /* Bold sans-serif */
            color: #000000 !important;
            margin-bottom: 1rem !important;
            border-bottom: 1px solid #000000 !important; /* Underline headers */
            padding-bottom: 0.25rem;
        }
        /* --- Character Selection --- */
        .character-column {
            border: 2px solid transparent; /* Default no border */
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            background-color: rgba(255, 255, 255, 0.5); /* Slightly transparent white */
            height: 100%; /* Allow column to take full height */
            display: flex; /* Use flexbox */
            flex-direction: column; /* Stack children vertically */
            transition: border-color 0.3s ease-in-out, background-color 0.3s ease-in-out;
        }
        .character-column.selected {
            border-color: #DAA520 !important; /* Gold border when selected */
            background-color: rgba(250, 250, 210, 0.8); /* Light yellow tint when selected */
        }
        .character-column img {
            max-width: 80%;
            max-height: 280px; /* Adjusted max-height */
            height: auto;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        /* Sidebar headers */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
             font-family: 'Oswald', sans-serif !important;
             color: #000000 !important;
             border-bottom: none !important; /* No underline in sidebar */
        }
        /* Objective List Styling */
        .character-column ul {
            list-style-type: none; /* Remove default bullets */
            padding-left: 5px; /* Adjust left padding */
            margin-top: 0.5rem; /* Add some space above the list */
            text-align: left; /* Align text to the left */
            padding-bottom: 0.5rem; /* Add some padding below objectives */
        }
        .character-column li {
            margin-bottom: 0.3rem; /* Space between objectives */
            display: flex; /* Use flexbox for alignment */
            align-items: center; /* Vertically align icon and text */
        }
        /* Make description take available space, pushing objectives down */
        .character-column .description-wrapper { /* Target the new wrapper div */
            flex-grow: 1; /* Allow description wrapper to grow */
            margin-bottom: 0.5rem; /* Add space below description */
        }
        /* --- Dashboard Metrics (Sidebar) --- */
        .stMetric {
            background-color: #FFFFFF !important; /* White background for metrics */
            border: 1px solid #000000 !important;
            border-radius: 4px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stMetric > label { /* Label */
            font-family: 'Oswald', sans-serif !important;
            color: #000000 !important;
        }
        .stMetric > div > div > div { /* Value */
            font-family: 'Lato', sans-serif !important;
            font-weight: bold;
            color: #000000 !important;
        }
        .stMetric > div > div > p { /* Delta */
             font-family: 'Lato', sans-serif !important;
             color: #555555 !important; /* Grey delta */
        }
        /* Icon Styling for Sidebar */
        .metric-icon {
            height: 1.5em; /* Adjust size */
            width: 1.5em;
            display: block;
            margin: 0.2em auto 0 auto; /* Center and add some top margin */
        }
        /* --- Cards --- */
        .card-container {
            border: 1px solid #000000;
            border-radius: 8px;
            margin-bottom: 15px;
            background-color: #FAFAD2; /* Parchment background */
            height: 300px; /* Increased height for cards */
            display: flex;
            flex-direction: column;
            padding: 0; /* Remove padding from container */
            overflow: hidden;
            transition: border 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        }
        .card-container.selected {
            border: 3px solid #DAA520 !important;
            box-shadow: 0 0 10px 2px #DAA520 !important;
        }
        .card-top-bar {
            min-height: 3.5em;
            margin-bottom: 10px;
            padding: 6px 8px; /* Reduced padding */
            display: flex;
            align-items: center;
            flex-shrink: 0;
            color: #FFFFFF !important; /* White text for title */
        }
        .card-top-bar.monetary { background-color: #0072BB; } /* Monopoly Blue */
        .card-top-bar.fiscal { background-color: #A0522D; } /* Sienna Brown for Fiscal */
        .card-top-bar.default { background-color: #8B4513; } /* Brown */
        .card-title {
            font-family: 'Oswald', sans-serif !important;
            font-weight: bold;
            font-size: 1.1em;
            text-align: left;
            margin-bottom: 0;
            margin-left: 0.5em; /* Space after stance icon */
            line-height: 1.3;
            word-wrap: break-word;
            overflow-wrap: break-word;
            color: inherit; /* Inherit color from parent (.card-top-bar) */
        }
        .card-icon {
            height: 1.1em;
            width: 1.1em;
            vertical-align: middle;
            filter: brightness(0) invert(1);
            margin-right: 0.4em;
            flex-shrink: 0;
        }
        .stance-icon {
            height: 1em;
            width: 1em;
            vertical-align: middle;
            filter: brightness(0) invert(1);
            margin-left: 0.5em;
            flex-shrink: 0;
        }
        .card-main-content {
            padding: 0 10px 8px 10px; /* Reduced padding */
            flex-grow: 1; /* Allow content area to grow */
            overflow-y: auto; /* Allow scrolling if needed */
            min-height: 0; /* Allow shrinking for flexbox */
            display: flex;
            flex-direction: column;
            justify-content: space-between; /* Push button to bottom */
        }
        .card-desc {
            font-family: 'Lato', sans-serif !important;
            font-size: 0.9em;
            color: #000000 !important;
            margin-bottom: 10px;
        }
        .card-main-content .stExpander {
            padding: 0 !important;
            margin-top: auto; /* Push expander towards bottom before button */
            margin-bottom: 5px; /* Space before button */
        }
         .card-main-content .stExpander p { /* Style caption inside expander */
            font-size: 0.8em;
            color: #555555;
        }
        .card-stance-bar {
            height: 16px; /* Increased height */
            width: 100%;
            margin-top: auto; /* Push to bottom */
            margin-bottom: 5px; /* Space before button */
            border-radius: 2px;
            text-align: center;
            color: white;
            font-size: 0.8em; /* Slightly larger text */
            line-height: 16px; /* Match height for vertical centering */
            font-weight: bold;
        }
        .expansionary-bar { background-color: #4CAF50; } /* Green */
        .contractionary-bar { background-color: #f44336; } /* Red */
        /* --- Event Cards --- */
        .event-card {
            border: 1px solid #cccccc; /* Lighter border than policy cards */
            border-radius: 5px;
            padding: 10px 15px; /* Add padding */
            margin-bottom: 10px;
            background-color: #ffffff; /* White background */
        }
        .event-card-title {
            font-family: 'Oswald', sans-serif !important;
            font-weight: bold;
            font-size: 1.1em;
            color: #000000 !important;
            margin-bottom: 5px;
        }
        .event-card-desc {
            font-family: 'Lato', sans-serif !important;
            font-size: 0.95em;
            color: #333333 !important;
            margin-bottom: 8px;
        }
        .event-card .stExpander {
            border: none !important;
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }
         .event-card .stExpander p { /* Style caption inside expander */
            font-size: 0.85em;
            color: #555555;
        }
        /* --- Buttons --- */
        .stButton > button {
            font-family: 'Oswald', sans-serif !important;
            border: 1px solid #000000 !important;
            border-radius: 3px !important;
            background-color: #FFFFFF !important;
            color: #000000 !important;
            width: 100%;
            margin-top: 10px; /* Space above button */
            padding: 0.5rem 1rem !important; /* Adjust padding */
            transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out, transform 0.1s ease-in-out; /* Smooth transition including transform */
            flex-shrink: 0; /* Prevent button from shrinking */
        }
        .stButton > button:hover {
            background-color: #cccccc !important; /* Slightly darker grey hover */
            color: #000000 !important;
            border-color: #000000 !important;
            transform: scale(1.02); /* Slight scale up on hover */
        }
         .stButton > button[kind="primary"] { /* Selected button */
            background-color: #aaaaaa !important; /* Lighter grey for selected */
            color: #000000 !important; /* Black text for selected */
            border-color: #000000 !important;
        }
        /* --- Dividers --- */
        hr {
            border-top: 1px solid #000000 !important;
            margin-top: 1rem !important;
            margin-bottom: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

def display_title_logo():
    """Displays the game title and logo."""
    logo_uri = get_logo_data_uri()
    if logo_uri:
        st.markdown(f'''<div style="text-align: center;">
                            <div class="title-container" style="background-color: transparent !important; padding: 0.5rem 0;">
                                <img src="{logo_uri}" alt="SFCGame Logo" style="height: 120px; display: block; margin-left: auto; margin-right: auto;">
                            </div>
                       </div>''', unsafe_allow_html=True)
    else:
        st.warning("Logo image 'sfcgamelogo.png' not found or could not be loaded. Displaying text title.")
        st.markdown('<div style="text-align: center;"><div class="title-container"><h1>SFCGAME</h1></div></div>', unsafe_allow_html=True)

def display_character_selection():
    """Renders the character selection screen."""
    st.header("Choose Your Economic Advisor")
    st.write("Select the advisor whose economic philosophy and objectives align with your strategy.")

    cols = st.columns(len(CHARACTERS))
    selected_id = st.session_state.selected_character_id

    for i, (char_id, char_data) in enumerate(CHARACTERS.items()):
        with cols[i]:
            container_class = "character-column"
            if char_id == selected_id:
                container_class += " selected"

            img_path = char_data.get('image_path')
            img_html = ""
            if img_path:
                try:
                    # Use relative path assuming assets/ is accessible
                    full_img_path = os.path.join("assets", "characters", os.path.basename(img_path))
                    img_data_uri = get_base64_of_bin_file(full_img_path)
                    if img_data_uri:
                        img_html = f'<img src="data:image/png;base64,{img_data_uri}" alt="{char_data["name"]}">'
                    else:
                        img_html = f'<p style="color: red;">Image not found: {full_img_path}</p>'
                except Exception as e:
                    img_html = f'<p style="color: red;">Error loading image: {e}</p>'
                    logging.error(f"Error loading character image {img_path}: {e}")

            # Objective List Generation
            objective_icon_map = {
                "gdp_index": "Yk", "unemployment": "ER", "inflation": "PI", "debt_gdp": "GD_GDP"
            }
            objectives_list = list(char_data.get('objectives', {}).items())
            objectives_html = ""
            for j in range(3): # Always generate 3 list items
                if j < len(objectives_list):
                    obj_key, obj = objectives_list[j]
                    icon_uri = get_icon_data_uri(objective_icon_map.get(obj_key, ''))
                    icon_img = f'<img src="{icon_uri}" style="height: 1em; width: 1em; margin-right: 0.5em;">' if icon_uri else ''
                    objectives_html += f"""<li>
                            {icon_img}
                            <small>{obj['label']}: {obj['condition']} {obj['target_value']}{'%' if obj['target_type'] == 'percent' else ''}</small>
                        </li>"""
                else:
                    objectives_html += '<li><small>&nbsp;</small></li>' # Placeholder for alignment

            st.markdown(f"""
            <div class="{container_class}">
                <div style="flex-grow: 1;"> <!-- Wrapper for content above objectives -->
                    {img_html}
                    <h4>{char_data['name']}</h4>
                    <p><small>{char_data['description']}</small></p>
                </div>
                <div> <!-- Wrapper for objectives -->
                    <p><strong>Objectives:</strong></p>
                    <ul>{objectives_html}</ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Selection Button - Logic handled in game_logic.py
            button_label = "Selected" if char_id == selected_id else "Select"
            button_type = "primary" if char_id == selected_id else "secondary"
            if st.button(button_label, key=f"select_{char_id}", type=button_type, use_container_width=True):
                # Trigger state update handled by the calling function in game_logic
                st.session_state.action_trigger = ("select_character", char_id)
                st.rerun() # Rerun to process the action

# --- New function for KPIs and Events ---
def display_kpi_and_events_section():
    """Renders the Year Header, KPI plots, and Active Events."""
    current_year = st.session_state.current_year
    st.header(f"Year {current_year}")

    # --- Display KPI Plots in 2x2 Grid ---
    st.markdown("##### Key Economic Indicators")
    row1_cols = st.columns(2)
    with row1_cols[0]:
        st.altair_chart(create_kpi_plot('Yk_Index', 'GDP Index (Y1=100)'), use_container_width=True)
    with row1_cols[1]:
        st.altair_chart(create_kpi_plot('PI', 'Inflation Rate'), use_container_width=True)
    row2_cols = st.columns(2)
    with row2_cols[0]:
        st.altair_chart(create_kpi_plot('Unemployment', 'Unemployment Rate'), use_container_width=True)
    with row2_cols[1]:
        st.altair_chart(create_kpi_plot('GD_GDP', 'Debt/GDP Ratio'), use_container_width=True)

    # --- Display Active Events ---
    st.markdown("##### Active Events")
    active_events = st.session_state.get('active_events_this_year', [])
    if active_events:
        num_event_cols = min(len(active_events), 3)
        event_cols = st.columns(num_event_cols)
        for i, event_name in enumerate(active_events):
            with event_cols[i % num_event_cols]:
                event_details = ECONOMIC_EVENTS.get(event_name, {})
                event_desc = event_details.get('desc', 'No description available.')
                param_name = event_details.get('param')
                effect_value = event_details.get('effect')
                effect_str = ""
                if param_name and effect_value is not None and np.isfinite(effect_value):
                    param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown Parameter")
                    formatted_val = format_effect(param_name, effect_value)
                    effect_str = f"Effect: {formatted_val} on {param_name} ({param_desc})"
                    effect_str = f'<small style="color: #888;"><i>{effect_str}</i></small>'

                st.markdown(f"""
                <div class="event-card" style="min-height: 100px; display: flex; flex-direction: column; justify-content: flex-start;">
                    <div>
                        <div class="event-card-title">{event_name}</div>
                        <div class="event-card-desc">{event_desc}</div>
                        {effect_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("None")

# --- Renamed function for Policy Selection ---
def display_policy_selection_section():
    """Renders the UI for the Policy Card selection part of the YEAR_START phase."""
    current_year = st.session_state.current_year # Keep for button keys if needed

    st.markdown("---") # Divider

    # --- Card Selection UI ---
    st.subheader("Select Policy Cards to Play")
    available_cards = st.session_state.player_hand
    selected_cards_this_turn = st.session_state.cards_selected_this_year
    max_cards_allowed = 2

    if not available_cards:
        st.write("No policy cards currently in hand.")
    else:
        unique_card_names = sorted(list(set(
            card_name for card_name in available_cards
            if POLICY_CARDS.get(card_name, {}).get('type') in ["Fiscal", "Monetary"]
        )))

        if not unique_card_names:
            st.write("No Fiscal or Monetary policy cards currently in hand.")
        else:
            num_cards = len(unique_card_names)
            num_cols = min(num_cards, MAX_CARDS_PER_ROW)
            cols = st.columns(num_cols)
            card_render_index = 0
            for card_name in unique_card_names:
                with cols[card_render_index % num_cols]:
                    card_info = POLICY_CARDS.get(card_name, {})
                    is_selected = card_name in selected_cards_this_turn
                    card_type = card_info.get('type', 'Unknown').lower()
                    card_stance = card_info.get('stance', None)

                    # Prepare Effect String
                    effect_str_parts = []
                    boost_applied_display = False
                    bonus_multiplier_to_apply = 1.0
                    selected_char_id = st.session_state.get('selected_character_id')
                    if selected_char_id and selected_char_id in CHARACTERS and card_stance and card_type:
                        character_data = CHARACTERS[selected_char_id]
                        bonus_criteria = character_data.get('bonus_criteria', [])
                        bonus_multiplier = character_data.get('bonus_multiplier', 1.0)
                        criteria_matched = any(
                            card_stance == crit_stance and card_type.lower() == crit_type.lower()
                            for crit_stance, crit_type in bonus_criteria
                        )
                        if criteria_matched:
                            bonus_multiplier_to_apply = bonus_multiplier
                            boost_applied_display = True

                    card_effects_list = card_info.get('effects', [])
                    for effect_detail in card_effects_list:
                        param_name = effect_detail.get('param')
                        base_effect = effect_detail.get('effect')
                        if param_name and isinstance(base_effect, (int, float)) and np.isfinite(base_effect):
                            actual_effect = base_effect * bonus_multiplier_to_apply
                            formatted_effect = format_effect(param_name, actual_effect)
                            param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown")
                            if formatted_effect != "N/A":
                                effect_str_parts.append(f"{formatted_effect} on {param_name} ({param_desc})")

                    if effect_str_parts:
                        boost_indicator = " (Boosted!)" if boost_applied_display else ""
                        effects_combined = "; ".join(effect_str_parts)
                        effect_str = f'<small><i>Effect{boost_indicator}: {effects_combined}</i></small>'
                    else:
                        effect_str = '<small><i>Effect details missing.</i></small>'

                    # Card Rendering
                    card_container_class = "card-container selected" if is_selected else "card-container"
                    icon_data_uri = get_icon_data_uri(card_type)
                    icon_html = f'<img src="{icon_data_uri}" class="card-icon">' if icon_data_uri else "❓"
                    top_bar_color_class = f"{card_type}" if card_type in ["monetary", "fiscal"] else "default"

                    st.markdown(f'''
                    <div class="{card_container_class}">
                        <div class="card-top-bar {top_bar_color_class}">
                           {icon_html} <span class="card-title">{card_type.capitalize()}: {card_name}</span>
                        </div>
                        <div class="card-main-content">
                            <div class="card-desc">
                                {card_info.get('desc', 'No description.')}<br>
                                {effect_str}
                            </div>
                            {'<div class="card-stance-bar ' + card_stance + '-bar">' + card_stance.capitalize() + '</div>' if card_stance else ''}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                    # Selection Button - Logic handled in game_logic.py
                    button_label = "Deselect" if is_selected else "Select"
                    button_type = "primary" if is_selected else "secondary"
                    button_key = f"select_{card_name}_{card_render_index}_{current_year}"
                    if st.button(button_label, key=button_key, type=button_type, use_container_width=True):
                        st.session_state.action_trigger = ("toggle_card_selection", card_name)
                        st.rerun()

                card_render_index += 1

    st.divider()
    if selected_cards_this_turn:
        st.write("Selected for this turn:")
        for card_name in selected_cards_this_turn: st.markdown(f"- {card_name}")
    else:
        st.write("No cards selected for this turn.")

    # --- Detailed Data Expanders ---
    st.divider()
    with st.expander("SFC Matrices"):
        model_state = st.session_state.sfc_model_object
        if model_state.solutions:
            current_solution = model_state.solutions[-1]
            prev_solution = model_state.solutions[-2] if len(model_state.solutions) > 1 else st.session_state.get('initial_state_dict')

            display_balance_sheet_matrix(current_solution)
            st.divider()
            if prev_solution: display_revaluation_matrix(current_solution, prev_solution); st.divider()
            else: st.caption("Revaluation matrix requires previous period data.")
            if prev_solution: display_transaction_flow_matrix(current_solution, prev_solution)
            else: st.caption("Transaction flow matrix requires previous period data.")
        else:
            st.caption("Matrices require simulation results.")

    with st.expander("View History Table"):
        if st.session_state.history:
            column_mapping = {
                'year': 'Year', 'Yk': 'Real GDP (Yk)', 'PI': 'Inflation (PI)', 'ER': 'Employment Rate (ER)',
                'GRk': 'Capital Growth (GRk)', 'Rb': 'Bill Rate (Rb)', 'Rl': 'Loan Rate (Rl)', 'Rm': 'Deposit Rate (Rm)',
                'BUR': 'Debt Burden (BUR)', 'Q': "Tobin's Q (Q)", 'CAR': 'Capital Adequacy (CAR)',
                'PSBR': 'Gov Deficit (PSBR)', 'GD': 'Gov Debt Stock (GD)', 'Y': 'Nominal GDP (Y)',
                'V': 'Household Wealth (V)', 'Lhs': 'Household Loans (Lhs)', 'Lfs': 'Firm Loans (Lfs)',
                'cards_played': 'Cards Played', 'events': 'Active Events'
            }
            history_df = pd.DataFrame(st.session_state.history).sort_values(by='year', ascending=False)
            display_df = history_df[[col for col in column_mapping if col in history_df.columns]].rename(columns=column_mapping)
            st.dataframe(display_df)
        else: st.write("No history recorded yet.")

    # --- Proceed Button ---
    can_proceed = len(selected_cards_this_turn) <= max_cards_allowed
    if not can_proceed:
        st.warning(f"You can select a maximum of {max_cards_allowed} cards per turn.")
    if st.button("Confirm Policies & Run Simulation", disabled=not can_proceed):
        st.session_state.action_trigger = ("confirm_policies", None)
        st.rerun()

def display_dilemma():
    """Renders the Advisor's Dilemma screen."""
    st.header(f"Year {st.session_state.current_year} - Advisor's Dilemma")
    dilemma_info = st.session_state.current_dilemma['data']
    st.subheader(dilemma_info['title'])
    st.markdown(f"_{dilemma_info['flavor_text']}_")
    st.markdown("---")
    col1, col2 = st.columns(2)
    option_a = dilemma_info['option_a']
    option_b = dilemma_info['option_b']

    def format_dilemma_option(option_data):
        """Helper to format dilemma option details."""
        add_cards = option_data.get('add_cards', [])
        remove_cards = option_data.get('remove_cards', [])
        details = ""
        if add_cards: details += f"Adds: {', '.join(add_cards)}\n"
        if remove_cards: details += f"Removes: {', '.join(remove_cards)}"
        return details.strip()

    with col1:
        st.markdown(f"**Option A: {option_a['name']}**")
        if st.button(f"Choose: {option_a['name']}", key="dilemma_a", use_container_width=True):
            st.session_state.action_trigger = ("choose_dilemma", "A")
            st.rerun()
        if option_a.get('choice_flavour'):
            st.caption(f"*{option_a['choice_flavour']}*")
        option_a_details = format_dilemma_option(option_a)
        if option_a_details:
            st.caption(option_a_details)

    with col2:
        st.markdown(f"**Option B: {option_b['name']}**")
        if st.button(f"Choose: {option_b['name']}", key="dilemma_b", use_container_width=True):
            st.session_state.action_trigger = ("choose_dilemma", "B")
            st.rerun()
        if option_b.get('choice_flavour'):
            st.caption(f"*{option_b['choice_flavour']}*")
        option_b_details = format_dilemma_option(option_b)
        if option_b_details:
            st.caption(option_b_details)

def display_game_over_screen(all_objectives_met, results_summary):
    """Renders the game over screen with results and feedback form."""
    st.header("Game Over!")
    st.balloons()

    # Display Objective Results
    st.subheader("Objective Results")
    if results_summary:
        st.dataframe(pd.DataFrame(results_summary).set_index("Objective"))
    else:
        st.warning("No game objectives were set or results available.")

    if all_objectives_met:
        st.success("Congratulations! You met all objectives!")
    else:
        st.error("Unfortunately, you did not meet all objectives.")

    # Feedback Form
    st.divider()
    st.subheader("Feedback")
    st.write("We'd love your feedback to make this game better!")
    RECIPIENT_EMAIL = "omareth@gmail.com" # Consider moving to config

    with st.form("feedback_form"):
        enjoyment = st.text_area("What did you enjoy most? (Optional)")
        confusion = st.text_area("Was anything confusing? (Optional)")
        suggestions = st.text_area("Suggestions for improvement? (Optional)")
        other_comments = st.text_area("Any other comments? (Optional)")
        user_identity = st.text_input("Your Name/Email (Optional):")
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            subject = "SFCGame Feedback"
            body = f"""Enjoyment: {enjoyment or 'N/A'}\n\nConfusion: {confusion or 'N/A'}\n\nSuggestions: {suggestions or 'N/A'}\n\nOther Comments: {other_comments or 'N/A'}\n\nUser: {user_identity or 'Anonymous'}"""
            mailto_url = f"mailto:{RECIPIENT_EMAIL}?subject={quote(subject)}&body={quote(body)}"
            st.success("Feedback prepared! Click the link below to open your email client.")
            st.markdown(f'<a href="{mailto_url}" target="_blank">Click here to send feedback via email</a>', unsafe_allow_html=True)
            logging.info(f"Generated mailto link for feedback. User: {user_identity or 'Anonymous'}")

    # Final SFC Matrices
    st.divider()
    st.subheader("Final Economic State (SFC Matrices)")
    model_state = st.session_state.get('sfc_model_object')
    if model_state and hasattr(model_state, 'solutions') and model_state.solutions:
        final_solution = model_state.solutions[-1]
        second_last_solution = model_state.solutions[-2] if len(model_state.solutions) >= 2 else st.session_state.get('initial_state_dict')
        display_balance_sheet_matrix(final_solution)
        st.divider()
        if second_last_solution:
            display_revaluation_matrix(final_solution, second_last_solution); st.divider()
            display_transaction_flow_matrix(final_solution, second_last_solution)
        else:
            st.caption("Revaluation and Transaction Flow matrices require previous period data.")
    else:
        st.warning("Could not display final SFC matrices due to missing simulation data.")

def display_credits():
    """Displays the credits and model explanation expander."""
    st.divider()
    with st.expander("Credits and Model Explanation", expanded=False):
        st.markdown("""
        ### Code Credits
        Powered by:
        *   **pylinsolve**: [https://github.com/kennt/pylinsolve](https://github.com/kennt/pylinsolve)
        *   **monetary-economics**: [https://github.com/kennt/monetary-economics](https://github.com/kennt/monetary-economics)
        (Both by Kent Barber)

        ### About the Model Engine
        Uses pylinsolve for iterative equation solving (Gauss-Seidel, Newton-Raphson, Broyden) tailored for Stock-Flow Consistent (SFC) models.

        ### The GROWTH Model Explained
        Based on Chapter 11 of Godley & Lavoie's *"Monetary Economics"* (2007).

        #### Key Features
        *   **Stock-Flow Consistent**: Complete accounting consistency.
        *   **Exogenous Policy**: Gov spending growth, tax rates, bill rate set by policy.
        *   **Growing Economy**: Requires active policy for full employment without inflation.
        *   **Investment & Capital**: Endogenous pricing mark-up, self-financing targets.
        *   **Equity Markets**: Firms issue shares, households purchase.
        *   **Loan Dynamics**: Household & firm borrowing, default modeling.
        *   **Banking System**: Capital reserves, loan rate mark-up on deposit rate.

        #### Model Structure
        Five sectors (households, firms, banks, central bank, government) interacting via production, consumption, investment, saving, wage/price setting, portfolio allocation, lending, fiscal operations.
        """)