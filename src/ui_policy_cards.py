# src/ui_policy_cards.py
"""Handles rendering the policy card selection UI."""

import streamlit as st
import numpy as np

# Import project modules
from src.utils import get_icon_data_uri, format_effect
from src.config import MAX_CARDS_PER_ROW, PARAM_DESCRIPTIONS
from characters import CHARACTERS # Assuming characters.py is in the root
from cards import POLICY_CARDS # Assuming cards.py is in the root
from matrix_display import ( # Assuming matrix_display.py is in the root
    display_balance_sheet_matrix, display_revaluation_matrix,
    display_transaction_flow_matrix
)
import pandas as pd # Needed for history table


def render_policy_card_html(card_name, card_info, is_selected=False, is_disabled=False, display_only=False, boost_applied=False):
    """Generates the HTML markdown for a single policy card.

    Args:
        card_name (str): The name of the card.
        card_info (dict): The dictionary containing card details from POLICY_CARDS.
        is_selected (bool): Whether the card is currently selected.
        is_disabled (bool): Whether the card interaction should be disabled.
        display_only (bool): If True, hides selection elements (used for display outside selection).
        boost_applied (bool): Whether character boost is active for display.

    Returns:
        str: The HTML markdown string for the card.
    """
    card_type = card_info.get('type', 'Unknown').lower()
    card_stance = card_info.get('stance', None)

    # Prepare Effect String (Simplified for display, assumes boost is pre-calculated if needed)
    effect_str_parts = []
    card_effects_list = card_info.get('effects', [])
    for effect_detail in card_effects_list:
        param_name = effect_detail.get('param')
        base_effect = effect_detail.get('effect')
        if param_name and isinstance(base_effect, (int, float)) and np.isfinite(base_effect):
            # In display_only mode, we might not have the multiplier easily available,
            # so we just show the base effect unless boost_applied is explicitly True.
            # For more accuracy, the calling function could pre-calculate the actual effect.
            actual_effect = base_effect * (CHARACTERS.get(st.session_state.get('selected_character_id'), {}).get('bonus_multiplier', 1.0) if boost_applied else 1.0)
            formatted_effect = format_effect(param_name, actual_effect)
            param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown")
            if formatted_effect != "N/A":
                effect_str_parts.append(f"{formatted_effect} on {param_name} ({param_desc})")

    if effect_str_parts:
        boost_indicator = " (Boosted!)" if boost_applied else ""
        effects_combined = "; ".join(effect_str_parts)
        effect_str = f'<small><i>Effect{boost_indicator}: {effects_combined}</i></small>'
    else:
        effect_str = '<small><i>Effect details missing.</i></small>'

    # Card Rendering
    card_container_class = "card-container selected" if is_selected and not display_only else "card-container"
    if is_disabled or display_only:
        card_container_class += " disabled" # Add disabled class for styling

    icon_data_uri = get_icon_data_uri(card_type)
    icon_html = f'<img src="{icon_data_uri}" class="card-icon">' if icon_data_uri else "❓"
    top_bar_color_class = f"{card_type}" if card_type in ["monetary", "fiscal"] else "default"

    card_html = f'''
    <div class="{card_container_class}">
        <div class="card-top-bar {top_bar_color_class}">
           {icon_html} <span class="card-title">{card_type.capitalize()}: {card_name}</span>
        </div>
        <div class="card-main-content">
            <div class="card-desc">
                {card_info.get('desc', 'No description.')}
                {'<br><small><i>Duration: ' + str(card_info.get('duration')) + (' turn' if card_info.get('duration') == 1 else ' turns') + '</i></small>' if card_info.get('duration', 0) > 0 else ''}<br>
                {effect_str}
            </div>
            {'<div class="card-stance-bar ' + card_stance + '-bar">' + card_stance.capitalize() + '</div>' if card_stance else ''}
        </div>
    </div>
    '''
    return card_html


