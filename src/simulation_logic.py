from chapter_11_model_growth import Model

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


            # --- Run Baseline Simulation ---
            # Triggered after main simulation for 'next_year' is complete
            # Baseline starts from the state *at the beginning* of 'next_year'
            if next_year <= GAME_END_YEAR: # Only run if not already past the end year
                logging.info(f"Preparing to run baseline simulation starting from Year {next_year}.")
                try:
                    # Deep copy necessary states to isolate baseline run
                    original_model_id = id(st.session_state.sfc_model_object) # Capture original ID before copy
                    baseline_start_model = copy.deepcopy(st.session_state.sfc_model_object)
                    baseline_start_history = copy.deepcopy(st.session_state.history)
                    baseline_start_persistent = copy.deepcopy(st.session_state.persistent_effects)
                    baseline_start_temporary = copy.deepcopy(st.session_state.temporary_effects)
                    char_id = st.session_state.selected_character_id
                    copied_model_id = id(baseline_start_model) # Capture copied ID
                    logging.debug(f"Baseline Year {next_year}: Deep copied model state for baseline. Original ID: {original_model_id}, Copied ID: {copied_model_id}")
                    event_seq = st.session_state.full_event_sequence

                    baseline_history_results = run_baseline_simulation(
                        start_year=next_year, # Baseline starts from the year we just simulated *to*
                        initial_model_state=baseline_start_model,
                        initial_history=baseline_start_history,
                        full_event_sequence=event_seq,
                        initial_persistent_effects=baseline_start_persistent,
                        initial_temporary_effects=baseline_start_temporary,
                        character_id=char_id
                    )

                    if baseline_history_results is not None:
                        # Store results keyed by the year the baseline *starts* from
                        st.session_state.baseline_results[next_year] = baseline_history_results
                        logging.info(f"Successfully ran and stored baseline simulation starting from Year {next_year}.")
                        # Optional: Convert to DataFrame immediately if preferred
                        # st.session_state.baseline_results[next_year] = pd.DataFrame(baseline_history_results)
                        logging.debug(f"Baseline Year {next_year}: Storing results in st.session_state.baseline_results[{next_year}]")
                    else:
                        logging.error(f"Baseline simulation starting from Year {next_year} failed.")
                        # Store None or empty list to indicate failure?
                        st.session_state.baseline_results[next_year] = None

                except Exception as baseline_err:
                    logging.exception(f"Unexpected error during baseline simulation setup or execution for start year {next_year}:")
                    st.warning(f"Baseline simulation run failed for Year {next_year}. See logs.")
                    st.session_state.baseline_results[next_year] = None # Mark as failed
            # --- End Baseline Simulation ---


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


