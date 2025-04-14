# game_mechanics.py
"""
This module defines the data structures and initial logic for cards and events
from events import CHARACTER_EVENTS
in the SFC Economic Strategy Game.
"""
import numpy as np # Needed for default value
import random
import copy # Needed for deep copying parameters
from cards import POLICY_CARDS # Import card definitions
from events import ECONOMIC_EVENTS # Import event definitions
import streamlit as st # Import streamlit to access session state
from characters import CHARACTERS # Import character definitions
from dilemmas import DILEMMAS # Import dilemma definitions
import logging # Added for logging

# --- Card Definitions (Moved to cards.py) ---

# --- Event Definitions (Moved to events.py) ---


# --- Helper Functions for Dilemma Card Replacement ---

def get_card_policy_type(card_name):
    """Gets the combined policy type (e.g., 'Expansionary Fiscal') for a card."""
    if card_name not in POLICY_CARDS:
        return None
    card_data = POLICY_CARDS[card_name]
    card_type = card_data.get('type')
    card_stance = card_data.get('stance')
    if card_type in ["Fiscal", "Monetary"] and card_stance in ["expansionary", "contractionary"]:
        # Capitalize stance for consistency
        return f"{card_stance.capitalize()} {card_type}"
    # Handle neutral or other types if necessary, for now return None if not standard combo
    return None

def get_generic_equivalent(policy_type):
    """Maps a policy type string to its generic equivalent card name."""
    # This mapping assumes standard cards represent the generic versions
    mapping = {
        "Expansionary Fiscal": "Increase Government Spending", # Default generic
        "Contractionary Fiscal": "Decrease Government Spending", # Default generic
        "Expansionary Monetary": "Interest Rate Cut", # Default generic
        "Contractionary Monetary": "Interest Rate Hike", # Default generic
        # Add more specific mappings if needed based on parameters later
    }
    # More specific overrides based on common parameters (optional refinement)
    # e.g., if policy_type == "Expansionary Fiscal" and card affects 'theta' primarily -> "Cut Income Tax Rate"
    # e.g., if policy_type == "Contractionary Monetary" and card affects 'ADDbl' primarily -> "Quantitative Tightening"
    return mapping.get(policy_type)

def find_card_in_locations(card_name, hand, deck, discard_pile):
    """Checks if a card exists in the hand, deck, or discard pile. Returns location ('hand', 'deck', 'discard') or None."""
    # Check hand first as it's the most immediate location
    if card_name in hand:
        return 'hand'
    if card_name in deck:
        return 'deck'
    if card_name in discard_pile:
        return 'discard'
    return None

def replace_card_in_location(location, card_to_remove, card_to_add, hand, deck, discard_pile):
    """Replaces a card in the specified location (hand, deck, or discard). Adds the new card to the deck."""
    try:
        if location == 'hand':
            hand.remove(card_to_remove)
            deck.append(card_to_add) # Add the new card to the deck for shuffling
            logging.info(f"Replaced '{card_to_remove}' (from hand) with '{card_to_add}' (added to deck).")
            return True
        elif location == 'deck':
            deck.remove(card_to_remove)
            deck.append(card_to_add) # Add the new card to the deck
            logging.info(f"Replaced '{card_to_remove}' with '{card_to_add}' in deck.")
            return True
        elif location == 'discard':
            discard_pile.remove(card_to_remove)
            deck.append(card_to_add) # Add the new card to the deck
            logging.info(f"Replaced '{card_to_remove}' (from discard) with '{card_to_add}' (added to deck).")
            return True
    except ValueError:
        logging.error(f"Failed to remove '{card_to_remove}' from {location} during replacement.")
    return False

