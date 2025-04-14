# src/ui_kpi_events.py
"""Handles rendering the KPI plots and Active Events section."""

import streamlit as st
import numpy as np

# Import project modules
from src.ui_plotting import create_kpi_plot
from src.config import PARAM_DESCRIPTIONS
from src.utils import format_effect
from events import ECONOMIC_EVENTS, CHARACTER_EVENTS # Assuming events.py is in the root
from events import ECONOMIC_EVENTS # Assuming events.py is in the root

def display_kpi_and_events_section():
    """Renders the Year Header, KPI plots, and Active Events."""
    current_year = st.session_state.current_year
    st.header(f"Year {current_year}")

    # --- Display KPI Plots in 2x2 Grid ---
    st.markdown("##### Key Economic Indicators")
    row1_cols = st.columns(2)
    with row1_cols[0]:
        # Use the imported plotting function
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
        # Combine both event dictionaries for easier lookup
        all_events = {**ECONOMIC_EVENTS, **CHARACTER_EVENTS}
        for i, event_name in enumerate(active_events):
            with event_cols[i % num_event_cols]:
                event_details = all_events.get(event_name, {})
                event_desc = event_details.get('desc', 'No description available.')
                param_name = event_details.get('param')
                effect_value = event_details.get('effect')
                effect_str = ""
                if param_name and effect_value is not None and np.isfinite(effect_value):
                    param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown Parameter")
                    formatted_val = format_effect(param_name, effect_value)
                    effect_str = f"Effect: {formatted_val} on {param_name} ({param_desc})"
                    effect_str = f'<small style="color: #888;"><i>{effect_str}</i></small>'

                # Calculate duration string conditionally
                duration_str = ""
                duration = event_details.get('duration', 0)
                if duration > 0:
                    turn_suffix = 'turn' if duration == 1 else 'turns'
                    duration_str = f'<small style="color: #888;"><i>Duration: {duration} {turn_suffix}</i></small>'

                # Render event card
                st.markdown(f"""
                <div class="event-card" style="min-height: 100px;">
                    <div class="event-card-title">{event_name}</div>
                    <div class="event-card-desc">{event_desc}</div>
                    <div class="event-card-effect">{effect_str}</div>
                    <div class="event-card-duration">{duration_str}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("None")