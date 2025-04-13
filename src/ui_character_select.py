# src/ui_character_select.py
"""Handles the rendering of the character selection screen."""

import streamlit as st
import os
import logging

# Import project modules
from src.utils import get_base64_of_bin_file, get_icon_data_uri
from characters import CHARACTERS # Assuming characters.py is in the root

def display_character_selection():
    """Renders the character selection screen using custom HTML/CSS for responsiveness."""
    st.header("Choose Your Economic Advisor")
    st.write("Select the advisor whose economic philosophy and objectives align with your strategy.")

    selected_id = st.session_state.selected_character_id
    character_ids = list(CHARACTERS.keys())
    num_chars = len(character_ids)

    # CSS is removed, relying on Streamlit columns for layout.
    # Basic styling for selected card (can be moved to a central CSS file later)
    st.markdown("""
        <style>
            .selected-character-card {
                border: 2px solid #1E90FF; /* DodgerBlue */
                border-radius: 8px; /* Match column gap */
                padding: 1rem; /* Add padding inside the border */
                margin: -1rem; /* Offset padding to align border with column edge */
                box-shadow: 0 0 10px rgba(30, 144, 255, 0.3);
            }
            /* .char-image CSS removed - using st.image width parameter */
             .objectives {
                text-align: left;
                font-size: 0.9em;
                width: 100%;
                margin-bottom: 1rem;
                color: #444;
            }
            .objectives strong {
                display: block;
                margin-bottom: 0.5rem;
            }
            .objectives ul {
                list-style: none;
                padding-left: 0;
                margin-top: 0;
            }
            .objectives li {
                margin-bottom: 0.3rem;
                line-height: 1.4;
            }
            .objectives img.icon {
                height: 1.1em;
                width: 1.1em;
                margin-right: 0.5em;
                vertical-align: middle;
                display: inline-block;
            }
            .stButton>button {
                 width: 100%; /* Make button full width */
            }
        </style>
    """, unsafe_allow_html=True)

    # --- Display Characters using Streamlit Columns ---
    objective_icon_map = {
        "gdp_index": "Yk", "unemployment": "ER", "inflation": "PI", "debt_gdp": "GD_GDP"
    }

    # Define number of columns
    cols_per_row = 4
    cols = st.columns(cols_per_row)

    # Loop through characters and place them in columns
    for i, char_id in enumerate(character_ids):
        char_data = CHARACTERS[char_id]
        is_selected = (char_id == selected_id)
        selected_class = "selected-character-card" if is_selected else "" # Class for CSS styling

        # Get the current column
        col = cols[i % cols_per_row]

        # Use a container within the column for better structure and potential styling
        # Apply the selected class to the container if the character is selected
        with col:
            # The container now acts as the 'card'
            # We add a div with the class inside the container for the border styling
            st.markdown(f'<div class="{selected_class}">', unsafe_allow_html=True)

            # Display Image - Use st.image or markdown for base64
            img_path = char_data.get('image_path')
            if img_path:
                try:
                    full_img_path = os.path.join("assets", "characters", os.path.basename(img_path))
                    # Using st.image might be simpler if direct CSS control isn't needed
                    # st.image(full_img_path, width=150) # Alternative
                    # Use st.image directly with width parameter
                    st.image(full_img_path, width=150)

                except FileNotFoundError:
                    st.error(f"Image file not found: {full_img_path}")
                    logging.warning(f"Character image file not found: {full_img_path}")
                except Exception as e:
                    st.error("Error loading image.")
                    logging.error(f"Error loading character image {img_path}: {e}")
            else:
               # Placeholder if no image - Use markdown with class for consistency
                pass # Added to satisfy the else block when no image path exists


            # Display Name - Use st.subheader or markdown
            st.subheader(char_data['name'])

            # Display Description
            st.caption(char_data['description']) # Use caption for description

            # Display Objectives
            objectives_list = list(char_data.get('objectives', {}).items())
            objectives_html = "<div class='objectives'><strong>Objectives:</strong><ul>"
            if objectives_list:
                for obj_key, obj in objectives_list:
                    icon_uri = get_icon_data_uri(objective_icon_map.get(obj_key, ''))
                    icon_img = f'<img src="{icon_uri}" class="icon" alt="{obj_key} icon">' if icon_uri else ''
                    objectives_html += f"""<li>
                            {icon_img}
                            <small>{obj['label']}: {obj['condition']} {obj['target_value']}{'%' if obj['target_type'] == 'percent' else ''}</small>
                        </li>"""
            else:
                objectives_html += "<li><small>No specific objectives.</small></li>"
            objectives_html += "</ul></div>"
            # Keep objectives HTML structure but ensure it's within the column
            st.markdown(objectives_html, unsafe_allow_html=True)

            # Select Button (remains a Streamlit element for interactivity)
            button_label = "Selected" if is_selected else "Select"
            button_type = "primary" if is_selected else "secondary"
            # Button remains largely the same, width handled by CSS/Streamlit column
            if st.button(button_label, key=f"select_{char_id}", type=button_type):
                st.session_state.action_trigger = ("select_character", char_id)
                st.rerun()

            # Close the inner div used for border styling
            st.markdown('</div>', unsafe_allow_html=True)




    # No need to close grid container as st.columns handles it