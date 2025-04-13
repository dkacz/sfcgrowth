# src/simulation_logic.py
"""Handles the core simulation step for one year and baseline calculations."""

import streamlit as st
import logging
import copy
import sys
import numpy as np
import pandas as pd # Keep pandas import if needed for logging/analysis later

# Import project modules
from src.utils import NullIO # Import NullIO utility
from src.config import GAME_END_YEAR

# Import specific calculators if needed elsewhere, or keep for clarity
from src.objective_evaluator import (
    calculate_gdp_index, calculate_unemployment_rate,
    calculate_inflation_rate, calculate_debt_gdp_ratio, calculate_kpis
)
# Import model components
from chapter_11_model_growth import (
    create_growth_model, growth_parameters, growth_exogenous, growth_variables, Model
)
from pysolve.model import SolutionNotFoundError

# Import game mechanics
try:
    from game_mechanics import apply_effects
except ImportError as e:
    st.error(f"Failed to import game_mechanics in simulation_logic.py: {e}.")
    st.stop()


def run_simulation_step():
    """Executes the simulation for one year based on current state."""
    current_year = st.session_state.current_year
    next_year = current_year + 1
    logging.info(f"Entering SIMULATION phase for year {next_year}")

    # --- Get Previous State and Inputs ---
    prev_model = st.session_state.sfc_model_object
    cards_to_play = st.session_state.cards_selected_this_year
    events_active = st.session_state.active_events_this_year # Carry-over/player-triggered
    # Get scheduled economic events for the year being simulated (next_year)
    scheduled_events = st.session_state.full_event_sequence.get(next_year, [])
    logging.debug(f"[Actual Run Y{next_year}] Fetched scheduled events: {scheduled_events}")
    # Combine with carry-over/player-triggered events
    combined_events = events_active + scheduled_events
    logging.debug(f"[Actual Run Y{next_year}] Combined events for apply_effects: {combined_events}")

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
        # Pass the current state dictionaries and capture the updated ones
        # --- DETAILED COMPARISON LOGGING: Actual Run Pre-apply_effects ---
        logging.info(f"[Actual Run Y{next_year}] Pre-apply_effects: latest_solution_values = {latest_solution_values}")
        logging.info(f"[Actual Run Y{next_year}] Pre-apply_effects: persistent_effects_state = {st.session_state.persistent_effects}")
        logging.info(f"[Actual Run Y{next_year}] Pre-apply_effects: temporary_effects_state = {st.session_state.temporary_effects}")
        # --- END DETAILED COMPARISON LOGGING ---

        # --- High-Precision Logging for Persistent Effects ---\n        persistent_effects_to_log = st.session_state.persistent_effects\n        log_persistent_state_precise_dict = {}\n        for key, value in persistent_effects_to_log.items():\n            if isinstance(value, float):\n                log_persistent_state_precise_dict[key] = \"{:.18f}\".format(value)\n            else:\n                log_persistent_state_precise_dict[key] = value\n        log_message = f\"[Actual Run Y{next_year}] Pre-apply_effects (HIGH PRECISION): persistent_effects_state = {log_persistent_state_precise_dict}\"\n        logging.info(log_message)\n        # --- End High-Precision Logging ---\n
        final_numerical_params, updated_persistent_effects, updated_temporary_effects = apply_effects(
            base_params=base_numerical_params,
            latest_solution=latest_solution_values, # Pass the previous solution
            persistent_effects_state=copy.deepcopy(st.session_state.persistent_effects), # Pass DEEP COPY of persistent state
            temporary_effects_state=st.session_state.temporary_effects,   # Pass current temporary state
            cards_played=cards_to_play,
            active_events=combined_events, # Use combined list
            character_id=st.session_state.get('selected_character_id')
        )
        # Update session state with the modified effects lists/dicts
        st.session_state.persistent_effects = updated_persistent_effects
        st.session_state.temporary_effects = updated_temporary_effects
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
                 logging.debug(f"Copied {len(model_to_simulate.solutions)} solutions history from previous model.")
                 model_to_simulate.current_solution = model_to_simulate.solutions[-1]
                 logging.debug("Set current_solution for the fresh model instance.")
        else:
             logging.debug("Year 1 simulation: Skipping history copy, letting solve() initialize.")
             model_to_simulate.solutions = [] # Ensure it's an empty list for year 1

        # --- DETAILED LOGGING: Pre-Solve State (Actual Run) ---
        log_msg_act = f"[Actual Run Y{next_year}] Pre-Solve State:"
        log_msg_act += f"\n  Params (Sample): theta={final_numerical_params.get('theta', 'N/A'):.4f}, GRg={final_numerical_params.get('GRg', 'N/A'):.4f}, Rbbar={final_numerical_params.get('Rbbar', 'N/A'):.4f}, ADDbl={final_numerical_params.get('ADDbl', 'N/A'):.4f}"
        if latest_solution_values:
             y_lag_key = '_Y__1' if '_Y__1' in latest_solution_values else 'Y'
             gd_lag_key = '_GD__1' if '_GD__1' in latest_solution_values else 'GD'
             v_lag_key = '_V__1' if '_V__1' in latest_solution_values else 'V'
             y_val = latest_solution_values.get(y_lag_key, 'N/A')
             gd_val = latest_solution_values.get(gd_lag_key, 'N/A')
             v_val = latest_solution_values.get(v_lag_key, 'N/A')
             y_str = f"{y_val:.2f}" if isinstance(y_val, (int, float)) else str(y_val)
             gd_str = f"{gd_val:.2f}" if isinstance(gd_val, (int, float)) else str(gd_val)
             v_str = f"{v_val:.2f}" if isinstance(v_val, (int, float)) else str(v_val)
             log_msg_act += f"\n  Lagged Vars (Sample): {y_lag_key}={y_str}, {gd_lag_key}={gd_str}, {v_lag_key}={v_str}"
        else:
             log_msg_act += f"\n  Lagged Vars: N/A (Year 1 or missing prev solution)"
        logging.info(log_msg_act)
        log_params_act = {k: final_numerical_params.get(k, 'N/A') for k in ['alpha1', 'GRg', 'theta', 'Rbbar', 'RA', 'ADDbl']}
        log_prev_vars_act = {}
        if latest_solution_values:
            yk_lag_key = '_Yk__1' if next_year > 1 and '_Yk__1' in latest_solution_values else 'Yk'
            pi_lag_key = '_PI__1' if next_year > 1 and '_PI__1' in latest_solution_values else 'PI'
            gd_lag_key = '_GD__1' if next_year > 1 and '_GD__1' in latest_solution_values else 'GD'
            v_lag_key = '_V__1' if next_year > 1 and '_V__1' in latest_solution_values else 'V'
            log_prev_vars_act = {
                yk_lag_key: latest_solution_values.get(yk_lag_key, 'N/A'),
                pi_lag_key: latest_solution_values.get(pi_lag_key, 'N/A'),
                gd_lag_key: latest_solution_values.get(gd_lag_key, 'N/A'),
                v_lag_key: latest_solution_values.get(v_lag_key, 'N/A')
            }
        logging.info(f"[Actual Run Y{next_year}] PRE-SOLVE DETAILED: Params={log_params_act}, PrevVars={log_prev_vars_act}")
        # --- End Detailed Logging ---

        # --- DETAILED COMPARISON LOGGING: Actual Run Pre-solve ---
        logging.info(f"[Actual Run Y{next_year}] Pre-solve: final_numerical_params = {final_numerical_params}")
        # --- END DETAILED COMPARISON LOGGING ---

        # --- Run the simulation for one year ---
        with st.spinner(f"Simulating Year {next_year}..."):
            sys.stdout = NullIO() # Suppress solver output
            logging.debug(f"Attempting model.solve() for year {next_year}...")
            logging.debug(f"[Actual Run Y{next_year}] Solver history length before solve: {len(model_to_simulate.solutions)}")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout # Restore stdout
            logging.debug(f"model.solve() completed for year {next_year}.")

            # --- Post-Solve State Update ---
            latest_sim_solution = model_to_simulate.solutions[-1]

            # Store the NEWLY SOLVED model object
            st.session_state.sfc_model_object = model_to_simulate

            # --- Tolerance Check for Persistent Effects ---
            tolerance = 1e-15
            keys_zeroed = []
            # Use list(items()) to allow modification during iteration
            persistent_effects_dict = st.session_state.persistent_effects
            for key, value in list(persistent_effects_dict.items()):
                if isinstance(value, float) and abs(value) < tolerance and value != 0.0:
                    persistent_effects_dict[key] = 0.0
                    keys_zeroed.append(f"{key} ({value:.2e} -> 0.0)")
            if keys_zeroed:
                logging.debug(f"[Tolerance Check Y{next_year}] Zeroed out near-zero persistent effects: {', '.join(keys_zeroed)}")
            # --- End Tolerance Check ---

            # Record History
            history_entry = copy.deepcopy(latest_sim_solution)
            history_entry['year'] = next_year
            history_entry['played_cards'] = list(cards_to_play)
            history_entry['events'] = list(combined_events) # Store the combined list of events applied
            history_entry['persistent_effects'] = copy.deepcopy(st.session_state.persistent_effects)
            history_entry['temporary_effects'] = copy.deepcopy(st.session_state.temporary_effects)

            # --- Calculate and Add KPIs to the history entry ---
            base_yk = st.session_state.get('base_yk') # Needed for GDP Index
            calculate_kpis(history_entry, base_yk) # Modifies history_entry in-place

            # Log a sample of the keys being appended
            log_keys_sample = list(history_entry.keys())[:10] + ['...'] if len(history_entry) > 10 else list(history_entry.keys())
            logging.debug(f"Appending full solution to history for Year {next_year}. Keys sample: {log_keys_sample}")
            logging.debug(f"History entry created for Year {next_year}. Persistent effects stored: {history_entry.get('persistent_effects')}")
            st.session_state.history.append(history_entry)

            # --- Store Played Cards History for Baseline Runs ---
            if 'actual_played_cards_history' not in st.session_state:
                st.session_state.actual_played_cards_history = {}
            st.session_state.actual_played_cards_history[next_year] = list(cards_to_play)
            logging.debug(f"Stored played cards for Year {next_year} in actual_played_cards_history: {st.session_state.actual_played_cards_history[next_year]}")
            # --- End Store Played Cards ---

            # --- DETAILED LOGGING: Key Vars & KPIs After Actual Solve ---
            log_solved_vars_act = {k: history_entry.get(k, 'N/A') for k in ['Yk', 'PI', 'GD', 'V']}
            log_kpis_act = {k: history_entry.get(k, 'N/A') for k in ['Yk_Index', 'Inflation', 'GD_GDP', 'Unemployment']}
            logging.info(f"[Actual Run Y{next_year}] POST-SOLVE DETAILED: SolvedVars={log_solved_vars_act}, KPIs={log_kpis_act}")
            # --- End Detailed Logging ---

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


            # Baseline simulations are now run only at GAME_OVER


            # --- Advance Game State ---
            if next_year >= GAME_END_YEAR: # Game ends AFTER simulating final year
                st.session_state.current_year = next_year # Advance year for final display
                # Baseline simulations are now triggered by the button in ui_game_over.py

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


