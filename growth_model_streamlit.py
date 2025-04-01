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
import altair as alt # Keep altair import for potential future use if needed

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
CARDS_TO_DRAW_PER_YEAR = 4 # Draw 4 cards per year as requested
MAX_CARDS_PER_ROW = 4 # For card display layout
ICON_DIR = "assets/icons" # Define icon directory
SPARKLINE_YEARS = 10 # Number of years for sparkline history

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

# --- Variable Descriptions (Keep for potential future use) ---
VARIABLE_DESCRIPTIONS = {
    "Yk": "Real Gross Domestic Product: Total value of goods and services produced, adjusted for inflation.",
    "PI": "Inflation Rate: Percentage increase in the general price level.",
    "Unemployment": "Unemployment Rate: Percentage of the labor force that is jobless and looking for work.",
    "GRk": "Capital Growth Rate: Percentage change in the stock of physical capital.",
    "Rb": "Bill Rate: Interest rate on short-term government debt (Treasury Bills).",
    "Rl": "Loan Rate: Interest rate charged by banks on loans to firms and households.",
    "Rm": "Deposit Rate: Interest rate paid by banks on deposits.",
    "Q": "Tobin's Q: Ratio of the market value of firms' capital to its replacement cost.",
    "K": "Capital Stock: The total value of physical capital (machinery, buildings, etc.) used in production.",
    "INV": "Investment: Spending by firms on new capital goods.",
    "CONS": "Consumption: Spending by households on goods and services.",
    "BUR": "Debt Burden Ratio: Ratio of household debt service payments to disposable income.",
    "W": "Wage Rate: The nominal wage paid to labor.",
    "CAR": "Capital Adequacy Ratio: Ratio of a bank's capital to its risk-weighted assets.",
    "Lhs": "Loans to Households: Outstanding loan balances held by the household sector.",
    "PSBR": "Public Sector Borrowing Requirement: The government's budget deficit.",
    "GD_GDP": "Government Debt to GDP Ratio: Ratio of total government debt to nominal GDP."
}


# Helper dict for parameter descriptions (extracted from chapter_11_model_growth.py)
PARAM_DESCRIPTIONS = {
    'Rbbar': 'Interest rate on bills, set exogenously',
    'RA': 'Random shock to expectations on real sales',
    'ADDbl': 'Spread between long-term interest rate and rate on bills',
    'ro': 'Reserve requirement parameter',
    'NCAR': 'Normal capital adequacy ratio of banks',
    'GRg': 'Growth rate of real government expenditures',
    'theta': 'Income tax rate',
    'GRpr': 'Growth rate of productivity',
    'NPLk': 'Proportion of Non-Performing loans',
    'etan': 'Speed of adjustment of actual employment to desired employment',
    'alpha1': 'Propensity to consume out of income',
    'gamma0': 'Exogenous growth in the real stock of capital',
    'Rln': 'Normal interest rate on loans',
    'eta0': 'Ratio of new loans to personal income - exogenous component',
    'delta': 'Rate of depreciation of fixed capital',
    'beta': 'Parameter in expectation formations on real sales',
    'omega3': 'Speed of adjustment of wages to target value'
    # Add others if needed by cards/events
}


# --- Helper Functions ---
class NullIO(io.StringIO):
    def write(self, txt):
        pass

def format_percent(value):
    """Formats a float as a percentage string."""
    if not np.isfinite(value):
        return "N/A"
    return f"{value*100:.2f}%"

