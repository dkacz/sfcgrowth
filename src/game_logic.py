# src/game_logic.py
"""Handles the main game loop, phase transitions, and action processing."""

import streamlit as st
import logging
import pandas as pd
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