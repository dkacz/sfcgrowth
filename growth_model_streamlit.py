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
import json
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
    from dilemmas import DILEMMAS
    from game_mechanics import select_dilemma, apply_dilemma_choice # Add new functions
    from cards import POLICY_CARDS
    from events import ECONOMIC_EVENTS
    from matrix_display import (
        format_value,
        display_balance_sheet_matrix, display_revaluation_matrix,
        display_transaction_flow_matrix
    )
    from characters import CHARACTERS # Import CHARACTERS at top level
except ImportError as e:
    st.error(f"Failed to import game components: {e}. Ensure cards.py, events.py, game_mechanics.py, matrix_display.py, characters.py are present.")
    st.stop()


# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='debug_session.log',
                    filemode='w') # 'w' overwrites the file each time

# --- Constants ---
INITIAL_HAND_SIZE = 5
CARDS_TO_DRAW_PER_YEAR = 4 # Draw 4 cards per year as requested
MAX_CARDS_PER_ROW = 4 # For card display layout
ICON_DIR = "assets/icons" # Define icon directory
SPARKLINE_YEARS = 10 # Number of years for sparkline history
GAME_END_YEAR = 10 # Define the final year

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
    "GD_GDP": "Government Debt to GDP Ratio: Ratio of total government debt to nominal GDP.",
    "GovBalance_GDP": "Government Balance as % of GDP: Surplus (+) or Deficit (-)."
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
    'omega3': 'Speed of adjustment of wages to target value',
    'omega0': 'Constant term in wage Phillips curve',
    'omega1': 'Coefficient on expected inflation in wage Phillips curve',
    'omega2': 'Coefficient on unemployment gap in wage Phillips curve',
    'alpha2': 'Propensity to consume out of wealth',
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
    # Return a placeholder or empty string if icon not found
    return "" # Changed to return empty string

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

# --- Helper function to create KPI plots ---
def create_kpi_plot(metric_key, y_axis_title):
    logging.debug(f"Entering create_kpi_plot for metric: {metric_key}")
    # Fetch full history starting from Year 1 for KPI plots
    plot_df = get_sparkline_data(metric_key, st.session_state.current_year, fetch_full_history=True)
    logging.debug(f"create_kpi_plot({metric_key}) - plot_df from get_sparkline_data:\n{plot_df}")
    if plot_df is not None and not plot_df.empty:
        # Check if data exists
        # Define colors based on metric_key (using theme/standard colors)
        # Using Blue, Green, Grey, Black for theme alignment
        if metric_key == 'Yk_Index':
            plot_color = "#1FB25A" # Green (Fiscal card color)
        elif metric_key == 'PI':
            plot_color = "#000000" # Black
        elif metric_key == 'Unemployment':
            plot_color = "#0072BB" # Blue (Monetary card color)
        elif metric_key == 'GD_GDP':
            plot_color = "#555555" # Dark Grey
        else:
            plot_color = "#1FB25A" # Default Green

        # Determine axis format
        y_axis_format = ".1f" # Default format for index
        if metric_key in ['PI', 'Unemployment', 'GD_GDP']:
            y_axis_format = ".1%" # Percentage format

        # --- Correction for Percentage Scaling ---
        # Divide values by 100 if the axis format is percentage,
        # as Altair's format expects raw proportions (e.g., 0.20 for 20%)
        plot_df_corrected = plot_df.copy() # Avoid modifying original df used elsewhere
        if y_axis_format.endswith('%'):
            plot_df_corrected[metric_key] = plot_df_corrected[metric_key] / 100.0
        # --- End Correction ---

        # Base chart
        # Use the corrected DataFrame for plotting
        base = alt.Chart(plot_df_corrected.reset_index()).encode(
            # X-Axis: Set domain explicitly from Year 1 to current year
            x=alt.X('Year:O',
                    axis=alt.Axis(title='Year' if metric_key in ['Unemployment', 'GD_GDP'] else None,
                                  labels=True if metric_key in ['Unemployment', 'GD_GDP'] else False,
                                  labelAngle=-45, grid=False),
                    # Explicit domain based on data, with padding
                    scale=alt.Scale(domain=[plot_df.index.min(), plot_df.index.max()], paddingOuter=0.1)
                   ),
            tooltip=[
                alt.Tooltip('Year:O', title='Simulation Year'),
                # Use y_axis_title for tooltip, format based on corrected data
                alt.Tooltip(f'{metric_key}:Q', format=y_axis_format, title=y_axis_title)
            ]
        ) # Added missing closing parenthesis for encode()
        # Handle single data point case (e.g., first year) OR line chart case
        if len(plot_df_corrected) == 1:
            # --- Single Point Chart Logic ---
            single_value = plot_df_corrected[metric_key].iloc[0]
            if np.isclose(single_value, 0): padding = 0.01
            else: padding = abs(single_value) * 0.15
            y_domain = [single_value - padding, single_value + padding]
            # Ensure lower bound is not unnecessarily negative (allow negative for PI)
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']: # Added Yk_Index here
                 y_domain[0] = max(0, y_domain[0])

            y_axis_scale = alt.Scale(domain=y_domain, zero=False)

            chart = base.mark_point(size=100, filled=True, color=plot_color).encode(
                 y=alt.Y(f'{metric_key}:Q',
                         axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                         scale=y_axis_scale # Apply explicit scale
                        )
            ) # Closed parenthesis for encode() here
        else: # Correctly placed else statement
            # --- Line Chart Logic (for 2+ points) ---
            min_val = plot_df_corrected[metric_key].min()
            max_val = plot_df_corrected[metric_key].max()
            data_range = max_val - min_val
            if np.isclose(data_range, 0):
                if np.isclose(max_val, 0): padding = 0.01
                else: padding = abs(max_val) * 0.15
            else:
                padding = data_range * 0.15

            y_domain = [min_val - padding, max_val + padding]
            # Ensure lower bound is not unnecessarily negative (allow negative for PI)
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']: # Added Yk_Index here
                 y_domain[0] = max(0, y_domain[0])

            y_axis_scale = alt.Scale(domain=y_domain, zero=False)

            line = base.mark_line(
                point=alt.OverlayMarkDef(color=plot_color),
                color=plot_color,
                strokeWidth=2
            ).encode(
                y=alt.Y(f'{metric_key}:Q',
                        axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                        scale=y_axis_scale # Apply explicit scale
                )
            )

            last_point_df_corrected = plot_df_corrected.reset_index().iloc[[-1]]
            labels = alt.Chart(last_point_df_corrected).mark_text(
                align='left', baseline='middle', dx=7, fontSize=11
            ).encode(
                x=alt.X('Year:O'),
                y=alt.Y(f'{metric_key}:Q'),
                text=alt.Text(f'{metric_key}:Q', format=y_axis_format),
                color=alt.value(plot_color)
            )

            chart_layers = [line, labels]
            # Add zero reference line only if the calculated domain includes zero
            if y_domain[0] <= 0 <= y_domain[1]:
                 zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                     color='grey', strokeDash=[2,2], size=1
                 ).encode(y='y')
                 chart_layers.append(zero_line)

            chart = alt.layer(*chart_layers)

        # --- Common Chart Configuration (Applied to both single point and line) ---
        chart = chart.properties(
            height=200,
            padding={"left": 20} # Added left padding
        ).configure_view(
            fill=None,
            stroke='#cccccc'
        ).configure_axis(
            labelFont='Lato',
            titleFont='Oswald',
            titleFontSize=12,
            labelFontSize=11
        ).interactive()

        return chart # Return the configured chart (point or line)
    else: # Case where plot_df is None or empty
        logging.warning(f"create_kpi_plot({metric_key}) - Returning None because plot_df is None or empty.")
        return None # Return None if plot_df is None or empty



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
    /* Style the container holding the card elements */
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
    /* Style expander within event card */
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
    # Start with CHARACTER_SELECTION phase
    st.session_state.game_phase = "CHARACTER_SELECTION"
    st.session_state.selected_character_id = None
    st.session_state.game_objectives = {}

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
    # Deck creation moved to after character selection
    st.session_state.deck = [] # Initialize empty deck
    st.session_state.player_hand = [] # Initialize empty hand
    st.session_state.discard_pile = [] # Initialize discard pile
    logging.info("Initialized empty deck, hand, and discard pile.")
    st.session_state.active_events_this_year = []
    st.session_state.cards_selected_this_year = []
    st.session_state.history = [] # Initialize history as empty
    st.session_state.initial_params = {} # For year 0 adjustments
    st.session_state.temporary_effects = [] # Initialize list to track temporary event effects
    st.session_state.persistent_effects = {} # Initialize dict to track cumulative persistent card effects

    st.session_state.seen_dilemmas = set() # Initialize set to track seen dilemmas
    st.session_state.current_dilemma = None # To store the currently active dilemma
    st.session_state.dilemma_processed_for_year = -1 # Initialize to a non-valid year
    logging.info("Game Initialized at Year 0.")
    st.rerun() # Rerun to start the flow