def format_effect(param, effect):
    """Formats the effect value nicely based on typical parameter scales."""
    if not isinstance(effect, (int, float)) or not np.isfinite(effect):
        return "N/A"
    # Rates, Ratios, Proportions shown as percentage points (p.p.)
    if param in ['Rbbar', 'ADDbl', 'ro', 'NCAR', 'theta', 'NPLk', 'alpha1', 'delta', 'eta0', 'Rln', 'GRg', 'GRpr', 'gamma0']:
        return f"{effect*100:+.1f} p.p."
    # Speed of adjustment / Expectation parameters (unitless or specific scale)
    elif param in ['etan', 'beta', 'omega3']:
         return f"{effect:+.3f}" # Show more precision
    # Other shocks (like RA) might be direct adjustments
    else:
        # Default absolute change format
        return f"{effect:+.3f}"

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

    base64_string = get_base64_of_bin_file(logo_path)
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
    /* Style the container holding the card elements */
    .card-container {
        border: 1px solid #000000;
        border-radius: 8px;
        margin-bottom: 15px;
        background-color: #FAFAD2; /* Parchment background */
        height: 250px; /* Fixed height for cards */
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
    .card-top-bar.fiscal { background-color: #1FB25A; } /* Monopoly Green */
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
    /* Container for the main content below the top bar */
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
    /* Ensure expander takes minimal space */
    .card-main-content .stExpander {
        padding: 0 !important;
        margin-top: auto; /* Push expander towards bottom before button */
        margin-bottom: 5px; /* Space before button */
    }
     .card-main-content .stExpander p { /* Style caption inside expander */
        font-size: 0.8em;
        color: #555555;
    }
    /* --- Stance Bar --- */
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
    .expansionary-bar {
        background-color: #4CAF50; /* Green */
    }
    .contractionary-bar {
        background-color: #f44336; /* Red */
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
                # Attempt to set any exogenous value, converting to float if possible
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
        # Base Yk will be set after the first simulation (Year 1)
        st.session_state.base_yk = None
        logging.info("Stored initial model object (unsolved) and initial state dict in session state.")

    except Exception as e:
        st.error(f"Fatal Error: An unexpected error occurred during model initialization: {e}")
        logging.exception("Unexpected error during model initialization.")
        st.stop()
    # --- End of Model Initialization ---

    # --- Game Variables Initialization ---
    st.session_state.deck = create_deck()
 # Still create the deck
    st.session_state.player_hand = [] # Initialize empty hand
    logging.info("Initialized deck (no initial hand draw).")
    st.session_state.active_events_this_year = []
    st.session_state.cards_selected_this_year = []
    st.session_state.history = [] # Initialize history as empty
    st.session_state.initial_params = {} # For year 0 adjustments

    logging.info("Game Initialized at Year 0.")
    st.rerun() # Rerun to start the flow


# --- Sidebar ---
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
    # --- Helper function to create sparkline data ---
    def get_sparkline_data(metric_key, num_years):
        if not hasattr(st.session_state, 'sfc_model_object') or not st.session_state.sfc_model_object.solutions:
            return None
        solutions = st.session_state.sfc_model_object.solutions
        # Allow processing even if only one solution exists (for single point display)
        if not solutions: # Check if solutions list is empty
            return None

        start_index = max(0, len(solutions) - num_years)
        history_slice = solutions[start_index:]

        # Extract data, handling potential missing keys or non-numeric values gracefully
        data = []
        years = []
        # Assuming solutions[0] corresponds to year 0, solutions[1] to year 1 etc.
        start_actual_year = start_index # Adjust if year numbering is different

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
                if gd_val is not None and y_val is not None and np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(y_val, 0):
                    val = (gd_val / y_val) * 100 # Calculate ratio and scale to percentage
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
            # Removed Yk_Index logging from here as calculation is post-loop

        if len(data) < 2: # Still need at least 2 valid points overall
             return None

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

        # Explicitly drop rows where the metric value is NaN BEFORE setting index
        # This ensures Altair receives only valid points for the y-axis
        # Important: Do this *after* potential post-loop calculations
        df.dropna(subset=[metric_key], inplace=True)

        # Check again if enough points remain after dropping NaNs
        # Allow returning a DataFrame with a single point
        if df.empty:
            logging.debug(f"SPARKLINE {metric_key} - Not enough valid points after dropna.")
            return None

        # Set index after cleaning
        df.set_index('Year', inplace=True)
        return df

    # --- Function to create Vega-Lite spec for sidebar (minimalist) ---
    def create_sparkline_spec(data_df, metric_key):
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
                "y": {"field": metric_key, "type": "quantitative", "axis": None}, # Hide Y axis
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
    def display_metric_sparkline(metric_key, label, icon_key, format_func, delta_val):
        spark_df = get_sparkline_data(metric_key, SPARKLINE_YEARS)
        current_val = latest_history_entry.get(metric_key, np.nan)
        # Special handling for unemployment
        if metric_key == 'Unemployment':
            er_val = latest_history_entry.get('ER', np.nan)
            current_val = max(0.005, (1 - er_val)) if np.isfinite(er_val) else np.nan
            icon_key = "ER" # Use ER icon
        # Special handling for Real GDP Index
        elif metric_key == 'Yk_Index':
            yk_val = latest_history_entry.get('Yk', np.nan)
            base_yk = st.session_state.get('base_yk')
 # Base Yk is now from Year 1 results
            if is_first_result_year and np.isfinite(yk_val): # Year 1 result
                current_val = 100.0 # Define Year 1 index as 100
            elif base_yk and np.isfinite(yk_val) and not np.isclose(base_yk, 0):
 # Subsequent years
                current_val = (yk_val / base_yk) * 100
 # Calculate index relative to Year 1
            else:
                current_val = np.nan # Cannot calculate index
            icon_key = "Yk" # Use Yk icon
            format_func = lambda x: f"{x:.1f}" if np.isfinite(x) else "N/A" # Custom format for index
        # Special handling for Gov Debt / GDP Ratio
        elif metric_key == 'GD_GDP':
            gd_val = latest_history_entry.get('GD', np.nan)
            y_val = latest_history_entry.get('Y', np.nan)
            if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(y_val, 0):
                current_val = gd_val / y_val # Calculate the ratio
            else:
                current_val = np.nan # Cannot calculate ratio
            icon_key = "GD_GDP" # Use correct icon key
            format_func = format_percent # Use percentage format

        icon_data_uri = get_icon_data_uri(icon_key)
        cols = st.sidebar.columns([1, 5, 2])
 # Give value column even more relative width
 # Give value column more relative width
        with cols[0]:
            if icon_data_uri: st.markdown(f'<img src="{icon_data_uri}" class="metric-icon">', unsafe_allow_html=True)
        with cols[1]:
            if metric_key == 'GD_GDP': logging.debug(f"CHECK GD_GDP DISPLAY - current_val: {current_val}, type: {type(current_val)}")
            st.metric(label=label, value=format_func(current_val), delta=delta_val)
        with cols[2]:
            if spark_df is not None and not spark_df.empty: # Ensure data exists
                try:
                    spec = create_sparkline_spec(spark_df, metric_key)
                    if spec:
 # Check if spec was created successfully
                        # Pass spec directly to st.vega_lite_chart, explicitly setting theme
                        st.vega_lite_chart(spec, use_container_width=True, theme="streamlit")
                except Exception as e:
                    logging.error(f"Error creating st.vega_lite_chart for {metric_key}: {e}")


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

    # --- Display Core Metrics ---
    # Display Yk as an index
    yk_index_val = np.nan
    yk_index_prev = np.nan
    base_yk = st.session_state.get('base_yk')
    if base_yk and not np.isclose(base_yk, 0):
        if np.isfinite(yk_val): yk_index_val = (yk_val / base_yk) * 100
        if prev_year_data and np.isfinite(yk_prev): yk_index_prev = (yk_prev / base_yk) * 100
    # Calculate delta for the index (percentage point change from previous index value)
    # Calculate delta for the index (percentage change from previous index value)
    delta_yk_index = None if is_first_result_year else get_delta(yk_index_val, yk_index_prev)
    display_metric_sparkline("Yk_Index", "Real GDP Index (Y1=100)", "Yk", lambda x: f"{x:.1f}" if np.isfinite(x) else "N/A", delta_yk_index)

    display_metric_sparkline("PI", "Inflation (PI)", "PI", format_percent, delta_pi)
    display_metric_sparkline("Unemployment", "Unemployment Rate", "ER", format_percent, delta_unemp)
    display_metric_sparkline("GRk", "Capital Growth (GRk)", "GRk", format_percent, delta_grk)


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

    # --- Display Financial Metrics ---
    display_metric_sparkline("Rb", "Bill Rate (Rb)", "Rb", format_percent, delta_rb)
    display_metric_sparkline("Rl", "Loan Rate (Rl)", "Rl", format_percent, delta_rl)
    display_metric_sparkline("Rm", "Deposit Rate (Rm)", "Rm", format_percent, delta_rm)
    display_metric_sparkline("Q", "Tobin's Q", "Q", format_value, delta_q)
    display_metric_sparkline("BUR", "Debt Burden (BUR)", "BUR", format_percent, delta_bur)
    display_metric_sparkline("CAR", "Capital Adequacy (CAR)", "CAR", format_percent, delta_car)


    psbr_val = latest_history_entry.get('PSBR', np.nan)
    gd_val = latest_history_entry.get('GD', np.nan)
    y_val = latest_history_entry.get('Y', np.nan)
    psbr_prev = prev_year_data.get('PSBR') if prev_year_data else np.nan
    y_prev = prev_year_data.get('Y') if prev_year_data else np.nan
    delta_psbr = None if is_first_result_year else get_delta(psbr_val, psbr_prev)

    # Calculate Gov Debt / GDP Ratio, handle potential division by zero or NaN
    gd_gdp_val = np.nan
    if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(y_val, 0):
        gd_gdp_val = gd_val / y_val
    else:
        logging.warning(f"Cannot calculate GD/GDP for year {st.session_state.current_year}. GD={gd_val}, Y={y_val}")

    gd_gdp_prev = np.nan
    if prev_year_data:
        gd_prev = prev_year_data.get('GD', np.nan) # Corrected syntax
        if np.isfinite(gd_prev) and np.isfinite(y_prev) and not np.isclose(y_prev, 0):
            gd_gdp_prev = gd_prev / y_prev
        else:
             logging.warning(f"Cannot calculate previous GD/GDP. GD_prev={gd_prev}, Y_prev={y_prev}")

    delta_gd_gdp = None if is_first_result_year else get_delta_percent(gd_gdp_val, gd_gdp_prev)

    # --- Display Government Metrics ---
    display_metric_sparkline("PSBR", "Gov Deficit (PSBR)", "PSBR", format_value, delta_psbr)
    display_metric_sparkline("GD_GDP", "Gov Debt / GDP", "GD_GDP", format_percent, delta_gd_gdp)

# --- End of Dashboard Display ---

# --- Sector Summary Display ---
def display_sector_summary(latest_solution):
    """Displays key summary data for each economic sector in the sidebar."""
    st.sidebar.markdown("---") # Add a divider
    st.sidebar.markdown("##### Sector Summaries")

    # Households
    with st.sidebar.expander("Households", expanded=False):
        hh_v = latest_solution.get('V', np.nan)
        hh_ydr = latest_solution.get('YDr', np.nan)
        hh_c = latest_solution.get('CONS', np.nan) # Changed key from C to CONS
        st.metric(label="Wealth (V)", value=format_value(hh_v))
        st.metric(label="Disposable Income (YDr)", value=format_value(hh_ydr))
        st.metric(label="Consumption (C)", value=format_value(hh_c))

    # Firms
    with st.sidebar.expander("Firms", expanded=False):
        f_k = latest_solution.get('K', np.nan)
        f_i = latest_solution.get('INV', np.nan) # Changed key from I to INV
        f_fu = latest_solution.get('FUf', np.nan) # Corrected key for Firm Retained Earnings
        st.metric(label="Capital Stock (K)", value=format_value(f_k))
        st.metric(label="Investment (I)", value=format_value(f_i))
        st.metric(label="Retained Earnings (FUf)", value=format_value(f_fu))

    # Government
    with st.sidebar.expander("Government", expanded=False):
        g_gd = latest_solution.get('GD', np.nan) # Total Gov Debt
        g_psbr = latest_solution.get('PSBR', np.nan)
        g_t = latest_solution.get('T', np.nan) # Total Taxes
        g_g = latest_solution.get('G', np.nan) # Gov Spending
        st.metric(label="Total Debt (GD)", value=format_value(g_gd))
        st.metric(label="Deficit (PSBR)", value=format_value(g_psbr))
        st.metric(label="Taxes (T)", value=format_value(g_t))
        st.metric(label="Spending (G)", value=format_value(g_g))

    # Banks
    with st.sidebar.expander("Banks", expanded=False):
        b_lfs = latest_solution.get('Lfs', np.nan) # Loans to Firms
        b_lhs = latest_solution.get('Lhs', np.nan) # Loans to Households
        b_m = latest_solution.get('Ms', np.nan) # Deposits (Supply)
        b_ofb = latest_solution.get('OFb', np.nan) # Own Funds (Equity)
        b_car = latest_solution.get('CAR', np.nan) # Capital Adequacy Ratio
        st.metric(label="Loans to Firms (Lfs)", value=format_value(b_lfs))
        st.metric(label="Loans to Households (Lhs)", value=format_value(b_lhs))
        st.metric(label="Deposits (Ms)", value=format_value(b_m))
        st.metric(label="Own Funds (OFb)", value=format_value(b_ofb))
        st.metric(label="Capital Adequacy (CAR)", value=format_percent(b_car))

    # Central Bank
    with st.sidebar.expander("Central Bank", expanded=False): # Corrected indentation
        cb_bcb = latest_solution.get('Bcbd', np.nan) # Changed key from Bcb to Bcbd
        # cb_as = latest_solution.get('As', np.nan) # Removed - 'As' not found in model vars
        st.metric(label="Bills Held (Bcb)", value=format_value(cb_bcb))
        # st.metric(label="Advances to Banks (As)", value=format_value(cb_as)) # Removed

# Call the sector summary function if results are available
if st.session_state.current_year > 0 and st.session_state.history:
    # Ensure latest_history_entry is defined from the metric display block
    if 'latest_history_entry' in locals():
         display_sector_summary(latest_history_entry)
    else:
         # Fallback or error handling if latest_history_entry isn't available
         # This might happen if the metric display logic fails or is skipped
         logging.warning("latest_history_entry not available for sector summary display.")
         # Optionally try to get it again, though this duplicates logic:
         model_state = st.session_state.get('sfc_model_object')
         if model_state and model_state.solutions:
             display_sector_summary(model_state.solutions[-1])



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

             # Display Start Game button first
             if st.button("Start Game"): # Changed button text
                 st.session_state.game_phase = "SIMULATION" # Skip POLICY for Year 0->1
                 st.session_state.initial_params_set = True # Lock initial params
                 if "year_start_processed" in st.session_state: del st.session_state.year_start_processed # Clean up flag
                 st.rerun()

             # Then display the less prominent advanced options
             with st.expander("Advanced: Set Initial Economic Conditions", expanded=False): # Set expanded=False
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
                        # Read from the state dict where initial values are stored, not getattr
                         current_model_val = st.session_state.initial_state_dict.get(param_key, default_val)
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
                             # Store the slider's current value in the temporary dict
                             st.session_state.initial_params[slider_key] = new_value
                             # Directly check if this new value differs from the main state dict
                             if not np.isclose(st.session_state.initial_state_dict.get(param_key, default_val), new_value):
                                 initial_params_changed = True # Mark that *some* change occurred this cycle
                         initial_params_to_set[param_key] = new_value

                 # Always update the model and state dict with the latest slider values from this render
                 if initial_params_to_set: # Ensure there are values to set
                     try:
                         st.session_state.sfc_model_object.set_values(initial_params_to_set)
                         st.session_state.initial_state_dict.update(initial_params_to_set)
                         if initial_params_changed: # Show success only if a value actually changed this cycle
                             st.success("Initial parameters updated.")
                     except Exception as e:
                         st.error(f"Error applying initial parameters: {e}")

    # --- Year > 0: Combined Dashboard & Policy ---
    else:
        # --- Display Year Start Info (Events & KPI Plots) ---
        st.markdown("---") # Divider
        info_cols = st.columns([1, 1, 1, 1]) # Create columns for layout
        with info_cols[0]:
            st.markdown("##### Active Events")
            if st.session_state.active_events_this_year:
                for event_name in st.session_state.active_events_this_year:
                    event_data = ECONOMIC_EVENTS.get(event_name, {})
                    event_desc = event_data.get('desc', 'No description available.')
                    affected_vars = event_data.get('affected_vars', [])
                    # Build detailed affected variables string with descriptions
                    affected_vars_details = ""
                    if affected_vars:
                        details_list = []
                        for var in affected_vars:
                            # Handle special case for Unemployment derived from ER
                            if var == "ER" and "Unemployment" in VARIABLE_DESCRIPTIONS:
                                var_display_name = "Unemployment"
                                var_desc = VARIABLE_DESCRIPTIONS["Unemployment"]
                            else:
                                var_display_name = var
                                var_desc = VARIABLE_DESCRIPTIONS.get(var, "No description available.")
                            details_list.append(f"- **{var_display_name}:** _{var_desc}_")
                        if details_list:
                            affected_vars_details = "\n**Affected Variables:**\n" + "\n".join(details_list)

                    # Display event name, description, and detailed affected variables
                    st.info(f"**{event_name}:** {event_desc}{affected_vars_details}")
            else:
                st.caption("None")

        # Helper to create simple KPI plots
        def create_kpi_plot(metric_key, title):
            plot_df = get_sparkline_data(metric_key, SPARKLINE_YEARS) # Reuse sparkline data getter
            if plot_df is not None and not plot_df.empty:
                # Check if data exists
                # Define colors based on metric_key (using theme/standard colors)
                plot_color = "#1FB25A" # Default: Green (e.g., for GDP)
                y_axis_format = ".1f" # Default format
                if metric_key == 'PI':
                    plot_color = "#FF8C00" # Orange for Inflation
                    y_axis_format = ".1%" # Percentage format
                elif metric_key == 'Unemployment':
                    plot_color = "#0072BB" # Blue for Unemployment
                    y_axis_format = ".1%" # Percentage format

                # Base chart
                base = alt.Chart(plot_df.reset_index()).encode(
                    x=alt.X('Year:O', axis=alt.Axis(title='Year', labelAngle=-45, grid=False)), # Keep X grid off
                    tooltip=[
                        alt.Tooltip('Year:O', title='Simulation Year'),
                        alt.Tooltip(f'{metric_key}:Q', format=y_axis_format, title=title) # Use dynamic format and title
                    ]
                )

                # Handle single data point case (e.g., first year)
                if len(plot_df) == 1:
                    # Define Y-axis scale for single point
                    single_value = plot_df[metric_key].iloc[0]
                    # Calculate a small domain around the single value, handle zero case
                    if np.isclose(single_value, 0):
                        domain_padding = 1.0 # Example padding for zero
                    else:
                        domain_padding = abs(single_value) * 0.2 # 20% padding
                    y_domain_single = [single_value - domain_padding, single_value + domain_padding]

                    # Override domain for specific metrics if needed (e.g., ensure 0 is included)
                    if metric_key == 'Unemployment':
                        y_domain_single = [max(0, y_domain_single[0]), max(1, y_domain_single[1])] # Ensure >= 0
                    elif metric_key == 'PI':
                        pass # Allow negative inflation

                    y_axis_scale_single = alt.Scale(domain=y_domain_single, zero=(metric_key != 'Yk_Index'))

                    # Create a chart with just a point
                    chart = base.mark_point(
                        size=100, # Make point visible
                        filled=True,
                        color=plot_color
                    ).encode(
                         y=alt.Y(f'{metric_key}:Q',
                                 axis=alt.Axis(title=title, format=y_axis_format, grid=True, titlePadding=10),
                                 scale=y_axis_scale_single # Apply specific scale
                                )
                    ).properties(
                         title=alt.TitleParams(text=title, anchor='start', fontSize=14),
                         height=150
                    ).configure_view(
                        fill=None, stroke='lightgray' # Transparent background, subtle border
                    ).interactive()
                else:
                    # Existing logic for line chart (now indented)
                    # Define Y-axis scale for line chart
                    min_val = plot_df[metric_key].min()
                    max_val = plot_df[metric_key].max()
                    data_range = max_val - min_val
                    if np.isclose(data_range, 0):
                         # Handle case where all values are the same
                         if np.isclose(min_val, 0): padding = 1.0
                         else: padding = abs(min_val) * 0.1
                    else:
                         padding = data_range * 0.1 # 10% padding

                    y_domain_line = [min_val - padding, max_val + padding]

                     # Override domain for specific metrics if needed
                    if metric_key == 'Unemployment':
                        y_domain_line = [max(0, y_domain_line[0]), max(1, y_domain_line[1])] # Ensure >= 0
                    elif metric_key == 'PI':
                        pass # Allow negative inflation

                    y_axis_scale_line = alt.Scale(domain=y_domain_line, zero=(metric_key != 'Yk_Index'))

                    line = base.mark_line(
                        point=alt.OverlayMarkDef(color=plot_color), # Style points to match line
                        color=plot_color, # Use defined color
                        strokeWidth=2 # Slightly thicker line
                    ).encode(
                        y=alt.Y(f'{metric_key}:Q',
                                axis=alt.Axis(
                                    title=title, # Use full title passed to function
                                    format=y_axis_format, # Use dynamic format
                                    grid=True, # Add Y-axis gridlines
                                    titlePadding=10 # Add padding to title
                                ),
                                scale=y_axis_scale_line # Apply specific scale
                        )
                    )

                    # Add text label for the last point
                    last_point_df = plot_df.reset_index().iloc[[-1]]
                    labels = alt.Chart(last_point_df).mark_text(
                        align='left',
                        baseline='middle',
                        dx=7, # Offset text to the right of the point
                        fontSize=11
                    ).encode(
                        x=alt.X('Year:O'),
                        y=alt.Y(f'{metric_key}:Q'),
                        text=alt.Text(f'{metric_key}:Q', format=y_axis_format),
                        color=alt.value(plot_color) # Match label color to line
                    )

                    # Add zero reference line for specific metrics
                    if metric_key in ['PI', 'Unemployment']:
                        zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                            color='grey', strokeDash=[2,2], size=1
                        ).encode(y='y')
                        chart_layers = [line, labels, zero_line]
                    else:
                        chart_layers = [line, labels]

                    # Configure overall chart properties
                    # Layer the components
                    chart = alt.layer(*chart_layers).properties(
                        # Use alt.TitleParams for more control over title appearance
                        title=alt.TitleParams(
                            text=title,
                            anchor='start', # Align title left
                            fontSize=14,
                            subtitleFontSize=12
                        ),
                        height=150 # Make slightly taller
                    ).configure_view(
                        fill=None, stroke='lightgray' # Transparent background, subtle border
                    ).interactive() # Allow zooming/panning

                return chart # Return the styled line or point chart
            return None # Return None if plot_df is None or empty

        with info_cols[1]:
            st.altair_chart(create_kpi_plot('Yk', 'Real GDP Trend'), use_container_width=True)
        with info_cols[2]:
            st.altair_chart(create_kpi_plot('PI', 'Inflation Trend'), use_container_width=True)
        with info_cols[3]:
            st.altair_chart(create_kpi_plot('Unemployment', 'Unemployment Trend'), use_container_width=True)
        st.markdown("---") # Divider

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
        max_cards_allowed = 2 # Define max cards here for use in selection logic

        if not available_cards:
            st.write("No policy cards currently in hand.")
        else:
            # Filter cards to only show Fiscal and Monetary
            # Show only UNIQUE card names for selection
            unique_card_names = sorted(list(set(
                card_name for card_name in available_cards
                if POLICY_CARDS.get(card_name, {}).get('type') in ["Fiscal", "Monetary"]
            )))

            if not unique_card_names:
                st.write("No Fiscal or Monetary policy cards currently in hand.")
                # Exit this block if no displayable cards
                # Note: This assumes the 'else' block below handles the case where displayable_cards is empty

            num_cards = len(unique_card_names)
            num_cols = min(num_cards, MAX_CARDS_PER_ROW)
            cols = st.columns(num_cols)

            card_render_index = 0 # Index for column assignment
            for card_name in unique_card_names: # Iterate over unique list
                col_index = card_render_index % num_cols # Use card_render_index instead of i
                with cols[col_index]:
                    card_info = POLICY_CARDS.get(card_name, {})
                    is_selected = card_name in selected_cards_this_turn
                    card_type = card_info.get('type', 'Unknown').lower()
                    param_name = card_info.get('param')
                    param_effect = card_info.get('effect')
                    param_desc = PARAM_DESCRIPTIONS.get(param_name, "N/A")
                    formatted_effect = format_effect(param_name, param_effect)

                    # Determine card container class based on selection
                    card_container_class = "card-container"
                    if is_selected:
                        card_container_class += " selected"

                    # --- Card Rendering using Streamlit Elements ---
                    with st.container():
                        # Apply card container styling via CSS class
                        # We need to manually construct the top bar HTML here
                        icon_data_uri = get_icon_data_uri(card_type)
                        icon_html = f'<img src="{icon_data_uri}" class="card-icon">' if icon_data_uri else "❓"
                        card_stance = card_info.get('stance', None)
                        # Removed old stance_icon_html logic

                        top_bar_color_class = f"{card_type}" if card_type in ["monetary", "fiscal"] else "default"
                        # Use st.markdown for the top bar structure
                        st.markdown(f'''
                        <div class="{card_container_class}"> <!-- Apply container class -->
                            <div class="card-top-bar {top_bar_color_class}">
                               {icon_html} <span class="card-title">{card_type.capitalize()}: {card_name}</span>
                            </div>
                            <div class="card-main-content">
                                <div class="card-desc">
                                    {card_info.get('desc', 'No description available.')}<br>
                                    <small><i>Effect: {formatted_effect} on {param_name} ({param_desc})</i></small>
                                </div>
                                <!-- Button will be placed below by Streamlit -->
                                {'<div class="card-stance-bar ' + card_stance + '-bar">' + card_stance.capitalize() + '</div>' if card_stance else ''}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

                        # Place Button *outside* markdown, but *inside* the column's context
                        # Use a container to help manage layout within the flex column
                        with st.container():
                            button_label = "Deselect" if is_selected else "Select"
                            button_type = "primary" if is_selected else "secondary"
                            button_key = f"select_{card_name}_{card_render_index}_{st.session_state.current_year}"
 # Use render index for unique key
                            if st.button(button_label, key=button_key, type=button_type, use_container_width=True):
                                if is_selected:
                                    st.session_state.cards_selected_this_year.remove(card_name)
                                    st.rerun() # Rerun after deselecting
                                else:
                                    # --- Add Duplicate Name Check ---
                                    # This check might be redundant now if only unique names are displayed, but keep for safety
                                    if card_name in st.session_state.cards_selected_this_year:
                                        st.warning(f"Cannot select two '{card_name}' cards in the same turn.")
                                    # --- Add Max Card Check before appending ---
                                    elif len(st.session_state.cards_selected_this_year) >= max_cards_allowed:
                                        st.warning(f"You can only select up to {max_cards_allowed} cards.")
                                    else:
                                        st.session_state.cards_selected_this_year.append(card_name)
                                        st.rerun() # Rerun only if selection was successful

                    card_render_index += 1 # Increment render index


        st.divider()
        if selected_cards_this_turn:
            st.write("Selected for this turn:")
            for card_name in selected_cards_this_turn: st.markdown(f"- {card_name}")
        else:
            st.write("No cards selected for this turn.")
        # --- End of Card Selection UI ---

        # --- Detailed Data Expanders ---
        st.divider()
 # Keep divider above expanders
        with st.expander("SFC Matrices"): # Renamed Expander
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
                # Define mapping for clearer column names
                column_mapping = {
                    'year': 'Year', # Keep simple
                    'Yk': 'Real GDP (Yk)',
                    'PI': 'Inflation (PI)',
                    'ER': 'Employment Rate (ER)',
                    'GRk': 'Capital Growth (GRk)',
                    'Rb': 'Bill Rate (Rb)',
                    'Rl': 'Loan Rate (Rl)',
                    'Rm': 'Deposit Rate (Rm)', # Added
                    'BUR': 'Debt Burden (BUR)',
                    'Q': "Tobin's Q (Q)",
                    'CAR': 'Capital Adequacy (CAR)', # Added
                    'PSBR': 'Gov Deficit (PSBR)',
                    'GD': 'Gov Debt Stock (GD)',
                    'Y': 'Nominal GDP (Y)',
                    'V': 'Household Wealth (V)', # Added
                    'Lhs': 'Household Loans (Lhs)', # Added
                    'Lfs': 'Firm Loans (Lfs)', # Added
                    'cards_played': 'Cards Played', # Keep simple
                    'events': 'Active Events' # Keep simple
                }
                history_df = pd.DataFrame(st.session_state.history).sort_values(by='year', ascending=False)
                # Select and rename columns that exist in the DataFrame
                display_df = history_df[[col for col in column_mapping if col in history_df.columns]].rename(columns=column_mapping)
                st.dataframe(display_df) # Display the renamed DataFrame
            else: st.write("No history recorded yet.")

        # --- End Detailed Data Expanders ---


        # Button to proceed (for Year > 0)
        # --- Add Card Limit Check ---
        max_cards_allowed = 2
        can_proceed = len(selected_cards_this_turn) <= max_cards_allowed
        if not can_proceed:
            st.warning(f"You can select a maximum of {max_cards_allowed} cards per turn.")

        if st.button("Confirm Policies & Run Simulation", disabled=not can_proceed):
            st.session_state.game_phase = "SIMULATION"
            if "year_start_processed" in st.session_state: del st.session_state.year_start_processed
            st.rerun()

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
    # Initialize base parameters correctly depending on the year
    if st.session_state.current_year == 0:
        # For Year 1 simulation, start from the potentially modified initial state dict
        base_numerical_params = {k: v for k, v in st.session_state.initial_state_dict.items() if isinstance(v, (int, float))}
        logging.debug("Base numerical parameters for Year 1 constructed from initial_state_dict.")
    else:
        # For subsequent years, start from default parameters + exogenous
        base_numerical_params = copy.deepcopy(growth_parameters)
        temp_model_for_param_check = create_growth_model()
        defined_param_names = set(temp_model_for_param_check.parameters.keys())
        for key, value in growth_exogenous:
            if key in defined_param_names:
                 try: base_numerical_params[key] = float(value)
                 except: logging.warning(f"Could not convert exogenous parameter {key}={value} to float.")
        logging.debug(f"Base numerical parameters for Year {st.session_state.current_year + 1} constructed from defaults.")

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
            # --- Log Key Simulation Results ---
            logging.info(f"--- Year {st.session_state.current_year + 1} Simulation Results ---")
            yk_val = latest_sim_solution.get('Yk')
            pi_val = latest_sim_solution.get('PI')
            er_val = latest_sim_solution.get('ER')
            unemp_val = (1 - er_val) * 100 if isinstance(er_val, (int, float)) and np.isfinite(er_val) else 'N/A'
            psbr_val = latest_sim_solution.get('PSBR')
            gd_val = latest_sim_solution.get('GD')
            y_val = latest_sim_solution.get('Y')

            logging.info(f"  Real GDP (Yk): {yk_val:.2f}" if isinstance(yk_val, (int, float)) else f"  Real GDP (Yk): {yk_val}")
            logging.info(f"  Inflation (PI): {pi_val*100:.2f}%" if isinstance(pi_val, (int, float)) else f"  Inflation (PI): {pi_val}")
            logging.info(f"  Unemployment Rate: {unemp_val:.2f}%" if isinstance(unemp_val, (int, float)) else f"  Unemployment Rate: {unemp_val}")
            logging.info(f"  Gov Deficit (PSBR): {psbr_val:.2f}" if isinstance(psbr_val, (int, float)) else f"  Gov Deficit (PSBR): {psbr_val}")
            logging.info(f"  Gov Debt (GD): {gd_val:.2f}" if isinstance(gd_val, (int, float)) else f"  Gov Debt (GD): {gd_val}")
            logging.info(f"  Nominal GDP (Y): {y_val:.2f}" if isinstance(y_val, (int, float)) else f"  Nominal GDP (Y): {y_val}")
            logging.info(f"  Cards Played: {cards_to_play}")
            logging.info(f"  Active Events: {events_active}")
            # --- End Log Key Simulation Results ---

            # Store the NEWLY SOLVED model object for the next turn
            st.session_state.sfc_model_object = model_to_simulate

            # Record History
            current_results = { 'year': st.session_state.current_year + 1 }
            # Expand list of variables to record
            history_vars = ['Yk', 'PI', 'ER', 'GRk', 'Rb', 'Rl', 'Rm', 'BUR', 'Q', 'CAR', 'PSBR', 'GD', 'Y', 'V', 'Lhs', 'Lfs']
            for key in history_vars:
                 current_results[key] = latest_sim_solution.get(key, np.nan)
            current_results['cards_played'] = list(cards_to_play)
            current_results['events'] = list(events_active)
            st.session_state.history.append(current_results)

            # Add played cards to the set for "Learn More" tracking
            if cards_to_play:
                # No longer needed as "Learn More" is removed
                # st.session_state.played_card_names.update(cards_to_play)
                # logging.debug(f"Updated played cards set: {st.session_state.played_card_names}")
                pass

            # Update Hand (Only if not first simulation)
            # --- Set base Yk after first simulation (Year 1) --- 
            if st.session_state.current_year == 0 and st.session_state.base_yk is None:
                base_yk_val = latest_sim_solution.get('Yk')
                if base_yk_val is not None and np.isfinite(base_yk_val):
                    st.session_state.base_yk = base_yk_val
                    logging.info(f"Set base Yk for indexing after Year 1 simulation: {st.session_state.base_yk}")
                else:
                    logging.error("Failed to set base Yk after Year 1 simulation - Yk value invalid.")

            # Discard *all* remaining cards (played or unplayed) after simulation
            if st.session_state.current_year >= 0:
 # Apply discard logic even after year 1 simulation
                current_hand = st.session_state.player_hand
                if current_hand: # Log discarded cards if hand wasn't already empty
                    logging.info(f"Discarding end-of-turn hand: {', '.join(current_hand)}")
                st.session_state.player_hand = [] # Clear hand completely

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
        st.rerun() # Rerun to display the next YEAR_START or error state

elif st.session_state.game_phase == "SIMULATION_ERROR":
    # Correct year display for error message
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    if st.button("Acknowledge Error (Stops Game)"): st.stop()

else:
    st.error(f"Unknown game phase: {st.session_state.game_phase}")

# --- Debug Info (Optional) ---
# with st.expander("Debug Info"): st.write("Session State:", st.session_state)
