# src/ui_dilemma.py
"""Handles rendering the Advisor's Dilemma screen."""

import streamlit as st

def format_dilemma_option(option_data):
    """Helper to format dilemma option details clearly (1 add/1 remove)."""
    add_cards = option_data.get('add_cards', [])
    remove_cards = option_data.get('remove_cards', [])

    # Get the first valid card name from each list, if available
    first_add = next((card for card in add_cards if card), None)
    first_remove = next((card for card in remove_cards if card), None)

    parts = []
    if first_add:
        parts.append(f"Adds: {first_add}")
    if first_remove:
        parts.append(f"Removes: {first_remove}")

    # Join the parts with a newline for better readability if both are present
    return "\n".join(parts)

def display_dilemma():
    """Renders the Advisor's Dilemma screen."""
    st.header(f"Year {st.session_state.current_year} - Advisor's Dilemma")
    dilemma_info = st.session_state.current_dilemma['data']
    st.subheader(dilemma_info['title'])
    st.markdown(f"_{dilemma_info['flavor_text']}_")
    st.markdown("---")
    col1, col2 = st.columns(2)
    option_a = dilemma_info['option_a']
    option_b = dilemma_info['option_b']

    with col1:
        st.markdown(f"**Option A: {option_a['name']}**")
        # The action trigger logic remains here as it directly modifies session state
        # based on the button click in this specific UI component.
        if st.button(f"Choose: {option_a['name']}", key="dilemma_a", use_container_width=True):
            st.session_state.action_trigger = ("choose_dilemma", "A")
            st.rerun()
        if option_a.get('choice_flavour'):
            # Use markdown with unsafe_allow_html to ensure vertical expansion
            st.markdown(f"<div style='height: auto; overflow-y: visible; margin-bottom: 1.5em;'>*{option_a['choice_flavour']}*</div>", unsafe_allow_html=True)
        option_a_details = format_dilemma_option(option_a)
        if option_a_details:
            st.markdown(option_a_details)

    with col2:
        st.markdown(f"**Option B: {option_b['name']}**")
        # The action trigger logic remains here as it directly modifies session state
        # based on the button click in this specific UI component.
        if st.button(f"Choose: {option_b['name']}", key="dilemma_b", use_container_width=True):
            st.session_state.action_trigger = ("choose_dilemma", "B")
            st.rerun()
        if option_b.get('choice_flavour'):
            # Use markdown with unsafe_allow_html to ensure vertical expansion
            st.markdown(f"<div style='height: auto; overflow-y: visible; margin-bottom: 1.5em;'>*{option_b['choice_flavour']}*</div>", unsafe_allow_html=True)
        option_b_details = format_dilemma_option(option_b)
        if option_b_details:
            st.markdown(option_b_details)