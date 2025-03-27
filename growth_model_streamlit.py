import streamlit as st
import pandas as pd
import numpy as np
import copy
import sys
import io
# import matplotlib.pyplot as plt # No longer needed
from contextlib import redirect_stdout
import logging
# Import the necessary components from the model definition file
from chapter_11_model_growth import (
    create_growth_model, growth_parameters, growth_exogenous,
    growth_variables, baseline # baseline is now just the definition + initial values
)
from pysolve.model import SolutionNotFoundError, Model
# Import game mechanics functions
from game_mechanics import (
    create_deck, draw_cards, check_for_events, apply_effects # Removed POLICY_CARDS, ECONOMIC_EVENTS
)
# Import card and event definitions
from cards import POLICY_CARDS

from events import ECONOMIC_EVENTS
# Import matrix display functions
from matrix_display import (
    format_value,
    display_balance_sheet_matrix, display_revaluation_matrix,
    display_transaction_flow_matrix
)

# Suppress extraneous output during model solving
class NullIO(io.StringIO):
    def write(self, txt):
        pass

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# --- Constants ---
INITIAL_HAND_SIZE = 5
CARDS_TO_DRAW_PER_YEAR = 2
MAX_CARDS_PER_ROW = 4 # For card display layout
# INITIAL_STABILIZATION_PERIODS = 10 # Removed

# --- Parameter Categories Definition (Re-added) ---
# Define categories of parameters for the initial setup sliders
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
        ("omega1", "Parameter in wage equation (omega1)", 1.005, 0.9, 1.1),
        ("omega2", "Parameter in wage equation (omega2)", 2.0, 1.0, 3.0),
        ("omega3", "Speed of wage adjustment (omega3)", 0.45621, 0.1, 0.9),
        ("GRpr", "Growth rate of productivity (GRpr)", 0.03, 0.0, 0.1),
        ("BANDt", "Upper band of flat Phillips curve (BANDt)", 0.07, 0.0, 0.1),
        ("BANDb", "Lower band of flat Phillips curve (BANDb)", 0.05, 0.0, 0.1),
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


# --- Helper Functions (Remaining) ---
def format_percent(value):
    """Formats a float as a percentage string."""
    # Check for NaN or infinite values
    if not np.isfinite(value):
        return "N/A"
    return f"{value*100:.2f}%"

# format_value moved to matrix_display.py

def get_delta(current_val, prev_val):
    """ Helper to calculate delta string for st.metric """
    if prev_val is None or not np.isfinite(current_val) or not np.isfinite(prev_val) or np.isclose(current_val, prev_val): # Use isclose for float comparison
        return None # No change or no previous data
    diff = current_val - prev_val
    # Format delta similar to main value
    if abs(diff) >= 1000:
         return f"{diff:,.0f}"
    elif abs(diff) < 1 and diff != 0:
         return f"{diff:.3f}"
    else:
         return f"{diff:.2f}"


def get_delta_percent(current_val, prev_val):
     """ Helper to calculate delta string for percentage st.metric """
     if prev_val is None or not np.isfinite(current_val) or not np.isfinite(prev_val) or np.isclose(current_val, prev_val): # Use isclose for float comparison
         return None
     delta = (current_val - prev_val) * 100
     return f"{delta:.2f}%" # Difference in percentage points

# --- Matrix Display Functions (Moved to matrix_display.py) ---
# display_balance_sheet_matrix, display_revaluation_matrix, display_transaction_flow_matrix removed


# --- Page Configuration ---
st.set_page_config(page_title="SFC Economic Strategy Game", layout="wide")

# --- Custom CSS Injection ---
# Basic retro theme attempt
st.markdown("""
<style>
    /* Import a monospace font (adjust path or use web font if needed) */
    /* @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap'); */

    html, body, [class*="st-"], button, input, textarea, select {
        /* font-family: 'Press Start 2P', monospace; */ /* Example pixel font */
        font-family: 'Consolas', 'Courier New', monospace !important; /* More common monospace */
        color: #E0E0E0; /* Light gray text */
    }

    /* Main background */
    .stApp {
        background-color: #1E1E1E; /* Dark background */
    }

    /* Containers for metrics and cards */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
        background-color: #2A2A2A; /* Slightly lighter dark */
        border: 1px solid #444;
        border-radius: 5px;
        padding: 10px !important; /* Use important to override default */
        margin-bottom: 10px;
    }
    /* Target card containers specifically in POLICY phase */
    /* This selector might be fragile and depend on Streamlit's internal structure */
    /* It targets containers within columns within the main block */
    div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
         box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
         background-color: #333; /* Darker background for cards */
         border: 1px solid #555;
    }


    /* Metric labels */
    [data-testid="stMetricLabel"] > div {
        color: #AAAAAA !important; /* Dimmer label */
        font-size: 0.9em !important;
    }

    /* Metric values */
    [data-testid="stMetricValue"] {
        color: #00FF7F !important; /* Green accent */
        font-size: 1.5em !important;
    }

    /* Metric delta (positive) */
    [data-testid="stMetricDelta"] svg {
        fill: #00FF7F !important; /* Green arrow */
    }
    [data-testid="stMetricDelta"] div {
         color: #00FF7F !important; /* Green text */
    }

     /* Metric delta (negative) */
    [data-testid="stMetricDelta"][aria-label*="Decrease"] svg {
         fill: #FF6347 !important; /* Red arrow */
    }
     [data-testid="stMetricDelta"][aria-label*="Decrease"] div {
         color: #FF6347 !important; /* Red text */
    }

    /* Subheaders inside containers */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] h5 {
        color: #00FF7F; /* Green accent for subheaders inside containers */
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
        font-size: 1em; /* Slightly smaller subheader */
    }


</style>
""", unsafe_allow_html=True)