def find_and_replace_random_by_type(policy_type, card_to_add, hand, deck, discard_pile):
    """Finds all cards of a specific policy_type in hand, deck, or discard, replaces one randomly."""
    candidates = []
    # Find all candidates in hand
    for i, card_name in enumerate(hand):
        if get_card_policy_type(card_name) == policy_type:
            candidates.append({'name': card_name, 'location': 'hand', 'index': i})
    # Find all candidates in deck
    for i, card_name in enumerate(deck):
        if get_card_policy_type(card_name) == policy_type:
            candidates.append({'name': card_name, 'location': 'deck', 'index': i})
    # Find all candidates in discard
    for i, card_name in enumerate(discard_pile):
         if get_card_policy_type(card_name) == policy_type:
            candidates.append({'name': card_name, 'location': 'discard', 'index': i})

    if not candidates:
        logging.warning(f"No cards of type '{policy_type}' found to replace randomly.")
        return None # Return None if no candidates

    # Choose a random candidate to replace
    chosen_candidate = random.choice(candidates)
    card_to_remove = chosen_candidate['name']
    location = chosen_candidate['location']

    logging.info(f"Randomly selected '{card_to_remove}' of type '{policy_type}' in {location} for replacement.")

    # Perform the replacement
    # Perform the replacement (passing hand now) and return the removed card's name on success
    if replace_card_in_location(location, card_to_remove, card_to_add, hand, deck, discard_pile):
        return card_to_remove # Return name of removed card
    else:
        return None # Return None if replacement failed


# --- Deck and Hand Management (Basic Functions - To be expanded) ---

def create_deck(character_id=None):
    """Creates the starting deck exclusively from the character's defined starting cards.

    Args:
        character_id (str, optional): The ID of the character whose starting deck to create.

    Returns:
        list: A shuffled list of card names for the starting deck, or an empty list
              if the character ID is invalid or has no starting deck defined.
    """
    deck = [] # Initialize deck as empty list
    logging.info(f"Attempting to create deck for character_id: {character_id}")

    if character_id and character_id in CHARACTERS:
        character_data = CHARACTERS[character_id]
        # Use .get() for safety, default to None if key missing
        starting_cards = character_data.get('starting_deck')

        if starting_cards is not None and isinstance(starting_cards, list):
            # Create a copy to avoid modifying the original list in CHARACTERS
            deck = list(starting_cards) # Or copy.copy(starting_cards)
            logging.info(f"Creating starting deck for character '{character_id}' with {len(deck)} cards from 'starting_deck'.")
        else:
            # Log specific reason for empty deck
            if starting_cards is None:
                logging.warning(f"Character ID '{character_id}' found, but 'starting_deck' key is missing. Creating empty deck.")
            elif not isinstance(starting_cards, list):
                 logging.warning(f"Character ID '{character_id}' found, but 'starting_deck' is not a list (type: {type(starting_cards)}). Creating empty deck.")
            # Deck remains empty []
    else:
        if character_id:
            # Log if the specific ID was not found
            logging.warning(f"Character ID '{character_id}' not found in CHARACTERS. Creating empty deck.")
        else:
            # Log if no ID was provided at all
            logging.warning("No character ID provided to create_deck. Creating empty deck.")
        # Deck remains empty []

    logging.debug(f"Deck composition BEFORE shuffle: {deck}") # Log before shuffle
    random.shuffle(deck) # Shuffle the final deck (shuffling empty list is safe)
    logging.info(f"Final starting deck created with {len(deck)} cards.")
    logging.debug(f"Final shuffled deck sample (first 10): {deck[:10]}") # Log sample after shuffle
    return deck

