# src/simulation_logic.py
"""Handles the core simulation step for one year."""

import streamlit as st
import logging
import copy
import sys
import numpy as np
import pandas as pd # Keep pandas import if needed for logging/analysis later

# Import project modules
from src.utils import NullIO # Import NullIO utility
from src.config import GAME_END_YEAR

# Import model components
from chapter_11_model_growth import (
    create_growth_model, growth_parameters, growth_exogenous, growth_variables
)
from pysolve.model import SolutionNotFoundError

# Import game mechanics
try:
    from game_mechanics import apply_effects
except ImportError as e:
    st.error(f"Failed to import game_mechanics in simulation_logic.py: {e}.")
    st.stop()


def run_simulation():
    """Executes the simulation for one year based on current state."""
    current_year = st.session_state.current_year
    next_year = current_year + 1
    logging.info(f"Entering SIMULATION phase for year {next_year}")

    # --- Get Previous State and Inputs ---
    prev_model = st.session_state.sfc_model_object
    cards_to_play = st.session_state.cards_selected_this_year
    events_active = st.session_state.active_events_this_year

    # Get the state dictionary from the end of the previous turn
    if current_year == 0: # First simulation uses initial dict
         latest_solution_values = st.session_state.initial_state_dict
         logging.debug("Using initial state dict as previous state for Year 1 apply_effects.")
    elif not prev_model.solutions:
         logging.error("Previous model solutions missing unexpectedly after Year 0.")
         st.error("Internal Error: Missing previous simulation results. Cannot proceed.")
         st.session_state.game_phase = "SIMULATION_ERROR" # Go to error state
         st.rerun()
         return # Stop execution
    else:
        latest_solution_values = prev_model.solutions[-1]

    # --- Calculate and Apply Parameters ---
    # Initialize base parameters correctly depending on the year
    if current_year == 0:
        base_numerical_params = {k: v for k, v in st.session_state.initial_state_dict.items() if isinstance(v, (int, float))}
        logging.debug("Base numerical parameters for Year 1 constructed from initial_state_dict.")
    else:
        base_numerical_params = copy.deepcopy(growth_parameters)
        temp_model_for_param_check = create_growth_model()
        defined_param_names = set(temp_model_for_param_check.parameters.keys())
        for key, value in growth_exogenous:
            if key in defined_param_names:
                 try: base_numerical_params[key] = float(value)
                 except: logging.warning(f"Could not convert exogenous parameter {key}={value} to float.")
        logging.debug(f"Base numerical parameters for Year {next_year} constructed from defaults.")

    final_numerical_params = {}
    try:
        final_numerical_params = apply_effects(
            base_params=base_numerical_params,
            latest_solution=latest_solution_values,
            cards_played=cards_to_play,
            active_events=events_active,
            character_id=st.session_state.get('selected_character_id')
        )
        logging.debug("Final numerical parameters calculated.")
        st.session_state.debug_last_params = final_numerical_params # Store for logging
    except Exception as e:
        st.error(f"Error during apply_effects: {e}")
        logging.exception("Error calling apply_effects:")
        st.session_state.game_phase = "SIMULATION_ERROR"
        st.rerun()
        return # Stop execution

    # --- Initialize Fresh Model, Set State, and Run Simulation ---
    model_to_simulate = create_growth_model()
    old_stdout = sys.stdout
    try:
        # 1. Set defaults
        model_to_simulate.set_values(growth_parameters)
        model_to_simulate.set_values(growth_exogenous)
        model_to_simulate.set_values(growth_variables)
        logging.debug("Set default params/vars on fresh model instance.")

        # 2. Set final parameters
        model_to_simulate.set_values(final_numerical_params)
        logging.debug("Set final numerical parameters on fresh model instance.")

        # 3. Copy History & Set Current Solution (Only if not first simulation)
        if current_year > 0:
            if not prev_model.solutions:
                 logging.error("Previous model solutions missing unexpectedly after Year 0.")
                 raise RuntimeError("Missing previous simulation results.") # Raise error to be caught
            else:
                 model_to_simulate.solutions = copy.deepcopy(prev_model.solutions)
                 logging.debug("Copied solutions history from previous model.")
                 model_to_simulate.current_solution = model_to_simulate.solutions[-1]
                 logging.debug("Set current_solution for the fresh model instance.")
        else:
             logging.debug("Year 1 simulation: Skipping history copy, letting solve() initialize.")

        # --- Run the simulation for one year ---
        with st.spinner(f"Simulating Year {next_year}..."):
            sys.stdout = NullIO() # Suppress solver output
            logging.debug(f"Attempting model.solve() for year {next_year}...")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout # Restore stdout

            # --- BEGIN SINGLE FILE LOGGING ---
            log_prefix = f"Year {next_year} SOLVED"
            variables_logged = False
            params_logged = False

            # Log Variables
            log_output_vars = f"{log_prefix} - Variables:"
            if hasattr(model_to_simulate, 'solutions') and model_to_simulate.solutions:
                last_solution = model_to_simulate.solutions[-1]
                all_vars = sorted(list(last_solution.keys()))
                for var in all_vars:
                    val = last_solution.get(var, 'N/A')
                    val_str = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                    log_output_vars += f" | {var}={val_str}"
                variables_logged = True
            else:
                 log_output_vars += " | ERROR: Model solutions not found or empty."
            logging.info(log_output_vars)

            # Log Parameters Used
            log_output_params = f"{log_prefix} - Parameters Used:"
            final_params_to_log = st.session_state.get('debug_last_params', {})
            if final_params_to_log:
                combined_param_keys = sorted(final_params_to_log.keys())
                for param in combined_param_keys:
                    val = final_params_to_log.get(param, 'N/A')
                    val_str = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                    log_output_params += f" | {param}={val_str}"
                params_logged = True
            else:
                 log_output_params += " | ERROR: debug_last_params not accessible for logging"
            logging.info(log_output_params)

            if not variables_logged or not params_logged:
                 logging.error(f"Year {next_year}: Failed to log full debug information.")
            # --- END SINGLE FILE LOGGING ---
            logging.debug(f"model.solve() completed for year {next_year}.")

            # --- Post-Solve State Update ---
            latest_sim_solution = model_to_simulate.solutions[-1]

            # Store the NEWLY SOLVED model object
            st.session_state.sfc_model_object = model_to_simulate

            # Record History
            current_results = { 'year': next_year }
            history_vars = ['Yk', 'PI', 'ER', 'GRk', 'Rb', 'Rl', 'Rm', 'BUR', 'Q', 'CAR', 'PSBR', 'GD', 'Y', 'V', 'Lhs', 'Lfs']
            for key in history_vars:
                 current_results[key] = latest_sim_solution.get(key, np.nan)
            current_results['cards_played'] = list(cards_to_play) # Record cards played this turn
            current_results['events'] = list(events_active) # Record events active this turn
            st.session_state.history.append(current_results)

            # Set base Yk after first simulation (Year 1)
            if current_year == 0 and st.session_state.base_yk is None:
                base_yk_val = latest_sim_solution.get('Yk')
                if base_yk_val is not None and np.isfinite(base_yk_val):
                    st.session_state.base_yk = base_yk_val
                    logging.info(f"Set base Yk for indexing after Year 1 simulation: {st.session_state.base_yk}")
                else:
                    logging.error("Failed to set base Yk after Year 1 simulation - Yk value invalid.")

            # Discard hand
            current_hand = st.session_state.player_hand
            if current_hand:
                logging.info(f"Discarding end-of-turn hand: {', '.join(current_hand)}")
                st.session_state.discard_pile.extend(current_hand)
            st.session_state.player_hand = [] # Clear hand

            # Clear turn-specific state
            st.session_state.cards_selected_this_year = []
            st.session_state.active_events_this_year = []
            if 'debug_last_params' in st.session_state:
                del st.session_state.debug_last_params # Clean up debug state

            # --- Advance Game State ---
            if next_year >= GAME_END_YEAR: # Game ends AFTER simulating final year
                st.session_state.current_year = next_year # Advance year for final display
                st.session_state.game_phase = "GAME_OVER"
                logging.info(f"Final simulation (Year {next_year}) complete. Proceeding to GAME_OVER.")
            else:
                st.session_state.current_year = next_year
                st.session_state.game_phase = "YEAR_START"
                logging.info(f"Simulation complete. Advancing to Year {st.session_state.current_year} YEAR_START.")

    except SolutionNotFoundError as e:
        sys.stdout = old_stdout # Restore stdout
        st.error(f"Model failed to converge for Year {next_year}. Error: {str(e)}")
        logging.error(f"SolutionNotFoundError for Year {next_year}: {e}")
        st.session_state.game_phase = "SIMULATION_ERROR"
    except Exception as e:
        sys.stdout = old_stdout # Restore stdout
        st.error(f"An unexpected error occurred during simulation for Year {next_year}: {str(e)}")
        logging.exception(f"Unexpected error in SIMULATION phase (Year {next_year}):")
        st.session_state.game_phase = "SIMULATION_ERROR"
    finally:
        sys.stdout = old_stdout # Ensure stdout is always restored
        st.rerun() # Rerun to display the next phase or error state