# --- Game Title ---
st.title("SFC Economic Strategy Game")
st.markdown("Manage the economy through yearly turns using policy cards and responding to events.")

# --- Game State Initialization ---
if "game_initialized" not in st.session_state:
    st.session_state.game_initialized = True
    st.session_state.current_year = 0
    st.session_state.game_phase = "YEAR_START"

    # --- Construct Initial State (t=0) Dictionary ---
    # --- Create and Initialize Model Object ---
    # Reverting to initial solve approach
    try:
        # Construct dictionary first
        logging.info("Constructing initial t=0 state dictionary...")
        initial_state_dict = {}
        initial_state_dict.update(growth_parameters)
        # Need to define these sets before using them
        defined_param_names = set(growth_parameters.keys())
        defined_variable_names = set(v[0] for v in growth_variables)
        for key, value in growth_exogenous:
            try:
                if key in defined_param_names or key in defined_variable_names:
                     initial_state_dict[key] = float(value)
            except (TypeError, ValueError):
                 if isinstance(value, str):
                     initial_state_dict[key] = value # Keep string ref
                 else:
                     logging.warning(f"Could not convert exogenous value {key}={value} to float. Skipping.")
        for key, value in growth_variables:
             try:
                 if isinstance(value, str):
                     initial_state_dict[key] = value # Keep string ref
                 else:
                     initial_state_dict[key] = float(value)
             except (TypeError, ValueError):
                 logging.warning(f"Could not convert variable value {key}={value} to float. Skipping.")
        logging.info(f"Initial t=0 state dictionary constructed with {len(initial_state_dict)} entries.")

        # Create fresh model and set values
        initial_model_object = create_growth_model()
        initial_model_object.set_values(initial_state_dict)

        # Perform the initial solve
        logging.info("Attempting initial solve step (t=0 calculation)...")
        initial_model_object.solve(iterations=1000, threshold=1e-6)
        logging.info("Initial solve step completed.")

        # Store the *solved* t=0 state
        solved_t0_state = copy.copy(initial_model_object.solutions[-1])

        # Reset the model's history to only contain the solved t=0 state
        initial_model_object.solutions = [solved_t0_state]
        initial_model_object.current_solution = solved_t0_state

        # Store the fully initialized model object in session state
        st.session_state.sfc_model_object: Model = initial_model_object
        logging.info("Initialized model object stored in session state.")

    except SolutionNotFoundError as e:
        st.error(f"Fatal Error: Initial model state failed to converge. Cannot start game. Error: {e}")
        logging.exception("Initial model solve failed.")
        st.stop()
    except Exception as e:
        st.error(f"Fatal Error: An unexpected error occurred during model initialization: {e}")
        logging.exception("Unexpected error during model initialization.")
        st.stop()
    # --- End of Model Initialization ---

    # Initialize deck, hand, history, etc.
    st.session_state.deck = create_deck()
    st.session_state.player_hand = []
    st.session_state.deck, st.session_state.player_hand = draw_cards(
        st.session_state.deck, st.session_state.player_hand, INITIAL_HAND_SIZE
    )
    st.session_state.active_events_this_year = []
    st.session_state.cards_selected_this_year = []
    st.session_state.history = []
    st.session_state.initial_params = {}

    st.info("Game Initialized. Ready to start Year 1.")
    st.rerun() # Rerun to ensure state is fully set before proceeding


# --- Sidebar ---
st.sidebar.header("Game Information")

# Display Hand and Events
st.sidebar.header("Player Hand")
if not st.session_state.player_hand:
    st.sidebar.write("Hand is empty.")
else:
    st.sidebar.caption("Cards in hand (Select in Policy Phase):")
    for card_name in st.session_state.player_hand:
         st.sidebar.markdown(f"- {card_name}")

st.sidebar.header("Active Events")
if not st.session_state.active_events_this_year:
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
st.header(f"Year: {st.session_state.current_year}")
st.subheader(f"Phase: {st.session_state.game_phase.replace('_', ' ').title()}")