def draw_cards(deck, hand, discard_pile, target_hand_size):
    """
    Draws cards from the deck, attempting to add a specific number of *unique*
    Fiscal or Monetary policy cards to the hand, up to the target_hand_size.
    Existing cards in hand are preserved. Reshuffles discard pile if deck is empty.

    Returns:
        tuple: (updated_deck, updated_hand, updated_discard_pile)
    """
    logging.debug(f"--- Entering draw_cards ---")
    logging.debug(f"Initial state - Deck size: {len(deck)}, Hand: {hand}, Discard size: {len(discard_pile)}, Target size: {target_hand_size}")
    drawn_unique_policy_cards = []
    # Calculate how many *new* unique policy cards we aim to add
    # Note: This assumes the hand might already contain some cards we want to keep.
    # For the Streamlit app, the hand is usually empty at the start of the draw phase.
    unique_policy_in_hand = {card for card in hand if POLICY_CARDS.get(card, {}).get('type') in ["Fiscal", "Monetary"]}
    cards_needed = target_hand_size - len(unique_policy_in_hand)
    logging.debug(f"Unique policy cards currently in hand: {unique_policy_in_hand}")
    logging.debug(f"Need to draw {cards_needed} new unique policy cards.")

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
                logging.info(f"Deck empty. Reshuffling {len(discard_pile)} cards from discard pile: {discard_pile}")
                deck.extend(discard_pile)
                discard_pile = [] # Clear discard pile
                random.shuffle(deck)
                logging.debug(f"Deck reshuffled. New size: {len(deck)}. Sample (first 10): {deck[:10]}")
                drawn_this_cycle = set() # Reset cycle tracking after reshuffle
                # Update initial_deck_size in case it changed (though it shouldn't here)
                initial_deck_size = len(deck) # Reset initial size to new deck size
                # Continue loop with the reshuffled deck

        # Ensure deck is not empty after potential reshuffle before popping
        if not deck:
             logging.warning("Deck still empty after attempting reshuffle. Cannot draw.")
             break

        card_name = deck.pop()
        logging.debug(f"Popped card: '{card_name}'. Deck size now: {len(deck)}")

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
                logging.debug(f"Card '{card_name}' is unique policy card. Adding to drawn_unique_policy_cards.")
                drawn_unique_policy_cards.append(card_name)
                card_added_to_hand = True # Mark that this card went to hand
            else:
                 logging.debug(f"Card '{card_name}' is policy card but not unique this draw cycle or already in hand.")
        else:
             logging.debug(f"Card '{card_name}' is not Fiscal/Monetary type or not found in POLICY_CARDS.")

        # If the card wasn't added to the hand, put it in the discard pile
        if not card_added_to_hand:
            logging.debug(f"Card '{card_name}' not added to hand. Adding to discard pile.")
            discard_pile.append(card_name)

    if drawn_unique_policy_cards:
        hand.extend(drawn_unique_policy_cards)
        logging.info(f"Drew {len(drawn_unique_policy_cards)} unique policy cards: {', '.join(drawn_unique_policy_cards)}")

    logging.debug(f"--- Exiting draw_cards ---")
    logging.debug(f"Final state - Deck size: {len(deck)}, Hand: {hand}, Discard size: {len(discard_pile)}")
    return deck, hand, discard_pile

def check_for_events(year):
    """Retrieves the pre-generated events for the specified year."""
    if 'full_event_sequence' not in st.session_state:
        logging.error("check_for_events called but 'full_event_sequence' not found in session state.")
        st.error("Internal Error: Event sequence not generated.")
        return [] # Return empty list to prevent further errors

    event_sequence = st.session_state.full_event_sequence
    if year not in event_sequence:
        logging.warning(f"Year {year} not found in pre-generated event sequence. Returning empty list.")
        return []

    triggered_events = event_sequence[year]
    logging.debug(f"Retrieved pre-generated events for Year {year}: {triggered_events}")
    return triggered_events

# --- Applying Effects (Revised Logic) ---

