# src/game_logic.py
"""Handles the main game loop, phase transitions, and action processing."""

import streamlit as st
import logging
import pandas as pd
import random
from src.config import MAX_CARDS_PLAYED_PER_YEAR, INITIAL_HAND_SIZE, GAME_END_YEAR
from src.simulation_logic import run_simulation_step
from game_mechanics import draw_cards # Assuming draw_cards is needed
from src.game_phases import run_year_start_phase # Needed for fast_forward


# import numpy as np # Moved to objective_evaluator.py

# Import project modules
# Removed config imports (moved to game_phases/action_handlers)
# Removed utils imports (moved to game_phases)
# Removed UI imports (moved to game_phases)
# Removed objective_evaluator import (moved to game_phases)
from src.action_handlers import ( # Import action handlers
    handle_character_selection_action, handle_dilemma_choice_action,
    handle_card_toggle_action, handle_confirm_policies_action
)
from src.game_phases import ( # Import phase logic functions
    run_character_selection_phase, run_year_start_phase,
    run_simulation_phase, run_game_over_phase, run_simulation_error_phase
)
# Removed simulation_logic import placeholder
# Removed game component imports (moved to game_phases/action_handlers)
# Removed try-except block for component imports


# (Action Handlers moved to src/action_handlers.py)

# (Phase Logic Functions moved to src/game_phases.py)


def handle_fast_forward():
    """Simulates the game automatically with random choices until GAME_END_YEAR."""
    logging.info("--- Starting Fast Forward Simulation ---")
    st.session_state._is_fast_forwarding = True # Set flag
    try: # Wrap the main logic in try
        if 'selected_character_id' not in st.session_state or not st.session_state.selected_character_id:
            st.error("Cannot fast forward: No character selected.")
            logging.error("Fast forward triggered without a selected character.")
            return

        # Ensure the first simulation (Year 0 -> 1) has run if needed
        if st.session_state.current_year == 0:
            logging.info("Fast Forward: Running initial simulation (Year 0 -> 1).")
            # The character selection already triggers the first simulation and advances year to 1
            # So, we start the loop from year 1
            pass # No action needed here, year should be 1 already if char selected

        start_loop_year = st.session_state.current_year
        logging.info(f"Fast Forward: Starting loop from Year {start_loop_year} to {GAME_END_YEAR}.")

        for year in range(start_loop_year, GAME_END_YEAR + 1):
            st.session_state.current_year = year
            logging.info(f"--- Fast Forward: Simulating Year {year} ---")

            # 1. Process Year Start (Events, Dilemma Check)
            # This function handles getting events and potentially setting a dilemma
            try:
                run_year_start_phase() # Use the correct function name
                logging.debug(f"Fast Forward Year {year}: run_year_start_phase completed.")
            except Exception as e:
                logging.error(f"Fast Forward Year {year}: Error during run_year_start_phase: {e}")
                st.error(f"Error processing start of Year {year} during fast forward.")
                st.session_state.game_phase = "SIMULATION_ERROR"
                return # Stop fast forward on error

            # 2. Handle Dilemma (if any)
            if st.session_state.get('current_dilemma'):
                dilemma_id = st.session_state.current_dilemma.get('id', 'Unknown')
                choice = random.choice(['A', 'B'])
                logging.info(f"Fast Forward Year {year}: Randomly choosing option {choice} for dilemma {dilemma_id}.")
                try:
                    handle_dilemma_choice_action(choice)
                except Exception as e:
                    logging.error(f"Fast Forward Year {year}: Error during handle_dilemma_choice_action: {e}")
                    st.error(f"Error handling dilemma choice in Year {year} during fast forward.")
                    st.session_state.game_phase = "SIMULATION_ERROR"
                    return # Stop fast forward on error

            # 3. Draw Cards (if needed - YEAR_START might handle this after dilemma)
            # Check if hand is empty, draw if necessary. run_year_start_phase should handle drawing after dilemma.
            if not st.session_state.player_hand:
                 logging.debug(f"Fast Forward Year {year}: Hand is empty, attempting draw.")
                 try:
                     st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
                         st.session_state.deck,
                         st.session_state.player_hand,
                         st.session_state.discard_pile,
                         st.session_state.get('target_hand_size', INITIAL_HAND_SIZE) # Use target or default
                     )
                     logging.info(f"Fast Forward Year {year}: Drew cards. New hand size: {len(st.session_state.player_hand)}")
                 except Exception as e:
                     logging.error(f"Fast Forward Year {year}: Error drawing cards: {e}")
                     st.error(f"Error drawing cards in Year {year} during fast forward.")
                     st.session_state.game_phase = "SIMULATION_ERROR"
                     return

            # 4. Select Random Policies
            available_cards = st.session_state.player_hand
            # --- Modified Logic: Always try to select 2 cards ---
            if len(available_cards) >= 2:
                num_to_select = 2
            elif len(available_cards) == 1:
                num_to_select = 1
            else:
                num_to_select = 0
            # --- End Modification ---
            selected_cards = random.sample(available_cards, num_to_select) if available_cards else []
            st.session_state.cards_selected_this_year = selected_cards
            logging.info(f"Fast Forward Year {year}: Randomly selected policies: {selected_cards}")

            # 5. Run Simulation for the year
            logging.info(f"Fast Forward Year {year}: Triggering simulation.")
            try:
                # run_simulation() handles the simulation, state updates, and advances year/phase internally
                # It also includes the baseline run logic we fixed.
                # We need to prevent it from rerunning streamlit within the loop.
                # Temporarily override st.rerun
                original_rerun = st.rerun
                st.rerun = lambda: logging.info("Fast Forward: Suppressed st.rerun() within simulation loop.")

                run_simulation_step() # This will simulate year -> year+1

                st.rerun = original_rerun # Restore original rerun

                # Check if simulation ended in error
                if st.session_state.game_phase == "SIMULATION_ERROR":
                    logging.error(f"Fast Forward Year {year}: Simulation ended in error state.")
                    st.error(f"Simulation failed during fast forward in Year {year}.")
                    return # Stop
                # Check if game ended prematurely (shouldn't happen here but good practice)
                if st.session_state.game_phase == "GAME_OVER" and year < GAME_END_YEAR:
                     logging.warning(f"Fast Forward Year {year}: Game ended prematurely.")
                     break # Exit loop if game over

            except Exception as e:
                st.rerun = original_rerun # Ensure rerun is restored on error
                logging.error(f"Fast Forward Year {year}: Error during run_simulation: {e}")
                st.error(f"Simulation failed during fast forward in Year {year}.")
                st.session_state.game_phase = "SIMULATION_ERROR"
                return # Stop fast forward on error

            # run_simulation should have advanced the year and phase, loop continues
            logging.info(f"Fast Forward Year {year}: Simulation step finished. Current state year: {st.session_state.current_year}, phase: {st.session_state.game_phase}")

        # After loop completes (or breaks on GAME_OVER)
        logging.info("--- Fast Forward Simulation Complete ---")
        # Ensure phase is GAME_OVER if loop finished normally
        if st.session_state.game_phase != "SIMULATION_ERROR":
            st.session_state.game_phase = "GAME_OVER"

    finally:
        # Ensure flag is always removed
        if hasattr(st.session_state, '_is_fast_forwarding'):
            del st.session_state._is_fast_forwarding
        logging.info("--- Fast Forward Simulation Finished ---")
        st.rerun() # Final rerun to show the game over screen