# --- Phase Logic ---
if st.session_state.game_phase == "YEAR_START":
    st.write("Review the economic situation. New cards drawn and events checked.")

    # --- Initial Parameter Adjustment (Year 0 Only) ---
    # This section might need adjustment if initial params should affect the stabilization run
    if st.session_state.current_year == 0 and "initial_params_set" not in st.session_state:
         # Ensure solutions list is not empty before accessing
         if not st.session_state.sfc_model_object.solutions:
             st.error("Model state has no solutions for initial parameter adjustment.")
             st.stop()
         with st.expander("Advanced: Set Initial Economic Conditions"):
             st.caption("Adjust the starting parameters for the economy. These settings are locked once you start the Policy Phase.")
             initial_params_changed = False
             initial_params_to_set = {}
             # Get the latest solution state from the initial model object *after manual init*
             latest_solution = st.session_state.sfc_model_object.solutions[-1] # Should be index 0

             # Need defined_param_names here for the check below
             defined_param_names = set(growth_parameters.keys())

             # Use parameter_categories defined in this file
             for category, params in parameter_categories.items():
                 st.markdown(f"**{category}**")
                 for param_key, param_name, default_val, min_val, max_val in params:
                     # Use current value from the latest solution object as the default
                     # Provide default_val as fallback if key not in solution (e.g., for params not vars)
                     current_model_val = latest_solution.get(param_key, default_val)
                     slider_key = f"initial_slider_{param_key}"

                     # Slider setup
                     range_magnitude = max_val - min_val
                     step_size = 0.01 # Default step
                     if range_magnitude <= 0.01: step_size = 0.0001
                     elif range_magnitude <= 0.1: step_size = 0.0005
                     elif range_magnitude <= 1.0: step_size = 0.001
                     elif range_magnitude <= 10.0: step_size = 0.005

                     format_spec = "%.2f" # Default format
                     if step_size < 0.001: format_spec = "%.5f"
                     elif step_size < 0.01: format_spec = "%.4f"
                     elif step_size < 0.1: format_spec = "%.3f"

                     # Use session state to store slider value temporarily to avoid immediate model update on every interaction
                     if slider_key not in st.session_state.initial_params:
                         # Try converting current_model_val to float safely
                         try:
                             initial_float_val = float(current_model_val)
                         except (TypeError, ValueError):
                             logging.warning(f"Could not convert initial value {param_key}={current_model_val} to float. Using default: {default_val}")
                             initial_float_val = float(default_val)
                         st.session_state.initial_params[slider_key] = initial_float_val


                     new_value = st.slider(
                         param_name,
                         min_value=float(min_val),
                         max_value=float(max_val),
                         value=st.session_state.initial_params[slider_key], # Use value from temp state
                         step=step_size,
                         format=format_spec,
                         key=slider_key
                     )
                     # Check if slider value changed
                     # Use np.isclose for robust float comparison
                     if not np.isclose(st.session_state.initial_params[slider_key], new_value):
                          st.session_state.initial_params[slider_key] = new_value # Update temp state
                          initial_params_changed = True

                     # Store the potentially changed value for bulk update
                     # We only store parameters here, as variables shouldn't be set by sliders
                     if param_key in defined_param_names: # Check if it's a parameter
                         initial_params_to_set[param_key] = new_value

             # Apply changes if any slider was moved
             if initial_params_changed:
                 try:
                     st.session_state.sfc_model_object.set_values(initial_params_to_set)
                     # Update the manually created initial solution as well
                     st.session_state.sfc_model_object.solutions[0].update(initial_params_to_set)
                     st.session_state.sfc_model_object.current_solution.update(initial_params_to_set)
                     st.success("Initial parameters updated in model state.")
                 except Exception as e:
                     st.error(f"Error applying initial parameters: {e}")
                 # No rerun here, let user confirm by moving to next phase


    # --- Draw Cards and Check Events (Run only once per YEAR_START phase, and only if year > 0) ---
    if st.session_state.current_year > 0:
        if "year_start_processed" not in st.session_state or st.session_state.year_start_processed != st.session_state.current_year:

            # Draw cards
            st.session_state.deck, st.session_state.player_hand = draw_cards(
                st.session_state.deck, st.session_state.player_hand, CARDS_TO_DRAW_PER_YEAR
            )
            st.toast(f"Drew {CARDS_TO_DRAW_PER_YEAR} cards.") # Use toast for less intrusive notification

            # Check for events based on the *previous* year's state
            previous_model_state = st.session_state.sfc_model_object # This holds the result of the last completed year
            st.session_state.active_events_this_year = check_for_events(previous_model_state)
            if st.session_state.active_events_this_year:
                 st.warning(f"New Events Occurred: {', '.join(st.session_state.active_events_this_year)}")

            st.session_state.year_start_processed = st.session_state.current_year # Mark as processed for this year
            st.session_state.cards_selected_this_year = [] # Clear selections from previous year
            st.rerun() # Rerun to update sidebar display immediately

    # --- Economic Dashboard ---
    st.subheader("Economic Dashboard (Previous Year's Results)")
    model_state = st.session_state.sfc_model_object # Represents state *after* the last completed year
    # Ensure solutions list is not empty before accessing
    if not model_state.solutions:
         st.error("Model state has no solutions. Initialization might have failed.")
         st.stop()
    latest_solution = model_state.solutions[-1] # Get the latest solution for current values


    # Get previous year's data for calculating changes (delta) if available
    prev_year_data = None
    if len(st.session_state.history) > 0:
        target_year = st.session_state.current_year # The year that just finished
        # History stores results *for* year N, model_state is *after* year N.
        prev_year_data = next((item for item in reversed(st.session_state.history) if item['year'] == target_year), None)

    # Display Metrics in Containers
    with st.container(border=True):
        st.markdown("##### Macroeconomic Indicators")
        # Row 1: Core Macro Indicators
        col1, col2, col3, col4 = st.columns(4)
        yk_val = latest_solution.get('Yk', 0.0)
        pi_val = latest_solution.get('PI', 0.0)
        er_val = latest_solution.get('ER', 1.0) # Default to 1 (full employment) if not found
        grk_val = latest_solution.get('GRk', 0.0)

        # Use t=0 state from session state model for first year comparison
        yk_prev = prev_year_data.get('Yk') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('Yk')
        pi_prev = prev_year_data.get('PI') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('PI')
        er_prev = prev_year_data.get('ER') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('ER')
        grk_prev = prev_year_data.get('GRk') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('GRk')


        col1.metric("Real GDP (Yk)", format_value(yk_val), delta=get_delta(yk_val, yk_prev))
        col2.metric("Inflation (PI)", format_percent(pi_val), delta=get_delta_percent(pi_val, pi_prev))
        col3.metric("Unemployment (1-ER)", format_percent(1-er_val), delta=get_delta_percent(1-er_val, (1-er_prev) if er_prev is not None else None))
        col4.metric("Capital Growth (GRk)", format_percent(grk_val), delta=get_delta_percent(grk_val, grk_prev))

    with st.container(border=True):
        st.markdown("##### Financial Indicators")
        # Row 2: Financial Indicators
        col5, col6, col7, col8 = st.columns(4)
        rb_val = latest_solution.get('Rb', 0.0) # Bill rate (Policy Rate)
        rl_val = latest_solution.get('Rl', 0.0) # Loan rate
        bur_val = latest_solution.get('BUR', 0.0) # Burden of personal debt
        q_val = latest_solution.get('Q', 0.0) # Tobin's Q

        # Use t=0 state from session state model for first year comparison
        rb_prev = prev_year_data.get('Rb') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('Rb')
        rl_prev = prev_year_data.get('Rl') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('Rl')
        bur_prev = prev_year_data.get('BUR') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('BUR')
        q_prev = prev_year_data.get('Q') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('Q')


        col5.metric("Policy Rate (Rb)", format_percent(rb_val), delta=get_delta_percent(rb_val, rb_prev))
        col6.metric("Loan Rate (Rl)", format_percent(rl_val), delta=get_delta_percent(rl_val, rl_prev))
        col7.metric("Debt Burden (BUR)", format_value(bur_val), delta=get_delta(bur_val, bur_prev))
        col8.metric("Tobin's Q", format_value(q_val), delta=get_delta(q_val, q_prev))

    with st.container(border=True):
        st.markdown("##### Government Indicators")
        # Row 3: Government Indicators
        col9, col10, col11, col12 = st.columns(4)
        psbr_val = latest_solution.get('PSBR', 0.0)
        gd_val = latest_solution.get('GD', 0.0)
        y_val = latest_solution.get('Y', 0.0) # Nominal GDP for ratios
        debt_ratio = (gd_val / y_val) if y_val else 0
        deficit_ratio = (psbr_val / y_val) if y_val else 0

        # Use t=0 state from session state model for first year comparison
        psbr_prev = prev_year_data.get('PSBR') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('PSBR')
        gd_prev = prev_year_data.get('GD') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('GD')
        y_prev = prev_year_data.get('Y') if prev_year_data else st.session_state.sfc_model_object.solutions[0].get('Y')

        debt_ratio_prev = (gd_prev / y_prev) if (y_prev and gd_prev is not None) else None
        deficit_ratio_prev = (psbr_prev / y_prev) if (y_prev and psbr_prev is not None) else None

        col9.metric("Gov Deficit (PSBR)", format_value(psbr_val), delta=get_delta(psbr_val, psbr_prev))
        col10.metric("Gov Debt (GD)", format_value(gd_val), delta=get_delta(gd_val, gd_prev))
        col11.metric("Deficit / GDP", format_percent(deficit_ratio), delta=get_delta_percent(deficit_ratio, deficit_ratio_prev))
        col12.metric("Debt / GDP", format_percent(debt_ratio), delta=get_delta_percent(debt_ratio, debt_ratio_prev))


    st.divider()

    if st.button("Start Policy Phase"):
        st.session_state.game_phase = "POLICY"
        st.session_state.initial_params_set = True # Lock initial params
        if "year_start_processed" in st.session_state: # Clean up flag
             del st.session_state.year_start_processed
        st.rerun()

