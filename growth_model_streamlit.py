# Refactored growth_model_streamlit.py content
import streamlit as st
import pandas as pd
import numpy as np
import copy
import sys
import io
from contextlib import redirect_stdout
import logging
import os
import base64 # Import base64 encoding

# Import the necessary components from the model definition file
from chapter_11_model_growth import (
    create_growth_model, growth_parameters, growth_exogenous,
    growth_variables # Removed baseline import
)
from pysolve.model import SolutionNotFoundError, Model

# Import game mechanics functions (Assuming these exist and are correct)
# Make sure these files are present in the new branch
try:
    from game_mechanics import (
        create_deck, draw_cards, check_for_events, apply_effects
    )
    from cards import POLICY_CARDS
    from events import ECONOMIC_EVENTS
    from matrix_display import (
        format_value,
        display_balance_sheet_matrix, display_revaluation_matrix,
        display_transaction_flow_matrix
    )
except ImportError as e:
    st.error(f"Failed to import game components: {e}. Ensure cards.py, events.py, game_mechanics.py, matrix_display.py are present.")
    st.stop()


# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
INITIAL_HAND_SIZE = 5
CARDS_TO_DRAW_PER_YEAR = 2
MAX_CARDS_PER_ROW = 4 # For card display layout
ICON_DIR = "assets/icons" # Define icon directory

# --- Icon Mapping ---
# Maps internal keys/types to filenames in ICON_DIR
ICON_FILENAME_MAP = {
    # Card Types
    "monetary": "monetary_icon.png",
    "fiscal": "fiscal_icon.png",
    # Dashboard Metrics (using keys from history/solution dicts)
    "Yk": "factory.png",
    "PI": "inflation_icon.png",
    "ER": "people.png", # Note: We calculate unemployment from ER
    "GRk": "buildingouparrow.png",
    "Rb": "percentagescroll.png",
    "Rl": "percentagescroll.png", # Reusing bill rate icon for loan rate
    "Rm": "pig.png",
    "Q": "tobins_q_icon.png",
    "BUR": "bendingman.png",
    "CAR": "plusshield.png",
    "PSBR": "dollardownarrow.png",
    "GD_GDP": "fiscal_icon.png" # Reusing fiscal icon for Gov Debt/GDP ratio
}
# Removed EMOJI_MAP

# --- Helper Functions ---
class NullIO(io.StringIO):
    def write(self, txt):
        pass

def format_percent(value):
    """Formats a float as a percentage string."""
    if not np.isfinite(value):
        return "N/A"
    return f"{value*100:.2f}%"

def get_delta(current_val, prev_val):
    """ Helper to calculate PERCENTAGE delta string for st.metric """
    # Check for invalid inputs first
    if not np.isfinite(current_val) or prev_val is None or not np.isfinite(prev_val):
        return None

    # Handle zero previous value
    if np.isclose(prev_val, 0):
        if np.isclose(current_val, 0):
            return "0.0%" # No change from zero
        else:
            return "N/A" # Undefined percentage change from zero

    # Calculate percentage change
    delta_pct = ((current_val - prev_val) / prev_val) * 100

    if np.isclose(delta_pct, 0):
        return "0.0%"
    else:
        return f"{delta_pct:+.1f}%" # Show sign and one decimal place

def get_delta_percent(current_val, prev_val):
     """ Helper to calculate percentage POINT delta string for st.metric """
     # Fix condition order: check for None before calling isfinite
     if not np.isfinite(current_val) or prev_val is None or not np.isfinite(prev_val) or np.isclose(current_val, prev_val):
         return None
     delta = (current_val - prev_val) * 100
     # Format as percentage points, including sign
     return f"{delta:+.2f} % pts" # More explicit label

# --- Icon Handling with Base64 ---
@st.cache_data # Cache the encoded icons
def get_base64_of_bin_file(bin_file):
    """ Reads binary file and returns base64 encoded string """
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        logging.warning(f"Icon file not found: {bin_file}")
        return None
    except Exception as e:
        logging.error(f"Error reading icon file {bin_file}: {e}")
        return None

def get_icon_data_uri(icon_key):
    """Gets the base64 data URI for an icon."""
    filename = ICON_FILENAME_MAP.get(icon_key)
    if filename:
        filepath = os.path.join(ICON_DIR, filename)
        base64_string = get_base64_of_bin_file(filepath)
        if base64_string:
            return f"data:image/png;base64,{base64_string}"
    return None # Return None if key not in map or file error

# --- Logo Handling ---
@st.cache_data # Cache the encoded logo
def get_logo_data_uri(logo_filename="sfcgamelogo.png"):
    """Reads the logo file and returns base64 encoded data URI."""
    # Assuming logo is in the root directory
    logo_path = logo_filename
    if not os.path.exists(logo_path):
        logging.warning(f"Logo file not found at specified path: {logo_path}")
        return None

    base64_string = get_base64_of_bin_file(logo_path) # Reuse existing helper
    if base64_string:
        # Assuming PNG format, adjust if needed
        return f"data:image/png;base64,{base64_string}"
    else:
        logging.warning(f"Failed to encode logo file: {logo_path}")
        return None