# MODIFIED Signature: Added persistent_effects_state and temporary_effects_state arguments
def apply_effects(base_params, latest_solution, persistent_effects_state, temporary_effects_state, cards_played=None, active_events=None, character_id=None):
    """
    Calculates the combined effects of persistent effects, temporary effects,
    cards played this turn, and active events on parameters. Reads/writes persistent
    and temporary effects from/to the provided state dictionaries/lists.

    Args:
        base_params (dict): Dictionary of base numerical parameters (model defaults + exogenous).
        latest_solution (dict): Dictionary of variable values from the previous turn's solution (used for context if needed, not as base).
        persistent_effects_state (dict): The dictionary holding current persistent effects.
        temporary_effects_state (list): The list holding current temporary effects.
        cards_played (list, optional): List of card names played this turn. Defaults to None.
        active_events (list, optional): List of event names active this turn. Defaults to None.
        character_id (str, optional): The ID of the selected character, used for applying bonuses. Defaults to None.

    Returns:
        tuple: (final_params, updated_persistent_effects, updated_temporary_effects)
               - final_params (dict): Final parameters after all effects.
               - updated_persistent_effects (dict): The modified persistent effects dictionary.
               - updated_temporary_effects (list): The modified temporary effects list.
    """
    if cards_played is None:
        cards_played = []
    if active_events is None:
        active_events = []

    # Use the passed-in state directly, ensure they are mutable copies if needed upstream
    current_persistent_effects = persistent_effects_state # This will be updated by new persistent cards
    incoming_temporary_effects = temporary_effects_state # Effects active at the start of the turn
    new_temporary_effects_this_turn = [] # Effects added by cards/events this turn

    # Start with a deep copy of the TRUE base parameters for this turn
    final_params = copy.deepcopy(base_params)
    # We will apply effects in stages:
    # 1. Process cards/events to update persistent state and collect new temporary effects. Apply instant event effects.
    # 2. Apply cumulative persistent effects (now including new ones).
    # 3. Apply all active temporary effects (old and new) and update durations for next turn.
    # logging.debug(f"apply_effects started with base_params keys: {list(final_params.keys())}") # COMMENTED OUT FOR BREVITY
    # Removed block that inherited parameters from latest_solution to fix double-counting.
    # Calculations now start directly from base_params.


    # --- 2. Apply Active Temporary Effects and Update Durations ---
    # --- Process Effects of Cards Played THIS Turn (Update State / Collect New Temp Effects) ---
    # (Card processing loop - lines 366-456 - will modify state/collect effects)

    # --- Process New Event Effects (Apply Instant / Collect Temp) ---
    # (Event processing loop - lines 459-494 - will modify state/collect effects/apply instant)

    # --- Apply Cumulative Persistent Card Effects (Now includes new cards) ---
    # This loop now runs AFTER the card/event processing loops have updated current_persistent_effects
    persistent_effects_applied = {} # Track what was applied
    for param, cumulative_effect in current_persistent_effects.items():
        if param in final_params:
            try:
                # Apply cumulative effect to the current value in final_params
                current_val_before_persist = float(final_params[param])
                new_val = current_val_before_persist + cumulative_effect
                final_params[param] = new_val
                persistent_effects_applied[param] = cumulative_effect # Track what was applied
                logging.info(f"[Persistent Apply] Applied TOTAL cumulative effect for '{param}': {current_val_before_persist:.4f} + {cumulative_effect:.4f} -> {new_val:.4f}")
            except (TypeError, ValueError) as e:
                logging.error(f"[Persistent Apply Error] Could not apply TOTAL persistent effect for param '{param}'. Current Value: {final_params.get(param)}. Error: {e}")
        else:
            logging.warning(f"[Persistent Apply Warning] Param '{param}' from persistent_effects not found in final_params.")


    # --- Apply Active Temporary Effects (Old and New) and Update Durations ---
    next_turn_temporary_effects = [] # Build the list for the *next* turn
    active_temp_effects_applied = {} # Track effects applied this turn

    # Combine incoming effects and newly added temporary effects for processing this turn
    all_temp_effects_to_process = incoming_temporary_effects + new_temporary_effects_this_turn
    logging.debug(f"Processing {len(incoming_temporary_effects)} incoming temp effects and {len(new_temporary_effects_this_turn)} new temp effects.")

    for temp_effect in all_temp_effects_to_process: # Iterate over combined list
        param = temp_effect['param']
        effect = temp_effect['effect']
        source = temp_effect.get('source', 'Unknown Source')
        remaining_duration = temp_effect['remaining_duration']

        # Apply effect if it's still active (duration > 0)
        if remaining_duration > 0:
            if param in final_params:
                try:
                    current_val = float(final_params[param])
                    new_val = current_val + effect
                    final_params[param] = new_val
                    active_temp_effects_applied[param] = active_temp_effects_applied.get(param, 0) + effect # Track cumulative application this turn
                    logging.info(f"[Temp Apply Active] Applied effect from '{source}' to '{param}': {current_val:.4f} + {effect:.4f} -> {new_val:.4f} (Had {remaining_duration} turns left)")
                except (TypeError, ValueError) as e:
                    logging.error(f"[Temp Apply Active Error] Could not apply active temp effect for param '{param}' from '{source}'. Value: {final_params.get(param)}. Error: {e}")
            else:
                logging.warning(f"[Temp Apply Active Warning] Param '{param}' from active temporary effect ({source}) not found in final_params.")

        # Decrement duration *after* applying the effect for this turn
        temp_effect['remaining_duration'] -= 1

        # Keep the effect for the next turn only if duration is still positive
        if temp_effect['remaining_duration'] > 0:
            next_turn_temporary_effects.append(temp_effect)
        else:
             logging.info(f"[Temp Expire] Temporary effect from '{source}' on param '{param}' expired.")

    # Note: The state list `incoming_temporary_effects` is effectively replaced by `next_turn_temporary_effects` at the end.

    # --- Process Effects of Cards Played THIS Turn (Update State / Collect New Temp Effects) ---
    # This section now primarily updates state dictionaries/lists
    for card_name in cards_played:
        if card_name not in POLICY_CARDS:
            logging.warning(f"Card '{card_name}' not found in POLICY_CARDS. Skipping.")
            continue

        card_data = POLICY_CARDS[card_name]
        card_effects_list = card_data.get('effects', [])
        card_stance = card_data.get('stance')
        card_type = card_data.get('type')
        card_duration = card_data.get('duration') # Check for duration

        if not isinstance(card_effects_list, list):
            logging.error(f"Card '{card_name}' has invalid 'effects' format. Skipping card.")
            continue

        # --- Apply Character Bonus (Check once per card) ---
        bonus_multiplier_to_apply = 1.0
        bonus_applied_log = False
        if character_id and character_id in CHARACTERS and card_stance and card_type:
            character_data = CHARACTERS[character_id]
            bonus_criteria = character_data.get('bonus_criteria', [])
            bonus_multiplier = character_data.get('bonus_multiplier', 1.0)
            criteria_matched = any(
                card_stance == crit_stance and card_type.lower() == crit_type.lower()
                for crit_stance, crit_type in bonus_criteria
            )
            if criteria_matched:
                bonus_multiplier_to_apply = bonus_multiplier
                bonus_applied_log = True
                logging.info(f"Character '{character_id}' bonus ({bonus_multiplier_to_apply}x) applies to '{card_name}'.")
        # --- End Character Bonus ---

        # --- Iterate through each effect dictionary in the list ---
        for effect_dict in card_effects_list:
            param = effect_dict.get('param')
            base_effect = effect_dict.get('effect')

            if param is None or base_effect is None:
                logging.warning(f"Invalid effect dictionary in card '{card_name}': {effect_dict}. Skipping effect.")
                continue

            # Apply the bonus multiplier
            actual_effect = base_effect * bonus_multiplier_to_apply
            log_prefix = "[Effect Bonus]" if bonus_applied_log else "[Effect]"

            # --- Handle Persistent vs Temporary Card Effects ---
            if card_duration is None or card_duration <= 0: # PERSISTENT Card (or duration 0/invalid)
                # Update the persistent effects state dictionary
                current_persistent_total = current_persistent_effects.get(param, 0.0)
                new_persistent_total = current_persistent_total + actual_effect
                current_persistent_effects[param] = new_persistent_total # Update the dict directly
                logging.info(f"[Persistent Update] Card '{card_name}' updated cumulative effect for '{param}' from {current_persistent_total:.4f} to {new_persistent_total:.4f} (added {actual_effect:.4f})")
                # Log the update to the persistent state. The cumulative effect will be applied later.
                logging.info(f"{log_prefix} Card '{card_name}' (Persistent) updated state for '{param}'. Effect: {actual_effect:.4f}. New Total Persist State: {new_persistent_total:.4f}")

            elif card_duration > 0: # TEMPORARY Card
                # Collect the effect details to be processed later in the temporary effects block
                if param is not None and actual_effect is not None:
                    new_effect_data = {
                        'source': f"Card: {card_name}",
                        'param': param,
                        'effect': actual_effect, # Store the delta effect
                        'remaining_duration': card_duration # Store the initial duration
                    }
                    new_temporary_effects_this_turn.append(new_effect_data)
                    logging.info(f"{log_prefix} Card '{card_name}' (Temp Duration: {card_duration}) collecting new temporary effect for '{param}': {actual_effect:.4f}. Will be processed later.")
                    logging.info(f"[Temp Collect] Collecting temporary effect from card '{card_name}' on '{param}' for {card_duration} turns.")
                else:
                    logging.warning(f"Skipping temporary effect collection for card '{card_name}' due to missing data (param/effect).")
            # else: card_duration is likely invalid (e.g., negative), treat as persistent or log warning?
            # Current logic treats None or <= 0 as persistent.

        # --- End of loop through effects list for a single card ---

    # --- Process New Event Effects (Apply Instant / Collect Temp) ---
    # These are processed after cards.
    for event_name in active_events:
         if event_name in ECONOMIC_EVENTS:
            event = ECONOMIC_EVENTS[event_name]
            param = event.get('param')
            effect = event.get('effect')
            duration = event.get('duration')

            if param is None or effect is None:
                logging.warning(f"Event '{event_name}' has missing param or effect. Skipping.")
                continue

            # Check if the event effect is temporary or instant
            if duration is not None and duration > 0: # Temporary Event
                # Collect the effect details to be processed later in the temporary effects block
                if param is not None and effect is not None:
                    new_effect_data = {
                        'source': f"Event: {event_name}",
                        'param': param,
                        'effect': effect, # Store the delta effect
                        'remaining_duration': duration # Store the initial duration
                    }
                    new_temporary_effects_this_turn.append(new_effect_data)
                    logging.info(f"[Temp Collect] Collecting temporary effect from event '{event_name}' on '{param}' for {duration} turns. Effect: {effect:.4f}")
                else:
                    logging.warning(f"Skipping temporary effect collection for event '{event_name}' due to missing data (param/effect).")
            else:
                # Instant Event: Apply directly to final_params now.
                if param in final_params:
                    # Get current value *from the dictionary we are modifying*
                    current_value = final_params.get(param) # Should exist if check passes

                    # Ensure we are working with floats
                    try:
                        current_float = float(current_value) # Use current value from final_params
                        new_value = current_float + effect
                        final_params[param] = new_value # Update the dictionary
                        logging.info(f"[Instant Effect] Event '{event_name}' changing '{param}' from {current_float:.4f} to {new_value:.4f}")
                    except (TypeError, ValueError) as e:
                         logging.error(f"[Instant Effect Error] Event '{event_name}' failed for param '{param}'. Value: {current_value}. Error: {e}")
                else:
                    logging.warning(f"[Instant Effect Warning] Param '{param}' not found in final_params for instant event '{event_name}'.")
         else:
             logging.warning(f"Event '{event_name}' not found in ECONOMIC_EVENTS.")

    # logging.debug(f"apply_effects finished. Returning final_params keys: {list(final_params.keys())}") # COMMENTED OUT FOR BREVITY
    # MODIFIED: Return the updated state dictionaries/lists
    # Return the calculated parameters and the updated state lists/dicts for the *next* turn
    return final_params, current_persistent_effects, next_turn_temporary_effects