elif st.session_state.game_phase == "POLICY":
    st.subheader("Select Policy Cards to Play")
    st.write("Click on a card to select or deselect it.")

    available_cards = st.session_state.player_hand
    selected_cards_this_turn = st.session_state.cards_selected_this_year # This is a list

    if not available_cards:
        st.write("No cards in hand.")
    else:
        # Create columns for card layout
        num_cards = len(available_cards)
        num_cols = min(num_cards, MAX_CARDS_PER_ROW)
        cols = st.columns(num_cols)

        for i, card_name in enumerate(available_cards):
            col_index = i % num_cols
            with cols[col_index]:
                card_info = POLICY_CARDS.get(card_name, {})
                is_selected = card_name in selected_cards_this_turn

                # Use an expander or container for visual separation
                # Apply a CSS class for card styling
                with st.container(border=True): # Using border=True for now, CSS class can override
                    st.markdown(f"**{card_name}** ({card_info.get('type', 'N/A')})")
                    st.caption(card_info.get('desc', 'No description available.'))
                    # REMOVED internal param details below:
                    # st.markdown(f"<small>Param: {card_info.get('param', 'N/A')}, Effect: {card_info.get('effect', 'N/A')}</small>", unsafe_allow_html=True)

                    button_label = "Deselect" if is_selected else "Select"
                    button_type = "primary" if is_selected else "secondary"
                    # Use card name and index in key for uniqueness across reruns and turns
                    button_key = f"select_{card_name}_{i}_{st.session_state.current_year}" # Added index i

                    if st.button(button_label, key=button_key, type=button_type, use_container_width=True):
                        if is_selected:
                            st.session_state.cards_selected_this_year.remove(card_name)
                        else:
                            # Optional: Limit number of cards playable per turn?
                            # max_playable = 1
                            # if len(st.session_state.cards_selected_this_year) < max_playable:
                            st.session_state.cards_selected_this_year.append(card_name)
                            # else:
                            #     st.warning(f"You can only play {max_playable} card(s) per turn.")
                        st.rerun() # Rerun to update button state

    st.divider()


    # Display summary of selected cards
    if selected_cards_this_turn:
        st.write("Selected for this turn:")
        for card_name in selected_cards_this_turn:
             st.markdown(f"- {card_name}")
    else: # Corrected indentation
        st.write("No cards selected for this turn.")

    if st.button("Confirm Policies & Run Simulation"):
        st.session_state.game_phase = "SIMULATION"
        st.rerun()

