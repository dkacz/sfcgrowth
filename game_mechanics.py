"""
This module defines the data structures and initial logic for cards and events
in the SFC Economic Strategy Game.
"""
import numpy as np # Needed for default value
import random
import copy # Needed for deep copying parameters
from cards import POLICY_CARDS # Import card definitions
from events import ECONOMIC_EVENTS # Import event definitions
import streamlit as st # Import streamlit to access session state
from characters import CHARACTERS # Import character definitions
import logging # Added for logging

# --- Card Definitions (Moved to cards.py) ---

# --- Event Definitions (Moved to events.py) ---

# --- Deck and Hand Management (Basic Functions - To be expanded) ---

def create_deck(character_id=None):
    """Creates a deck of policy cards.

    If a character_id is provided, cards preferred by that character
    will be more prevalent in the deck. Otherwise, creates a standard
    deck with equal distribution.
    """
    # Base deck: 2 copies of each policy card
    base_deck = list(POLICY_CARDS.keys()) * 2
    deck = list(base_deck) # Start with the base deck

    if character_id and character_id in CHARACTERS:
        # Add extra copies of the character's preferred cards
        # Note: 'starting_deck' in characters.py now represents the *additional* cards
        preferred_cards = CHARACTERS[character_id].get('starting_deck', [])
        deck.extend(preferred_cards) # Add the preferred list to the base deck
        logging.info(f"Creating deck biased towards character: {character_id}")
    else:
        if character_id:
            logging.warning(f"Character ID '{character_id}' not found. Creating default deck.")
        # If no character or invalid ID, the deck remains the base deck
        logging.info("Creating default deck.")

    random.shuffle(deck) # Shuffle the final combined deck
    logging.info(f"Deck created with {len(deck)} cards.")
    return deck

def draw_cards(deck, hand, discard_pile, target_hand_size):
    """
    Draws cards from the deck, attempting to add a specific number of *unique*
    Fiscal or Monetary policy cards to the hand, up to the target_hand_size.
    Existing cards in hand are preserved. Reshuffles discard pile if deck is empty.

    Returns:
        tuple: (updated_deck, updated_hand, updated_discard_pile)
    """
    drawn_unique_policy_cards = []
    # Calculate how many *new* unique policy cards we aim to add
    # Note: This assumes the hand might already contain some cards we want to keep.
    # For the Streamlit app, the hand is usually empty at the start of the draw phase.
    unique_policy_in_hand = {card for card in hand if POLICY_CARDS.get(card, {}).get('type') in ["Fiscal", "Monetary"]}
    cards_needed = target_hand_size - len(unique_policy_in_hand)

    if cards_needed <= 0:
        logging.debug(f"Hand already meets or exceeds target unique policy cards ({len(unique_policy_in_hand)}/{target_hand_size}). No draw needed.")
        return deck, hand, discard_pile # Target already met or exceeded

    # Keep track of cards drawn this cycle to avoid infinite loops if deck cycles
    drawn_this_cycle = set()
    # Use combined size for cycle check after potential reshuffle
    initial_deck_size = len(deck) + len(discard_pile) # Check against total available cards

    while len(drawn_unique_policy_cards) < cards_needed:
        if not deck:
            if not discard_pile:
                logging.warning("Deck and discard pile empty. Cannot draw more cards.")
                break # Stop if both are empty
            else:
                # Reshuffle discard pile into deck
                logging.info(f"Deck empty. Reshuffling {len(discard_pile)} cards from discard pile.")
                deck.extend(discard_pile)
                discard_pile = [] # Clear discard pile
                random.shuffle(deck)
                drawn_this_cycle = set() # Reset cycle tracking after reshuffle
                # Update initial_deck_size in case it changed (though it shouldn't here)
                initial_deck_size = len(deck) # Reset initial size to new deck size
                # Continue loop with the reshuffled deck

        # Ensure deck is not empty after potential reshuffle before popping
        if not deck:
             logging.warning("Deck still empty after attempting reshuffle. Cannot draw.")
             break

        card_name = deck.pop()

        # Add card to discard pile *after* drawing it and processing it
        # We will add it later, only if it's not added to the hand

        # Check if we've cycled through the entire deck without finding enough cards
        # Use >= check for safety, although == should be sufficient if logic is correct
        if card_name in drawn_this_cycle and len(drawn_this_cycle) >= initial_deck_size:
             logging.warning(f"Cycled through deck ({len(drawn_this_cycle)}/{initial_deck_size}), could not find enough unique policy cards. Found {len(drawn_unique_policy_cards)}/{cards_needed}.")
             # Put the last drawn card back if we break due to cycling
             discard_pile.append(card_name)
             break
        drawn_this_cycle.add(card_name)

        card_info = POLICY_CARDS.get(card_name)
        card_added_to_hand = False
        if card_info and card_info.get('type') in ["Fiscal", "Monetary"]:
            # Check if it's unique among cards already in hand AND cards drawn this turn
            if card_name not in unique_policy_in_hand and card_name not in drawn_unique_policy_cards:
                drawn_unique_policy_cards.append(card_name)
                card_added_to_hand = True # Mark that this card went to hand

        # If the card wasn't added to the hand, put it in the discard pile
        if not card_added_to_hand:
            discard_pile.append(card_name)

    if drawn_unique_policy_cards:
        hand.extend(drawn_unique_policy_cards)
        logging.info(f"Drew {len(drawn_unique_policy_cards)} unique policy cards: {', '.join(drawn_unique_policy_cards)}")

    return deck, hand, discard_pile

