# src/ui_main.py
"""Functions for rendering the main Streamlit UI content area."""

import streamlit as st
# import pandas as pd # Moved to ui_policy_cards.py
import numpy as np
import logging
# import altair as alt # Moved to ui_plotting.py
# from urllib.parse import quote # Moved to ui_game_over.py
import os

# Import project modules
from src.utils import (
    get_logo_data_uri, get_icon_data_uri, format_effect # Removed get_base64_of_bin_file
)
from src.config import MAX_CARDS_PER_ROW, PARAM_DESCRIPTIONS, GAME_END_YEAR
from src.ui_css import display_css # Import the CSS function
from src.ui_character_select import display_character_selection # Import character selection UI
from src.ui_plotting import create_kpi_plot # Import plotting function
from src.ui_kpi_events import display_kpi_and_events_section # Import KPI/Events UI
from src.ui_policy_cards import display_policy_selection_section # Import Policy Card UI
from src.ui_dilemma import display_dilemma # Import Dilemma UI
from src.ui_game_over import display_game_over_screen # Import Game Over UI
from src.ui_credits import display_credits # Import Credits UI
from characters import CHARACTERS # Assuming characters.py is in the root
from cards import POLICY_CARDS # Assuming cards.py is in the root
from events import ECONOMIC_EVENTS # Assuming events.py is in the root
# from matrix_display import ( # Moved to ui_policy_cards.py and ui_game_over.py
#     display_balance_sheet_matrix, display_revaluation_matrix,
#     display_transaction_flow_matrix
# )
# Import the specific plot function from ui_sidebar (or move it to utils if more appropriate)
# For now, let's assume it's needed here too, or we pass the charts as arguments.
# Re-evaluating: KPI plots are generated *within* the YEAR_START logic, so the function needs to be accessible there.
# Let's define it here for now, potentially moving it later if needed elsewhere.

# (create_kpi_plot function moved to src/ui_plotting.py)

# --- UI Rendering Functions ---

# (display_css function moved to src/ui_css.py)

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

# (display_character_selection function moved to src/ui_character_select.py)

# (display_kpi_and_events_section function moved to src/ui_kpi_events.py)

# (display_policy_selection_section function moved to src/ui_policy_cards.py)

# (display_dilemma function moved to src/ui_dilemma.py)

# (display_game_over_screen function moved to src/ui_game_over.py)

# (display_credits function moved to src/ui_credits.py)