def run_baseline_simulation(start_year, initial_model_state: Model, initial_history: list, full_event_sequence: dict, initial_persistent_effects: dict, initial_temporary_effects: list, character_id: str):
    """
    Runs a baseline simulation from a given start year to the end of the game,
    assuming no policy cards are played. Uses deep copies of initial states.

    Args:
        start_year (int): The year the baseline simulation starts (e.g., Year N+1).
        initial_model_state (Model): A deep copy of the sfc_model_object at the start of start_year.
        initial_history (list): A deep copy of the game history *dictionaries* up to the start of start_year.
        full_event_sequence (dict): The pre-generated event sequence for the whole game.
        initial_persistent_effects (dict): A deep copy of persistent effects at the start of start_year.
        initial_temporary_effects (list): A deep copy of temporary effects at the start of start_year.
        character_id (str): The ID of the selected character.

    Returns:
        list: A list of result dictionaries for the baseline simulation years. Returns None on error.
    """
    logging.info(f"--- Starting Baseline Simulation from Year {start_year} to {GAME_END_YEAR} ---")
    baseline_run_history = [] # Store results for this specific baseline run
    # Use the deep copied states passed as arguments
    current_model = initial_model_state
    baseline_persistent_effects = initial_persistent_effects
    baseline_temporary_effects = initial_temporary_effects

    # Ensure the model object's solution history matches the passed history list length
    # Note: initial_model_state is assumed to be a deepcopy of the *solved* model from the *end* of year start_year-1
    if len(current_model.solutions) != len(initial_history):
         logging.warning(f"[Baseline Init] Mismatch between initial model solutions ({len(current_model.solutions)}) and initial history list ({len(initial_history)}). Using model's solutions.")
         # Potentially rebuild history list from model solutions if needed, but proceed with caution.

    for baseline_year in range(start_year, GAME_END_YEAR + 1):
        logging.debug(f"[Baseline Year {baseline_year}] Starting simulation step.")

        # --- Get Previous State and Inputs for Baseline ---
        if not current_model.solutions:
             if baseline_year == 1: # Special case for baseline starting at year 1
                 # Use the game's initial state dict (should be available via st.session_state)
                 prev_solution_values = st.session_state.get('initial_state_dict', {})
                 if not prev_solution_values:
                      logging.error("[Baseline Year 1] Initial game state dict missing!")
                      return None
                 logging.debug(f"[Baseline Year {baseline_year}] Using initial game state dict as previous state.")
             else:
                  logging.error(f"[Baseline Year {baseline_year}] Model solutions missing unexpectedly.")
                  return None # Indicate error
        else:
            prev_solution_values = current_model.solutions[-1]
            logging.debug(f"[Baseline Year {baseline_year}] Using previous baseline solution as previous state.")

        cards_to_play = [] # Baseline assumes NO cards are played
        events_active = full_event_sequence.get(baseline_year, [])
        logging.debug(f"[Baseline Year {baseline_year}] Events active: {events_active}")

        # --- Calculate and Apply Parameters (Baseline Specific) ---
        # Use default parameters as the absolute base each year
        base_numerical_params = copy.deepcopy(growth_parameters)
        temp_model_for_param_check = create_growth_model()
        defined_param_names = set(temp_model_for_param_check.parameters.keys())
        for key, value in growth_exogenous:
            if key in defined_param_names:
                 try: base_numerical_params[key] = float(value)
                 except: logging.warning(f"[Baseline Year {baseline_year}] Could not convert exogenous parameter {key}={value} to float.")

        # Mock session state for apply_effects
        original_temp_effects = st.session_state.get('temporary_effects')
        original_pers_effects = st.session_state.get('persistent_effects')
        # Set the session state effects to *our baseline's current effects* before calling apply_effects
        st.session_state.temporary_effects = baseline_temporary_effects
        st.session_state.persistent_effects = baseline_persistent_effects

        final_numerical_params = {}
        try:
            # apply_effects will read and *modify* the mocked session state effects
            final_numerical_params = apply_effects(
                base_params=base_numerical_params,
                latest_solution=prev_solution_values,
                cards_played=cards_to_play, # Crucially empty
                active_events=events_active,
                character_id=character_id
            )
            logging.debug(f"[Baseline Year {baseline_year}] Final numerical parameters calculated.")
            # IMPORTANT: Capture the modified effects from the mocked session state back into our baseline variables
            baseline_temporary_effects = st.session_state.temporary_effects
            baseline_persistent_effects = st.session_state.persistent_effects

        except Exception as e:
            logging.error(f"[Baseline Year {baseline_year}] Error during apply_effects: {e}")
            st.session_state.temporary_effects = original_temp_effects # Restore before returning
            st.session_state.persistent_effects = original_pers_effects
            return None
        finally:
             # Restore original session state effects ALWAYS
             st.session_state.temporary_effects = original_temp_effects
             st.session_state.persistent_effects = original_pers_effects

        # --- Initialize Fresh Model, Set State, and Run Simulation (Baseline Specific) ---
        model_to_simulate = create_growth_model()
        old_stdout = sys.stdout
        try:
            # 1. Set defaults
            model_to_simulate.set_values(growth_parameters)
            model_to_simulate.set_values(growth_exogenous)
            model_to_simulate.set_values(growth_variables)

            # 2. Set final parameters calculated for baseline
            model_to_simulate.set_values(final_numerical_params)

            # 3. Copy History & Set Current Solution from *baseline's* history
            # The 'current_model' object holds the baseline's evolving state
            if current_model.solutions:
                 model_to_simulate.solutions = copy.deepcopy(current_model.solutions)
                 model_to_simulate.current_solution = model_to_simulate.solutions[-1]
                 logging.debug(f"[Baseline Year {baseline_year}] Copied baseline solutions history ({len(model_to_simulate.solutions)} entries).")
            else:
                 logging.debug(f"[Baseline Year {baseline_year}] No previous baseline solutions to copy.")

            # --- Run the simulation for one baseline year ---
            sys.stdout = NullIO()
            logging.debug(f"[Baseline Year {baseline_year}] Attempting model.solve()...")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout
            logging.debug(f"[Baseline Year {baseline_year}] model.solve() completed.")

            # --- Post-Solve State Update (Baseline Specific) ---
            latest_sim_solution = model_to_simulate.solutions[-1]

            # Update the baseline's model object for the next iteration's history copy
            current_model = model_to_simulate

            # Record Baseline History
            current_results = { 'year': baseline_year }
            history_vars = ['Yk', 'PI', 'ER', 'GRk', 'Rb', 'Rl', 'Rm', 'BUR', 'Q', 'CAR', 'PSBR', 'GD', 'Y', 'V', 'Lhs', 'Lfs']
            for key in history_vars:
                 current_results[key] = latest_sim_solution.get(key, np.nan)
            current_results['cards_played'] = [] # Explicitly empty
            current_results['events'] = list(events_active)
            baseline_run_history.append(current_results)
            logging.debug(f"[Baseline Year {baseline_year}] Result appended to baseline history.")

        except SolutionNotFoundError as e:
            sys.stdout = old_stdout
            logging.error(f"[Baseline Year {baseline_year}] Model failed to converge. Error: {str(e)}")
            return None
        except Exception as e:
            sys.stdout = old_stdout
            logging.error(f"[Baseline Year {baseline_year}] An unexpected error occurred during simulation: {str(e)}")
            logging.exception(f"Unexpected error in baseline simulation (Year {baseline_year}):")
            return None
        finally:
            sys.stdout = old_stdout

    logging.info(f"--- Finished Baseline Simulation from Year {start_year}. Recorded {len(baseline_run_history)} years. ---")
    return baseline_run_history