# --- REFACTORED Baseline Simulation Function ---
def run_baseline_simulation(
    start_year: int, # Year to skip policies
    actual_game_history: list, # List of dicts from st.session_state.history
    initial_game_state_dict: dict, # Dict from st.session_state.initial_state_dict (for year 0 state)
    full_event_sequence: dict,
    character_id: str,
    actual_played_cards_history: dict,
    game_base_yk: float # Pass the base Yk from the actual run
):
    """
    Runs a baseline simulation from a given start year to the end of the game,
    mirroring the actual simulation logic but skipping policy cards for start_year.

    Args:
        start_year (int): The year whose policy impact is being isolated (cards skipped this year).
        actual_game_history (list): The list of history dictionaries from the actual game run.
        initial_game_state_dict (dict): The initial state dictionary for Year 0.
        full_event_sequence (dict): The pre-generated event sequence.
        character_id (str): The ID of the selected character.
        actual_played_cards_history (dict): Maps year number to list of cards played in the actual game.
        game_base_yk (float): The base Yk value calculated after Year 1 in the actual run.

    Returns:
        list: A list of result dictionaries for the baseline simulation years. Returns None on error.
    """
    logging.info(f"--- Starting REFACTORED Baseline Simulation from Year {start_year} to {GAME_END_YEAR} ---")
    baseline_run_results = [] # Store results {year: solution_dict}

    # Initialize baseline-specific effect states using the state *before* start_year
    if start_year == 1:
        baseline_persistent_effects = {}
        baseline_temporary_effects = []
        logging.debug(f"[Baseline Start Year {start_year}] Initializing effects as empty.")
    elif len(actual_game_history) >= start_year - 1:
         # Get state from end of year start_year - 1 (index start_year - 2)
         prev_actual_state = actual_game_history[start_year - 2]
         baseline_persistent_effects = copy.deepcopy(prev_actual_state.get('persistent_effects', {}))
         baseline_temporary_effects = copy.deepcopy(prev_actual_state.get('temporary_effects', []))
         logging.debug(f"[Baseline Start Year {start_year}] Initializing effects from actual history index {start_year - 2}.")
    else:
         logging.error(f"[Baseline Start Year {start_year}] Cannot initialize baseline effects: actual_game_history length ({len(actual_game_history)}) is too short.")
         return None

    logging.debug(f"[Baseline Start Year {start_year}] Initial persistent effects: {baseline_persistent_effects}")
    logging.debug(f"[Baseline Start Year {start_year}] Initial temporary effects: {baseline_temporary_effects}")

    for baseline_year in range(start_year, GAME_END_YEAR + 1):
        logging.debug(f"[Baseline Year {baseline_year}] Starting simulation step.")

        # 1. Get Previous State (from actual history or previous baseline step)
        # This determines the starting variable values and the history for the solver
        previous_solver_solutions = []
        if baseline_year == 1: # Special case: use initial game state dict as the 'previous solution'
            latest_solution_values = copy.deepcopy(initial_game_state_dict)
            previous_solver_solutions = [] # No history before year 1
            logging.debug(f"[Baseline Year {baseline_year}] Using initial_game_state_dict as previous state. No solver history.")
        elif baseline_year == start_year: # First step of this specific baseline run
             # Use the state from the *actual* run at the end of year baseline_year - 1
             history_index = baseline_year - 2 # -1 for 0-based, -1 for previous year
             if len(actual_game_history) > history_index:
                 latest_solution_values = copy.deepcopy(actual_game_history[history_index])
                 # Use the actual game history up to this point for the solver
                 previous_solver_solutions = copy.deepcopy(actual_game_history[:history_index+1]) # Include the state we are starting from
                 logging.debug(f"[Baseline Year {baseline_year}] Using actual history index {history_index} as previous state. Using actual history slice [: {history_index+1}] for solver.")
             else:
                 logging.error(f"[Baseline Year {baseline_year}] Cannot get previous state: actual_game_history length ({len(actual_game_history)}) too short for index {history_index}.")
                 return None
        else: # Subsequent baseline steps use the previous baseline result
            if not baseline_run_results:
                 logging.error(f"[Baseline Year {baseline_year}] Cannot get previous state: baseline_run_results is empty.")
                 return None
            latest_solution_values = baseline_run_results[-1] # Get the solution dict from previous baseline step
            # Use the history built by this baseline run for the solver
            previous_solver_solutions = copy.deepcopy(baseline_run_results)
            logging.debug(f"[Baseline Year {baseline_year}] Using previous baseline step result as previous state. Using baseline history (len {len(previous_solver_solutions)}) for solver.")

        # 2. Determine Cards & Events
        cards_to_play = [] if baseline_year == start_year else actual_played_cards_history.get(baseline_year, [])
        # Use events from the actual game history for this year
        history_index_for_events = baseline_year - 1 # 0-based index for the year being simulated
        if len(actual_game_history) > history_index_for_events:
             events_active = actual_game_history[history_index_for_events].get('events', [])
        else:
             logging.warning(f"[Baseline Year {baseline_year}] Could not retrieve events from actual_game_history index {history_index_for_events}. Using empty list.")
             events_active = []
        logging.debug(f"[Baseline Year {baseline_year}] Cards to play: {cards_to_play}")
        logging.debug(f"[Baseline Year {baseline_year}] Events active: {events_active}")

        # 3. Calculate Base Params (Mimic actual run)
        if baseline_year == 1:
             base_numerical_params = {k: v for k, v in initial_game_state_dict.items() if isinstance(v, (int, float))}
             logging.debug(f"[Baseline Year {baseline_year}] Using initial state for base params.")
        else:
             base_numerical_params = copy.deepcopy(growth_parameters)
             temp_model_for_param_check = create_growth_model()
             defined_param_names = set(temp_model_for_param_check.parameters.keys())
             for key, value in growth_exogenous:
                 if key in defined_param_names:
                      try: base_numerical_params[key] = float(value)
                      except: logging.warning(f"[Baseline Year {baseline_year}] Could not convert exogenous parameter {key}={value} to float.")
             logging.debug(f"[Baseline Year {baseline_year}] Using defaults for base params.")

        # 4. Apply Effects (using local baseline effect states)
        final_numerical_params = {}
        try:
            logging.debug(f"[Baseline Year {baseline_year}] BEFORE apply_effects: baseline_persistent_effects = {baseline_persistent_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] BEFORE apply_effects: baseline_temporary_effects = {baseline_temporary_effects}")

            # --- DETAILED COMPARISON LOGGING: Baseline Run Pre-apply_effects ---
            # Note: 'latest_solution_values' holds the current state for this baseline year step
            logging.info(f"[Baseline Run Y{baseline_year} (Start Y{start_year})] Pre-apply_effects: current_solution_values = {latest_solution_values}") 
            logging.info(f"[Baseline Run Y{baseline_year} (Start Y{start_year})] Pre-apply_effects: current_persistent_effects = {baseline_persistent_effects}")
            logging.info(f"[Baseline Run Y{baseline_year} (Start Y{start_year})] Pre-apply_effects: current_temporary_effects = {baseline_temporary_effects}")
            # --- END DETAILED COMPARISON LOGGING ---


            final_numerical_params, updated_persistent, updated_temporary = apply_effects(
                base_params=base_numerical_params,
                latest_solution=latest_solution_values,
                persistent_effects_state=baseline_persistent_effects, # Use local baseline state
                temporary_effects_state=baseline_temporary_effects,   # Use local baseline state
                cards_played=cards_to_play,
                active_events=events_active,
                character_id=character_id
            )
            # Update local baseline effect states for next iteration
            baseline_persistent_effects = updated_persistent
            baseline_temporary_effects = updated_temporary
            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: baseline_persistent_effects = {baseline_persistent_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: baseline_temporary_effects = {baseline_temporary_effects}")

        except Exception as e:
            logging.exception(f"[Baseline Year {baseline_year}] Error during apply_effects:")
            return None

        # 5. Initialize Fresh Model
        model_to_simulate = create_growth_model()

        # 6. Set Model State (Mimic actual run)
        old_stdout = sys.stdout
        try:
            model_to_simulate.set_values(growth_parameters)
            model_to_simulate.set_values(growth_exogenous)
            model_to_simulate.set_values(growth_variables)
            model_to_simulate.set_values(final_numerical_params)
            logging.debug(f"[Baseline Year {baseline_year}] Set defaults and final params.")

            # Set Solver History (Crucial Change!)
            model_to_simulate.solutions = previous_solver_solutions # Use the history determined in step 1
            if model_to_simulate.solutions:
                 model_to_simulate.current_solution = model_to_simulate.solutions[-1]
                 logging.debug(f"[Baseline Year {baseline_year}] Set solver history (length {len(model_to_simulate.solutions)}) and current_solution.")
            else:
                 logging.debug(f"[Baseline Year {baseline_year}] Starting solve with empty history.")


            # --- DETAILED LOGGING: Pre-Solve State (Baseline Run) ---
            log_msg_bl = f"[Baseline Y{baseline_year} (from Y{start_year} start)] Pre-Solve State:"
            log_msg_bl += f"\n  Params (Sample): theta={final_numerical_params.get('theta', 'N/A'):.4f}, GRg={final_numerical_params.get('GRg', 'N/A'):.4f}, Rbbar={final_numerical_params.get('Rbbar', 'N/A'):.4f}, ADDbl={final_numerical_params.get('ADDbl', 'N/A'):.4f}"
            if latest_solution_values:
                 y_lag_key = '_Y__1' if '_Y__1' in latest_solution_values else 'Y'
                 gd_lag_key = '_GD__1' if '_GD__1' in latest_solution_values else 'GD'
                 v_lag_key = '_V__1' if '_V__1' in latest_solution_values else 'V'
                 y_val = latest_solution_values.get(y_lag_key, 'N/A')
                 gd_val = latest_solution_values.get(gd_lag_key, 'N/A')
                 v_val = latest_solution_values.get(v_lag_key, 'N/A')
                 y_str = f"{y_val:.2f}" if isinstance(y_val, (int, float)) else str(y_val)
                 gd_str = f"{gd_val:.2f}" if isinstance(gd_val, (int, float)) else str(gd_val)
                 v_str = f"{v_val:.2f}" if isinstance(v_val, (int, float)) else str(v_val)
                 log_msg_bl += f"\n  Lagged Vars (Sample): {y_lag_key}={y_str}, {gd_lag_key}={gd_str}, {v_lag_key}={v_str}"
            else:
                 log_msg_bl += f"\n  Lagged Vars: N/A (Missing prev solution)"
            logging.info(log_msg_bl)
            log_params_bl = {k: final_numerical_params.get(k, 'N/A') for k in ['alpha1', 'GRg', 'theta', 'Rbbar', 'RA', 'ADDbl']}
            log_prev_vars_bl = {}
            if latest_solution_values:
                 yk_lag_key = '_Yk__1' if baseline_year > 1 and '_Yk__1' in latest_solution_values else 'Yk'
                 pi_lag_key = '_PI__1' if baseline_year > 1 and '_PI__1' in latest_solution_values else 'PI'
                 gd_lag_key = '_GD__1' if baseline_year > 1 and '_GD__1' in latest_solution_values else 'GD'
                 v_lag_key = '_V__1' if baseline_year > 1 and '_V__1' in latest_solution_values else 'V'
                 log_prev_vars_bl = {
                     yk_lag_key: latest_solution_values.get(yk_lag_key, 'N/A'),
                     pi_lag_key: latest_solution_values.get(pi_lag_key, 'N/A'),
                     gd_lag_key: latest_solution_values.get(gd_lag_key, 'N/A'),
                     v_lag_key: latest_solution_values.get(v_lag_key, 'N/A')
                 }
            logging.info(f"[Baseline Y{baseline_year} (from Y{start_year} start)] PRE-SOLVE DETAILED: Params={log_params_bl}, PrevVars={log_prev_vars_bl}")
            # --- End Detailed Logging ---

            # --- DETAILED COMPARISON LOGGING: Baseline Run Pre-solve ---
            logging.info(f"[Baseline Run Y{baseline_year} (Start Y{start_year})] Pre-solve: final_numerical_params = {final_numerical_params}")
            # --- END DETAILED COMPARISON LOGGING ---


            # 7. Solve
            sys.stdout = NullIO()
            logging.debug(f"[Baseline Year {baseline_year}] Attempting model.solve(). Solver history length: {len(model_to_simulate.solutions)}")
            # Convergence debug logging removed.
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout
            logging.debug(f"[Baseline Year {baseline_year}] model.solve() completed.")

            # 8. Store Results
            solved_solution = model_to_simulate.solutions[-1]
            # Calculate KPIs using passed game_base_yk
            if game_base_yk is not None:
                 calculate_kpis(solved_solution, game_base_yk) # Modifies solved_solution
                 logging.debug(f"[Baseline Year {baseline_year}] KPIs calculated using game_base_yk={game_base_yk}.")
            else:
                 # Ensure keys exist even if calculation failed
                 solved_solution.setdefault('Yk_Index', None)
                 solved_solution.setdefault('Unemployment', None)
                 solved_solution.setdefault('Inflation', None)
                 solved_solution.setdefault('GD_GDP', None)
                 logging.warning(f"[Baseline Year {baseline_year}] Could not calculate KPIs due to missing game_base_yk.")

            # Add metadata
            solved_solution['year'] = baseline_year
            solved_solution['baseline_start_year'] = start_year # Add metadata for clarity
            solved_solution['played_cards'] = list(cards_to_play) # Log cards used this step
            solved_solution['events'] = list(events_active)
            # Store the persistent and temporary effects state *after* apply_effects for this baseline year
            solved_solution['persistent_effects'] = copy.deepcopy(baseline_persistent_effects)
            solved_solution['temporary_effects'] = copy.deepcopy(baseline_temporary_effects)
            # Store the full solution dict for this baseline year
            baseline_run_results.append(solved_solution)

            # --- DETAILED LOGGING: Key Vars & KPIs After Baseline Solve ---
            log_solved_vars_bl = {k: solved_solution.get(k, 'N/A') for k in ['Yk', 'PI', 'GD', 'V']}
            log_kpis_bl = {k: solved_solution.get(k, 'N/A') for k in ['Yk_Index', 'Inflation', 'GD_GDP', 'Unemployment']}
            logging.info(f"[Baseline Y{baseline_year} (from Y{start_year} start)] POST-SOLVE DETAILED: SolvedVars={log_solved_vars_bl}, KPIs={log_kpis_bl}")
            # --- End Detailed Logging ---

        except SolutionNotFoundError as e:
            sys.stdout = old_stdout
            logging.error(f"[Baseline Year {baseline_year}] Model failed to converge. Error: {str(e)}")
            return None # Indicate failure
        except Exception as e:
            sys.stdout = old_stdout
            logging.exception(f"[Baseline Year {baseline_year}] An unexpected error occurred during simulation:")
            return None
        finally:
            sys.stdout = old_stdout # Ensure stdout is always restored

    logging.info(f"--- Finished REFACTORED Baseline Simulation from Year {start_year}. Recorded {len(baseline_run_results)} years. ---")
    return baseline_run_results

# --- (Keep the rest of the file unchanged) ---
