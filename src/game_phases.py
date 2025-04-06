# src/game_phases.py
"""Handles the logic and UI rendering for specific game phases."""

import streamlit as st
import logging

# Import project modules & components
from src.config import CARDS_TO_DRAW_PER_YEAR, GAME_END_YEAR
from src.ui_character_select import display_character_selection
from src.ui_kpi_events import display_kpi_and_events_section
from src.ui_policy_cards import display_policy_selection_section
from src.ui_dilemma import display_dilemma
from src.ui_game_over import display_game_over_screen
from src.objective_evaluator import evaluate_objectives
# Import simulation logic - needs to exist or be handled gracefully
try:
    from src.simulation_logic import run_simulation
except ImportError:
    # Define a placeholder if simulation_logic doesn't exist yet or handle error
    def run_simulation():
        st.error("Simulation logic not implemented yet.")
        logging.error("Attempted to run simulation, but src.simulation_logic.run_simulation not found.")
        st.session_state.game_phase = "SIMULATION_ERROR" # Transition to error state

# Import game mechanics needed for phases
try:
    from game_mechanics import draw_cards, check_for_events, select_dilemma
    from dilemmas import DILEMMAS # Needed for select_dilemma potentially
    from events import ECONOMIC_EVENTS # Needed for check_for_events potentially
except ImportError as e:
    logging.error(f"Failed to import game components in game_phases.py: {e}")
    # Define placeholders or raise error if critical
    def draw_cards(deck, hand, discard, count): return deck, hand, discard
    def check_for_events(results): return []
    def select_dilemma(advisor_id, seen): return None, None
    st.error(f"Failed to import game mechanics: {e}. Phase logic might be incomplete.")


# --- Phase Logic Functions ---

def run_character_selection_phase():
    """Runs the logic and UI for the CHARACTER_SELECTION phase."""
    display_character_selection()
    # Action processing happens via st.rerun() triggered by button clicks in display_character_selection