# --- Sidebar ---
# Display Character Image and Objectives side-by-side if character selected
if st.session_state.get('selected_character_id'):
    char_id = st.session_state.selected_character_id
    char_data = CHARACTERS.get(char_id)

    if char_data: # Check if character data was found
        st.sidebar.header(f"Advisor: {char_data['name']}") # Display the name

    # Create two columns in the sidebar
    col1, col2 = st.sidebar.columns([1, 2]) # Adjust ratio if needed (e.g., [1, 3])

    # --- Column 1: Character Image ---
    with col1:
        if char_data:
            img_path = char_data.get('image_path')
            if img_path:
                try:
                    img_data_uri = get_base64_of_bin_file(img_path)
                    if img_data_uri:
                        # Display image, slightly smaller width
                        st.image(f"data:image/png;base64,{img_data_uri}", width=70, use_container_width=False)
 # Reduced width, use use_container_width
                    else:
                        logging.warning(f"Could not encode image for character {char_id} at path: {img_path}")
                except Exception as e:
                    logging.error(f"Error loading/displaying character image {img_path}: {e}")

    # --- Column 2: Objectives ---
    with col2:
        st.markdown(f"**Objectives (Y{GAME_END_YEAR})**") # Use bold markdown, shorter title
        objectives = st.session_state.get('game_objectives', {})
        if objectives:
            for obj_key, details in objectives.items():
                target_str = ""
                if details['target_type'] == 'percent':
                    target_str = f"{details['target_value']:.0f}%"
                elif details['target_type'] == 'index':
                     target_str = f"{details['target_value']:.0f}"
                else:
                     target_str = f"{details['target_value']}" # Default
                # Display objective using smaller text
                st.markdown(f"<small>- {details['label']}: {details['condition']} {target_str}</small>", unsafe_allow_html=True)
        else:
            st.caption("Objectives not set.")

    # Add divider below the columns
    st.sidebar.divider()


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
    def get_sparkline_data(metric_key, num_years, fetch_full_history=False): # Added fetch_full_history flag
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
            # Removed Yk_Index logging from here as calculation is post-loop

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

        # Filter out rows where the metric value is exactly zero
        if not fetch_full_history: logging.debug(f"SPARKLINE({metric_key}) DF before zero filter:\n{df}")
        # Do this *before* dropping NaNs to handle cases where zero might be valid but unwanted
        df = df[~np.isclose(df[metric_key], 0.0)]
        if not fetch_full_history: logging.debug(f"SPARKLINE({metric_key}) DF after zero filter:\n{df}")

        # Explicitly drop rows where the metric value is NaN BEFORE setting index
        # This ensures Altair receives only valid points for the y-axis
        # Important: Do this *after* potential post-loop calculations and zero filtering
        df.dropna(subset=[metric_key], inplace=True)

        # Check again if enough points remain after dropping NaNs
        # Allow returning a DataFrame with a single point
        if df.empty:
            logging.debug(f"SPARKLINE {metric_key} - Not enough valid points after dropna.")
            return None
        # Allow returning a DataFrame with a single point (handled by create_kpi_plot)
    # Removed elif len(df) < 2 check here


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
        elif metric_key == 'GD_GDP': # Keep this for the core metric display
            gd_val = latest_history_entry.get('GD', np.nan)
            y_val = latest_history_entry.get('Y', np.nan)
            if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                current_val = gd_val / y_val # Calculate the ratio
            else:
                current_val = np.nan # Cannot calculate ratio
            icon_key = "GD_GDP" # Use correct icon key
            format_func = format_percent # Use percentage format

        # Special handling for Gov Balance / GDP Ratio
        elif metric_key == 'GovBalance_GDP':
            psbr_val = latest_history_entry.get('PSBR', np.nan)
            y_val = latest_history_entry.get('Y', np.nan)
            if np.isfinite(psbr_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                current_val = -psbr_val / y_val # Calculate balance ratio
            else:
                current_val = np.nan
            icon_key = "PSBR" # Reuse deficit icon for now
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


    # --- Core Metrics Display ---
    st.sidebar.markdown("##### Core Economic Indicators")

    # Fetch current and previous values for delta calculation
    yk_val = latest_history_entry.get('Yk', np.nan)
    pi_val = latest_history_entry.get('PI', np.nan)
    er_val = latest_history_entry.get('ER', np.nan)
    rb_val = latest_history_entry.get('Rb', np.nan)
    gd_val = latest_history_entry.get('GD', np.nan)
    y_val = latest_history_entry.get('Y', np.nan)
    psbr_val = latest_history_entry.get('PSBR', np.nan)
    grk_val = latest_history_entry.get('GRk', np.nan) # Added GRk back

    yk_prev = prev_year_data.get('Yk') if prev_year_data else np.nan
    pi_prev = prev_year_data.get('PI') if prev_year_data else np.nan
    er_prev = prev_year_data.get('ER') if prev_year_data else np.nan
    rb_prev = prev_year_data.get('Rb') if prev_year_data else np.nan
    gd_prev = prev_year_data.get('GD') if prev_year_data else np.nan
    y_prev = prev_year_data.get('Y') if prev_year_data else np.nan
    psbr_prev = prev_year_data.get('PSBR') if prev_year_data else np.nan
    grk_prev = prev_year_data.get('GRk') if prev_year_data else np.nan # Added GRk back

    # Calculate deltas (handle potential division by zero or NaN)
    delta_yk_index = None # Delta for index is tricky, maybe show absolute change?
    delta_yk_percent = None if is_first_result_year else get_delta(yk_val, yk_prev) # Calculate Real GDP % Change
    delta_pi = None if is_first_result_year else get_delta_percent(pi_val, pi_prev)
    delta_unemp = None if is_first_result_year else get_delta_percent((1-er_val), (1-er_prev))
    delta_rb = None if is_first_result_year else get_delta_percent(rb_val, rb_prev)
    delta_grk = None if is_first_result_year else get_delta_percent(grk_val, grk_prev) # Added GRk back

    # Calculate current and previous GD/GDP ratio
    gd_gdp_curr = (gd_val / y_val) if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0) else np.nan
    gd_gdp_prev = (gd_prev / y_prev) if np.isfinite(gd_prev) and np.isfinite(y_prev) and not np.isclose(float(y_prev), 0) else np.nan
    delta_gd_gdp = None if is_first_result_year else get_delta_percent(gd_gdp_curr, gd_gdp_prev)

    # Calculate current and previous Gov Balance/GDP ratio
    # Note: PSBR is deficit (positive value), so balance is -PSBR
    gov_bal_gdp_curr = (-psbr_val / y_val) if np.isfinite(psbr_val) and np.isfinite(y_val) and y_val != 0 else np.nan
    gov_bal_gdp_prev = (-psbr_prev / y_prev) if np.isfinite(psbr_prev) and np.isfinite(y_prev) and y_prev != 0 else np.nan
    delta_gov_bal_gdp = None if is_first_result_year else get_delta_percent(gov_bal_gdp_curr, gov_bal_gdp_prev)


    # Display core metrics (Using original metrics from commit)
    # Display core metrics (Using original metrics from commit) - Modified Yk_Index to include delta
    display_metric_sparkline('Yk_Index', 'Real GDP Index (Y1=100)', 'Yk', lambda x: f"{x:.1f}", delta_yk_percent) # Pass pre-formatted string directly
    display_metric_sparkline('PI', 'Inflation Rate', 'PI', format_percent, delta_pi)
    display_metric_sparkline('Unemployment', 'Unemployment Rate', 'ER', format_percent, delta_unemp)
    display_metric_sparkline("GD_GDP", "Gov Debt / GDP", "GD_GDP", format_percent, delta_gd_gdp) # Moved here

    st.sidebar.divider()

    # --- Sector Expanders (Restored from commit) ---
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
    if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
        gd_gdp_val = gd_val / y_val
    else:
        logging.warning(f"Cannot calculate GD/GDP for year {st.session_state.current_year}. GD={gd_val}, Y={y_val}")

    gd_gdp_prev = np.nan
    if prev_year_data:
        gd_prev = prev_year_data.get('GD', np.nan) # Corrected syntax
        if np.isfinite(gd_prev) and np.isfinite(y_prev) and not np.isclose(float(y_prev), 0):
            gd_gdp_prev = gd_prev / y_prev
        else:
             logging.warning(f"Cannot calculate previous GD/GDP. GD_prev={gd_prev}, Y_prev={y_prev}")

    delta_gd_gdp = None if is_first_result_year else get_delta_percent(gd_gdp_val, gd_gdp_prev)

    # --- Display Government Metrics ---
    # Display Gov Balance / GDP instead of absolute deficit
    display_metric_sparkline("GovBalance_GDP", "Gov Balance / GDP", "PSBR", format_percent, delta_gov_bal_gdp)

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
        f_grk = latest_solution.get('GRk', np.nan) # Get Capital Growth Rate
        st.metric(label="Capital Stock (K)", value=format_value(f_k))
        st.metric(label="Investment (I)", value=format_value(f_i))
        st.metric(label="Retained Earnings (FUf)", value=format_value(f_fu))
        st.metric(label="Capital Growth (GRk)", value=format_percent(f_grk)) # Display GRk here

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
    # Log solutions state before attempting to plot KPIs
    solutions_exist = hasattr(st.session_state, 'sfc_model_object') and hasattr(st.session_state.sfc_model_object, 'solutions')
    solutions_len = len(st.session_state.sfc_model_object.solutions) if solutions_exist and st.session_state.sfc_model_object.solutions is not None else 0
    logging.debug(f"Year {st.session_state.current_year} YEAR_START: Before KPI plots. Solutions exist: {solutions_exist}, Length: {solutions_len}")
    if solutions_exist and solutions_len > 0:
        logging.debug(f"Solutions keys (first entry): {list(st.session_state.sfc_model_object.solutions[0].keys())[:10]}...") # Log first few keys

        # Generate KPI plots and store them in variables
        st.markdown("##### Key Economic Indicators") # Re-add header here
        row1_cols = st.columns(2)
        with row1_cols[0]:
            # Use shorter title and display immediately
            st.altair_chart(create_kpi_plot('Yk_Index', 'GDP Index (Y1=100)'), use_container_width=True)
        with row1_cols[1]:
             # Use shorter title and display immediately
            st.altair_chart(create_kpi_plot('PI', 'Inflation Rate'), use_container_width=True)

        row2_cols = st.columns(2)
        with row2_cols[0]:
             # Use shorter title and display immediately
            st.altair_chart(create_kpi_plot('Unemployment', 'Unemployment Rate'), use_container_width=True)
        with row2_cols[1]:
             # Use shorter title and display immediately
             st.altair_chart(create_kpi_plot('GD_GDP', 'Debt/GDP Ratio'), use_container_width=True)


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
if st.session_state.game_phase == "CHARACTER_SELECTION":
    st.header("Choose Your Economic Advisor")
    st.write("Select the advisor whose economic philosophy and objectives align with your strategy.")

    cols = st.columns(len(CHARACTERS))
    selected_id = st.session_state.selected_character_id

    for i, (char_id, char_data) in enumerate(CHARACTERS.items()):
        with cols[i]:
            container_class = "character-column"
            if char_id == selected_id:
                container_class += " selected"

            # Use markdown with inline style for background image if available
            img_path = char_data.get('image_path')
            img_html = ""
            if img_path:
                try:
                    img_data_uri = get_base64_of_bin_file(img_path)
                    if img_data_uri:
                        img_html = f'<img src="data:image/png;base64,{img_data_uri}" alt="{char_data["name"]}">'
                    else:
                        img_html = f'<p style="color: red;">Image not found: {img_path}</p>'
                except Exception as e:
                    img_html = f'<p style="color: red;">Error loading image: {e}</p>'
                    logging.error(f"Error loading character image {img_path}: {e}")

            # --- Objective List Generation with Icons ---
            # Mapping from objective keys to icon keys in ICON_FILENAME_MAP
            objective_icon_map = {
                "gdp_index": "Yk",
                "unemployment": "ER", # Using Employment Rate icon
                "inflation": "PI",
                "debt_gdp": "GD_GDP" # Using Gov Debt/GDP icon
            }

            # Generate objective list items HTML string, padding with empty items if needed
            objectives_list = list(char_data.get('objectives', {}).items())
            objectives_html = ""
            for j in range(3): # Always generate 3 list items
                if j < len(objectives_list):
                    obj_key, obj = objectives_list[j]
                    objectives_html += f"""<li>
                            <img src="{get_icon_data_uri(objective_icon_map.get(obj_key, ''))}" style="height: 1em; width: 1em; margin-right: 0.5em;">
                            <small>{obj['label']}: {obj['condition']} {obj['target_value']}{'%' if obj['target_type'] == 'percent' else ''}</small>
                        </li>"""
                else:
                    # Add an empty list item with a non-breaking space to maintain height
                    objectives_html += '<li><small>&nbsp;</small></li>'


            st.markdown(f"""
            <div class="{container_class}">
                <div style="flex-grow: 1;"> <!-- Wrapper for content above objectives -->
                    {img_html}
                    <h4>{char_data['name']}</h4>
                    <p><small>{char_data['description']}</small></p>
                </div>
                <div> <!-- Wrapper for objectives -->
                    <p><strong>Objectives:</strong></p>
                    <ul>
                        {objectives_html}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Selection Button
            button_label = "Selected" if char_id == selected_id else "Select"
            button_type = "primary" if char_id == selected_id else "secondary"
            # When a character button is clicked, start the game immediately
            if st.button(button_label, key=f"select_{char_id}", type=button_type, use_container_width=True):
                # Set the selected character ID first
                st.session_state.selected_character_id = char_id
                selected_id = char_id # Update local variable for immediate use

                # --- Set Game Objectives based on Character ---
                st.session_state.game_objectives = CHARACTERS[selected_id].get('objectives', {})
                logging.info(f"Character '{CHARACTERS[selected_id]['name']}' selected. Objectives set: {st.session_state.game_objectives}")

                # --- Create Deck based on Character ---
                st.session_state.deck = create_deck(character_id=selected_id)
                logging.info(f"Deck created based on character '{selected_id}'. Deck size: {len(st.session_state.deck)}")

                # --- Initial Draw ---
                st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
                    st.session_state.deck,
                    st.session_state.player_hand,
                    st.session_state.discard_pile,
                    INITIAL_HAND_SIZE
                )
                logging.info(f"Drew initial hand of {INITIAL_HAND_SIZE} cards. Hand size: {len(st.session_state.player_hand)}")

                # --- Start First Simulation (Year 0 -> Year 1) ---
                st.session_state.game_phase = "SIMULATION" # Trigger first simulation
                st.session_state.cards_selected_this_year = [] # No cards played in year 0
                st.session_state.active_events_this_year = [] # No events in year 0
                logging.info("Proceeding to first simulation (Year 0 -> Year 1).")
                st.rerun() # Rerun to start the simulation phase

    # Confirmation button and related logic removed. Game starts on character button click.


elif st.session_state.game_phase == "YEAR_START":
    logging.debug(f"--- Entering YEAR_START for Year {st.session_state.current_year} ---")
    logging.debug(f"Value of 'dilemma_processed_for_year' at phase start: {st.session_state.get('dilemma_processed_for_year', 'Not Set')}")
    # --- RESTRUCTURED DILEMMA LOGIC ---
    current_year = st.session_state.current_year
    dilemma_already_processed_this_year = st.session_state.get('dilemma_processed_for_year', -1) == current_year
    logging.debug(f"Year {current_year}: Start YEAR_START phase. Dilemma processed flag = {dilemma_already_processed_this_year}")

    # --- Step 1: Check if a dilemma needs to be selected ---
    if not dilemma_already_processed_this_year and not st.session_state.current_dilemma:
        # Only try to select if year is valid (not first or last year)
        if current_year > 0 and current_year < (GAME_END_YEAR - 1):
            advisor_id = st.session_state.get('selected_character_id')
            if advisor_id:
                dilemma_id, dilemma_data = select_dilemma(advisor_id, st.session_state.seen_dilemmas)
                if dilemma_id and dilemma_data:
                    st.session_state.current_dilemma = {"id": dilemma_id, "data": dilemma_data}
                    st.session_state.seen_dilemmas.add(dilemma_id)
                    logging.info(f"Selected new dilemma: {dilemma_id} for year {current_year}")
                    # Rerun needed to display the newly selected dilemma cleanly before card selection etc.
                    # st.rerun() # Rerun immediately after selecting a *new* dilemma
                else:
                    logging.info(f"No unseen dilemmas available for advisor '{advisor_id}' in year {current_year}.")
            else:
                logging.warning("Cannot select dilemma: advisor_id not found.")

    # --- Step 2: If a dilemma is active, display it and stop ---
    if st.session_state.current_dilemma:
        st.header(f"Year {st.session_state.current_year} - Advisor's Dilemma")
        dilemma_info = st.session_state.current_dilemma['data']
        st.subheader(dilemma_info['title'])
        st.markdown(f"_{dilemma_info['flavor_text']}_")
        st.markdown("---")
        col1, col2 = st.columns(2)
        option_a = dilemma_info['option_a']
        option_b = dilemma_info['option_b']
        with col1:
            st.markdown(f"**Option A: {option_a['name']}**")
            # --- Option A UI Enhancement ---
            add_a = option_a.get('add_cards', [])
            remove_a = option_a.get('remove_cards', [])
            tooltip_a = ""
            if add_a: tooltip_a += f"Adds: {', '.join(add_a)}\n"
            if remove_a: tooltip_a += f"Removes: {', '.join(remove_a)}"
            tooltip_a = tooltip_a.strip() # Remove trailing newline if only one effect type

            if st.button(f"Choose: {option_a['name']}", key="dilemma_a", use_container_width=True):
                # Caption moved outside this block
                logging.info(f"Dilemma {st.session_state.current_dilemma['id']} - Option A chosen.")
                # Unpack the action descriptions
                st.session_state.deck, st.session_state.discard_pile, action_descriptions = apply_dilemma_choice(
                    option_a, st.session_state.deck, st.session_state.discard_pile
                )
                st.session_state.current_dilemma = None # Clear dilemma state
                st.session_state.dilemma_processed_for_year = st.session_state.current_year # Mark as processed for this year
                # Display the action descriptions in the toast message
                display_message = "Deck modified by dilemma choice!"
                if action_descriptions:
                    display_message += "\nChanges:\n* " + "\n* ".join(action_descriptions)
                st.toast(display_message)
                st.rerun() # Rerun to proceed to normal YEAR_START (without dilemma)
            if tooltip_a: st.caption(tooltip_a) # Display tooltip content as caption
        with col2:
            st.markdown(f"**Option B: {option_b['name']}**")
            # --- Option B UI Enhancement ---
            add_b = option_b.get('add_cards', [])
            remove_b = option_b.get('remove_cards', [])
            tooltip_b = ""
            if add_b: tooltip_b += f"Adds: {', '.join(add_b)}\n"
            if remove_b: tooltip_b += f"Removes: {', '.join(remove_b)}"
            tooltip_b = tooltip_b.strip() # Remove trailing newline if only one effect type

            if st.button(f"Choose: {option_b['name']}", key="dilemma_b", use_container_width=True):
                # Caption moved outside this block
                logging.info(f"Dilemma {st.session_state.current_dilemma['id']} - Option B chosen.")
                # Unpack the action descriptions
                st.session_state.deck, st.session_state.discard_pile, action_descriptions = apply_dilemma_choice(
                    option_b, st.session_state.deck, st.session_state.discard_pile
                )
                st.session_state.current_dilemma = None # Clear dilemma state
                st.session_state.dilemma_processed_for_year = st.session_state.current_year # Mark as processed for this year
                # Display the action descriptions in the toast message
                display_message = "Deck modified by dilemma choice!"
                if action_descriptions:
                    display_message += "\nChanges:\n* " + "\n* ".join(action_descriptions)
                st.toast(display_message)
                st.rerun() # Rerun to proceed to normal YEAR_START (without dilemma)
            if tooltip_b: st.caption(tooltip_b) # Display tooltip content as caption

        # Removed deferred plot display block. Plots are now displayed immediately after creation.

    else:
        # --- Step 3: NORMAL YEAR START LOGIC (Executes only if no dilemma was active/displayed above) ---
        # Display Current Year
        st.header(f"Year {st.session_state.current_year}") # ADDED YEAR DISPLAY
        # --- Display Active Events Below Plots (Original Vertical Layout) ---
        st.markdown("##### Active Events")
        active_events = st.session_state.get('active_events_this_year', []) # Use .get for safety
        if active_events:
            num_event_cols = min(len(active_events), 3) # Max 3 columns, adjust if fewer events
            event_cols = st.columns(num_event_cols)
            event_index = 0
            for event_name in active_events:
                col_index = event_index % num_event_cols
                with event_cols[col_index]:
                    event_details = ECONOMIC_EVENTS.get(event_name, {})
                    event_desc = event_details.get('desc', 'No description available.')
                    direct_param = event_details.get('param')
                    indirect_commentary = event_details.get('indirect_effects')

                    # Use a container for each card within the column
                    with st.container():
                        # Use markdown with CSS classes for styling
                        st.markdown(f"""
                        <div class="event-card" style="height: 180px; display: flex; flex-direction: column; justify-content: space-between;"> <!-- Added fixed height and flex -->
                            <div> <!-- Content div -->
                                <div class="event-card-title">{event_name}</div>
                                <div class="event-card-desc">{event_desc}</div>
                            </div>
                            <div> <!-- Expander div -->
                                <!-- Expander will be placed here by Streamlit -->
                            </div>
                        </div>

                    """, unsafe_allow_html=True)

                        # Add expander for affected variables inside the container but outside the markdown
                        if direct_param or indirect_commentary:
                            with st.expander("Details"):
                                if direct_param:
                                    param_desc = PARAM_DESCRIPTIONS.get(direct_param, "No description available.")
                                    st.markdown(f"**Directly Affects:** `{direct_param}` ({param_desc})")
                                if indirect_commentary:
                                    st.markdown(f"**Potential Indirect Effects:** _{indirect_commentary}_")
                event_index += 1
        else:
            st.caption("None")



        # Helper to create simple KPI plots
        # Removed create_kpi_plot definition from here to move it earlier

        # Check if it's the very first year start (Year 1)
        if st.session_state.current_year == 1 and not st.session_state.history:
            st.info("Welcome to your first year as economic advisor! Review the initial state and select your policies.")

        # --- Display KPI Plots in 2x2 Grid ---
        # KPI Plots and Active Events moved before dilemma check
        st.markdown("---") # Divider

        # --- Draw Cards and Check Events (Run only once per YEAR_START phase) ---
        if "year_start_processed" not in st.session_state or st.session_state.year_start_processed != st.session_state.current_year:
            # Draw cards - Now includes discard pile
            logging.debug(f"Hand BEFORE draw_cards (Year {st.session_state.current_year}): {st.session_state.player_hand}")
            st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
                st.session_state.deck,
                st.session_state.player_hand,
                st.session_state.discard_pile,
                CARDS_TO_DRAW_PER_YEAR
            )
            logging.debug(f"Hand AFTER draw_cards (Year {st.session_state.current_year}): {st.session_state.player_hand}")
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
                    # Define card_type and card_stance *before* boost calculation
                    card_type = card_info.get('type', 'Unknown').lower()
                    card_stance = card_info.get('stance', None)
                    # --- Prepare Effect String (Revised for 'effects' list) ---
                    effect_str_parts = []
                    boost_applied_display = False # Track if *any* effect was boosted

                    # Check if character bonus applies to this card
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
                            boost_applied_display = True # Mark boost if criteria match
                            logging.debug(f"Card '{card_name}': Character bonus {bonus_multiplier_to_apply}x applies.")

                    # Iterate through the list of effects for the card
                    card_effects_list = card_info.get('effects', [])
                    if not card_effects_list:
                         logging.warning(f"Card '{card_name}' has no 'effects' list or it's empty.")

                    for effect_detail in card_effects_list:
                        param_name = effect_detail.get('param')
                        base_effect = effect_detail.get('effect')
                        logging.debug(f"Card '{card_name}': Processing effect detail - Param: '{param_name}', Base Effect: '{base_effect}'")

                        # Basic validation for this effect entry
                        if param_name and isinstance(base_effect, (int, float)) and np.isfinite(base_effect):
                            # Apply bonus multiplier
                            actual_effect = base_effect * bonus_multiplier_to_apply
                            logging.debug(f"Card '{card_name}': Param '{param_name}', Actual Effect (after bonus): {actual_effect}")

                            # Format the effect value
                            formatted_effect = format_effect(param_name, actual_effect)
                            logging.debug(f"Card '{card_name}': Param '{param_name}', Formatted Effect: '{formatted_effect}'")

                            # Get parameter description
                            param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown Parameter")
                            if param_desc == "Unknown Parameter":
                                logging.warning(f"Card '{card_name}': param_name '{param_name}' not found in PARAM_DESCRIPTIONS.")
                            else:
                                logging.debug(f"Card '{card_name}': Param '{param_name}', Description: '{param_desc}'")


                            # Add to list if valid
                            if formatted_effect != "N/A":
                                effect_str_parts.append(f"{formatted_effect} on {param_name} ({param_desc})")
                            else:
                                logging.warning(f"Card '{card_name}': format_effect returned N/A for param={param_name}, effect={actual_effect}.")
                        else:
                            logging.warning(f"Card '{card_name}': Invalid or missing effect detail skipped: {effect_detail}")

                    # Construct the final display string
                    if effect_str_parts:
                        boost_indicator = " (Boosted!)" if boost_applied_display else ""
                        # Join multiple effects with a separator, e.g., a line break or semicolon
                        effects_combined = "; ".join(effect_str_parts)
                        effect_str = f'<small><i>Effect{boost_indicator}: {effects_combined}</i></small>'
                        logging.debug(f"Card '{card_name}': Final effect string: {effect_str}")
                    else:
                        # If no valid effects were found after iterating
                        logging.debug(f"Card '{card_name}': No valid effects found in 'effects' list. Displaying 'Effect details missing'.")
                        effect_str = '<small><i>Effect details missing.</i></small>'
                    # --- End Revised Effect String Logic ---

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
                                    {effect_str}
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
        temp_model_for_param_check = create_growth_model() # Fixed potential syntax error here
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
            active_events=events_active,
            character_id=st.session_state.get('selected_character_id') # Pass character ID
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
        st.session_state.debug_last_params = final_numerical_params # Store for logging
        with st.spinner(f"Simulating Year {st.session_state.current_year + 1}..."):
            sys.stdout = NullIO()
            logging.debug(f"Attempting model.solve() for year {st.session_state.current_year + 1}...")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            # --- BEGIN SINGLE FILE LOGGING ---
            current_year = st.session_state.current_year + 1
            log_prefix = f"Year {current_year} SOLVED"

            # Log Variables
            log_output_vars = f"{log_prefix} - Variables:"
            variables_logged = False
            if hasattr(model_to_simulate, 'solutions') and model_to_simulate.solutions and len(model_to_simulate.solutions) > 0:
                last_solution = model_to_simulate.solutions[-1]
                all_vars = list(last_solution.keys()) # Get keys from the solution dict
                sorted_vars = sorted(all_vars)
                for var in sorted_vars:
                    val = last_solution.get(var, 'N/A')
                    # Format value for logging
                    val_str = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                    log_output_vars += f" | {var}={val_str}"
                variables_logged = True
            else:
                 log_output_vars += " | ERROR: Model solutions not found or empty."
            logging.info(log_output_vars)

            # Log Parameters
            log_output_params = f"{log_prefix} - Parameters Used:"
            params_logged = False
            final_params_to_log = {}
            # Retrieve parameters stored in session state before the solve step
            if hasattr(st.session_state, 'debug_last_params'):
                final_params_to_log = st.session_state.debug_last_params
            elif hasattr(st.session_state, 'current_turn_params'): # Keep fallback just in case
                 final_params_to_log = st.session_state.current_turn_params

            if final_params_to_log:
                # Also include parameters defined directly in the model object if needed
                # all_params_model = list(model_to_simulate.parameters.keys())
                # combined_param_keys = sorted(list(set(final_params_to_log.keys()) | set(all_params_model)))
                combined_param_keys = sorted(final_params_to_log.keys()) # Log only params used in solve

                for param in combined_param_keys:
                    # Prioritize value from final_params_to_log (reflects runtime changes)
                    val = final_params_to_log.get(param, 'N/A')
                    val_str = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                    log_output_params += f" | {param}={val_str}"
                params_logged = True
            else:
                 log_output_params += " | ERROR: final_params not accessible for logging"
            logging.info(log_output_params)

            if not variables_logged or not params_logged:
                 logging.error(f"Year {current_year}: Failed to log full debug information.")
            # --- END SINGLE FILE LOGGING ---
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
                    # Add hand cards to discard pile before clearing
                    st.session_state.discard_pile.extend(current_hand)
                st.session_state.player_hand = [] # Clear hand completely

            # Clear turn-specific state
            st.session_state.cards_selected_this_year = []
            st.session_state.active_events_this_year = []

            # --- Auto-advance to next YEAR_START ---
            # Check if game should end (e.g., after Year 10)
            if st.session_state.current_year + 1 >= GAME_END_YEAR: # Game ends AFTER simulating year 10
                st.session_state.current_year += 1 # Advance year to 10 for final display
                st.session_state.game_phase = "GAME_OVER"
                logging.info(f"Final simulation (Year {st.session_state.current_year}) complete. Proceeding to GAME_OVER.")
            else:
                logging.debug(f"--- End of SIMULATION for Year {st.session_state.current_year} ---")
                logging.debug(f"Value of 'dilemma_processed_for_year' BEFORE year increment: {st.session_state.get('dilemma_processed_for_year', 'Not Set')}")
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

elif st.session_state.game_phase == "GAME_OVER": # Added GAME_OVER phase logic
    st.header("Game Over!")
    st.balloons()

    # --- Evaluate Objectives ---
    objectives = st.session_state.get('game_objectives', {})
    final_results = st.session_state.history[-1] # Get results from the last year
    all_objectives_met = True
    results_summary = []

    if not objectives:
        st.warning("No game objectives were set.")
        all_objectives_met = False # Cannot win without objectives
    else:
        st.subheader("Objective Results") # Add subheader for clarity
        for obj_key, details in objectives.items():
            current_value = None
            label = details['label']
            condition = details['condition']
            target = details['target_value']
            target_type = details['target_type']

            # Get the actual value from final results
            if obj_key == "gdp_index":
                yk_val = final_results.get('Yk', np.nan)
                base_yk = st.session_state.get('base_yk')
                if base_yk and np.isfinite(yk_val) and not np.isclose(base_yk, 0):
                    current_value = (yk_val / base_yk) * 100
            elif obj_key == "unemployment":
                er_val = final_results.get('ER', np.nan)
                if np.isfinite(er_val):
                    current_value = (1 - er_val) * 100 # As percentage
            elif obj_key == "inflation":
                pi_val = final_results.get('PI', np.nan)
                if np.isfinite(pi_val):
                    current_value = pi_val * 100 # As percentage
            elif obj_key == "debt_gdp":
                gd_val = final_results.get('GD', np.nan)
                y_val = final_results.get('Y', np.nan)
                if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                    current_value = (gd_val / y_val) * 100 # As percentage

            # Check if objective met
            met = False
            if current_value is not None:
                if condition == ">=" and current_value >= target: met = True
                elif condition == "<=" and current_value <= target: met = True
                elif condition == ">" and current_value > target: met = True
                elif condition == "<" and current_value < target: met = True

            if not met:
                all_objectives_met = False

            # Format for display (CORRECTED PLACEMENT)
            current_str = "N/A"
            target_str = f"{target:.0f}"
            if current_value is not None:
                 if target_type == 'percent':
                     current_str = f"{current_value:.1f}%"
                     target_str += "%"
                 elif target_type == 'index':
                     current_str = f"{current_value:.1f}"
                 else: # Default format (CORRECTED INDENTATION)
                     current_str = f"{current_value:.1f}"

            # Append results (CORRECTED PLACEMENT)
            results_summary.append({
                "Objective": label,
                "Target": f"{condition} {target_str}",
                "Actual": current_str,
                "Met?": "✅ Yes" if met else "❌ No"
            })
        # --- End of Objective Loop ---

    # Display Summary Table (Moved outside the loop)
    if results_summary:
        st.dataframe(pd.DataFrame(results_summary).set_index("Objective"))

    # Display Win/Loss Message (Moved outside the loop)
    if all_objectives_met:
        st.success("Congratulations! You met all objectives!")
    else:
        st.error("Unfortunately, you did not meet all objectives.")

    # --- Display Final SFC Matrices (Moved after objective results) ---
    st.divider()
    st.subheader("Final Economic State (SFC Matrices)")

    # Retrieve final solutions
    final_solution = None
    second_last_solution = None
    model_state = st.session_state.get('sfc_model_object')

    if model_state and hasattr(model_state, 'solutions') and len(model_state.solutions) >= 2:
        final_solution = model_state.solutions[-1]
        second_last_solution = model_state.solutions[-2]
    elif model_state and hasattr(model_state, 'solutions') and len(model_state.solutions) == 1:
        final_solution = model_state.solutions[-1]
        second_last_solution = st.session_state.get('initial_state_dict')
        logging.warning("Game Over after 1 year, using initial state for matrix comparison.")
    else:
        logging.error("Could not retrieve sufficient solutions for Game Over matrix display.")
        st.warning("Could not display final SFC matrices due to missing simulation data.")

    # Display Matrices if solutions are available
    if final_solution:
        display_balance_sheet_matrix(final_solution)
        st.divider()
        if second_last_solution:
            display_revaluation_matrix(final_solution, second_last_solution)
            st.divider()
            display_transaction_flow_matrix(final_solution, second_last_solution)
        else:
            st.caption("Revaluation and Transaction Flow matrices require data from the previous period, which is unavailable.")

    # Option to restart? (Could be added later)
    # if st.button("Play Again?"):
    #     # Reset relevant session state keys
    #     st.session_state.clear() # Or selectively clear
    #     st.rerun()

elif st.session_state.game_phase == "SIMULATION_ERROR": # Keep this block
    # Correct year display for error message
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    if st.button("Acknowledge Error (Stops Game)"): st.stop()

else: # Keep this block
    st.error(f"Unknown game phase: {st.session_state.game_phase}")


# --- Credits and Model Explanation ---
with st.expander("Credits and Model Explanation"):
    st.markdown("""
    ### Code Credits
    This game is powered by economic modeling code from two key repositories:

    *   **pylinsolve**: A Python-based equation solving system created by Kent Barber (GitHub: kennt)
        [https://github.com/kennt/pylinsolve](https://github.com/kennt/pylinsolve)

    *   **monetary-economics**: Implementation of Stock-Flow Consistent (SFC) economic models based on Godley and Lavoie's work, also maintained by Kent Barber
        [https://github.com/kennt/monetary-economics](https://github.com/kennt/monetary-economics)

    ### About the Model Engine
    The engine uses pylinsolve, which processes textual descriptions of equations and runs solvers iteratively until converging to a solution. The system offers three solving methods: Gauss-Seidel, Newton-Raphson, and Broyden. It was specifically developed for implementing Stock-Flow Consistent (SFC) economic models.

    ### The GROWTH Model Explained
    The game is based on the **GROWTH** model from Chapter 11 of Wynne Godley and Marc Lavoie's influential 2007 book *"Monetary Economics: An Integrated Approach to Credit, Money, Income, Production and Wealth."*

    #### Key Features of the Model
    *   **Stock-Flow Consistent Framework**: The model maintains complete accounting consistency between flows (income, spending) and stocks (wealth, debt), with comprehensive balance sheets and transaction matrices.
    *   **Policy Variables as Exogenous Inputs**:
        *   Government spending grows at an exogenously determined rate
        *   Tax rates are set exogenously by policy makers
        *   The policy interest rate (bill rate) is set exogenously by the central bank
    *   **Growing Economy**: Unlike simpler models, this describes a growing economy that requires active fiscal and monetary policy management to achieve full employment without inflation.
    *   **Investment and Capital**: Firms undertake fixed investment with endogenous pricing mark-up, depending on dividend payments and their target for self-financing through retained earnings.
    *   **Equity Markets**: Firms issue stock market shares which households can purchase, creating a complete capital market.
    *   **Loan Dynamics**: Both households and firms borrow from banks, with personal loans determined as a proportion of disposable income. The model also accounts for corporate loan defaults.
    *   **Banking System**: Banks maintain capital reserves to fulfill regulatory obligations, with the loan rate determined as a mark-up on the deposit rate.

    #### Model Structure
    The economy is divided into five sectors - households, firms, banks, a central bank, and government - each with distinct functions and objectives. These sectors interact through:
    *   Production and consumption decisions
    *   Investment and saving
    *   Wage setting and price formation
    *   Portfolio allocation (money, bills, bonds, equities)
    *   Bank lending and capital requirements
    *   Government fiscal operations
    """)
# --- End Credits ---

# --- Debug Info (Optional) ---
# with st.expander("Debug Info"): st.write("Session State:", st.session_state)
