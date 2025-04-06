# src/game_logic.py
"""Handles the main game loop, phase transitions, and action processing."""

import streamlit as st
import logging
import pandas as pd
import numpy as np

# Import project modules
from src.config import INITIAL_HAND_SIZE, CARDS_TO_DRAW_PER_YEAR, GAME_END_YEAR
from src.utils import format_percent, format_value # Import necessary utils
from src.ui_main import ( # Import UI functions needed within logic phases
    display_character_selection, display_kpi_and_events_section, # UPDATED
    display_policy_selection_section, display_dilemma, # UPDATED
    display_game_over_screen
)
# Import simulation logic (will be created next)
# from src.simulation_logic import run_simulation

# Import game component modules (assuming they are in the root or accessible path)
try:
    from game_mechanics import (
        create_deck, draw_cards, check_for_events, apply_effects,
        select_dilemma, apply_dilemma_choice
    )
    from dilemmas import DILEMMAS
    from cards import POLICY_CARDS
    from events import ECONOMIC_EVENTS
    from characters import CHARACTERS
except ImportError as e:
    st.error(f"Failed to import game components in game_logic.py: {e}. Ensure necessary files are present.")
    st.stop()


# --- Action Handlers ---

def handle_character_selection_action(char_id):
    """Handles the selection of a character."""
    st.session_state.selected_character_id = char_id
    logging.info(f"Character '{CHARACTERS[char_id]['name']}' selected.")

    # Set Game Objectives based on Character
    st.session_state.game_objectives = CHARACTERS[char_id].get('objectives', {})
    logging.info(f"Objectives set: {st.session_state.game_objectives}")

    # Create Deck based on Character
    st.session_state.deck = create_deck(character_id=char_id)
    logging.info(f"Deck created. Size: {len(st.session_state.deck)}")

    # Initial Draw
    st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
        st.session_state.deck,
        st.session_state.player_hand,
        st.session_state.discard_pile,
        INITIAL_HAND_SIZE
    )
    logging.info(f"Drew initial hand. Size: {len(st.session_state.player_hand)}")

    # Start First Simulation (Year 0 -> Year 1)
    st.session_state.game_phase = "SIMULATION"
    st.session_state.cards_selected_this_year = []
    st.session_state.active_events_this_year = []
    logging.info("Proceeding to first simulation (Year 0 -> Year 1).")

def handle_dilemma_choice_action(choice):
    """Handles the player's choice for the current dilemma."""
    dilemma_id = st.session_state.current_dilemma['id']
    dilemma_data = st.session_state.current_dilemma['data']
    option = dilemma_data['option_a'] if choice == "A" else dilemma_data['option_b']

    logging.info(f"Dilemma {dilemma_id} - Option {choice} chosen.")
    st.session_state.deck, st.session_state.discard_pile, action_descriptions = apply_dilemma_choice(
        option, st.session_state.deck, st.session_state.discard_pile
    )
    st.session_state.current_dilemma = None # Clear dilemma state
    st.session_state.dilemma_processed_for_year = st.session_state.current_year # Mark as processed

    display_message = "Deck modified by dilemma choice!"
    if action_descriptions:
        display_message += "\nChanges:\n* " + "\n* ".join(action_descriptions)
    st.toast(display_message)
    # No phase change here, rerun will take care of displaying YEAR_START without dilemma

def handle_card_toggle_action(card_name):
    """Handles selecting or deselecting a policy card."""
    selected_cards = st.session_state.cards_selected_this_year
    max_cards_allowed = 2 # Define max cards here
    is_selected = card_name in selected_cards

    if is_selected:
        selected_cards.remove(card_name)
    else:
        # Add checks before appending
        if card_name in selected_cards: # Should not happen with unique display, but safety check
             st.warning(f"Cannot select two '{card_name}' cards in the same turn.")
        elif len(selected_cards) >= max_cards_allowed:
            st.warning(f"You can only select up to {max_cards_allowed} cards.")
        else:
            selected_cards.append(card_name)
    # No phase change, rerun updates UI

def handle_confirm_policies_action():
    """Handles confirming selected policies and proceeding to simulation."""
    st.session_state.game_phase = "SIMULATION"
    if "year_start_processed" in st.session_state:
        del st.session_state.year_start_processed # Clean up flag

# --- Phase Logic Functions ---

def run_character_selection_phase():
    """Runs the logic and UI for the CHARACTER_SELECTION phase."""
    display_character_selection()
    # Action processing happens via st.rerun() triggered by button clicks

