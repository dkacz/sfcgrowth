# src/state_manager.py
"""Manages the initialization and potentially updates of the game state."""

import streamlit as st
import logging

# Import model components needed for initialization
from chapter_11_model_growth import (
    create_growth_model, growth_parameters, growth_exogenous, growth_variables
)
from pysolve.model import Model # Import Model class

def initialize_game_state():
    """Initializes the game state in st.session_state if not already done."""
    if "game_initialized" not in st.session_state:
        st.session_state.game_initialized = True
        logging.info("--- Initializing Game State (Starting Year 0) ---")
        st.session_state.current_year = 0
        # Start with CHARACTER_SELECTION phase
        st.session_state.game_phase = "CHARACTER_SELECTION"
        st.session_state.selected_character_id = None
        st.session_state.game_objectives = {}

        # --- Model Initialization (No Initial Solve) ---
        try:
            # Construct dictionary first
            logging.info("Constructing initial t=0 state dictionary...")
            initial_state_dict = {}
            initial_state_dict.update(growth_parameters)
            defined_param_names = set(growth_parameters.keys())
            defined_variable_names = set(v[0] for v in growth_variables)
            for key, value in growth_exogenous:
                try:
                    # Attempt to set any exogenous value, converting to float if possible
                    initial_state_dict[key] = float(value)
                except (TypeError, ValueError):
                     if isinstance(value, str): initial_state_dict[key] = value
                     else: logging.warning(f"Could not convert exogenous value {key}={value} to float. Skipping.")
            for key, value in growth_variables:
                 try:
                     if isinstance(value, str): initial_state_dict[key] = value
                     else: initial_state_dict[key] = float(value)
                 except (TypeError, ValueError):
                     logging.warning(f"Could not convert variable value {key}={value} to float. Skipping.")
            logging.info(f"Initial t=0 state dictionary constructed with {len(initial_state_dict)} entries.")

            # Create fresh model and set values
            logging.info("Creating initial model object and setting values...")
            initial_model_object = create_growth_model()
            initial_model_object.set_values(initial_state_dict)

            # Store the UNSOLVED model object and the initial dictionary
            st.session_state.sfc_model_object: Model = initial_model_object
            st.session_state.initial_state_dict = initial_state_dict # Store for Year 0 display
            # Base Yk will be set after the first simulation (Year 1)
            st.session_state.base_yk = None
            logging.info("Stored initial model object (unsolved) and initial state dict in session state.")

        except Exception as e:
            st.error(f"Fatal Error: An unexpected error occurred during model initialization: {e}")
            logging.exception("Unexpected error during model initialization.")
            st.stop()
        # --- End of Model Initialization ---

        # --- Game Variables Initialization ---
        # Deck creation moved to after character selection
        st.session_state.deck = [] # Initialize empty deck
        st.session_state.player_hand = [] # Initialize empty hand
        st.session_state.discard_pile = [] # Initialize discard pile
        logging.info("Initialized empty deck, hand, and discard pile.")
        st.session_state.active_events_this_year = []
        st.session_state.cards_selected_this_year = []
        st.session_state.history = [] # Initialize history as empty
        st.session_state.initial_params = {} # For year 0 adjustments
        st.session_state.temporary_effects = [] # Initialize list to track temporary event effects
        st.session_state.persistent_effects = {} # Initialize dict to track cumulative persistent card effects

        st.session_state.seen_dilemmas = set() # Initialize set to track seen dilemmas
        st.session_state.current_dilemma = None # To store the currently active dilemma
        st.session_state.dilemma_processed_for_year = -1 # Initialize to a non-valid year
        logging.info("Game Initialized at Year 0.")
        st.rerun() # Rerun to start the flow