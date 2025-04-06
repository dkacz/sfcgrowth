# src/utils.py
"""Utility functions for formatting, calculations, and file handling."""

import io
import numpy as np
import base64
import os
import logging

# Import constants from config
from src.config import ICON_FILENAME_MAP, ICON_DIR, PARAM_DESCRIPTIONS

# --- Helper Classes ---
class NullIO(io.StringIO):
    """A StringIO class that ignores writes."""
    def write(self, txt):
        pass

# --- Formatting Functions ---
def format_percent(value):
    """Formats a float as a percentage string."""
    if not np.isfinite(value):
        return "N/A"
    return f"{value*100:.2f}%"

def format_value(value, precision=2):
    """Formats a float or number to a specific precision string."""
    if not np.isfinite(value):
        return "N/A"
    return f"{value:.{precision}f}"

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

# --- Delta Calculation Functions ---
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

def get_delta_points(current_val, prev_val):
    """ Helper to calculate absolute point delta string for st.metric """
    # Check for invalid inputs first
    if not np.isfinite(current_val) or prev_val is None or not np.isfinite(prev_val):
        return None

    # Handle cases where values are very close (treat as no change)
    if np.isclose(current_val, prev_val):
        return None # Or return "→ 0.0 pts" if explicit zero change is desired

    delta = current_val - prev_val
    arrow = "↑" if delta >= 0 else "↓"
    sign = "+" if delta >= 0 else "" # Explicit sign for positive/zero
    # NOTE: Original function was incomplete. Returning formatted string.
    # Consider if a different return format is needed.
    return f"{arrow} {sign}{abs(delta):.1f} pts"

def get_delta_percentage_formatted(current_val, prev_val):
    """ Helper to calculate PERCENTAGE delta string with arrow format """
    # Check for invalid inputs first
    if not np.isfinite(current_val) or prev_val is None or not np.isfinite(prev_val):
        return None

    # Handle zero previous value
    if np.isclose(prev_val, 0):
        if np.isclose(current_val, 0):
            return None # No change from zero, treat as no delta
        else:
            return "N/A" # Undefined percentage change from zero

    # Handle cases where values are very close (treat as no change)
    if np.isclose(current_val, prev_val):
        return None # Treat as no delta

    # Calculate percentage change
    # Use abs(prev_val) to avoid issues with negative base, but ensure prev_val is not zero
    if np.isclose(prev_val, 0): # Double check after initial check
        return "N/A"
    delta_pct = ((current_val - prev_val) / abs(prev_val)) * 100

    arrow = "↑" if delta_pct >= 0 else "↓"
    sign = "+" if delta_pct >= 0 else "" # Explicit sign for positive/zero
    # Format as percentage change, including sign, arrow, and one decimal place
    # Remove the extra arrow, keep sign and percentage
    return f"{sign}{delta_pct:.1f}%"

# --- Base64 Encoding Functions ---
# @st.cache_data # Removed Streamlit caching decorator
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
        # Assuming ICON_DIR is relative to the project root
        filepath = os.path.join(ICON_DIR, filename)
        base64_string = get_base64_of_bin_file(filepath)
        if base64_string:
            # Assuming PNG format, adjust if needed based on actual icon types
            file_extension = os.path.splitext(filename)[1].lower()
            mime_type = f"image/{file_extension[1:]}" if file_extension else "image/png" # Default to png
            return f"data:{mime_type};base64,{base64_string}"
    # Return a placeholder or empty string if icon not found
    return "" # Changed to return empty string

# @st.cache_data # Removed Streamlit caching decorator
def get_logo_data_uri(logo_filename="sfcgamelogo.png"):
    """Reads the logo file and returns base64 encoded data URI."""
    # Assuming logo is in the root directory relative to where the script runs
    logo_path = logo_filename
    if not os.path.exists(logo_path):
        # Try looking in 'assets' directory as a fallback
        logo_path_assets = os.path.join("assets", logo_filename)
        if os.path.exists(logo_path_assets):
            logo_path = logo_path_assets
        else:
            logging.warning(f"Logo file not found at specified path: {logo_filename} or in assets/")
            return None

    base64_string = get_base64_of_bin_file(logo_path)
    if base64_string:
        # Assuming PNG format, adjust if needed
        return f"data:image/png;base64,{base64_string}"
    else:
        logging.warning(f"Failed to encode logo file: {logo_path}")
        return None