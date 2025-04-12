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

# Import specific calculators if needed elsewhere, or keep for clarity
from src.objective_evaluator import (
    calculate_gdp_index, calculate_unemployment_rate,
    calculate_inflation_rate, calculate_debt_gdp_ratio
)
# Import the main KPI calculation function and streamlit
from src.objective_evaluator import calculate_kpis # Use src. not relative .
import streamlit as st # Added for accessing session state
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
            # Start with the complete solution dictionary from the model
            history_entry = copy.deepcopy(latest_sim_solution)

            # Add metadata
            history_entry['year'] = next_year
            # Use the correct variable 'cards_played' which holds the selected cards for the turn
            history_entry['played_cards'] = list(cards_to_play) # Use the correct variable name
            history_entry['events'] = list(events_active) # Record events active this turn
            history_entry['persistent_effects'] = copy.deepcopy(st.session_state.persistent_effects)
            history_entry['temporary_effects'] = copy.deepcopy(st.session_state.temporary_effects)

            # --- Calculate and Add KPIs to the history entry ---
            base_yk = st.session_state.get('base_yk') # Needed for GDP Index
            # Use history_entry (which contains the necessary raw values like Yk, Y, GD) for KPI calculations
            history_entry['Yk_Index'] = calculate_gdp_index(history_entry, base_yk)
            history_entry['Unemployment'] = calculate_unemployment_rate(history_entry)
            history_entry['Inflation'] = calculate_inflation_rate(history_entry) # Already a %
            history_entry['GD_GDP'] = calculate_debt_gdp_ratio(history_entry)
            # Note: Raw 'PI' is already in history_entry from the solution

            # Log a sample of the keys being appended
            log_keys_sample = list(history_entry.keys())[:10] + ['...'] if len(history_entry) > 10 else list(history_entry.keys())
            logging.debug(f"Appending full solution to history for Year {next_year}. Keys sample: {log_keys_sample}")
            st.session_state.history.append(history_entry)

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
                        initial_state_dict=baseline_start_model.solutions[-1] if baseline_start_model.solutions else None,
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