def run_year_start_phase():
    """Runs the logic and UI for the YEAR_START phase, including dilemmas."""
    current_year = st.session_state.current_year
    dilemma_already_processed_this_year = st.session_state.get('dilemma_processed_for_year', -1) == current_year

    # --- Step 1: Perform year start actions (draw cards, check events) only once per year ---
    if "year_start_processed" not in st.session_state or st.session_state.year_start_processed != current_year:
        logging.debug(f"Processing year start actions for Year {current_year}")
        # Card draw moved to after dilemma check
        # Check for events based on the *previous* year's state
        previous_year_results = None
        if st.session_state.history:
             previous_year_results = st.session_state.history[-1]
        elif current_year == 1: # Special case for first event check
             previous_year_results = st.session_state.get('initial_state_dict')
             if not previous_year_results:
                 logging.error("Initial state dict missing for Year 1 event check.")

        if previous_year_results:
            try:
                st.session_state.active_events_this_year = check_for_events(previous_year_results)
                if st.session_state.active_events_this_year:
                     st.warning(f"New Events Occurred: {', '.join(st.session_state.active_events_this_year)}")
                     logging.info(f"Active events for Year {current_year}: {st.session_state.active_events_this_year}")
            except Exception as e:
                logging.error(f"Error checking for events: {e}")
                st.error("Failed to check for economic events.")
                st.session_state.active_events_this_year = [] # Ensure it's reset
        else:
             st.session_state.active_events_this_year = []
             if current_year > 1:
                 logging.error(f"History missing when checking events for Year {current_year}.")

        st.session_state.year_start_processed = current_year
        st.session_state.cards_selected_this_year = [] # Reset selected cards
        logging.debug(f"Finished YEAR_START actions for Year {current_year}")

    # --- Step 2: Check if a *new* dilemma needs to be selected ---
    needs_new_dilemma_check = (
        not dilemma_already_processed_this_year and
        not st.session_state.get('current_dilemma') and # Check existence safely
        current_year > 0 and current_year < (GAME_END_YEAR - 1) # Ensure game end year logic is correct
    )

    if needs_new_dilemma_check:
        logging.debug(f"Checking for new dilemma for Year {current_year}")
        advisor_id = st.session_state.get('selected_character_id')
        if advisor_id:
            # Ensure the set for tracking removed cards exists in session state
            if 'removed_cards_this_playthrough' not in st.session_state:
                st.session_state.removed_cards_this_playthrough = set()
                logging.info("Initialized removed_cards_this_playthrough set.")

            try:
                # Pass the set of removed cards to the selection function
                dilemma_id, dilemma_data = select_dilemma(
                    advisor_id,
                    st.session_state.seen_dilemmas,
                    st.session_state.removed_cards_this_playthrough # Pass the tracking set
                )
                if dilemma_id and dilemma_data:
                    st.session_state.current_dilemma = {"id": dilemma_id, "data": dilemma_data}
                    st.session_state.seen_dilemmas.add(dilemma_id)
                    logging.info(f"Selected new dilemma: {dilemma_id} for year {current_year}")
                    # DO NOT rerun here - let the next step display dilemma + KPIs
                else:
                    logging.info(f"No unseen dilemmas available for advisor '{advisor_id}' in year {current_year}.")
            except Exception as e:
                logging.error(f"Error selecting dilemma: {e}")
                st.error("Failed to select an advisor dilemma.")
        else:
            logging.warning("Cannot select dilemma: advisor_id not found.")

    # --- Step 3: Display Dilemma + KPIs/Events OR KPIs/Events + Policy Selection ---
    if st.session_state.get('current_dilemma'):
        logging.debug(f"Displaying active dilemma for Year {current_year}")
        display_dilemma()
        logging.debug(f"Displaying KPIs and Events below dilemma for Year {current_year}")
        display_kpi_and_events_section()
    else:
        logging.debug(f"No active dilemma, displaying KPIs/Events for Year {current_year}")
        display_kpi_and_events_section()
        # --- Step 4: Draw cards if not already drawn this year (after dilemma) ---
        if st.session_state.get('cards_drawn_for_year', -1) != current_year:
            logging.debug(f"YEAR_START: Attempting to draw cards post-dilemma for Year {current_year}.")
            try:
                st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
                    st.session_state.deck,
                    st.session_state.player_hand,
                    st.session_state.discard_pile,
                    CARDS_TO_DRAW_PER_YEAR
                )
                st.toast(f"Drew {CARDS_TO_DRAW_PER_YEAR} cards.")
                logging.debug(f"Hand after draw: {st.session_state.player_hand}")
                logging.debug(f"YEAR_START: Finished drawing cards for Year {current_year}. Hand size: {len(st.session_state.player_hand)}")
                st.session_state.cards_drawn_for_year = current_year # Mark cards as drawn for this year
            except Exception as e:
                 logging.error(f"Error drawing cards in year start phase (post-dilemma): {e}")
                 st.error("Failed to draw cards for the new year.")
                 # Potentially transition to an error state or allow retry?


        logging.debug(f"Displaying policy selection UI for Year {current_year}")
        display_policy_selection_section()
        # Action processing (confirm policies) happens via st.rerun() triggered by button clicks

def run_simulation_phase():
    """Runs the simulation logic for the current year."""
    logging.info(f"Starting simulation for Year {st.session_state.current_year + 1}")
    try:
        run_simulation() # This function handles simulation steps and state updates (including phase transition)
        logging.info(f"Simulation successful for Year {st.session_state.current_year}.") # Year has been incremented inside run_simulation
    except Exception as e:
        logging.exception(f"Exception during simulation phase for year {st.session_state.current_year + 1}:")
        st.error(f"A critical error occurred during the simulation: {e}")
        st.session_state.game_phase = "SIMULATION_ERROR"
        # Rerun needed to display the error phase UI
        st.rerun()


def run_game_over_phase():
    """Runs the logic and UI for the GAME_OVER phase."""
    logging.info("Entering GAME_OVER phase.")
    try:
        all_met, summary = evaluate_objectives()
        display_game_over_screen(all_met, summary)
    except Exception as e:
        logging.exception("Error during game over phase:")
        st.error(f"An error occurred displaying the game over screen: {e}")

def run_simulation_error_phase():
    """Displays the simulation error message."""
    logging.error(f"Entering SIMULATION_ERROR phase for Year {st.session_state.current_year + 1}.")
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    st.info("Please review the logs (`debug_session.log`) for more details.")
    # Optional: Add a button to acknowledge and stop/reset
    # if st.button("Acknowledge Error (Stops Game)"): st.stop()