# --- Main Game Loop ---

def run_game():
    """The main entry point to run the game logic based on the current phase."""

    # Process any pending action triggered by UI interactions in the previous run
    action_trigger = st.session_state.pop('action_trigger', None)
    if action_trigger:
        action_type, action_payload = action_trigger
        logging.debug(f"Processing action: {action_type} with payload: {action_payload}")
        if action_type == "select_character":
            handle_character_selection_action(action_payload)
        elif action_type == "choose_dilemma":
            handle_dilemma_choice_action(action_payload)
        elif action_type == "toggle_card_selection":
            handle_card_toggle_action(action_payload)
        elif action_type == "confirm_policies":
            handle_confirm_policies_action()
        elif action_type == "fast_forward":
            handle_fast_forward() # Call the function now defined in this module

        # No need to rerun here, the main phase logic below will handle the updated state

    # Execute logic based on the current game phase
    phase = st.session_state.game_phase
    logging.debug(f"Executing game phase: {phase}")
    logging.info(f"run_game: Phase check. Current phase = '{phase}'") # Add log

    if phase == "CHARACTER_SELECTION":
        run_character_selection_phase()
    elif phase == "YEAR_START":
        run_year_start_phase()
    elif phase == "SIMULATION":
        run_simulation_phase()
    elif phase == "GAME_OVER":
        run_game_over_phase()
    elif phase == "SIMULATION_ERROR":
        run_simulation_error_phase()
    else:
        st.error(f"Unknown game phase: {phase}")
        logging.error(f"Unknown game phase encountered: {phase}")