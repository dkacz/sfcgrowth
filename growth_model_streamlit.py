# growth_model_streamlit.py
"""
Main Streamlit application script for the SFC Growth Model Game.
Orchestrates the game flow by calling functions from refactored modules.
"""

import streamlit as st
import logging
import sys
import os

# --- Add src directory to Python path ---
# This ensures that modules in the 'src' directory can be imported correctly.
# It assumes the script is run from the project root directory ('growth').
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

# --- Import Refactored Modules ---
try:
    from src.state_manager import initialize_game_state
    from src.ui_sidebar import display_sidebar
    from src.ui_main import display_css, display_title_logo, display_credits
    from src.game_logic import run_game
    # Config and Utils might be used implicitly by other modules, but import if needed directly.
    # from src.config import GAME_END_YEAR # Example if needed
    # from src.utils import format_percent # Example if needed
except ImportError as e:
    st.error(f"Fatal Error: Could not import necessary game modules: {e}")
    st.error("Please ensure the 'src' directory and all required Python files exist.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during module imports: {e}")
    logging.exception("Error during module imports:")
    st.stop()


# --- Logging Setup ---
# Configure logging (consider moving to a dedicated config/setup function if complex)
log_file = 'debug_session.log'
# Clear the log file at the start of each session if desired
# if not st.session_state.get("log_initialized", False):
#     try:
#         with open(log_file, 'w') as f:
#             f.write("") # Clear file
#         st.session_state.log_initialized = True
#     except IOError as e:
#         st.warning(f"Could not clear log file: {e}")

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    filename=log_file,
                    filemode='a') # Use 'a' to append to the log file across runs/sessions

logging.info("--- Streamlit App Start / Rerun ---")


# --- Page Configuration ---
# Set page config early, potentially using values from config.py if needed
# Initialize year for title before config if possible, otherwise default
page_title_year = st.session_state.get('current_year', 0)
page_title = f"SFCGAME - Year {page_title_year}"
st.set_page_config(page_title=page_title, layout="wide", initial_sidebar_state="expanded")

# --- Initialize Game State ---
# This function now handles the setup if it hasn't happened yet.
# It includes the st.rerun() call if initialization occurs.
initialize_game_state()

# --- Render UI Components ---
display_css()
display_title_logo()
display_sidebar() # Render the sidebar content

# --- Run Main Game Logic ---
# The run_game function now handles the logic based on st.session_state.game_phase
# and calls the appropriate UI rendering functions for the main area.
try:
    run_game()
except Exception as e:
    st.error(f"An unexpected error occurred during game execution: {e}")
    logging.exception("Error during run_game():")
    # Consider adding a button to reset or stop gracefully

# --- Display Credits ---
# Display credits at the bottom of the main area
display_credits()

# --- Debug Info (Optional) ---
# with st.expander("Debug Info"):
#    st.write("Session State:", st.session_state)

logging.info("--- Streamlit App End / Rerun ---")