# --- Revised SIMULATION Phase Logic ---
elif st.session_state.game_phase == "SIMULATION":
    # Correctly placed log
    logging.info(f"Entering SIMULATION phase for year {st.session_state.current_year + 1}")
    st.write("Applying policies and simulating the year's economic activity...")

    # Retrieve the current model state from session
    current_model = st.session_state.sfc_model_object

    # --- Prepare Inputs for Simulation Step ---
    cards_to_play = st.session_state.cards_selected_this_year
    events_active = st.session_state.active_events_this_year

    # Get the complete solution dictionary from the end of the previous turn
    if not current_model.solutions:
        st.error("Cannot simulate: No previous model solution found in session state.")
        st.stop()
    # This dictionary contains all variables, including internal lagged ones (_var__1)
    latest_solution_values = current_model.solutions[-1]

    # Construct the base numerical parameters for this turn
    # Start with the base parameters defined in the model file
    base_numerical_params = copy.deepcopy(growth_parameters)
    # Add exogenous parameters (filter from growth_exogenous list)
    # Need to be careful here, growth_exogenous also contains initial *variable* values
    # Let's assume parameters are those keys present in growth_parameters OR
    # keys from growth_exogenous that are ALSO in the model's defined parameters
    temp_model_for_param_check = create_growth_model() # Create a temp model just to access its defined param names
    defined_param_names = set(temp_model_for_param_check.parameters.keys())
    for key, value in growth_exogenous:
        if key in defined_param_names:
             # Ensure value is float, handle potential errors
             try:
                 base_numerical_params[key] = float(value)
             except (TypeError, ValueError):
                  logging.warning(f"Could not convert exogenous parameter {key}={value} to float during base param construction. Skipping.")
    logging.debug(f"Base numerical parameters constructed for turn.")


    # --- Calculate Final Parameters for the Turn using apply_effects ---
    st.write("Applying effects...")
    effect_log = io.StringIO()
    final_numerical_params = {} # Initialize
    try:
        with redirect_stdout(effect_log): # Capture logs from apply_effects
             final_numerical_params = apply_effects(
                 base_params=base_numerical_params,
                 latest_solution=latest_solution_values, # Pass previous solution for context if needed by effects
                 cards_played=cards_to_play,
                 active_events=events_active
             )
        logging.debug(f"Final numerical parameters after effects calculated.")
    except Exception as e:
        st.error(f"Error during apply_effects: {e}")
        logging.exception("Error calling apply_effects:")
        st.stop()

    # Display the log of applied effects (which now comes from logging within apply_effects)
    # We can still show the captured stdout if needed, or rely on terminal logs
    # st.text_area("Applied Effects Log:", effect_log.getvalue(), height=100) # Optional: show captured stdout


    # --- Initialize Fresh Model for Simulation ---
    model_to_simulate = create_growth_model()
    try:
        # 1. Set default parameters/variables first (needed by pysolve structure)
        model_to_simulate.set_values(growth_parameters)
        model_to_simulate.set_values(growth_exogenous)
        model_to_simulate.set_values(growth_variables)
        logging.debug("Set default params/vars on fresh model instance.")

        # 2. Set the final calculated numerical parameters for this turn (overrides defaults)
        model_to_simulate.set_values(final_numerical_params)
        logging.debug("Set final numerical parameters on fresh model instance.")


        # 3. Copy the entire solutions history from the previous model object
        #    and set the current solution pointer.
        prev_model = st.session_state.sfc_model_object # Get the model from the previous state
        model_to_simulate.solutions = copy.deepcopy(prev_model.solutions) # Deep copy the history
        model_to_simulate.current_solution = model_to_simulate.solutions[-1] # Set pointer
        logging.debug("Copied solutions history and set current_solution for the fresh model instance.")

    except Exception as e:
        st.error(f"Error setting initial state for simulation step: {e}")
        logging.exception("Error during model initialization for simulation step:")
        st.stop()


    # --- Run the simulation for one year ---
    try:
        with st.spinner(f"Simulating Year {st.session_state.current_year + 1}..."):
            # Suppress console output from pysolve
            old_stdout = sys.stdout
            sys.stdout = NullIO()



            logging.debug(f"Attempting model.solve() for year {st.session_state.current_year + 1}...")
            # Solve for the next step (1 year)
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            logging.debug(f"model.solve() completed for year {st.session_state.current_year + 1}.")


            # --- DEBUG LOGGING: Post-Solve State ---
            post_solve_solution = model_to_simulate.solutions[-1] # The newly added solution
            logging.debug(f"--- Year {st.session_state.current_year + 1} POST-SOLVE ---")
            logging.debug(f"  Yk: {post_solve_solution.get('Yk', 'N/A')}")
            logging.debug(f"  Kk: {post_solve_solution.get('Kk', 'N/A')}")
            logging.debug(f"  P:  {post_solve_solution.get('P', 'N/A')}")
            logging.debug(f"  W:  {post_solve_solution.get('W', 'N/A')}")
            logging.debug(f"  N:  {post_solve_solution.get('N', 'N/A')}")
            logging.debug(f"  ER: {post_solve_solution.get('ER', 'N/A')}")
            # Log etan *parameter value* after solve (should be unchanged by solve)
            logging.debug(f"  etan (param): {model_to_simulate.parameters.get('etan', 'N/A')}")

            # Store the updated model state (replace the old state)
            st.session_state.sfc_model_object = model_to_simulate

            # --- Record History (Include more vars for delta calculation) ---
            latest_sim_solution = model_to_simulate.solutions[-1]
            # Corrected closing brace placement
            current_results = {
                'year': st.session_state.current_year + 1,
                'Yk': latest_sim_solution.get('Yk', np.nan),
                'PI': latest_sim_solution.get('PI', np.nan),
                'ER': latest_sim_solution.get('ER', np.nan),
                # Add other key vars needed for dashboard deltas
                'GRk': latest_sim_solution.get('GRk', np.nan),
                'Rb': latest_sim_solution.get('Rb', np.nan),
                'Rl': latest_sim_solution.get('Rl', np.nan),
                'BUR': latest_sim_solution.get('BUR', np.nan),
                'Q': latest_sim_solution.get('Q', np.nan),
                'PSBR': latest_sim_solution.get('PSBR', np.nan),
                'GD': latest_sim_solution.get('GD', np.nan),
                'Y': latest_sim_solution.get('Y', np.nan),
                'cards_played': list(cards_to_play), # Store as list
                'events': list(events_active) # Store as list
            }
            st.session_state.history.append(current_results)

            # --- Update Hand ---
            # Remove played cards from hand
            current_hand = st.session_state.player_hand
            new_hand = [card for card in current_hand if card not in cards_to_play]
            st.session_state.player_hand = new_hand

            # Clear turn-specific state
            st.session_state.cards_selected_this_year = []
            st.session_state.active_events_this_year = []

            # Move to the next phase
            st.session_state.game_phase = "RESULTS"


            # --- Comprehensive Post-Solve Logging ---
            latest_solution_dict = model_to_simulate.solutions[-1]
            logging.debug(f"--- Year {st.session_state.current_year + 1} POST-SOLVE (Full State) ---")
            for key in sorted(latest_solution_dict.keys()):
                logging.debug(f"  {key}: {latest_solution_dict[key]}")
            # --- End Comprehensive Logging ---

    except Exception as e: # Catch any other unexpected errors during solve/post-solve
        st.error(f"An unexpected error occurred during simulation for Year {st.session_state.current_year + 1}: {str(e)}")
        logging.exception(f"Unexpected error in SIMULATION phase for year {st.session_state.current_year + 1}:")
        # Keep the phase as SIMULATION or move to a specific error state?
        # For now, let the finally block handle rerun, but the phase won't be RESULTS.
        # Optionally set a specific error phase:
        # st.session_state.game_phase = "UNEXPECTED_SIMULATION_ERROR"

    except SolutionNotFoundError as e:
        st.error(f"Model failed to converge for Year {st.session_state.current_year + 1}. The economy is unstable! Error: {str(e)}")
        # Do not update hand or clear state if simulation fails
        st.session_state.game_phase = "SIMULATION_ERROR" # Enter an error state

    finally:
        # Restore console output
        sys.stdout = old_stdout
        # Correctly placed log before rerun
        logging.info(f"SIMULATION phase end: Current game phase before rerun is '{st.session_state.game_phase}'")
        # Rerun to display results or error
        st.rerun()