def check_for_events(model_state):
    """Checks conditions and randomly triggers events based on defined probabilities."""
    # TODO: Implement state-dependent trigger conditions later if needed.
    triggered_events = []
    for event_name, event_data in ECONOMIC_EVENTS.items():
        # Use the defined probability for each event
        probability = event_data.get('probability', 0.0) # Default to 0 if not specified
        if random.random() < probability:
             triggered_events.append(event_name)
             logging.info(f"Event Triggered (Prob: {probability:.2f}): {event_name}")
    # --- Resolve Contradictory Events ---
    contradiction_sets = [
        {"Global Recession", "Global Boom"},
        {"Banking Sector Stress", "Banking Sector Calm"},
        {"Financial Market Stress", "Financial Market Rally"},
        {"Productivity Boom", "Productivity Bust"},
        {"Credit Boom", "Credit Crunch"},
        {"Infrastructure Investment Boom", "Natural Disaster"} # Assuming these are contradictory capital shocks
        # Add more pairs if needed (e.g., based on new inflation events if they have opposites)
    ]
    resolved_events = list(triggered_events) # Work on a copy
    for contradictory_pair in contradiction_sets:
        present_in_pair = [event for event in resolved_events if event in contradictory_pair]
        if len(present_in_pair) > 1:
            # Contradiction found! Keep only one randomly.
            keep_one = random.choice(present_in_pair)
            logging.warning(f"Contradiction detected: {present_in_pair}. Keeping '{keep_one}'.")
            # Remove all others from the pair that are in the resolved list
            for event_to_remove in present_in_pair:
                if event_to_remove != keep_one and event_to_remove in resolved_events:
                    resolved_events.remove(event_to_remove)
    triggered_events = resolved_events # Update the original list with resolved events
    # --- End Contradiction Resolution ---


    # Limit number of events per year? (Optional)
    max_events_per_year = 2
    if len(triggered_events) > max_events_per_year:
        logging.info(f"Limiting triggered events from {len(triggered_events)} to {max_events_per_year}.")
        triggered_events = random.sample(triggered_events, max_events_per_year)

    return triggered_events

# --- Applying Effects (Revised Logic) ---