def run_year_start_phase():
    """Runs the logic and UI for the YEAR_START phase, including dilemmas."""
    current_year = st.session_state.current_year
    dilemma_already_processed_this_year = st.session_state.get('dilemma_processed_for_year', -1) == current_year

    # --- Step 1: Perform year start actions (draw cards, check events) only once per year ---
    # This needs to happen regardless of whether a dilemma is shown or not.
    if "year_start_processed" not in st.session_state or st.session_state.year_start_processed != current_year:
        logging.debug(f"Processing year start actions for Year {current_year}")
        # Draw cards
        st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
            st.session_state.deck,
            st.session_state.player_hand,
            st.session_state.discard_pile,
            CARDS_TO_DRAW_PER_YEAR
        )
        st.toast(f"Drew {CARDS_TO_DRAW_PER_YEAR} cards.")
        logging.debug(f"Hand after draw: {st.session_state.player_hand}")

        # Check for events based on the *previous* year's state
        previous_year_results = None
        if st.session_state.history:
             previous_year_results = st.session_state.history[-1]
        elif current_year == 1: # Special case for first event check
             previous_year_results = st.session_state.get('initial_state_dict')
             if not previous_year_results:
                 logging.error("Initial state dict missing for Year 1 event check.")

        if previous_year_results:
            st.session_state.active_events_this_year = check_for_events(previous_year_results)
            if st.session_state.active_events_this_year:
                 st.warning(f"New Events Occurred: {', '.join(st.session_state.active_events_this_year)}")
                 logging.info(f"Active events for Year {current_year}: {st.session_state.active_events_this_year}")
        else:
             st.session_state.active_events_this_year = []
             if current_year > 1:
                 logging.error(f"History missing when checking events for Year {current_year}.")

        st.session_state.year_start_processed = current_year
        st.session_state.cards_selected_this_year = [] # Reset selected cards
        logging.debug(f"Finished YEAR_START actions for Year {current_year}")

    # --- Step 2: Check if a *new* dilemma needs to be selected ---
    # We only select a new dilemma if one isn't already active and hasn't been processed this year.
    needs_new_dilemma_check = (
        not dilemma_already_processed_this_year and
        not st.session_state.current_dilemma and
        current_year > 0 and current_year < (GAME_END_YEAR - 1)
    )

    if needs_new_dilemma_check:
        logging.debug(f"Checking for new dilemma for Year {current_year}")
        advisor_id = st.session_state.get('selected_character_id')
        if advisor_id:
            dilemma_id, dilemma_data = select_dilemma(advisor_id, st.session_state.seen_dilemmas)
            if dilemma_id and dilemma_data:
                st.session_state.current_dilemma = {"id": dilemma_id, "data": dilemma_data}
                st.session_state.seen_dilemmas.add(dilemma_id)
                logging.info(f"Selected new dilemma: {dilemma_id} for year {current_year}")
                # DO NOT rerun here - let the next step display dilemma + KPIs
            else:
                logging.info(f"No unseen dilemmas available for advisor '{advisor_id}' in year {current_year}.")
        else:
            logging.warning("Cannot select dilemma: advisor_id not found.")

    # --- Step 3: Display Dilemma + KPIs/Events OR KPIs/Events + Policy Selection ---
    if st.session_state.current_dilemma:
        # If a dilemma is active, display it first, then KPIs/Events.
        logging.debug(f"Displaying active dilemma for Year {current_year}")
        display_dilemma()
        logging.debug(f"Displaying KPIs and Events below dilemma for Year {current_year}")
        display_kpi_and_events_section()
        # Policy selection is implicitly hidden until dilemma is resolved (which clears current_dilemma and causes rerun)
    else:
        # If no dilemma is active, display KPIs/Events first, then Policy Selection.
        logging.debug(f"No active dilemma, displaying KPIs/Events for Year {current_year}")
        display_kpi_and_events_section()
        logging.debug(f"Displaying policy selection UI for Year {current_year}")
        display_policy_selection_section()
        # Action processing (confirm policies) happens via st.rerun() triggered by button clicks in display_policy_selection_section

def run_simulation_phase():
    """Runs the simulation logic for the current year."""
    # Import here to avoid potential circular dependency during module creation
    from src.simulation_logic import run_simulation
    run_simulation() # This function will handle the simulation steps and state updates

def evaluate_objectives():
    """Evaluates if game objectives were met based on final results."""
    objectives = st.session_state.get('game_objectives', {})
    final_results = st.session_state.history[-1] # Get results from the last year
    all_met = True
    summary = []

    if not objectives:
        logging.warning("No game objectives were set for evaluation.")
        return False, [] # Cannot win without objectives

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
            if np.isfinite(er_val): current_value = (1 - er_val) * 100
        elif obj_key == "inflation":
            pi_val = final_results.get('PI', np.nan)
            if np.isfinite(pi_val): current_value = pi_val * 100
        elif obj_key == "debt_gdp":
            gd_val = final_results.get('GD', np.nan)
            y_val = final_results.get('Y', np.nan)
            if np.isfinite(gd_val) and np.isfinite(y_val) and not np.isclose(float(y_val), 0):
                current_value = (gd_val / y_val) * 100

        # Check if objective met
        met = False
        if current_value is not None:
            if condition == ">=" and current_value >= target: met = True
            elif condition == "<=" and current_value <= target: met = True
            elif condition == ">" and current_value > target: met = True
            elif condition == "<" and current_value < target: met = True

        if not met: all_met = False

        # Format for display
        current_str = "N/A"
        target_str = f"{target:.0f}"
        if current_value is not None:
             if target_type == 'percent':
                 current_str = f"{current_value:.1f}%"; target_str += "%"
             elif target_type == 'index':
                 current_str = f"{current_value:.1f}"
             else: current_str = f"{current_value:.1f}"

        summary.append({
            "Objective": label, "Target": f"{condition} {target_str}",
            "Actual": current_str, "Met?": "✅ Yes" if met else "❌ No"
        })

    return all_met, summary

def run_game_over_phase():
    """Runs the logic and UI for the GAME_OVER phase."""
    all_met, summary = evaluate_objectives()
    display_game_over_screen(all_met, summary)

def run_simulation_error_phase():
    """Displays the simulation error message."""
    # Correct year display for error message
    st.error(f"Simulation failed for Year {st.session_state.current_year + 1}. Cannot proceed.")
    # Optional: Add a button to acknowledge and stop/reset
    # if st.button("Acknowledge Error (Stops Game)"): st.stop()


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
        # No need to rerun here, the main phase logic below will handle the updated state

    # Execute logic based on the current game phase
    phase = st.session_state.game_phase
    logging.debug(f"Executing game phase: {phase}")

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