def select_dilemma(advisor_id, seen_dilemmas, removed_cards_this_playthrough):
    """
    Selects a random, unseen dilemma for the given advisor, avoiding dilemmas
    that remove cards already targeted for removal this playthrough.

    Args:
        advisor_id (str): The ID of the current advisor.
        seen_dilemmas (set): A set of dilemma IDs already presented to the player.
        removed_cards_this_playthrough (set): A set of card names targeted for removal by dilemmas this playthrough.

    Returns:
        tuple: (dilemma_id, dilemma_data) if an unseen, valid dilemma is found,
               otherwise (None, None).
    """
    if advisor_id not in DILEMMAS:
        logging.error(f"Advisor ID '{advisor_id}' not found in DILEMMAS.")
        return None, None

    advisor_dilemmas = DILEMMAS[advisor_id]
    available_dilemma_ids = list(advisor_dilemmas.keys())

    unseen_dilemma_ids = [d_id for d_id in available_dilemma_ids if d_id not in seen_dilemmas]

    if not unseen_dilemma_ids:
        logging.info(f"No unseen dilemmas available for advisor '{advisor_id}'.")
        return None, None

    # Filter out dilemmas that try to remove already-removed cards
    valid_dilemma_ids = []
    for d_id in unseen_dilemma_ids:
        dilemma_data = advisor_dilemmas[d_id]
        removes_invalid_card = False
        # Check both options within the dilemma data structure
        for option_key in ['option_1', 'option_2']:
            if option_key in dilemma_data:
                cards_to_remove = dilemma_data[option_key].get('remove_cards', [])
                if any(card in removed_cards_this_playthrough for card in cards_to_remove):
                    removes_invalid_card = True
                    logging.debug(f"Filtering out dilemma '{d_id}' because option '{option_key}' removes already targeted card(s): {set(cards_to_remove) & removed_cards_this_playthrough}")
                    break # No need to check the other option
        if not removes_invalid_card:
            valid_dilemma_ids.append(d_id)

    if not valid_dilemma_ids: # Check if filtering left any dilemmas
        logging.warning(f"No unseen dilemmas available for advisor '{advisor_id}' after filtering for removed cards.")
        return None, None

    selected_dilemma_id = random.choice(valid_dilemma_ids) # Choose from valid ones
    selected_dilemma_data = advisor_dilemmas[selected_dilemma_id]
    logging.info(f"Selected dilemma '{selected_dilemma_id}' for advisor '{advisor_id}' (passed removal filter).")

    return selected_dilemma_id, selected_dilemma_data