def apply_effects(base_params, latest_solution, cards_played=None, active_events=None, character_id=None):
    """
    Calculates the combined effects of cards and events on parameters.

    Args:
        base_params (dict): Dictionary of base numerical parameters for the turn.
        latest_solution (dict): Dictionary of variable values from the previous turn's solution.
        cards_played (list, optional): List of card names played this turn. Defaults to None.
        active_events (list, optional): List of event names active this turn. Defaults to None.
        character_id (str, optional): The ID of the selected character, used for applying bonuses. Defaults to None.

    Returns:
        dict: A dictionary containing the final numerical parameter values for the current turn,
              reflecting the applied effects.
    """
    if cards_played is None:
        cards_played = []
    if active_events is None:
        active_events = []

    # Start with a deep copy of the base parameters to modify
    final_params = copy.deepcopy(base_params)

    # --- Process and Revert Expired Temporary Effects ---
    if 'temporary_effects' not in st.session_state:
        # Initialize if somehow missing (should have been done in streamlit app)
        st.session_state.temporary_effects = []
        logging.warning("Initialized st.session_state.temporary_effects in apply_effects.")

    expired_effects_to_revert = []

    # Iterate through existing temporary effects using list() to allow safe removal
    for temp_effect in list(st.session_state.temporary_effects):
        temp_effect['remaining_duration'] -= 1
        if temp_effect['remaining_duration'] <= 0:
            # Mark for reversion
            expired_effects_to_revert.append(temp_effect)
            logging.info(f"[Effect Revert] Expired temporary effect for event '{temp_effect['event_name']}' on param '{temp_effect['param']}'.")
            # Remove from original list
            st.session_state.temporary_effects.remove(temp_effect)
        # No else needed, effects that are not expired remain in st.session_state.temporary_effects

    # Apply reversions to final_params *before* applying new effects
    for expired_effect in expired_effects_to_revert:
        param_to_revert = expired_effect['param']
        effect_to_revert = expired_effect['effect'] # The original magnitude
        if param_to_revert in final_params:
            try:
                current_val = float(final_params[param_to_revert])
                reverted_val = current_val - effect_to_revert # Subtract the original effect
                final_params[param_to_revert] = reverted_val
                logging.info(f"[Effect Revert] Reverted '{param_to_revert}' from {current_val:.4f} to {reverted_val:.4f} (removed effect: {effect_to_revert:.4f})")
            except (TypeError, ValueError) as e:
                logging.error(f"[Effect Revert Error] Could not revert param '{param_to_revert}'. Value: {final_params[param_to_revert]}. Error: {e}")
        else:
            logging.warning(f"[Effect Revert Warning] Param '{param_to_revert}' not found in final_params during reversion.")

    # Apply card effects
    for card_name in cards_played:
        if card_name in POLICY_CARDS:
            card = POLICY_CARDS[card_name]
            param = card['param']
            effect = card['effect']
            card_stance = card.get('stance')
            card_type = card.get('type')

            # --- Apply Character Bonus (Updated Logic) ---
            bonus_applied = False
            if character_id and character_id in CHARACTERS and card_stance and card_type:
                character_data = CHARACTERS[character_id]
                bonus_criteria = character_data.get('bonus_criteria', [])
                bonus_multiplier = character_data.get('bonus_multiplier', 1.0)
 # Default to 1.0 (no bonus)

                # Check if the card's (stance, type) tuple matches any criteria
                criteria_matched = False
                for crit_stance, crit_type in bonus_criteria:
                    # Corrected: Compare card_type (already lower) with crit_type.lower()
                    if card_stance == crit_stance and card_type.lower() == crit_type.lower(): # Ensure case-insensitive comparison
                        criteria_matched = True
                        break

                if criteria_matched:
                    original_effect = effect
                    effect *= bonus_multiplier
 # Apply the multiplier
                    bonus_applied = True
                    logging.info(f"Character '{character_id}' bonus ({bonus_multiplier}x) applied to '{card_name}'. Effect: {original_effect:.4f} -> {effect:.4f}")
            # --- End Character Bonus ---

            # Get current value *from the dictionary we are modifying*
            # Fallback to base_params if somehow not yet in final_params (shouldn't happen with deepcopy)
            current_value = final_params.get(param, base_params.get(param, 0.0))

            # Ensure we are working with floats
            try:
                current_float = float(current_value)
                new_value = current_float + effect

                # Apply bounds if necessary (e.g., rates shouldn't go excessively negative)
                # Example: if param == 'Rbbar': new_value = max(0, new_value)

                final_params[param] = new_value # Update the dictionary
                # Use logging instead of print
                log_prefix = "[Effect Bonus]" if bonus_applied else "[Effect]"
                logging.info(f"{log_prefix} Card '{card_name}' changing {param} from {current_float:.4f} to {new_value:.4f}")
            except (TypeError, ValueError) as e:
                 logging.error(f"[Effect Error] Card '{card_name}' failed for param '{param}'. Value: {current_value}. Error: {e}")

    # Apply event effects (potentially cumulative on card effects)
    # Note: newly_added_temporary_effects is now handled by directly appending to session_state below
    for event_name in active_events:
         if event_name in ECONOMIC_EVENTS:
            event = ECONOMIC_EVENTS[event_name]
            param = event['param']
            effect = event['effect']

            # Get current value *from the dictionary we are modifying*
            # This now includes any changes made by cards
            current_value = final_params.get(param, base_params.get(param, 0.0))

            # Ensure we are working with floats
            try:
                current_float = float(current_value)
                new_value = current_float + effect

                # Apply bounds if necessary
                # Example: if param == 'GRpr': new_value = max(-0.1, new_value) # Prevent extreme negative growth

                final_params[param] = new_value # Update the dictionary
                # Use logging instead of print
                logging.info(f"[Effect] Event '{event_name}' changing {param} from {current_float:.4f} to {new_value:.4f}")

                # --- Check and Track New Temporary Event ---
                duration = event.get('duration')
                if duration is not None and duration > 0:
                    new_temp_effect_data = {
                        'event_name': event_name,
                        'param': param,
                        'effect': effect, # Store the actual effect magnitude applied
                        'remaining_duration': duration
                    }
                    # Append directly to session state list
                    st.session_state.temporary_effects.append(new_temp_effect_data)
                    logging.info(f"[Effect Track] Tracking temporary effect from '{event_name}' on '{param}' for {duration} turns.")

            except (TypeError, ValueError) as e:
                 logging.error(f"[Effect Error] Event '{event_name}' failed for param '{param}'. Value: {current_value}. Error: {e}")

    # No need to update session state here anymore, it was modified directly in the loop

    return final_params # Return the dictionary of modified parameters