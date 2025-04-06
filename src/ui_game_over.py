# src/ui_game_over.py
"""Handles rendering the game over screen."""

import streamlit as st
import pandas as pd
import logging
from urllib.parse import quote

# Import project modules
from matrix_display import ( # Assuming matrix_display.py is in the root
    display_balance_sheet_matrix, display_revaluation_matrix,
    display_transaction_flow_matrix
)

# Consider moving this to config if used elsewhere
RECIPIENT_EMAIL = "omareth@gmail.com"

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

    # Feedback Form
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
                try:
                    mailto_url = f"mailto:{RECIPIENT_EMAIL}?subject={quote(subject)}&body={quote(body)}"
                    st.success("Feedback prepared! Click the link below to open your email client.")
                    # Use target="_blank" to open in a new tab/window
                    st.markdown(f'<a href="{mailto_url}" target="_blank" rel="noopener noreferrer">Click here to send feedback via email</a>', unsafe_allow_html=True)
                    logging.info(f"Generated mailto link for feedback. User: {user_identity or 'Anonymous'}")
                except Exception as e:
                    st.error("Could not generate feedback link.")
                    logging.error(f"Error generating mailto link: {e}")


    # Final SFC Matrices
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