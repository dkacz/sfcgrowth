# src/action_handlers.py
"""Handles processing actions triggered by user interactions."""

import streamlit as st
import logging

# Import project modules & components
from src.config import INITIAL_HAND_SIZE, GAME_END_YEAR # Needed for character selection logic
try:
    from characters import CHARACTERS
    from game_mechanics import create_deck, draw_cards, apply_dilemma_choice
except ImportError as e:
    # This is a critical error if components are missing
    logging.error(f"Failed to import game components in action_handlers.py: {e}")
    # We can't use st.error here directly as it might not be in a Streamlit context always
    # Raise the error to potentially stop execution if this module is loaded early
    raise ImportError(f"Failed to import game components in action_handlers.py: {e}") from e


def handle_character_selection_action(char_id):
    """Handles the selection of a character."""
    if char_id not in CHARACTERS:
        logging.error(f"Invalid character ID selected: {char_id}")
        st.error("Invalid character selected. Please try again.")
        return # Prevent further processing

    st.session_state.selected_character_id = char_id
    logging.info(f"Character '{CHARACTERS[char_id]['name']}' selected.")

    # Set Game Objectives based on Character
    st.session_state.game_objectives = CHARACTERS[char_id].get('objectives', {})
    logging.info(f"Objectives set: {st.session_state.game_objectives}")

    # Create Deck based on Character
    try:
        st.session_state.deck = create_deck(character_id=char_id)
        logging.info(f"Deck created. Size: {len(st.session_state.deck)}")
    except Exception as e:
        logging.error(f"Error creating deck for character {char_id}: {e}")
        st.error("Failed to create the card deck for the selected character.")
        # Reset phase to allow re-selection? Or stop? For now, log and continue might be okay.
        return

    # Initial Draw
    try:
        st.session_state.deck, st.session_state.player_hand, st.session_state.discard_pile = draw_cards(
            st.session_state.deck,
            st.session_state.player_hand, # Assumes initialized empty list
            st.session_state.discard_pile, # Assumes initialized empty list
            INITIAL_HAND_SIZE
        )
        logging.info(f"Drew initial hand. Size: {len(st.session_state.player_hand)}")
    except Exception as e:
        logging.error(f"Error drawing initial hand: {e}")
        st.error("Failed to draw the initial hand of cards.")
        return

    # Start First Simulation (Year 0 -> Year 1)
    st.session_state.game_phase = "SIMULATION"
    st.session_state.cards_selected_this_year = []
    st.session_state.active_events_this_year = []
    logging.info("Proceeding to first simulation (Year 0 -> Year 1).")

def handle_dilemma_choice_action(choice):
    """Handles the player's choice for the current dilemma."""
    if 'current_dilemma' not in st.session_state or not st.session_state.current_dilemma:
        logging.warning("handle_dilemma_choice_action called but no current dilemma found.")
        return

    dilemma_id = st.session_state.current_dilemma.get('id')
    dilemma_data = st.session_state.current_dilemma.get('data')

    if not dilemma_id or not dilemma_data:
        logging.error("Current dilemma state is incomplete.")
        st.error("An error occurred processing the dilemma choice. Dilemma state incomplete.")
        st.session_state.current_dilemma = None # Clear potentially corrupt state
        return

    option = None
    if choice == "A" and 'option_a' in dilemma_data:
        option = dilemma_data['option_a']
    elif choice == "B" and 'option_b' in dilemma_data:
        option = dilemma_data['option_b']

    if option is None:
        logging.error(f"Invalid dilemma choice '{choice}' or missing option data for dilemma {dilemma_id}.")
        st.error("Invalid dilemma choice selected.")
        return

    logging.info(f"Dilemma {dilemma_id} - Option {choice} ('{option.get('name', 'N/A')}') chosen.")
    try:
        # Pass player_hand, deck, discard and unpack player_hand, deck, discard
        logging.debug(f"ACTION_HANDLER: Applying dilemma choice '{option.get('name', 'N/A')}'. Current hand size: {len(st.session_state.player_hand)}")
        st.session_state.player_hand, st.session_state.deck, st.session_state.discard_pile, action_descriptions = apply_dilemma_choice(
            option, st.session_state.player_hand, st.session_state.deck, st.session_state.discard_pile
        )
        logging.debug(f"ACTION_HANDLER: Finished applying dilemma choice. New hand size: {len(st.session_state.player_hand)}")
    except Exception as e:
        logging.error(f"Error applying dilemma choice {choice} for dilemma {dilemma_id}: {e}")
        st.error("An error occurred while applying the dilemma effects.")
        # Clear dilemma state even on error to prevent getting stuck?
        st.session_state.current_dilemma = None
        st.session_state.dilemma_processed_for_year = st.session_state.current_year
        return

    st.session_state.current_dilemma = None # Clear dilemma state
    st.session_state.dilemma_processed_for_year = st.session_state.current_year # Mark as processed

    display_message = f"Dilemma Choice '{option.get('name', 'N/A')}' Applied!"
    if action_descriptions:
        display_message += "\nChanges:\n* " + "\n* ".join(action_descriptions)
    st.toast(display_message)
    # No phase change here, rerun will take care of displaying YEAR_START without dilemma

def handle_card_toggle_action(card_name):
    """Handles selecting or deselecting a policy card."""
    if 'cards_selected_this_year' not in st.session_state:
        logging.error("handle_card_toggle_action called but 'cards_selected_this_year' not in session state.")
        st.error("Cannot select/deselect card: Game state error.")
        return

    selected_cards = st.session_state.cards_selected_this_year
    max_cards_allowed = 2 # Define max cards here or get from config
    is_selected = card_name in selected_cards

    if is_selected:
        selected_cards.remove(card_name)
        logging.debug(f"Card '{card_name}' deselected.")
    else:
        # Add checks before appending
        if len(selected_cards) >= max_cards_allowed:
            st.warning(f"You can only select up to {max_cards_allowed} cards.")
            logging.debug(f"Attempted to select card '{card_name}' but max cards ({max_cards_allowed}) already selected.")
        else:
            selected_cards.append(card_name)
            logging.debug(f"Card '{card_name}' selected.")
    # No phase change, rerun updates UI

def handle_confirm_policies_action():
    """Handles confirming selected policies and proceeding to simulation."""
    max_cards_allowed = 2 # Define max cards here or get from config
    selected_count = len(st.session_state.get('cards_selected_this_year', []))

    if selected_count > max_cards_allowed:
        st.error(f"Cannot proceed: Too many cards selected ({selected_count}/{max_cards_allowed}). Please deselect cards.")
        logging.warning("Attempted to confirm policies with too many cards selected.")
        return # Stay in the current phase

    logging.info(f"Policies confirmed: {st.session_state.get('cards_selected_this_year', [])}. Proceeding to simulation.")
    st.session_state.game_phase = "SIMULATION"
    # Clean up flags if they exist
    if "year_start_processed" in st.session_state:
        del st.session_state.year_start_processed
    if "dilemma_processed_for_year" in st.session_state:
        # We might keep this to prevent re-triggering dilemma if user goes back somehow,
        # but for now, let's assume linear progression and clean up.
        # Consider the implications if navigation becomes non-linear.
        pass # Keep dilemma_processed_for_year flag for now