# src/ui_game_over.py
"""Handles rendering the game over screen."""

import streamlit as st
import pandas as pd
import logging
from urllib.parse import quote
import smtplib # Added for SMTP
from email.message import EmailMessage # Added for email construction

import copy # For deep copying states
from src.simulation_logic import run_baseline_simulation
# Import project modules
from matrix_display import ( # Assuming matrix_display.py is in the root
    display_balance_sheet_matrix, display_revaluation_matrix,
    display_transaction_flow_matrix
)
from .ui_policy_cards import render_policy_card_html # Use the new function
from cards import POLICY_CARDS # Import from root cards.py

# RECIPIENT_EMAIL constant removed, will use st.secrets

def display_game_over_screen(all_objectives_met, results_summary):
    """Renders the game over screen with results and feedback form."""
    st.header("Game Over!")
    st.balloons()

    # Display Objective Results
    st.subheader("Objective Results")
    if results_summary:
        try:
            # Ensure results_summary is suitable for DataFrame creation
            df = pd.DataFrame(results_summary)
            if "Objective" in df.columns:
                st.dataframe(df.set_index("Objective"))
            else:
                st.dataframe(df) # Display as is if 'Objective' column is missing
                logging.warning("Game over results summary missing 'Objective' column.")
        except Exception as e:
            st.error(f"Error displaying objective results: {e}")
            logging.error(f"Error creating DataFrame from results_summary: {results_summary}. Error: {e}")
    else:
        st.warning("No game objectives were set or results available.")

    if all_objectives_met:
        st.success("Congratulations! You met all objectives!")
    else:
        st.error("Unfortunately, you did not meet all objectives.")

    # --- Baseline Comparison Section ---
    st.divider() # Separate from objective results
    st.subheader("Policy Impact Assessment")
    st.write("Run simulations to see how the economy would have performed without your policy changes from each year onwards.")

    if st.button("Run Baseline Comparisons"):
        # Check for necessary data in session state
        if 'history' not in st.session_state or not st.session_state.history:
            st.error("Main simulation history not found. Cannot run baselines.")
            logging.error("Baseline run trigger failed: Main simulation history missing.")
        elif 'full_event_sequence' not in st.session_state or not st.session_state.full_event_sequence:
            st.error("Full event sequence not found. Cannot run baselines.")
            logging.error("Baseline run trigger failed: Full event sequence missing.")
        elif 'initial_state_dict' not in st.session_state:
            st.error("Initial state dictionary ('initial_state_dict') not found. Cannot run baseline for Year 1.")
            logging.error("Baseline run trigger failed: 'initial_state_dict' missing.")
        elif 'persistent_effects' not in st.session_state:
            st.error("Persistent effects tracking not found. Cannot run baselines accurately.")
            logging.error("Baseline run trigger failed: 'persistent_effects' missing.")
        elif 'temporary_effects' not in st.session_state:
            st.error("Temporary effects tracking not found. Cannot run baselines accurately.")
            logging.error("Baseline run trigger failed: 'temporary_effects' missing.")
        elif 'selected_character_id' not in st.session_state:
            st.error("Selected character ID not found. Cannot run baselines.")
            logging.error("Baseline run trigger failed: 'selected_character_id' missing.")
        else:
            history = st.session_state.history
            full_event_sequence_dict = st.session_state.full_event_sequence
            initial_state_dict = st.session_state.initial_state_dict
            # Retrieve other necessary state components
            persistent_effects = st.session_state.persistent_effects
            temporary_effects = st.session_state.temporary_effects
            character_id = st.session_state.selected_character_id

            if 'baseline_results' not in st.session_state:
                st.session_state.baseline_results = {}

            # Determine the number of years simulated in the main run
            # Assuming history is a list where index = year - 1
            num_years = len(history)
            if num_years == 0:
                st.warning("No simulation history found. Cannot run baselines.")
                logging.warning("Baseline run trigger skipped: History is empty.")
            else:
                logging.info(f"Attempting baseline run. Checking state variables.")
                logging.info(f"st.session_state.initial_game_state exists: {'initial_game_state' in st.session_state}")
                if 'initial_game_state' in st.session_state:
                    logging.info(f"Type of initial_game_state: {type(st.session_state.initial_game_state)}")
                    # Avoid logging potentially large state objects directly
                logging.info(f"st.session_state.history exists: {'history' in st.session_state}")
                if 'history' in st.session_state:
                    logging.info(f"Type of history: {type(st.session_state.history)}")
                    logging.info(f"Length of history: {len(st.session_state.history)}")
                    if st.session_state.history:
                        logging.info(f"Type of history[0]: {type(st.session_state.history[0])}")


                with st.spinner(f"Running {num_years} baseline simulations (Year 1-{num_years} to Year {num_years})... This may take a moment."):
                    try:
                        logging.info(f"Starting baseline simulation runs for {num_years} years.")
                        all_successful = True
                        # Extract the history of cards played in the actual game run
                        actual_played_cards_history = {entry['year']: entry.get('played_cards', []) for entry in history if 'year' in entry}
                        logging.debug(f"Extracted actual played cards history: {actual_played_cards_history}")


                        for start_year in range(1, num_years + 1):
                            st.write(f"Running baseline starting from Year {start_year}...") # Progress update
                            logging.info(f"Running baseline for Year {start_year}...")

                            # Get initial state for this baseline run
                            if start_year == 1:
                                # Use the very initial state of the game
                                # For Year 1 baseline, use the initial dictionary
                                current_initial_state_dict = copy.deepcopy(initial_state_dict)
                                # History up to the start of year 1 is empty
                                initial_history_slice = []
                                # Effects at the start of year 1 are empty
                                initial_persistent_effects_slice = {}
                                initial_temporary_effects_slice = []
                            else:
                                # For Year N baseline, use state from the end of year N-1
                                history_index = start_year - 2
                                if history_index < len(history):
                                    # Pass the result dictionary from the end of the previous year
                                    current_initial_state_dict = copy.deepcopy(history[history_index])
                                    # Pass history up to the end of the previous year
                                    initial_history_slice = copy.deepcopy(history[:history_index+1])
                                    # Retrieve the effects state from the end of the previous year's history entry
                                    initial_persistent_effects_slice = copy.deepcopy(current_initial_state_dict.get('persistent_effects', {}))
                                    initial_temporary_effects_slice = copy.deepcopy(current_initial_state_dict.get('temporary_effects', []))
                                    logging.debug(f"Baseline Year {start_year}: Using persistent/temporary effects state from history entry for Year {start_year - 1}.")
                                else:
                                    error_msg = f"Cannot find history for year {start_year - 1} (index {start_year - 2}) to start baseline {start_year}. History length: {len(history)}."
                                    st.error(error_msg)
                                    logging.error(error_msg)
                                    all_successful = False
                                    break # Stop processing if history is inconsistent

                            # The run_baseline_simulation function expects the full event sequence dictionary
                            # and handles the year-by-year lookup internally.
                            # No need to slice here.
                            # Check if the event dictionary is available (already checked earlier, but good practice)
                            if not full_event_sequence_dict:
                                error_msg = "Full event sequence dictionary is empty. Cannot run baseline."
                                st.error(error_msg)
                                logging.error(error_msg)
                                all_successful = False
                                break # Stop processing if events are inconsistent

                            # Run the baseline simulation
                            # Assuming run_baseline_simulation handles its own logging for start/end
                            # Call run_baseline_simulation with all required arguments
                            # Note: Passing state dict instead of Model object for initial_model_state
                            # Note: Passing potentially incorrect (final) effect states
                            # Updated call to the refactored baseline function
                            baseline_history = run_baseline_simulation(
                                start_year=start_year,
                                actual_game_history=history, # Pass the full actual history list
                                initial_game_state_dict=initial_state_dict, # Pass the game's initial state dict
                                full_event_sequence=full_event_sequence_dict,
                                character_id=character_id,
                                actual_played_cards_history=actual_played_cards_history,
                                game_base_yk=st.session_state.base_yk # Pass base Yk for KPIs
                            )
                            # Store the result
                            st.session_state.baseline_results[start_year] = baseline_history
                            logging.info(f"Completed and stored baseline for Year {start_year}.")

                        if all_successful:
                            st.success(f"All {num_years} baseline simulations completed successfully!")
                            logging.info(f"Finished all {num_years} baseline simulation runs.")
                        else:
                            st.warning("Baseline simulation run completed with errors. Some baselines may be missing.")
                            logging.warning("Baseline simulation run finished with errors.")

                    except Exception as e:
                        st.error(f"An unexpected error occurred during baseline simulations: {e}")
                        logging.exception("Error running baseline simulations:")
                        # Clear potentially partial results
                        st.session_state.baseline_results = {}


    # --- Display Baseline Analysis ---
    if 'baseline_results' in st.session_state and st.session_state.baseline_results:
        st.divider()
        st.subheader("Year-by-Year Policy Impact Analysis")
        st.caption("Comparing the final outcome (Year 10) of the actual game vs. a baseline simulation where policies from this year onwards were *not* played.")

        history = st.session_state.history
        baseline_results = st.session_state.baseline_results
        num_years = len(history)

        # Add logging to inspect history content
        logging.debug("--- History content before analysis loop ---")
        for idx, entry in enumerate(history):
            year_num = idx + 1
            cards = entry.get('played_cards', 'MISSING_KEY')
            logging.debug(f"            History Year {year_num} (Index {idx}): played_cards = {cards}")
        logging.debug("--- End History content ---")


        # Ensure history is not empty and has the final year's data
        if not history:
            st.warning("Cannot display impact analysis: Main game history is empty.")
        else:
            actual_final_kpis = history[-1] # Get the final year's KPIs from the actual run

            # Define KPIs to compare and their display names/units
            kpi_keys = {
                "Yk_Index": "GDP Index",
                "Inflation": "Inflation", # Use the calculated KPI key
                "GD_GDP": "Gov Debt/GDP",
                "Unemployment": "Unemployment"
            }
            kpi_units = {
                "Yk_Index": " points",
                "PI": "%",
                "GD_GDP": "%",
                "Unemployment": "%"
            }

            analysis_performed = False # Flag to check if any year's analysis was shown
            for N in range(1, num_years + 1): # Iterate through years 1 to num_years
                year_index = N - 1
                if year_index >= len(history): continue # Safety check

                # Get cards played in Year N from the main history
                played_cards = history[year_index].get('played_cards', [])
                logging.debug(f"        Year {N}: Played cards check. Found cards: {bool(played_cards)}. Cards: {played_cards}") # LOG ADDED

                # --- Roo Debug Log: Log actual state when neutralizing cards are played ---
                neutralizing_pair_check = {'Increase Government Spending', 'Decrease Government Spending', 'Make Tax System More Progressive', 'Make Tax System Less Progressive'} # Add both pairs
                actual_cards_set = set(played_cards)
                is_neutralizing = (actual_cards_set == {'Increase Government Spending', 'Decrease Government Spending'} or
                                   actual_cards_set == {'Make Tax System More Progressive', 'Make Tax System Less Progressive'})

                if is_neutralizing:
                    actual_state_at_N = history[year_index]
                    log_subset_actual_N = {k: actual_state_at_N.get(k, 'N/A') for k in ['Yk_Index', 'Inflation', 'GD_GDP', 'Unemployment', 'alpha1', 'Rbbar', 'GRg', 'theta']}
                    logging.debug(f'          ACTUAL_STEP_N_RESULT Year={N} (Neutralizing): {log_subset_actual_N}')
                # --- End Roo Debug Log ---

                # --- Roo Debug Log: Log actual state when neutralizing cards are played ---
                neutralizing_pair_check = {'Increase Government Spending', 'Decrease Government Spending', 'Make Tax System More Progressive', 'Make Tax System Less Progressive'} # Add both pairs
                actual_cards_set = set(played_cards)
                is_neutralizing = (actual_cards_set == {'Increase Government Spending', 'Decrease Government Spending'} or
                                   actual_cards_set == {'Make Tax System More Progressive', 'Make Tax System Less Progressive'})

                if is_neutralizing:
                    actual_state_at_N = history[year_index]
                    log_subset_actual_N = {k: actual_state_at_N.get(k, 'N/A') for k in ['Yk_Index', 'Inflation', 'GD_GDP', 'Unemployment', 'alpha1', 'Rbbar', 'GRg', 'theta']}
                    logging.debug(f'          ACTUAL_STEP_N_RESULT Year={N} (Neutralizing): {log_subset_actual_N}')
                # --- End Roo Debug Log ---

                # Skip analysis if no cards were played this year
                if not played_cards:
                    continue

                # Baseline corresponding to *after* year N's decisions were made starts in N
                # FIX: Changed N + 1 to N based on how baselines are stored
                baseline_key = N
                # Add logging for validation
                logging.debug(f"        Analysis Loop Year N={N}: Attempting to access baseline_key={baseline_key}")
                logging.debug(f"        Available baseline keys: {list(baseline_results.keys())}")
                baseline_history = baseline_results.get(baseline_key)
                logging.debug(f"        Year {N}: Baseline history check for key {baseline_key}. Found: {bool(baseline_history)}. History length if found: {len(baseline_history) if baseline_history else 'N/A'}") # LOG ADDED

                # Check if the required baseline exists and is not empty
                if not baseline_history:
                    logging.warning(f"        Baseline data for comparison (starting Year {baseline_key}) not found for Year {N} analysis.")
                    continue # Skip this year if baseline is missing

                try:
                    baseline_final_kpis = baseline_history[-1] # Get the last entry (final year) of the baseline
                except IndexError:
                    logging.warning(f"        Year {N}: IndexError accessing baseline_history[-1] for key {baseline_key}.") # LOG ADDED
                    logging.warning(f"        Baseline data for comparison (starting Year {baseline_key}) is empty for Year {N} analysis.")
                    continue # Skip this year if baseline is empty

                analysis_performed = True # Mark that we are showing at least one year
                with st.expander(f"Impact of Year {N} Decisions"):
                    # Display played cards (names only for now)
                    st.markdown("**Policies Played:**")
                    if played_cards:
                        # Ensure max 4 columns for card display
                        # Always create 4 columns to maintain consistent card width
                        card_cols = st.columns(4)
                        for idx, card_name in enumerate(played_cards):
                            card_data = POLICY_CARDS.get(card_name)
                            if card_data:
                                # Use modulo to cycle through columns for correct wrapping
                                # Place card in its direct index column (0 or 1)
                                with card_cols[idx]:
                                    # Render card HTML using the new function
                                    card_html = render_policy_card_html(
                                        card_name=card_name,
                                        card_info=card_data,
                                        is_selected=False,
                                        is_disabled=True,
                                        display_only=True,
                                        boost_applied=False # Boost status not relevant/available here
                                    )
                                    st.markdown(card_html, unsafe_allow_html=True)
                            else:
                                # Use modulo here too for consistency, though less likely needed for error case
                                # Place caption in its direct index column
                                with card_cols[idx]:
                                    st.caption(f"Card: {card_name} (Data not found)")
                    else:
                        st.markdown("- None")
                    # TODO: Consider layout adjustments if many cards are played

                    st.markdown("**Impact on Final KPIs (Year 10):**")
                    impact_cols = st.columns(len(kpi_keys)) # Create columns for each KPI

                    # --- LOGGING: Show the dictionaries being compared ---
                    # --- Roo Debug Log: Log comparison data for ALL years ---
                    log_subset_actual = {k: actual_final_kpis.get(k, 'N/A') for k in kpi_keys}
                    log_subset_baseline = {k: baseline_final_kpis.get(k, 'N/A') for k in kpi_keys}
                    logging.debug(f"        Year {N} Comparison (Baseline Key {baseline_key}):")
                    logging.debug(f"          Actual KPIs: {log_subset_actual}")
                    logging.debug(f"          Baseline KPIs: {log_subset_baseline}")
                    # --- End Roo Debug Log ---

                    for i, (kpi_key, kpi_name) in enumerate(kpi_keys.items()):
                        impact = None # Initialize impact for each KPI

                        actual_val = actual_final_kpis.get(kpi_key)
                        baseline_val = baseline_final_kpis.get(kpi_key)
                        # Determine correct unit for the *difference*
                        if kpi_key in ['PI', 'Inflation', 'Unemployment', 'GD_GDP']: # Ensure Inflation uses p.p.
                            diff_unit = " p.p."
                        elif kpi_key == 'Yk_Index':
                             diff_unit = "%" # Display as percentage change
                        else:
                             diff_unit = " units" # Fallback for any other KPIs
                        # --- LOGGING: Detailed Impact Calculation ---
                        log_msg = f"            Year {N}, KPI {kpi_key}: Actual={actual_val}, Baseline={baseline_val}, DiffUnit={diff_unit}"
                        if kpi_key == 'GD_GDP':
                             actual_gd = actual_final_kpis.get('GD', 'N/A')
                             actual_y = actual_final_kpis.get('Y', 'N/A')
                             baseline_gd = baseline_final_kpis.get('GD', 'N/A')
                             baseline_y = baseline_final_kpis.get('Y', 'N/A')
                             log_msg += f"\n              Raw GD: Actual={actual_gd}, Baseline={baseline_gd}"
                             log_msg += f"\n              Raw Y: Actual={actual_y}, Baseline={baseline_y}"
                        logging.debug(log_msg)
                        # --- END LOGGING ---

                        with impact_cols[i]:
                            if actual_val is not None and baseline_val is not None:
                                try:
                                    # Calculate impact based on KPI type
                                    if kpi_key == 'Yk_Index':
                                        # Calculate percentage change for GDP Index
                                        if float(baseline_val) != 0: # Avoid division by zero
                                            impact = ((float(actual_val) / float(baseline_val)) - 1) * 100
                                        else:
                                            impact = None # Or some indicator of undefined change
                                    else:
                                        # Calculate absolute difference (percentage points) for others
                                        impact = float(actual_val) - float(baseline_val)

                                    # Display the metric if impact calculation was successful
                                    if impact is not None:
                                        formatted_value = f"{impact:+.1f}{diff_unit}"
                                        st.metric(label=f"{kpi_name}", value=formatted_value, delta=None)
                                        # Display raw values for comparison
                                        actual_display = f"{float(actual_val):.1f}" if isinstance(actual_val, (int, float)) else str(actual_val)
                                        baseline_display = f"{float(baseline_val):.1f}" if isinstance(baseline_val, (int, float)) else str(baseline_val)
                                        st.caption(f"Actual: {actual_display} | Baseline: {baseline_display}")
                                    else:
                                        st.caption(f"{kpi_name}: Change Undefined")
                                except (ValueError, TypeError) as e:
                                    st.caption(f"{kpi_name}: Calc Error")
                                    logging.error(f"Error calculating impact for {kpi_key} in Year {N}: {e}. Values: Actual={actual_val}, Baseline={baseline_val}")
                            else:
                                st.caption(f"{kpi_name}: N/A")
                                logging.warning(f"Missing KPI data for {kpi_key} in Year {N} analysis. Actual: {actual_val}, Baseline: {baseline_val}")
                                logging.debug(f"            Year {N}, KPI {kpi_key}: Missing actual or baseline value.") # LOG ADDED

            logging.debug(f"--- Finished analysis loop. analysis_performed = {analysis_performed} ---") # LOG ADDED
            if not analysis_performed:
                 st.info("No policy cards were played during the game, or baseline data is missing for comparison.")

    # --- Feedback Form ---
    st.divider()
    st.subheader("Feedback")
    st.write("We'd love your feedback to make this game better!")

    with st.form("feedback_form"):
        enjoyment = st.text_area("What did you enjoy most? (Optional)")
        confusion = st.text_area("Was anything confusing? (Optional)")
        suggestions = st.text_area("Suggestions for improvement? (Optional)")
        other_comments = st.text_area("Any other comments? (Optional)")
        user_identity = st.text_input("Your Name/Email (Optional):")
        submitted = st.form_submit_button("Submit Feedback")

        if submitted:
            subject = "SFCGame Feedback"
            body = f"""Enjoyment: {enjoyment or 'N/A'}\n\nConfusion: {confusion or 'N/A'}\n\nSuggestions: {suggestions or 'N/A'}\n\nOther Comments: {other_comments or 'N/A'}\n\nUser: {user_identity or 'Anonymous'}"""
            # Basic validation to prevent excessively long inputs (optional)
            if len(body) > 5000: # Limit body length
                 st.error("Feedback is too long. Please shorten your comments.")
            else:
                # --- SMTP Sending Logic ---
                try:
                    # Retrieve SMTP configuration from secrets
                    smtp_config = st.secrets.get("smtp", {})
                    server = smtp_config.get("server")
                    port = smtp_config.get("port")
                    username = smtp_config.get("username")
                    password = smtp_config.get("password")
                    recipient = smtp_config.get("recipient_email")

                    if not all([server, port, username, password, recipient]):
                        st.error("SMTP configuration is incomplete in .streamlit/secrets.toml. Cannot send feedback.")
                        logging.error("SMTP configuration incomplete in secrets.")
                    else:
                        # Construct the email message
                        msg = EmailMessage()
                        msg['Subject'] = subject
                        msg['From'] = username # Using the login username as the sender
                        msg['To'] = recipient
                        msg.set_content(body)

                        # Send the email
                        with smtplib.SMTP(server, port) as smtp_server:
                            smtp_server.starttls() # Secure the connection
                            smtp_server.login(username, password)
                            smtp_server.send_message(msg)

                        st.success("Feedback sent successfully!")
                        logging.info(f"Feedback sent via SMTP. User: {user_identity or 'Anonymous'}")

                except smtplib.SMTPAuthenticationError:
                    st.error("SMTP Authentication failed. Please check the username/password in your secrets file.")
                    logging.error("SMTP Authentication failed.")
                except smtplib.SMTPConnectError:
                    st.error(f"Failed to connect to the SMTP server ({server}:{port}). Please check the server/port details.")
                    logging.error(f"SMTP Connection failed for {server}:{port}")
                except Exception as e:
                    st.error(f"An unexpected error occurred while sending feedback: {e}")
                    logging.exception("Error sending feedback via SMTP:")


    # --- Final SFC Matrices ---
    st.divider()
    st.subheader("Final Economic State (SFC Matrices)")
    model_state = st.session_state.get('sfc_model_object')
    if model_state and hasattr(model_state, 'solutions') and model_state.solutions:
        final_solution = model_state.solutions[-1]
        # Safely get the second last solution or initial state
        second_last_solution = None
        if len(model_state.solutions) >= 2:
            second_last_solution = model_state.solutions[-2]
        elif 'initial_state_dict' in st.session_state:
             second_last_solution = st.session_state.get('initial_state_dict')

        try:
            display_balance_sheet_matrix(final_solution)
            st.divider()
            if second_last_solution:
                display_revaluation_matrix(final_solution, second_last_solution); st.divider()
                display_transaction_flow_matrix(final_solution, second_last_solution)
            else:
                st.caption("Revaluation and Transaction Flow matrices require previous period data (initial state or Year N-1).")
        except Exception as e:
            st.error(f"Error displaying final SFC matrices: {e}")
            logging.error(f"Error during final matrix display: {e}")
    else:
        st.warning("Could not display final SFC matrices due to missing simulation data.")


# (Code moved into display_game_over_screen function)