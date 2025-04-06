# src/ui_character_select.py
"""Handles the rendering of the character selection screen."""

import streamlit as st
import os
import logging

# Import project modules
from src.utils import get_base64_of_bin_file, get_icon_data_uri
from characters import CHARACTERS # Assuming characters.py is in the root

def display_character_selection():
    """Renders the character selection screen using an HTML table."""
    st.header("Choose Your Economic Advisor")
    st.write("Select the advisor whose economic philosophy and objectives align with your strategy.")

    selected_id = st.session_state.selected_character_id
    character_ids = list(CHARACTERS.keys())
    num_chars = len(character_ids)

    # --- Generate Table HTML ---
    table_html = '<table class="character-table"><tbody>'

    # Row 1: Names
    table_html += '<tr>'
    for char_id in character_ids:
        char_data = CHARACTERS[char_id]
        selected_class = "selected-character" if char_id == selected_id else ""
        # Use h5 for name font size
        table_html += f'<td class="{selected_class}"><h5>{char_data["name"]}</h5></td>'
    table_html += '</tr>'

    # Row 2: Images
    table_html += '<tr>'
    for char_id in character_ids:
        char_data = CHARACTERS[char_id]
        selected_class = "selected-character" if char_id == selected_id else ""
        img_html = ""
        img_path = char_data.get('image_path')
        if img_path:
            try:
                # Construct path relative to the project root
                full_img_path = os.path.join("assets", "characters", os.path.basename(img_path))
                img_data_uri = get_base64_of_bin_file(full_img_path)
                if img_data_uri:
                    # Image size controlled by CSS rule .character-table img
                    img_html = f'<img src="data:image/png;base64,{img_data_uri}" alt="{char_data["name"]}">'
                else:
                    img_html = f'<p style="color: red; font-size: small;">Image not found at {full_img_path}</p>'
                    logging.warning(f"Character image not found or empty: {full_img_path}")
            except Exception as e:
                img_html = f'<p style="color: red; font-size: small;">Error loading image</p>'
                logging.error(f"Error loading character image {img_path}: {e}")
        table_html += f'<td class="{selected_class}">{img_html}</td>'
    table_html += '</tr>'

    # Row 3: Descriptions
    table_html += '<tr>'
    for char_id in character_ids:
        char_data = CHARACTERS[char_id]
        selected_class = "selected-character" if char_id == selected_id else ""
        # Removed <small> tag for larger description font
        table_html += f'<td class="{selected_class}">{char_data["description"]}</td>'
    table_html += '</tr>'

    # Row 4: Objectives
    table_html += '<tr>'
    objective_icon_map = {
        "gdp_index": "Yk", "unemployment": "ER", "inflation": "PI", "debt_gdp": "GD_GDP"
    }
    for char_id in character_ids:
        char_data = CHARACTERS[char_id]
        selected_class = "selected-character" if char_id == selected_id else ""
        objectives_list = list(char_data.get('objectives', {}).items())
        objectives_html = "<strong>Objectives:</strong><ul>"
        if objectives_list:
            for obj_key, obj in objectives_list:
                icon_uri = get_icon_data_uri(objective_icon_map.get(obj_key, ''))
                icon_img = f'<img src="{icon_uri}" style="height: 1em; width: 1em; margin-right: 0.5em; vertical-align: middle;">' if icon_uri else ''
                objectives_html += f"""<li>
                        {icon_img}
                        <small>{obj['label']}: {obj['condition']} {obj['target_value']}{'%' if obj['target_type'] == 'percent' else ''}</small>
                    </li>"""
        else:
            objectives_html += "<li><small>No specific objectives.</small></li>"
        objectives_html += "</ul>"
        table_html += f'<td class="{selected_class}">{objectives_html}</td>'
    table_html += '</tr>'

    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)

    # --- Render Buttons Separately Below Table ---
    button_cols = st.columns(num_chars)
    for i, char_id in enumerate(character_ids):
        with button_cols[i]:
            button_label = "Selected" if char_id == selected_id else "Select"
            button_type = "primary" if char_id == selected_id else "secondary"
            # The action trigger logic remains here as it directly modifies session state
            # based on the button click in this specific UI component.
            if st.button(button_label, key=f"select_{char_id}", type=button_type, use_container_width=True):
                st.session_state.action_trigger = ("select_character", char_id)
                st.rerun()