# --- MODIFIED apply_dilemma_choice ---
def apply_dilemma_choice(chosen_option, hand, deck, discard_pile):
    """
    Applies the effects of a chosen dilemma option to the hand, deck, and discard pile,
    searching all locations for replacements/removals.

    Args:
        chosen_option (dict): The dictionary representing the chosen option
                              (containing 'add_cards' and 'remove_cards' lists).
        hand (list): The current hand list.
        deck (list): The current deck list.
        discard_pile (list): The current discard pile list.

    Returns:
        tuple: (updated_hand, updated_deck, updated_discard_pile, action_descriptions)
    """
    action_descriptions = [] # Initialize list to store descriptions
    cards_to_add_specific = chosen_option.get('add_cards', [])
    cards_to_remove = chosen_option.get('remove_cards', [])
    card_action_completed = False # Flag to ensure only ONE card action (replace/add) occurs

    logging.info(f"--- Applying Dilemma Choice ---")
    logging.info(f"Attempting to add: {cards_to_add_specific}")
    logging.info(f"Attempting to remove: {cards_to_remove}")
    logging.debug(f"Initial deck size: {len(deck)}, discard size: {len(discard_pile)}")
    # --- Roo Debug Log Start ---
    logging.debug(f"State before ADD: Hand ({len(hand)} cards): {hand}")
    logging.debug(f"State before ADD: Deck ({len(deck)} cards): {deck}")
    logging.debug(f"State before ADD: Discard ({len(discard_pile)} cards): {discard_pile}")
    # --- Roo Debug Log End ---
    # --- New Logic for Adding/Replacing ONE Card ---
    for specific_card in cards_to_add_specific:
        if card_action_completed: # If we already added/replaced a card, stop processing more.
            break

        policy_type = get_card_policy_type(specific_card)
        generic_equivalent = get_generic_equivalent(policy_type) if policy_type else None
        replaced = False

        if policy_type and generic_equivalent:
            logging.debug(f"Processing ADD '{specific_card}' (Type: {policy_type}, Generic: {generic_equivalent})")
            # 1. Try replacing generic equivalent
            # --- Roo Debug Log Start ---
            logging.debug(f"Attempting to find generic '{generic_equivalent}' in hand/deck/discard for replacement.")
            # --- Roo Debug Log End ---
            generic_location = find_card_in_locations(generic_equivalent, hand, deck, discard_pile)
            if generic_location:
                # --- Roo Debug Log Start ---
                logging.debug(f"Found generic '{generic_equivalent}' in '{generic_location}'. Attempting replacement.")
                # --- Roo Debug Log End ---
                replaced = replace_card_in_location(generic_location, generic_equivalent, specific_card, hand, deck, discard_pile)
                if replaced:
                     logging.info(f"Successfully replaced generic '{generic_equivalent}' with specific '{specific_card}'.")
                     action_descriptions.append(f"Added '{specific_card}', replacing '{generic_equivalent}'")
                     card_action_completed = True # Mark action as done
                     break # Exit the ADD CARD loop immediately
                # --- Roo Debug Log Start ---
                else:
                    logging.warning(f"Replacement of generic '{generic_equivalent}' in '{generic_location}' FAILED.")
                # --- Roo Debug Log End ---
            # 2. If generic not found or replacement failed, try replacing random of same type
            if not replaced:
                # --- Roo Debug Log Start ---
                logging.debug(f"Generic '{generic_equivalent}' not found or replacement failed. Trying random replacement of type '{policy_type}'.")
                # --- Roo Debug Log End ---
                logging.debug(f"Generic '{generic_equivalent}' not found in hand/deck/discard or replacement failed. Trying random replacement of type '{policy_type}'.")
                # Now returns the name of the replaced card or None
                replaced_card_name = find_and_replace_random_by_type(policy_type, specific_card, hand, deck, discard_pile)
                if replaced_card_name:
                    logging.info(f"Successfully replaced random card '{replaced_card_name}' of type '{policy_type}' with specific '{specific_card}'.")
                    action_descriptions.append(f"Added '{specific_card}', replacing '{replaced_card_name}' (random {policy_type})")
                    card_action_completed = True # Mark action as done
                    break # Exit the ADD CARD loop immediately
                # --- Roo Debug Log Start ---
                else:
                    logging.debug(f"Random replacement of type '{policy_type}' for '{specific_card}' also failed.")
                # --- Roo Debug Log End ---
        # --- Roo Debug Log Start ---
        elif not policy_type:
             logging.warning(f"Could not determine policy type for card '{specific_card}'. Skipping replacement.")
        elif not generic_equivalent:
             logging.warning(f"Could not determine generic equivalent for policy type '{policy_type}' (Card: '{specific_card}'). Skipping replacement.")
        # --- Roo Debug Log End ---

        # 3. If no replacement occurred (no generic, no same type, or invalid type), add directly
        # 3. Fallback: If no replacement occurred *for this card* AND no action completed yet overall
        if not replaced and not card_action_completed:
            # If no replacement happened for this specific card (due to missing generic, failed random replace, or invalid type), add it directly.
            logging.info(f"Card '{specific_card}' could not replace another card (or type unknown/generic missing). Adding directly to deck as the primary action.")
            deck.append(specific_card)
            action_descriptions.append(f"Added '{specific_card}' directly to deck")
            card_action_completed = True # Mark action as done
            break # Exit the ADD CARD loop immediately
    # --- Original Logic for Removing Cards ---
    # Process removals *after* additions/replacements to avoid conflicts if a removed card was also a replacement target
    # --- Roo Debug Log Start ---
    logging.debug(f"State before REMOVE: Hand ({len(hand)} cards): {hand}")
    logging.debug(f"State before REMOVE: Deck ({len(deck)} cards): {deck}")
    logging.debug(f"State before REMOVE: Discard ({len(discard_pile)} cards): {discard_pile}")
    # --- Roo Debug Log End ---
    for card_to_remove in cards_to_remove:
        removed_from_hand = False
        removed_from_deck = False
        removed_from_discard = False
        logging.debug(f"Attempting to remove '{card_to_remove}' from hand/deck/discard.")

        # Try removing from hand first
        if card_to_remove in hand:
            try:
                hand.remove(card_to_remove)
                logging.info(f"Removed card '{card_to_remove}' from hand.")
                removed_from_hand = True
            except ValueError:
                 logging.error(f"Error removing '{card_to_remove}' from hand despite check.") # Should not happen
        else:
            logging.debug(f"'{card_to_remove}' not found in hand.")

        # If not removed from hand, try removing from deck
        if not removed_from_hand:
            if card_to_remove in deck:
                try:
                    deck.remove(card_to_remove)
                    logging.info(f"Removed card '{card_to_remove}' from deck.")
                    removed_from_deck = True
                except ValueError:
                     logging.error(f"Error removing '{card_to_remove}' from deck despite check.") # Should not happen
            else:
                logging.debug(f"'{card_to_remove}' not found in deck.")

        # If not removed from hand or deck, try removing from discard pile
        if not removed_from_hand and not removed_from_deck:
             if card_to_remove in discard_pile:
                 try:
                     discard_pile.remove(card_to_remove)
                     logging.info(f"Removed card '{card_to_remove}' from discard pile.")
                     removed_from_discard = True
                 except ValueError:
                     logging.error(f"Error removing '{card_to_remove}' from discard despite check.") # Should not happen
             else:
                 logging.debug(f"'{card_to_remove}' not found in discard either.")

        # Log warning only if not found anywhere
        if not removed_from_hand and not removed_from_deck and not removed_from_discard:
            logging.warning(f"Card '{card_to_remove}' specified for removal not found in hand, deck, or discard pile.")

    # Shuffle the deck after all modifications
    random.shuffle(deck)
    logging.info("Deck shuffled after applying dilemma choice.")
    logging.debug(f"Final deck size: {len(deck)}, discard size: {len(discard_pile)}")
    logging.info(f"--- Finished Applying Dilemma Choice ---")

    # Return updated lists and descriptions
    return hand, deck, discard_pile, action_descriptions
