"""
This module defines the data structures and initial logic for cards and events
in the SFC Economic Strategy Game.
"""
import numpy as np # Needed for default value
import random
import copy # Needed for deep copying parameters
from cards import POLICY_CARDS # Import card definitions
from events import ECONOMIC_EVENTS # Import event definitions
import logging # Added for logging

# --- Card Definitions (Moved to cards.py) ---

# --- Event Definitions (Moved to events.py) ---

# --- Deck and Hand Management (Basic Functions - To be expanded) ---

def create_deck():
    """Creates a standard deck of policy cards."""
    # Simple approach: multiple copies of each card
    deck = list(POLICY_CARDS.keys()) * 3 # Example: 3 copies of each policy card
    random.shuffle(deck)
    return deck

def draw_cards(deck, hand, target_hand_size):
    """
    Draws cards from the deck, attempting to add a specific number of *unique*
    Fiscal or Monetary policy cards to the hand, up to the target_hand_size.
    Existing cards in hand are preserved.
    """
    drawn_unique_policy_cards = []
    # Calculate how many *new* unique policy cards we aim to add
    # Note: This assumes the hand might already contain some cards we want to keep.
    # For the Streamlit app, the hand is usually empty at the start of the draw phase.
    unique_policy_in_hand = {card for card in hand if POLICY_CARDS.get(card, {}).get('type') in ["Fiscal", "Monetary"]}
    cards_needed = target_hand_size - len(unique_policy_in_hand)

    if cards_needed <= 0:
        logging.debug(f"Hand already meets or exceeds target unique policy cards ({len(unique_policy_in_hand)}/{target_hand_size}). No draw needed.")
        return deck, hand # Target already met or exceeded

    # Keep track of cards drawn this cycle to avoid infinite loops if deck cycles
    drawn_this_cycle = set()
    initial_deck_size = len(deck)

    while len(drawn_unique_policy_cards) < cards_needed:
        if not deck:
            # Reshuffle discard pile if deck is empty (implement later if needed)
            logging.warning("Deck empty, cannot draw more cards.") # Use logging
            break # Stop if deck is empty

        card_name = deck.pop()

        # Check if we've cycled through the entire deck without finding enough cards
        if card_name in drawn_this_cycle and len(drawn_this_cycle) >= initial_deck_size:
             logging.warning(f"Cycled through deck, could not find enough unique policy cards. Found {len(drawn_unique_policy_cards)}/{cards_needed}.")
             break
        drawn_this_cycle.add(card_name)

        card_info = POLICY_CARDS.get(card_name)
        if card_info and card_info.get('type') in ["Fiscal", "Monetary"]:
            # Check if it's unique among cards already in hand AND cards drawn this turn
            if card_name not in unique_policy_in_hand and card_name not in drawn_unique_policy_cards:
                drawn_unique_policy_cards.append(card_name)

    if drawn_unique_policy_cards:
        hand.extend(drawn_unique_policy_cards)
        logging.info(f"Drew {len(drawn_unique_policy_cards)} unique policy cards: {', '.join(drawn_unique_policy_cards)}")

    return deck, hand

def check_for_events(model_state):
    """Checks conditions and randomly triggers events."""
    # TODO: Implement proper event triggering based on model_state conditions
    triggered_events = []
    # Example: Simple random chance for now
    for event_name, event_data in ECONOMIC_EVENTS.items():
        # Placeholder: Check if event has a probability defined
        probability = event_data.get('probability', 0.05) # Default 5% if not specified
        if random.random() < probability:
             triggered_events.append(event_name)

    # Limit number of events per year?
    max_events_per_year = 2
    if len(triggered_events) > max_events_per_year:
        triggered_events = random.sample(triggered_events, max_events_per_year)

    return triggered_events

# --- Applying Effects (Revised Logic) ---

def apply_effects(base_params, latest_solution, cards_played=None, active_events=None):
    """
    Calculates the combined effects of cards and events on parameters.

    Args:
        base_params (dict): Dictionary of base numerical parameters for the turn.
        latest_solution (dict): Dictionary of variable values from the previous turn's solution.
        cards_played (list, optional): List of card names played this turn. Defaults to None.
        active_events (list, optional): List of event names active this turn. Defaults to None.

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

    # Apply card effects
    for card_name in cards_played:
        if card_name in POLICY_CARDS:
            card = POLICY_CARDS[card_name]
            param = card['param']
            effect = card['effect']

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
                logging.info(f"[Effect] Card '{card_name}' changing {param} from {current_float:.4f} to {new_value:.4f}")
            except (TypeError, ValueError) as e:
                 logging.error(f"[Effect Error] Card '{card_name}' failed for param '{param}'. Value: {current_value}. Error: {e}")

    # Apply event effects (potentially cumulative on card effects)
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
            except (TypeError, ValueError) as e:
                 logging.error(f"[Effect Error] Event '{event_name}' failed for param '{param}'. Value: {current_value}. Error: {e}")


    return final_params # Return the dictionary of modified parameters