# --- End of Revised SIMULATION Phase Logic ---

elif st.session_state.game_phase == "RESULTS":
    st.write(f"Displaying results for Year {st.session_state.current_year + 1}.") # Year completed

    # --- Display Key Results (using same layout as dashboard for consistency) ---
    st.subheader("Economic Results")
    model_state = st.session_state.sfc_model_object
    latest_solution = model_state.solutions[-1] # Get the latest solution for current values

    # Get previous year's data for delta calculation
    prev_year_data = None
    # History stores results *for* year N+1. model_state is *after* year N+1.
    # To get delta for year N+1 results, we need results from year N.
    if st.session_state.current_year > 0: # Need at least year 1 results to compare to year 0 (baseline)
         target_year = st.session_state.current_year # Year that just finished
         prev_year_data = next((item for item in reversed(st.session_state.history) if item['year'] == target_year), None)

    # Define the source for t=0 comparison
    # Use the first solution stored in the session state model object
    t0_solution = st.session_state.sfc_model_object.solutions[0] if st.session_state.sfc_model_object.solutions else {}


    # Display Metrics in Containers
    with st.container(border=True):
        st.markdown("##### Macroeconomic Indicators")
        # Row 1: Core Macro Indicators
        col1, col2, col3, col4 = st.columns(4)
        yk_val = latest_solution.get('Yk', 0.0)
        pi_val = latest_solution.get('PI', 0.0)
        er_val = latest_solution.get('ER', 1.0)
        grk_val = latest_solution.get('GRk', 0.0)

        # Use t=0 state from session state model for first year comparison
        yk_prev = prev_year_data.get('Yk') if prev_year_data else t0_solution.get('Yk')
        pi_prev = prev_year_data.get('PI') if prev_year_data else t0_solution.get('PI')
        er_prev = prev_year_data.get('ER') if prev_year_data else t0_solution.get('ER')
        grk_prev = prev_year_data.get('GRk') if prev_year_data else t0_solution.get('GRk')


        col1.metric("Real GDP (Yk)", format_value(yk_val), delta=get_delta(yk_val, yk_prev))
        col2.metric("Inflation (PI)", format_percent(pi_val), delta=get_delta_percent(pi_val, pi_prev))
        col3.metric("Unemployment (1-ER)", format_percent(1-er_val), delta=get_delta_percent(1-er_val, (1-er_prev) if er_prev is not None else None))
        col4.metric("Capital Growth (GRk)", format_percent(grk_val), delta=get_delta_percent(grk_val, grk_prev))

    with st.container(border=True):
        st.markdown("##### Financial Indicators")
        # Row 2: Financial Indicators
        col5, col6, col7, col8 = st.columns(4)
        rb_val = latest_solution.get('Rb', 0.0)
        rl_val = latest_solution.get('Rl', 0.0)
        bur_val = latest_solution.get('BUR', 0.0)
        q_val = latest_solution.get('Q', 0.0)

        # Use t=0 state from session state model for first year comparison
        rb_prev = prev_year_data.get('Rb') if prev_year_data else t0_solution.get('Rb')
        rl_prev = prev_year_data.get('Rl') if prev_year_data else t0_solution.get('Rl')
        bur_prev = prev_year_data.get('BUR') if prev_year_data else t0_solution.get('BUR')
        q_prev = prev_year_data.get('Q') if prev_year_data else t0_solution.get('Q')


        col5.metric("Policy Rate (Rb)", format_percent(rb_val), delta=get_delta_percent(rb_val, rb_prev))
        col6.metric("Loan Rate (Rl)", format_percent(rl_val), delta=get_delta_percent(rl_val, rl_prev))
        col7.metric("Debt Burden (BUR)", format_value(bur_val), delta=get_delta(bur_val, bur_prev)) # Use non-% delta
        col8.metric("Tobin's Q", format_value(q_val), delta=get_delta(q_val, q_prev)) # Use non-% delta

    with st.container(border=True):
        st.markdown("##### Government Indicators")
        # Row 3: Government Indicators
        col9, col10, col11, col12 = st.columns(4)
        psbr_val = latest_solution.get('PSBR', 0.0)
        gd_val = latest_solution.get('GD', 0.0)
        y_val = latest_solution.get('Y', 0.0)
        debt_ratio = (gd_val / y_val) if y_val else 0
        deficit_ratio = (psbr_val / y_val) if y_val else 0

        # Use t=0 state from session state model for first year comparison
        psbr_prev = prev_year_data.get('PSBR') if prev_year_data else t0_solution.get('PSBR')
        gd_prev = prev_year_data.get('GD') if prev_year_data else t0_solution.get('GD')
        y_prev = prev_year_data.get('Y') if prev_year_data else t0_solution.get('Y')

        debt_ratio_prev = (gd_prev / y_prev) if (y_prev and gd_prev is not None) else None
        deficit_ratio_prev = (psbr_prev / y_prev) if (y_prev and psbr_prev is not None) else None


        col9.metric("Gov Deficit (PSBR)", format_value(psbr_val), delta=get_delta(psbr_val, psbr_prev))
        col10.metric("Gov Debt (GD)", format_value(gd_val), delta=get_delta(gd_val, gd_prev))
        col11.metric("Deficit / GDP", format_percent(deficit_ratio), delta=get_delta_percent(deficit_ratio, deficit_ratio_prev))
        col12.metric("Debt / GDP", format_percent(debt_ratio), delta=get_delta_percent(debt_ratio, debt_ratio_prev))

    st.divider()

    # (Placeholder for Consequence Calculation)
    st.write("--- Consequences Placeholder ---")

    # --- Detailed Financial Data ---
    with st.expander("View Detailed Financial Statements"):

        # Determine current and previous solutions ONCE for matrix display
        current_solution = latest_solution # Already available from line 1152

        prev_solution = None
        if len(model_state.solutions) > 1:
            # If more than one solution exists, the previous one is the second to last
            prev_solution = model_state.solutions[-2]
        # Note: If only the initial t=0 solution exists, prev_solution remains None,
        # and the matrix functions handle this gracefully.

        # --- Now call the display functions ---
        # Display Balance Sheet
        display_balance_sheet_matrix(current_solution)
        st.divider()

        # Display Revaluation Matrix (needs previous period)
        if prev_solution:
            display_revaluation_matrix(current_solution, prev_solution)
            st.divider()
        else:
            st.caption("Revaluation matrix requires data from the previous period (Year > 0).")

        # Display Transaction Flow Matrix (needs previous period)
        if prev_solution:
            display_transaction_flow_matrix(current_solution, prev_solution)
        else:
            st.caption("Transaction flow matrix requires data from the previous period (Year > 0).")



    # --- History Table ---
    with st.expander("View History Table"):
        if st.session_state.history:
            # Display latest year first
            history_df = pd.DataFrame(st.session_state.history).sort_values(by='year', ascending=False)
            st.dataframe(history_df)
        else:
            st.write("No history recorded yet.")

    # --- History Charts ---
    with st.expander("View Historical Trends"):
        if len(st.session_state.history) > 1:
            history_df = pd.DataFrame(st.session_state.history).set_index('year')

            # Select and prepare data for charting
            chart_data = pd.DataFrame()
            if 'Yk' in history_df.columns:
                chart_data['Real GDP (Yk)'] = history_df['Yk']
            if 'PI' in history_df.columns:
                chart_data['Inflation (PI %)'] = history_df['PI'] * 100
            if 'ER' in history_df.columns:
                chart_data['Unemployment Rate (%)'] = (1 - history_df['ER']) * 100

            if not chart_data.empty:
                st.line_chart(chart_data)
            else:
                st.caption("Not enough data or required columns missing for charts.")
        elif len(st.session_state.history) == 1:
             st.caption("Need at least two years of history to display trends.")
        else:
            st.caption("No history recorded yet.")


    if st.button("Start Next Year"):
        st.session_state.current_year += 1 # Increment year counter
        st.session_state.game_phase = "YEAR_START"
        st.rerun()

elif st.session_state.game_phase == "SIMULATION_ERROR":
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    # (Placeholder for error handling options, e.g., reset, go back)
    if st.button("Acknowledge Error (Stops Game)"):
         # Simple stop for now
         st.stop()

else:
    st.error(f"Unknown game phase: {st.session_state.game_phase}")


# --- Debug Info (Optional) ---
# with st.expander("Debug Info"):
#     st.write("Session State:", st.session_state)
