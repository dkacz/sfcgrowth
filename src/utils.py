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
    return f"{value*100:.1f}%"

def format_value(value, precision=2):
    """Formats a float or number to a specific precision string."""
    if not np.isfinite(value):
        return "N/A"
    return f"{value:.{precision}f}"

def format_effect(param, effect):
    """Formats the effect value nicely based on typical parameter scales.
    Handles integers without decimals (e.g., +1) and decimals only when needed (e.g., +0.5).
    """
    # --- Start: Robust Input Handling ---
    if effect is None:
        return "N/A" # Handle None explicitly

    try:
        # Explicitly convert input to a standard Python float
        numeric_effect = float(effect)
    except (ValueError, TypeError):
        # If conversion fails, log a warning and return the original value as a string
        logging.warning(f"format_effect: Could not convert effect '{effect}' (type: {type(effect)}) to float. Returning as string.")
        return str(effect)

    # Check for non-finite values *after* successful conversion
    if not np.isfinite(numeric_effect):
         return "N/A"
    # --- End: Robust Input Handling ---

    # Check if the parameter requires percentage point formatting (uses original param name)
    is_pp_param = param in ['Rbbar', 'ADDbl', 'ro', 'NCAR', 'theta', 'NPLk', 'alpha1', 'delta', 'eta0', 'Rln', 'GRg', 'GRpr', 'gamma0']

    # Determine the value to format (scale by 100 for p.p.), using the converted numeric value
    value_to_format = numeric_effect * 100 if is_pp_param else numeric_effect

    # Check if the value_to_format is effectively an integer (using a small tolerance)
    tolerance = 1e-9
    is_integer = abs(value_to_format - round(value_to_format)) < tolerance

    # --- Start: Robust Formatting ---
    try:
        # Determine the value to format (scale by 100 for p.p.), using the converted numeric value
        value_to_format = numeric_effect * 100 if is_pp_param else numeric_effect

        # Check if the value_to_format is effectively an integer (using a small tolerance)
        tolerance = 1e-9
        is_integer = abs(value_to_format - round(value_to_format)) < tolerance

        # Determine the format specifier and the value to use in the final format string
        if is_integer:
            # Format integer, manually adding sign
            int_value = int(round(value_to_format))
            sign = "+" if int_value >= 0 else ""
            formatted_number = f"{sign}{int_value}"
        else:
            # Format float, manually adding sign and using standard precision
            float_value = value_to_format
            sign = "+" if float_value >= 0 else ""
            # Use abs() to avoid double negative sign, format to 1 decimal place for p.p., 4 otherwise
            precision = 2 if is_pp_param else 4 # Increased precision for p.p.
            formatted_number = f"{sign}{abs(float_value):.{precision}f}"

    except Exception as e: # Catch any potential formatting error
        # Fallback if formatting fails unexpectedly
        logging.error(f"format_effect: Formatting failed unexpectedly for value '{effect}'. Error: {e}. Falling back to string representation.")
        # Fallback to the original unscaled value as a string
        formatted_number = str(numeric_effect)
    # --- End: Robust Formatting ---

    # Add units if necessary
    if is_pp_param:
        return f"{formatted_number} p.p."
    else:
        return formatted_number

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
     return f"{delta:+.1f} % pts" # More explicit label

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