# Removed get_emoji_for_key function

# --- Dynamic Page Title ---
# Initialize year for title before config if possible, otherwise default
page_title_year = st.session_state.get('current_year', 0)
page_title = f"SFCGAME - Year {page_title_year}"

# --- Page Configuration ---
# Force light theme to ensure cream background applies correctly
st.set_page_config(page_title=page_title, layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS (Monopoly Theme) ---
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
    /* Sidebar headers */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
         font-family: 'Oswald', sans-serif !important;
         color: #000000 !important;
         border-bottom: none !important; /* No underline in sidebar */
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
    .card {
        border: 1px solid #000000;
        border-radius: 8px; /* Slightly more rounded corners */
        margin-bottom: 15px;
        background-color: #FAFAD2; /* Parchment background */
        height: 250px; /* Fixed height for cards */
        display: flex;
        flex-direction: column;
        padding: 0; /* Remove default padding, handle internally */
        overflow: hidden; /* Ensure top border stays within bounds */
        transition: border 0.2s ease-in-out, box-shadow 0.2s ease-in-out; /* Smooth transition */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* Add subtle drop shadow */
    }
    .card-top-bar {
        /* Removed height/min-height */
        margin-bottom: 10px;
        padding: 8px 10px; /* Adjusted padding */
        display: flex; /* Use flexbox for alignment */
        align-items: center; /* Center items vertically */
        flex-shrink: 0; /* Prevent bar from shrinking */
    }
    .card.monetary .card-top-bar {
        background-color: #0072BB; /* Monopoly Blue */
    }
    .card.fiscal .card-top-bar {
        background-color: #1FB25A; /* Monopoly Green */
    }
    /* Add other colors as needed */
    .card.default .card-top-bar { /* Fallback */
        background-color: #8B4513; /* Brown */
    }
    .card-content {
        padding: 0 15px 15px 15px; /* Padding for content below bar */
        display: flex;
        flex-direction: column;
        flex-grow: 1; /* Allow content area to grow */
        justify-content: space-between; /* Push button to bottom */
        overflow-y: auto; /* Allow description to scroll if needed */
        min-height: 0; /* Allow shrinking for flexbox */
    }
    .card-title { /* Now inside top bar */
        font-family: 'Oswald', sans-serif !important;
        font-weight: bold;
        font-size: 1.1em;
        color: #FFFFFF !important; /* White text on colored bar */
        text-align: left; /* Align left now that icon is there */
        margin-bottom: 0; /* Remove bottom margin */
        margin-left: 0.5em; /* Space after icon */
        /* flex-grow: 1; Removed flex-grow */
        line-height: 1.3; /* Allow text to wrap naturally */
        word-wrap: break-word; /* Ensure wrapping */
        overflow-wrap: break-word; /* Ensure wrapping */
    }
    .card-icon { /* Icon inside card title bar */
        height: 1.1em; /* Adjusted size */
        width: 1.1em;
        vertical-align: middle; /* Keep middle align */
        filter: brightness(0) invert(1); /* Make black PNG white */
        margin-right: 0.4em; /* Adjust spacing */
        flex-shrink: 0; /* Prevent icon from shrinking */
    }
    .card-desc {
        font-family: 'Lato', sans-serif !important;
        font-size: 0.9em;
        color: #000000 !important;
        margin-bottom: 10px;
        /* flex-grow: 1; Let card-content handle growth */
    }
    .card.selected {
        border: 3px solid #DAA520 !important; /* Thicker Gold border */
        box-shadow: 0 0 10px 2px #DAA520 !important; /* Stronger gold glow */
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
        transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out; /* Smooth transition */
        flex-shrink: 0; /* Prevent button from shrinking */
    }
    .stButton > button:hover {
        background-color: #e0e0e0 !important; /* Light grey hover */
        color: #000000 !important;
        border-color: #000000 !important;
    }
     .stButton > button[kind="primary"] { /* Selected button */
        background-color: #555555 !important;
        color: #FFFFFF !important;
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


# --- Game Title ---
# Wrap title in a div for styling and center it
logo_data_uri = get_logo_data_uri() # Call the new helper
if logo_data_uri:
    # Display the logo image, remove red background from container, center image
    st.markdown(f'''<div style="text-align: center;">
                        <div class="title-container" style="background-color: transparent !important; padding: 0.5rem 0;">
                            <img src="{logo_data_uri}" alt="SFCGame Logo" style="height: 120px; display: block; margin-left: auto; margin-right: auto;">
                        </div>
                   </div>''', unsafe_allow_html=True)
else:
    # Fallback to the original text title if logo loading fails
    st.warning("Logo image 'sfcgamelogo.png' not found or could not be loaded. Displaying text title.")
    st.markdown('<div style="text-align: center;"><div class="title-container"><h1>SFCGAME</h1></div></div>', unsafe_allow_html=True)
# st.title("SFCGAME") # Original title call removed
# st.markdown("Manage the economy through yearly turns using policy cards and responding to events.") # Subtitle removed

# --- Game State Initialization ---
if "game_initialized" not in st.session_state:
    st.session_state.game_initialized = True
    logging.info("--- Initializing Game State (Starting Year 0) ---")
    st.session_state.current_year = 0
    st.session_state.game_phase = "YEAR_START" # Initial phase

    # --- Model Initialization (No Initial Solve) ---
    try:
        # Construct dictionary first
        logging.info("Constructing initial t=0 state dictionary...")
        initial_state_dict = {}
        initial_state_dict.update(growth_parameters)
        defined_param_names = set(growth_parameters.keys())
        defined_variable_names = set(v[0] for v in growth_variables)
        for key, value in growth_exogenous:
            try:
                if key in defined_param_names or key in defined_variable_names:
                     initial_state_dict[key] = float(value)
            except (TypeError, ValueError):
                 if isinstance(value, str): initial_state_dict[key] = value
                 else: logging.warning(f"Could not convert exogenous value {key}={value} to float. Skipping.")
        for key, value in growth_variables:
             try:
                 if isinstance(value, str): initial_state_dict[key] = value
                 else: initial_state_dict[key] = float(value)
             except (TypeError, ValueError):
                 logging.warning(f"Could not convert variable value {key}={value} to float. Skipping.")
        logging.info(f"Initial t=0 state dictionary constructed with {len(initial_state_dict)} entries.")

        # Create fresh model and set values
        logging.info("Creating initial model object and setting values...")
        initial_model_object = create_growth_model()
        initial_model_object.set_values(initial_state_dict)

        # Store the UNSOLVED model object and the initial dictionary
        st.session_state.sfc_model_object: Model = initial_model_object
        st.session_state.initial_state_dict = initial_state_dict # Store for Year 0 display
        logging.info("Stored initial model object (unsolved) and initial state dict in session state.")

    except Exception as e:
        st.error(f"Fatal Error: An unexpected error occurred during model initialization: {e}")
        logging.exception("Unexpected error during model initialization.")
        st.stop()
    # --- End of Model Initialization ---

    # --- Game Variables Initialization ---
    try:
        st.session_state.deck = create_deck()
        st.session_state.player_hand = []
        st.session_state.deck, st.session_state.player_hand = draw_cards(
            st.session_state.deck, st.session_state.player_hand, INITIAL_HAND_SIZE
        )
        logging.info("Initialized deck and player hand.")
    except Exception as e:
        st.error(f"Failed to initialize deck/hand: {e}")
        st.stop()

    st.session_state.active_events_this_year = []
    st.session_state.cards_selected_this_year = []
    st.session_state.history = [] # Initialize history as empty
    st.session_state.initial_params = {} # For year 0 adjustments

    logging.info("Game Initialized at Year 0.")
    st.rerun() # Rerun to start the flow


# --- Sidebar ---
st.sidebar.header("Game Information")

# --- Dashboard Display (Moved to Top of Sidebar) ---
st.sidebar.header("Economic Dashboard")
if st.session_state.current_year == 0 or not st.session_state.history: # Check year and history
     st.sidebar.caption("Waiting for first year results...")
else: # Only display if Year > 0 and history exists
    # --- Get data directly from model object solutions ---
    model_state = st.session_state.sfc_model_object
    if not model_state.solutions or len(model_state.solutions) < 2:
        # This case means the first simulation hasn't finished or failed
        # Should be caught by the outer 'if', but added for safety
        st.sidebar.caption("Simulation results not yet available.")
        latest_history_entry = st.session_state.initial_state_dict # Fallback
        prev_year_data = None
        is_first_result_year = True
    else:
        latest_history_entry = model_state.solutions[-1] # Latest solved state
        prev_year_data = model_state.solutions[-2]       # Previous solved state
        is_first_result_year = (len(model_state.solutions) == 2) # True if only t=0 and t=1 exist
        # Note: This assumes history list corresponds directly to solutions list length after year 0
        if is_first_result_year:
            # If it's the first result year (Year 1), the 'previous' data is t=0
            # We can still use solutions[-2] which is solutions[0]
            pass # prev_year_data is already solutions[0]
        elif len(model_state.solutions) < 2: # Should not happen if outer check works
             prev_year_data = st.session_state.initial_state_dict # Fallback

    # Display Metrics in Sidebar using columns and Base64 icons
    st.sidebar.markdown("##### Macro Indicators")
    yk_val = latest_history_entry.get('Yk', np.nan)
    pi_val = latest_history_entry.get('PI', np.nan)
    er_val = latest_history_entry.get('ER', np.nan)
    grk_val = latest_history_entry.get('GRk', np.nan)
    yk_prev = prev_year_data.get('Yk') if prev_year_data else np.nan
    pi_prev = prev_year_data.get('PI') if prev_year_data else np.nan
    er_prev = prev_year_data.get('ER') if prev_year_data else np.nan
    grk_prev = prev_year_data.get('GRk') if prev_year_data else np.nan
    delta_yk = None if is_first_result_year else get_delta(yk_val, yk_prev)
    delta_pi = None if is_first_result_year else get_delta_percent(pi_val, pi_prev)
    unemp_val = 1 - er_val if np.isfinite(er_val) else np.nan
    unemp_prev = 1 - er_prev if er_prev is not None and np.isfinite(er_prev) else np.nan
    delta_unemp = None if is_first_result_year else get_delta_percent(unemp_val, unemp_prev)
    delta_grk = None if is_first_result_year else get_delta_percent(grk_val, grk_prev)

    # GDP
    icon_data_uri = get_icon_data_uri("Yk")
    cols = st.sidebar.columns([1, 4]) # Adjust column ratio if needed
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Real GDP (Yk)", value=format_value(yk_val), delta=delta_yk)
    # Inflation
    icon_data_uri = get_icon_data_uri("PI")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Inflation (PI)", value=format_percent(pi_val), delta=delta_pi)
    # Unemployment
    icon_data_uri = get_icon_data_uri("ER") # Use ER key for icon
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Unemployment Rate", value=format_percent(unemp_val), delta=delta_unemp)
    # Capital Growth
    icon_data_uri = get_icon_data_uri("GRk")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Capital Growth (GRk)", value=format_percent(grk_val), delta=delta_grk)


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

    # Bill Rate
    icon_data_uri = get_icon_data_uri("Rb")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Bill Rate (Rb)", value=format_percent(rb_val), delta=delta_rb)
    # Loan Rate
    icon_data_uri = get_icon_data_uri("Rl")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Loan Rate (Rl)", value=format_percent(rl_val), delta=delta_rl)
    # Deposit Rate
    icon_data_uri = get_icon_data_uri("Rm")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Deposit Rate (Rm)", value=format_percent(rm_val), delta=delta_rm)
    # Tobin's Q
    icon_data_uri = get_icon_data_uri("Q")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Tobin's Q", value=format_value(q_val), delta=delta_q)
    # Debt Burden
    icon_data_uri = get_icon_data_uri("BUR")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Debt Burden (BUR)", value=format_percent(bur_val), delta=delta_bur)
    # Capital Adequacy
    icon_data_uri = get_icon_data_uri("CAR")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Capital Adequacy (CAR)", value=format_percent(car_val), delta=delta_car)


    st.sidebar.markdown("##### Government Sector")
    psbr_val = latest_history_entry.get('PSBR', np.nan)
    gd_val = latest_history_entry.get('GD', np.nan)
    y_val = latest_history_entry.get('Y', np.nan)
    psbr_prev = prev_year_data.get('PSBR') if prev_year_data else np.nan
    gd_prev = prev_year_data.get('GD') if prev_year_data else np.nan
    y_prev = prev_year_data.get('Y') if prev_year_data else np.nan
    delta_psbr = None if is_first_result_year else get_delta(psbr_val, psbr_prev)
    gd_gdp_val = gd_val / y_val if y_val and y_val != 0 else np.nan
    gd_gdp_prev = gd_prev / y_prev if prev_year_data and y_prev and y_prev != 0 else np.nan
    delta_gd_gdp = None if is_first_result_year else get_delta_percent(gd_gdp_val, gd_gdp_prev)

    # Gov Deficit
    icon_data_uri = get_icon_data_uri("PSBR")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Gov Deficit (PSBR)", value=format_value(psbr_val), delta=delta_psbr)
    # Gov Debt / GDP
    icon_data_uri = get_icon_data_uri("GD_GDP")
    cols = st.sidebar.columns([1, 4])
    with cols[0]:
        if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
    with cols[1]:
        st.metric(label="Gov Debt / GDP", value=format_percent(gd_gdp_val), delta=delta_gd_gdp)
# --- End of Dashboard Display ---

# Display Hand and Events
st.sidebar.header("Player Hand")
if not st.session_state.get("player_hand"): # Use .get for safety
    st.sidebar.write("Hand is empty.")
else:
    st.sidebar.caption("Cards in hand:")
    for card_name in st.session_state.player_hand:
         st.sidebar.markdown(f"- {card_name}")

st.sidebar.header("Active Events")
if not st.session_state.get("active_events_this_year"): # Use .get for safety
    st.sidebar.write("No active events.")
else:
    st.sidebar.caption("Events affecting this year:")
    for event_name in st.session_state.active_events_this_year:
        if event_name in ECONOMIC_EVENTS:
            st.sidebar.markdown(f"- **{event_name}**: {ECONOMIC_EVENTS[event_name]['desc']}")
        else:
            st.sidebar.markdown(f"- {event_name}") # Fallback if not found
st.sidebar.divider()


# --- Main App Logic ---

# --- Game Mode UI ---
# Removed Year Header
# Removed Phase Subheader

# --- Phase Logic ---
if st.session_state.game_phase == "YEAR_START":

    # --- Year 0: Initial Setup ---
    if st.session_state.current_year == 0:
        # Removed instructional text
        if "initial_params_set" not in st.session_state:
             if "sfc_model_object" not in st.session_state:
                 st.error("Model object not found in session state for initial parameter adjustment.")
                 st.stop()

             with st.expander("Advanced: Set Initial Economic Conditions"):
                 st.caption("Adjust the starting parameters for the economy. These settings are locked once you start the game.")
                 initial_params_changed = False
                 initial_params_to_set = {}
                 # Define categories of parameters for better organization
                 parameter_categories = {
                     "Growth Parameters": [
                         ("gamma0", "Base growth rate of real capital stock (gamma0)", 0.00122, 0.0, 0.01),
                         ("gammar", "Effect of interest rate on capital growth (gammar)", 0.1, 0.0, 0.5),
                         ("gammau", "Effect of utilization on capital growth (gammau)", 0.05, 0.0, 0.5),
                         ("delta", "Rate of depreciation of fixed capital (delta)", 0.10667, 0.05, 0.2),
                     ],
                     "Consumption Parameters": [
                         ("alpha1", "Propensity to consume out of income (alpha1)", 0.75, 0.5, 1.0),
                         ("alpha2", "Propensity to consume out of wealth (alpha2)", 0.064, 0.01, 0.2),
                         ("eps", "Speed of adjustment in income expectations (eps)", 0.5, 0.1, 1.0),
                     ],
                     "Government Parameters": [
                         ("GRg", "Growth rate of government expenditures (GRg)", 0.03, -0.05, 0.1),
                         ("theta", "Income tax rate (theta)", 0.22844, 0.1, 0.4),
                     ],
                     "Bank/Monetary Parameters": [
                         ("Rbbar", "Interest rate on bills (Rbbar)", 0.035, 0.0, 0.1),
                         ("ADDbl", "Spread between bonds and bills rate (ADDbl)", 0.02, 0.0, 0.05),
                         ("NPLk", "Proportion of non-performing loans (NPLk)", 0.02, 0.0, 0.1),
                         ("NCAR", "Normal capital adequacy ratio (NCAR)", 0.1, 0.05, 0.2),
                         ("bot", "Bottom value for bank net liquidity ratio (bot)", 0.05, 0.0, 0.1),
                         ("top", "Top value for bank net liquidity ratio (top)", 0.12, 0.1, 0.2),
                         ("ro", "Reserve requirement parameter (ro)", 0.05, 0.01, 0.1),
                         ("Rln", "Normal interest rate on loans (Rln)", 0.07, 0.02, 0.15),
                     ],
                     "Labor Market Parameters": [
                         ("omega0", "Parameter affecting target real wage (omega0)", -0.20594, -0.5, 0.0),
                         ("omega1", "Parameter in wage equation (omega1)", 1.005, 0.9, 1.1), # Default updated
                         ("omega2", "Parameter in wage equation (omega2)", 2.0, 1.0, 3.0),
                         ("omega3", "Speed of wage adjustment (omega3)", 0.45621, 0.1, 0.9),
                         ("GRpr", "Growth rate of productivity (GRpr)", 0.03, 0.0, 0.1),
                         ("BANDt", "Upper band of flat Phillips curve (BANDt)", 0.07, 0.0, 0.1), # Default updated
                         ("BANDb", "Lower band of flat Phillips curve (BANDb)", 0.05, 0.0, 0.1), # Default updated
                         ("etan", "Speed of employment adjustment (etan)", 0.6, 0.1, 1.0),
                         ("Nfe", "Full employment level (Nfe)", 94.76, 80.0, 110.0),
                     ],
                     "Personal Loan Parameters": [
                         ("eta0", "Base ratio of new loans to personal income (eta0)", 0.07416, 0.0, 0.2),
                         ("etar", "Effect of real interest rate on loan ratio (etar)", 0.4, 0.0, 1.0),
                         ("deltarep", "Ratio of loan repayments to stock (deltarep)", 0.1, 0.05, 0.2),
                     ],
                     "Firm Parameters": [
                         ("beta", "Speed of adjustment in sales expectations (beta)", 0.5, 0.1, 1.0),
                         ("gamma", "Speed of inventory adjustment (gamma)", 0.15, 0.0, 0.5),
                         ("sigmat", "Target inventories to sales ratio (sigmat)", 0.2, 0.1, 0.3),
                         ("sigman", "Param. influencing historic unit costs (sigman)", 0.1666, 0.1, 0.3),
                         ("eps2", "Speed of markup adjustment (eps2)", 0.8, 0.1, 1.0),
                         ("psid", "Ratio of dividends to gross profits (psid)", 0.15255, 0.1, 0.3),
                         ("psiu", "Ratio of retained earnings to investments (psiu)", 0.92, 0.7, 1.0),
                         ("RA", "Random shock to expectations on real sales (RA)", 0.0, -0.05, 0.05),
                     ],
                     "Portfolio Parameters": [
                         ("lambda20", "Param in household demand for bills (lambda20)", 0.25, 0.1, 0.4),
                         ("lambda30", "Param in household demand for bonds (lambda30)", -0.04341, -0.1, 0.1),
                         ("lambda40", "Param in household demand for equities (lambda40)", 0.67132, 0.5, 0.9),
                         ("lambdab", "Parameter determining bank dividends (lambdab)", 0.0153, 0.01, 0.03),
                         ("lambdac", "Parameter in household demand for cash (lambdac)", 0.05, 0.01, 0.1),
                     ],
                 }

                 for category, params in parameter_categories.items():
                     st.markdown(f"**{category}**")
                     for param_key, param_name, default_val, min_val, max_val in params:
                         current_model_val = getattr(st.session_state.sfc_model_object, param_key, default_val)
                         slider_key = f"initial_slider_{param_key}"
                         # Calculate step size dynamically based on range
                         range_val = float(max_val) - float(min_val)
                         if range_val <= 0.01: step_size = 0.0001
                         elif range_val <= 0.1: step_size = 0.001
                         elif range_val <= 1.0: step_size = 0.01
                         elif range_val <= 10.0: step_size = 0.1
                         else: step_size = 1.0 # Adjust if needed for very large ranges

                         # Determine format based on step size
                         if step_size < 0.001: format_spec = "%.4f"
                         elif step_size < 0.01: format_spec = "%.3f"
                         elif step_size < 0.1: format_spec = "%.2f"
                         else: format_spec = "%.1f"

                         if slider_key not in st.session_state.initial_params:
                             try: initial_float_val = float(current_model_val)
                             except: initial_float_val = float(default_val)
                             st.session_state.initial_params[slider_key] = initial_float_val
                         new_value = st.slider(
                             param_name, float(min_val), float(max_val),
                             st.session_state.initial_params[slider_key],
                             step=step_size, format=format_spec, key=slider_key
                         )
                         if not np.isclose(st.session_state.initial_params[slider_key], new_value):
                              st.session_state.initial_params[slider_key] = new_value
                              initial_params_changed = True
                         initial_params_to_set[param_key] = new_value

                 if initial_params_changed:
                     try:
                         st.session_state.sfc_model_object.set_values(initial_params_to_set)
                         st.session_state.initial_state_dict.update(initial_params_to_set)
                         st.success("Initial parameters updated in model state.")
                     except Exception as e:
                         st.error(f"Error applying initial parameters: {e}")

        if st.button("Start Game"): # Changed button text
            st.session_state.game_phase = "SIMULATION" # Skip POLICY for Year 0->1
            st.session_state.initial_params_set = True # Lock initial params
            if "year_start_processed" in st.session_state: del st.session_state.year_start_processed # Clean up flag
            st.rerun()

    # --- Year > 0: Combined Dashboard & Policy ---
    else:
        # Removed instructional text

        # --- Draw Cards and Check Events (Run only once per YEAR_START phase) ---
        if "year_start_processed" not in st.session_state or st.session_state.year_start_processed != st.session_state.current_year:
            # Draw cards
            st.session_state.deck, st.session_state.player_hand = draw_cards(
                st.session_state.deck, st.session_state.player_hand, CARDS_TO_DRAW_PER_YEAR
            )
            st.toast(f"Drew {CARDS_TO_DRAW_PER_YEAR} cards.")

            # Check for events based on the *previous* year's state
            if st.session_state.history:
                 previous_year_results = st.session_state.history[-1] # Use last year's results
            else:
                 # Should not happen in Year > 0 if logic is correct
                 logging.error("History is empty when checking events for Year > 0.")
                 previous_year_results = st.session_state.initial_state_dict # Fallback

            if previous_year_results:
                st.session_state.active_events_this_year = check_for_events(previous_year_results)
                if st.session_state.active_events_this_year:
                     st.warning(f"New Events Occurred: {', '.join(st.session_state.active_events_this_year)}")
            else:
                 st.session_state.active_events_this_year = []

            st.session_state.year_start_processed = st.session_state.current_year
            st.session_state.cards_selected_this_year = []
            st.rerun()

        # --- Card Selection UI ---
        st.subheader("Select Policy Cards to Play")
        # Removed instructional text

        available_cards = st.session_state.player_hand
        selected_cards_this_turn = st.session_state.cards_selected_this_year

        if not available_cards:
            st.write("No cards in hand.")
        else:
            num_cards = len(available_cards)
            num_cols = min(num_cards, MAX_CARDS_PER_ROW)
            cols = st.columns(num_cols)

            for i, card_name in enumerate(available_cards):
                col_index = i % num_cols
                with cols[col_index]:
                    card_info = POLICY_CARDS.get(card_name, {})
                    is_selected = card_name in selected_cards_this_turn
                    card_type = card_info.get('type', 'Unknown').lower()
                    card_classes = f"card {card_type}"
                    if is_selected:
                        card_classes += " selected"
                    # Determine icon data uri based on type
                    icon_data_uri = get_icon_data_uri(card_type)
                    # Use <img> tag for PNG icons with base64 data
                    icon_html = f'<img src="{icon_data_uri}" class="card-icon" alt="{card_type} icon">' if icon_data_uri else "❓" # Fallback icon


                    # Modified Markdown for Monopoly Card Structure with Icon
                    st.markdown(f"""
                    <div class="{card_classes}">
                        <div class="card-top-bar">
                           {icon_html} <span class="card-title">{card_name} ({card_info.get('type', 'N/A')})</span>
                        </div>
                        <div class="card-content">
                            <div class="card-desc">{card_info.get('desc', 'No description available.')}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    # Render button separately below the card markdown
                    button_label = "Deselect" if is_selected else "Select"
                    button_type = "primary" if is_selected else "secondary"
                    button_key = f"select_{card_name}_{i}_{st.session_state.current_year}"
                    # Place button below the card div
                    if st.button(button_label, key=button_key, type=button_type, use_container_width=True):
                        if is_selected:
                            st.session_state.cards_selected_this_year.remove(card_name)
                        else:
                            st.session_state.cards_selected_this_year.append(card_name)
                        st.rerun()
        st.divider()
        if selected_cards_this_turn:
            st.write("Selected for this turn:")
            for card_name in selected_cards_this_turn: st.markdown(f"- {card_name}")
        else:
            st.write("No cards selected for this turn.")
        # --- End of Card Selection UI ---

        # --- Detailed Data Expanders ---
        st.divider()
        with st.expander("View Detailed Financial Statements"):
            model_state = st.session_state.sfc_model_object # Get current model state
            current_solution_for_matrix = model_state.solutions[-1] # Latest solution
            prev_solution_for_matrix = None
            if st.session_state.current_year == 1:
                 if len(model_state.solutions) >= 1:
                     prev_solution_for_matrix = model_state.solutions[0] # Use SOLVED t=0 state
                 else: logging.error("Cannot find t=0 solution in model_state for Year 1 matrix display.")
            elif len(model_state.solutions) >= 2:
                 prev_solution_for_matrix = model_state.solutions[-2]

            display_balance_sheet_matrix(current_solution_for_matrix)
            st.divider()
            if prev_solution_for_matrix: display_revaluation_matrix(current_solution_for_matrix, prev_solution_for_matrix); st.divider()
            else: st.caption("Revaluation matrix requires data from the previous period.")
            if prev_solution_for_matrix: display_transaction_flow_matrix(current_solution_for_matrix, prev_solution_for_matrix)
            else: st.caption("Transaction flow matrix requires data from the previous period.")

        with st.expander("View History Table"):
            if st.session_state.history:
                history_df = pd.DataFrame(st.session_state.history).sort_values(by='year', ascending=False)
                st.dataframe(history_df)
            else: st.write("No history recorded yet.")

        with st.expander("View Historical Trends"):
            if len(st.session_state.history) > 0: # Need at least Year 1 results
                history_df = pd.DataFrame(st.session_state.history).set_index('year')
                chart_data = pd.DataFrame({
                    'Real GDP (Yk)': history_df['Yk'],
                    'Inflation (PI %)': history_df['PI'] * 100,
                    'Unemployment Rate (%)': (1 - history_df['ER']) * 100
                })
                st.line_chart(chart_data)
            else: st.caption("Need at least one year of history to display trends.")
        # --- End Detailed Data Expanders ---


        # Button to proceed (for Year > 0)
        if st.button("Confirm Policies & Run Simulation"):
            st.session_state.game_phase = "SIMULATION"
            if "year_start_processed" in st.session_state: del st.session_state.year_start_processed
            st.rerun()

# Removed POLICY phase block

elif st.session_state.game_phase == "SIMULATION":
    # Note: current_year is the year *starting* the simulation (0 for first run, 1 for second, etc.)
    logging.info(f"Entering SIMULATION phase for year {st.session_state.current_year + 1}")
    # Removed instructional text

    # --- Get Previous State and Inputs ---
    prev_model = st.session_state.sfc_model_object
    cards_to_play = st.session_state.cards_selected_this_year
    events_active = st.session_state.active_events_this_year

    # Get the state dictionary from the end of the previous turn for apply_effects context
    if st.session_state.current_year == 0: # First simulation uses initial dict
         latest_solution_values = st.session_state.initial_state_dict
         logging.warning("Using initial state dict as previous state for Year 1 apply_effects.")
    elif not prev_model.solutions:
         # Should not happen after year 0
         logging.error("Previous model solutions missing unexpectedly.")
         latest_solution_values = st.session_state.initial_state_dict # Fallback
    else:
        latest_solution_values = prev_model.solutions[-1] # Get state from end of previous year

    # --- Calculate and Apply Parameters ---
    base_numerical_params = copy.deepcopy(growth_parameters)
    temp_model_for_param_check = create_growth_model()
    defined_param_names = set(temp_model_for_param_check.parameters.keys())
    for key, value in growth_exogenous:
        if key in defined_param_names:
             try: base_numerical_params[key] = float(value)
             except: logging.warning(f"Could not convert exogenous parameter {key}={value} to float.")
    logging.debug("Base numerical parameters constructed.")

    final_numerical_params = {}
    try:
        final_numerical_params = apply_effects(
            base_params=base_numerical_params,
            latest_solution=latest_solution_values,
            cards_played=cards_to_play,
            active_events=events_active
        )
        logging.debug("Final numerical parameters calculated.")
    except Exception as e:
        st.error(f"Error during apply_effects: {e}")
        logging.exception("Error calling apply_effects:")
        st.stop()

    # --- Initialize Fresh Model, Set State, and Run Simulation ---
    model_to_simulate = create_growth_model()
    old_stdout = sys.stdout
    try: # Correctly indented try block
        # 1. Set defaults
        model_to_simulate.set_values(growth_parameters)
        model_to_simulate.set_values(growth_exogenous)
        model_to_simulate.set_values(growth_variables)
        logging.debug("Set default params/vars on fresh model instance.")

        # 2. Set final parameters
        model_to_simulate.set_values(final_numerical_params)
        logging.debug("Set final numerical parameters on fresh model instance.")

        # 3. Copy History & Set Current Solution (Only if not first simulation)
        if st.session_state.current_year > 0:
            if not prev_model.solutions:
                 logging.error("Previous model solutions missing unexpectedly after Year 0.")
                 # Handle error? Stop?
            else:
                 model_to_simulate.solutions = copy.deepcopy(prev_model.solutions)
                 logging.debug("Copied solutions history from previous model.")
                 model_to_simulate.current_solution = model_to_simulate.solutions[-1]
                 logging.debug("Set current_solution for the fresh model instance.")
        else:
             logging.warning("Year 1 simulation: Skipping history copy, letting solve() initialize.")


        # --- Run the simulation for one year ---
        with st.spinner(f"Simulating Year {st.session_state.current_year + 1}..."):
            sys.stdout = NullIO()
            logging.debug(f"Attempting model.solve() for year {st.session_state.current_year + 1}...")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            logging.debug(f"model.solve() completed for year {st.session_state.current_year + 1}.")
            sys.stdout = old_stdout

            # --- Post-Solve Logging & State Update ---
            latest_sim_solution = model_to_simulate.solutions[-1]
            logging.debug(f"--- Year {st.session_state.current_year + 1} POST-SOLVE (Full State) ---")
            for key in sorted(latest_sim_solution.keys()):
                 if not key.startswith('_'): logging.debug(f"  {key}: {latest_sim_solution[key]}")

            # Specific check for Rm and CAR
            rm_check = latest_sim_solution.get('Rm', 'Not Found')
            car_check = latest_sim_solution.get('CAR', 'Not Found')
            logging.debug(f"CHECK - Rm: {rm_check}, Type: {type(rm_check)}")
            logging.debug(f"CHECK - CAR: {car_check}, Type: {type(car_check)}")

            # Store the NEWLY SOLVED model object for the next turn
            st.session_state.sfc_model_object = model_to_simulate

            # Record History
            current_results = { 'year': st.session_state.current_year + 1 }
            for key in ['Yk', 'PI', 'ER', 'GRk', 'Rb', 'Rl', 'BUR', 'Q', 'PSBR', 'GD', 'Y']:
                 current_results[key] = latest_sim_solution.get(key, np.nan)
            current_results['cards_played'] = list(cards_to_play)
            current_results['events'] = list(events_active)
            st.session_state.history.append(current_results)

            # Update Hand (Only if not first simulation)
            if st.session_state.current_year > 0:
                current_hand = st.session_state.player_hand
                new_hand = [card for card in current_hand if card not in cards_to_play]
                st.session_state.player_hand = new_hand

            # Clear turn-specific state
            st.session_state.cards_selected_this_year = []
            st.session_state.active_events_this_year = []

            # --- Auto-advance to next YEAR_START ---
            st.session_state.current_year += 1
            st.session_state.game_phase = "YEAR_START"
            logging.info(f"Simulation complete. Advancing to Year {st.session_state.current_year} YEAR_START.")


    except SolutionNotFoundError as e: # Correctly indented except
        sys.stdout = old_stdout
        st.error(f"Model failed to converge for Year {st.session_state.current_year + 1}. Error: {str(e)}")
        st.session_state.game_phase = "SIMULATION_ERROR"
    except Exception as e: # Correctly indented except
        sys.stdout = old_stdout
        st.error(f"An unexpected error occurred during simulation: {str(e)}")
        logging.exception(f"Unexpected error in SIMULATION phase:")
        st.session_state.game_phase = "SIMULATION_ERROR" # Or other error state
    finally: # Correctly indented finally
        sys.stdout = old_stdout
        # No longer log phase here as it's set above before rerun
        # logging.info(f"SIMULATION phase end: Current game phase before rerun is '{st.session_state.game_phase}'")
        st.rerun() # Rerun to display the next YEAR_START

# Removed RESULTS phase block

elif st.session_state.game_phase == "SIMULATION_ERROR":
    # Correct year display for error message
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    if st.button("Acknowledge Error (Stops Game)"): st.stop()

else:
    st.error(f"Unknown game phase: {st.session_state.game_phase}")

# --- Debug Info (Optional) ---
# with st.expander("Debug Info"): st.write("Session State:", st.session_state)