def display_policy_selection_section():
    """Renders the UI for the Policy Card selection part of the YEAR_START phase."""
    current_year = st.session_state.current_year # Keep for button keys if needed

    st.markdown("---") # Divider

    # --- Card Selection UI ---
    st.subheader("Select Policy Cards to Play")
    available_cards = st.session_state.player_hand
    selected_cards_this_turn = st.session_state.cards_selected_this_year
    max_cards_allowed = 2 # Consider moving to config if it varies

    if not available_cards:
        st.write("No policy cards currently in hand.")
    else:
        unique_card_names = sorted(list(set(
            card_name for card_name in available_cards
            if POLICY_CARDS.get(card_name, {}).get('type') in ["Fiscal", "Monetary"]
        )))

        if not unique_card_names:
            st.write("No Fiscal or Monetary policy cards currently in hand.")
        else:
            num_cards = len(unique_card_names)
            num_cols = min(num_cards, MAX_CARDS_PER_ROW)
            cols = st.columns(num_cols)
            card_render_index = 0
            for card_name in unique_card_names:
                with cols[card_render_index % num_cols]:
                    card_info = POLICY_CARDS.get(card_name, {})
                    is_selected = card_name in selected_cards_this_turn
                    card_type = card_info.get('type', 'Unknown').lower()
                    card_stance = card_info.get('stance', None)

                    # Prepare Effect String
                    effect_str_parts = []
                    boost_applied_display = False
                    bonus_multiplier_to_apply = 1.0
                    selected_char_id = st.session_state.get('selected_character_id')
                    if selected_char_id and selected_char_id in CHARACTERS and card_stance and card_type:
                        character_data = CHARACTERS[selected_char_id]
                        bonus_criteria = character_data.get('bonus_criteria', [])
                        bonus_multiplier = character_data.get('bonus_multiplier', 1.0)
                        criteria_matched = any(
                            card_stance == crit_stance and card_type.lower() == crit_type.lower()
                            for crit_stance, crit_type in bonus_criteria
                        )
                        if criteria_matched:
                            bonus_multiplier_to_apply = bonus_multiplier
                            boost_applied_display = True

                    card_effects_list = card_info.get('effects', [])
                    for effect_detail in card_effects_list:
                        param_name = effect_detail.get('param')
                        base_effect = effect_detail.get('effect')
                        if param_name and isinstance(base_effect, (int, float)) and np.isfinite(base_effect):
                            actual_effect = base_effect * bonus_multiplier_to_apply
                            formatted_effect = format_effect(param_name, actual_effect)
                            param_desc = PARAM_DESCRIPTIONS.get(param_name, "Unknown")
                            if formatted_effect != "N/A":
                                effect_str_parts.append(f"{formatted_effect} on {param_name} ({param_desc})")

                    if effect_str_parts:
                        boost_indicator = " (Boosted!)" if boost_applied_display else ""
                        effects_combined = "; ".join(effect_str_parts)
                        effect_str = f'<small><i>Effect{boost_indicator}: {effects_combined}</i></small>'
                    else:
                        effect_str = '<small><i>Effect details missing.</i></small>'

                    # Card Rendering (using the new function)
                    card_html = render_policy_card_html(
                        card_name=card_name,
                        card_info=card_info,
                        is_selected=is_selected,
                        is_disabled=False, # Cards are selectable here
                        display_only=False, # We need the button below
                        boost_applied=boost_applied_display # Pass boost status
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Selection Button - Logic handled in game_logic.py
                    button_label = "Deselect" if is_selected else "Select"
                    button_type = "primary" if is_selected else "secondary"
                    button_key = f"select_{card_name}_{card_render_index}_{current_year}"
                    # The action trigger logic remains here as it directly modifies session state
                    # based on the button click in this specific UI component.
                    if st.button(button_label, key=button_key, type=button_type, use_container_width=True):
                        st.session_state.action_trigger = ("toggle_card_selection", card_name)
                        st.rerun()

                card_render_index += 1

    st.divider()
    if selected_cards_this_turn:
        st.write("Selected for this turn:")
        for card_name in selected_cards_this_turn: st.markdown(f"- {card_name}")
    else:
        st.write("No cards selected for this turn.")

    # --- Detailed Data Expanders ---
    st.divider()
    with st.expander("SFC Matrices"):
        model_state = st.session_state.sfc_model_object
        if model_state and hasattr(model_state, 'solutions') and model_state.solutions:
            current_solution = model_state.solutions[-1]
            prev_solution = model_state.solutions[-2] if len(model_state.solutions) > 1 else st.session_state.get('initial_state_dict')

            display_balance_sheet_matrix(current_solution)
            st.divider()
            if prev_solution: display_revaluation_matrix(current_solution, prev_solution); st.divider()
            else: st.caption("Revaluation matrix requires previous period data.")
            if prev_solution: display_transaction_flow_matrix(current_solution, prev_solution)
            else: st.caption("Transaction flow matrix requires previous period data.")
        else:
            st.caption("Matrices require simulation results.")

    with st.expander("View History Table"):
        if st.session_state.history:
            column_mapping = {
                'year': 'Year', 'Yk': 'Real GDP (Yk)', 'PI': 'Inflation (PI)', 'ER': 'Employment Rate (ER)',
                'GRk': 'Capital Growth (GRk)', 'Rb': 'Bill Rate (Rb)', 'Rl': 'Loan Rate (Rl)', 'Rm': 'Deposit Rate (Rm)',
                'BUR': 'Debt Burden (BUR)', 'Q': "Tobin's Q (Q)", 'CAR': 'Capital Adequacy (CAR)',
                'PSBR': 'Gov Deficit (PSBR)', 'GD': 'Gov Debt Stock (GD)', 'Y': 'Nominal GDP (Y)',
                'V': 'Household Wealth (V)', 'Lhs': 'Household Loans (Lhs)', 'Lfs': 'Firm Loans (Lfs)',
                'cards_played': 'Cards Played', 'events': 'Active Events'
            }
            history_df = pd.DataFrame(st.session_state.history).sort_values(by='year', ascending=False)
            display_df = history_df[[col for col in column_mapping if col in history_df.columns]].rename(columns=column_mapping)
            st.dataframe(display_df)
        else: st.write("No history recorded yet.")

    # --- Proceed Button ---
    can_proceed = len(selected_cards_this_turn) <= max_cards_allowed
    if not can_proceed:
        st.warning(f"You can select a maximum of {max_cards_allowed} cards per turn.")
    # The action trigger logic remains here as it directly modifies session state
    # based on the button click in this specific UI component.
    if st.button("Confirm Policies & Run Simulation", disabled=not can_proceed):
        st.session_state.action_trigger = ("confirm_policies", None)
        st.rerun()