def run_baseline_simulation(start_year, initial_state_dict, initial_history, full_event_sequence, initial_persistent_effects, initial_temporary_effects, character_id):
    """
    Runs a baseline simulation from a given start year to the end of the game,
    assuming no policy cards are played. Uses deep copies of initial states.

    Args:
        start_year (int): The year the baseline simulation starts (e.g., Year N+1).
        initial_state_dict (dict): A deep copy of the state dictionary at the start of start_year.
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
    # We will manage the model object internally for the baseline run
    baseline_persistent_effects = initial_persistent_effects
    baseline_temporary_effects = initial_temporary_effects
    # The 'current_model' will be created/updated inside the loop
    current_model = None # Initialize
    logging.debug(f"[Baseline Start Year {start_year}] Initial state dict keys (sample): {list(initial_state_dict.keys())[:10]}...")
    logging.debug(f"[Baseline Start Year {start_year}] Initial persistent effects: {initial_persistent_effects}")
    logging.debug(f"[Baseline Start Year {start_year}] Initial temporary effects: {initial_temporary_effects}")


    for baseline_year in range(start_year, GAME_END_YEAR + 1):
        logging.debug(f"[Baseline Year {baseline_year}] Starting simulation step.")

        # --- Get Previous State for Baseline ---
        # For the first year of this baseline run, use the provided initial_state_dict
        if baseline_year == start_year:
            prev_solution_values = initial_state_dict
            logging.debug(f"[Baseline Year {baseline_year}] Using provided initial_state_dict as previous state.")
        # For subsequent years, use the results from the previous baseline year simulation
        elif baseline_run_history:
             prev_solution_values = baseline_run_history[-1] # Get the dict from the last simulated year
             logging.debug(f"[Baseline Year {baseline_year}] Using previous baseline year's result dict as previous state.")
        else:
             # This should not happen if start_year > 1 and baseline_run_history is empty
             logging.error(f"[Baseline Year {baseline_year}] Cannot find previous state. History is empty.")
             return None # Indicate error

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
            # --- LOGGING: Before apply_effects --- 
            logging.debug(f"[Baseline Year {baseline_year}] BEFORE apply_effects: Mocked persistent_effects = {baseline_persistent_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] BEFORE apply_effects: Mocked temporary_effects = {baseline_temporary_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] BEFORE apply_effects: cards_played = {cards_to_play}") # Should be empty

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
            # --- LOGGING: After apply_effects --- 
            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: Updated baseline_persistent_effects = {baseline_persistent_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: Updated baseline_temporary_effects = {baseline_temporary_effects}")

            baseline_persistent_effects = st.session_state.persistent_effects

            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: Updated baseline_persistent_effects = {baseline_persistent_effects}")
            logging.debug(f"[Baseline Year {baseline_year}] AFTER apply_effects: Updated baseline_temporary_effects = {baseline_temporary_effects}")

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

            # 3. Set Current Solution based on the previous year's baseline results
            # The model needs the *previous* year's solution to calculate the current year
            # For the very first year (baseline_year == start_year), solve() handles initialization
            # Always set the previous year's solution state before solving the current year.
            # For the first year (baseline_year == start_year), prev_solution_values comes from initial_state_dict.
            # For subsequent years, it comes from the previous baseline iteration.
            if prev_solution_values:
                 # We need to set the variables from the dictionary onto the model
                 # Note: This assumes prev_solution_values contains all necessary variables
                 model_to_simulate.current_solution = prev_solution_values
                 # Since we create a fresh model each loop, its solutions list is empty.
                 # Initialize it with the previous step's solution for solve() to work correctly.
                 model_to_simulate.solutions = [prev_solution_values]
                 logging.debug(f"[Baseline Year {baseline_year}] Set previous year's solution into model (from {'initial_state_dict' if baseline_year == start_year else 'previous baseline step'}).")
            else:
                 # This case should ideally not happen if initial_state_dict is always provided for start_year
                 # and subsequent steps populate baseline_run_history.
                 logging.error(f"[Baseline Year {baseline_year}] Could not set previous solution state (prev_solution_values is missing).")
                 # Handle error or continue cautiously? For now, log and continue.

            # --- LOGGING: Before solve ---
            # Ensure prev_solution_values exists before trying to access its keys for logging
            if prev_solution_values:
                logging.debug(f"[Baseline Year {baseline_year}] Preparing model state before solve. Previous solution keys (sample): {list(prev_solution_values.keys())[:10]}...")
            else:
                logging.warning(f"[Baseline Year {baseline_year}] Preparing model state before solve. No previous solution values available for logging.")


            # --- Run the simulation for one baseline year ---
            logging.debug(f"[Baseline Year {baseline_year}] Preparing model state before solve. Previous solution keys (sample): {list(prev_solution_values.keys())[:10]}...")

            sys.stdout = NullIO()
            logging.debug(f"[Baseline Year {baseline_year}] Attempting model.solve()...")
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout
            logging.debug(f"[Baseline Year {baseline_year}] model.solve() completed.")

            # --- Post-Solve State Update (Baseline Specific) ---
            latest_sim_solution = model_to_simulate.solutions[-1]
            # --- Calculate KPIs for baseline history ---
            game_base_yk = st.session_state.get('base_yk')
            if game_base_yk is not None:
                 calculate_kpis(latest_sim_solution, game_base_yk)
                 logging.debug(f"[Baseline Year {baseline_year}] KPIs calculated using game_base_yk={game_base_yk}. Result: {{ {{k: latest_sim_solution.get(k) for k in ['Yk_Index', 'Unemployment', 'Inflation', 'GD_GDP']}} }}") # Doubled braces for dict comp
            else:
                 # Ensure keys exist even if calculation failed, prevent KeyErrors later
                 latest_sim_solution.setdefault('Yk_Index', None)
                 latest_sim_solution.setdefault('Unemployment', None)
                 latest_sim_solution.setdefault('Inflation', None)
                 latest_sim_solution.setdefault('GD_GDP', None)
                 logging.warning(f"[Baseline Year {baseline_year}] Could not calculate KPIs due to missing st.session_state.base_yk.")
            # --- End KPI Calculation ---


            # Update the baseline's model object for the next iteration's history copy
            # Store the results dictionary for the next iteration
            baseline_run_history.append(latest_sim_solution)
            # No need to update current_model here as we create a fresh one each loop

            # Record Baseline History
            current_results = { 'year': baseline_year }
            history_vars = ['Yk', 'PI', 'ER', 'GRk', 'Rb', 'Rl', 'Rm', 'BUR', 'Q', 'CAR', 'PSBR', 'GD', 'Y', 'V', 'Lhs', 'Lfs']
            for key in history_vars:
                 current_results[key] = latest_sim_solution.get(key, np.nan)
            current_results['cards_played'] = [] # Explicitly empty
            current_results['events'] = list(events_active)
            # The results dictionary 'current_results' was already appended above
            logging.debug(f"[Baseline Year {baseline_year}] Result dictionary processed.")

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


def run_counterfactual_simulation(target_year, card_names_to_exclude):
    """
    Runs a counterfactual simulation starting from before the target year,
    excluding the specified cards that were played in the target year.
    
    Args:
        target_year (int): The year from which to exclude the specified cards
        card_names_to_exclude (list): List of card names to exclude from the simulation
        
    Returns:
        list: A list of result dictionaries for the counterfactual simulation years
    """
    logging.info(f"--- Starting Counterfactual Simulation excluding cards from Year {target_year} ---")
    
    # Find the history entry for the year before the target year
    prev_year = target_year - 1
    if prev_year < 1:
        logging.error(f"Cannot run counterfactual for target year {target_year} as there is no previous year data.")
        return None
    
    # Get history entries for the relevant years
    history_df = pd.DataFrame(st.session_state.history)
    prev_year_entry = history_df[history_df['year'] == prev_year].iloc[0].to_dict() if not history_df[history_df['year'] == prev_year].empty else None
    target_year_entry = history_df[history_df['year'] == target_year].iloc[0].to_dict() if not history_df[history_df['year'] == target_year].empty else None
    
    if prev_year_entry is None or target_year_entry is None:
        logging.error(f"Missing required history entries for counterfactual simulation (prev_year: {prev_year}, target_year: {target_year}).")
        return None
    
    # Extract the cards played in the target year
    cards_played_in_target_year = target_year_entry.get('played_cards', [])
    
    # Create a new list of cards to play, excluding the specified cards
    counterfactual_cards = [card for card in cards_played_in_target_year if card not in card_names_to_exclude]
    logging.info(f"Original cards played in Year {target_year}: {cards_played_in_target_year}")
    logging.info(f"Cards being excluded: {card_names_to_exclude}")
    logging.info(f"Counterfactual cards to play: {counterfactual_cards}")
    
    # Prepare for simulation
    # Deep copy necessary states to isolate counterfactual run
    initial_state_dict = copy.deepcopy(prev_year_entry)
    
    # Create a list to store the history of the counterfactual simulation
    counterfactual_history = []
    
    # Initialize with the state from the year before the target year
    counterfactual_history.append(initial_state_dict)
    
    # Deep copy persistent and temporary effects from the previous year
    persistent_effects = copy.deepcopy(prev_year_entry.get('persistent_effects', {}))
    temporary_effects = copy.deepcopy(prev_year_entry.get('temporary_effects', []))
    
    # Get character ID and event sequence
    char_id = st.session_state.selected_character_id
    event_seq = st.session_state.full_event_sequence
    
    # Run simulation from the previous year to the end of the game
    for sim_year in range(prev_year + 1, GAME_END_YEAR + 1):
        logging.debug(f"[Counterfactual Year {sim_year}] Starting simulation step.")
        
        # Get previous solution values
        if sim_year == prev_year + 1:
            prev_solution_values = initial_state_dict
        else:
            prev_solution_values = counterfactual_history[-1]
        
        # Determine cards to play for this year
        if sim_year == target_year:
            cards_to_play = counterfactual_cards
        else:
            # For years after the target year, use what was actually played
            year_entry = history_df[history_df['year'] == sim_year].iloc[0].to_dict() if not history_df[history_df['year'] == sim_year].empty else None
            cards_to_play = year_entry.get('played_cards', []) if year_entry is not None else []
        
        # Get active events for this year
        events_active = event_seq.get(sim_year, [])
        
        # Calculate and apply parameters
        base_numerical_params = copy.deepcopy(growth_parameters)
        temp_model_for_param_check = create_growth_model()
        defined_param_names = set(temp_model_for_param_check.parameters.keys())
        for key, value in growth_exogenous:
            if key in defined_param_names:
                try: base_numerical_params[key] = float(value)
                except: logging.warning(f"[Counterfactual Year {sim_year}] Could not convert exogenous parameter {key}={value} to float.")
        
        # Mock session state for apply_effects
        original_temp_effects = st.session_state.get('temporary_effects')
        original_pers_effects = st.session_state.get('persistent_effects')
        st.session_state.temporary_effects = temporary_effects
        st.session_state.persistent_effects = persistent_effects
        
        final_numerical_params = {}
        try:
            final_numerical_params = apply_effects(
                base_params=base_numerical_params,
                latest_solution=prev_solution_values,
                cards_played=cards_to_play,
                active_events=events_active,
                character_id=char_id
            )
            # Update effects with the modified ones from session state
            temporary_effects = st.session_state.temporary_effects
            persistent_effects = st.session_state.persistent_effects
        except Exception as e:
            logging.error(f"[Counterfactual Year {sim_year}] Error during apply_effects: {e}")
            st.session_state.temporary_effects = original_temp_effects
            st.session_state.persistent_effects = original_pers_effects
            return None
        finally:
            # Restore original session state effects
            st.session_state.temporary_effects = original_temp_effects
            st.session_state.persistent_effects = original_pers_effects
        
        # Initialize model and run simulation
        model_to_simulate = create_growth_model()
        old_stdout = sys.stdout
        try:
            # Set defaults
            model_to_simulate.set_values(growth_parameters)
            model_to_simulate.set_values(growth_exogenous)
            model_to_simulate.set_values(growth_variables)
            
            # Set final parameters
            model_to_simulate.set_values(final_numerical_params)
            
            # Set current solution
            if prev_solution_values:
                model_to_simulate.current_solution = prev_solution_values
                model_to_simulate.solutions = [prev_solution_values]
            
            # Run simulation
            sys.stdout = NullIO()
            model_to_simulate.solve(iterations=1000, threshold=1e-6)
            sys.stdout = old_stdout
            
            # Get solution and calculate KPIs
            latest_sim_solution = model_to_simulate.solutions[-1]
            game_base_yk = st.session_state.get('base_yk')
            if game_base_yk is not None:
                calculate_kpis(latest_sim_solution, game_base_yk)
            else:
                latest_sim_solution.setdefault('Yk_Index', None)
                latest_sim_solution.setdefault('Unemployment', None)
                latest_sim_solution.setdefault('Inflation', None)
                latest_sim_solution.setdefault('GD_GDP', None)
            
            # Add metadata
            latest_sim_solution['year'] = sim_year
            latest_sim_solution['played_cards'] = list(cards_to_play)
            latest_sim_solution['events'] = list(events_active)
            latest_sim_solution['persistent_effects'] = copy.deepcopy(persistent_effects)
            latest_sim_solution['temporary_effects'] = copy.deepcopy(temporary_effects)
            
            # Add to counterfactual history
            counterfactual_history.append(latest_sim_solution)
            
        except SolutionNotFoundError as e:
            sys.stdout = old_stdout
            logging.error(f"[Counterfactual Year {sim_year}] Model failed to converge. Error: {str(e)}")
            return None
        except Exception as e:
            sys.stdout = old_stdout
            logging.error(f"[Counterfactual Year {sim_year}] Unexpected error: {str(e)}")
            logging.exception(f"Unexpected error in counterfactual simulation (Year {sim_year}):")
            return None
        finally:
            sys.stdout = old_stdout
    
    logging.info(f"--- Finished Counterfactual Simulation for cards from Year {target_year}. Recorded {len(counterfactual_history)} years. ---")
    return counterfactual_history[1:]  # Skip the first entry which is the prev_year