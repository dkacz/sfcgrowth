# src/objective_evaluator.py
"""Handles the evaluation of game objectives at the end of the game."""

import streamlit as st # Needed for session_state access
import numpy as np
import logging

def evaluate_objectives():
    """Evaluates if game objectives were met based on final results."""
    objectives = st.session_state.get('game_objectives', {})
    if not st.session_state.history:
        logging.error("Cannot evaluate objectives: History is empty.")
        return False, [{"Objective": "Error", "Target": "-", "Actual": "No history", "Met?": "❌"}]

    final_results = st.session_state.history[-1] # Get results from the last year
    all_met = True
    summary = []

    if not objectives:
        logging.warning("No game objectives were set for evaluation.")
        # Return False (cannot win without objectives) and an informative summary
        return False, [{"Objective": "N/A", "Target": "-", "Actual": "No objectives set", "Met?": "-"}]

    for obj_key, details in objectives.items():
        current_value = None
        label = details.get('label', obj_key) # Use key as fallback label
        condition = details.get('condition')
        target = details.get('target_value')
        target_type = details.get('target_type')

        if condition is None or target is None or target_type is None:
            logging.warning(f"Skipping objective '{label}' due to missing details (condition, target, or type).")
            summary.append({
                "Objective": label, "Target": "Invalid",
                "Actual": "N/A", "Met?": "❓"
            })
            all_met = False # Cannot guarantee win if objectives are invalid
            continue

        # Get the actual value from final results
        try:
            if obj_key == "gdp_index":
                yk_val = final_results.get('Yk')
                base_yk = st.session_state.get('base_yk')
                if base_yk is not None and yk_val is not None and not np.isclose(float(base_yk), 0):
                    current_value = (float(yk_val) / float(base_yk)) * 100
                else:
                    logging.warning(f"Could not calculate GDP Index for objective '{label}'. Yk: {yk_val}, Base Yk: {base_yk}")
            elif obj_key == "unemployment":
                er_val = final_results.get('ER')
                if er_val is not None: current_value = (1 - float(er_val)) * 100
            elif obj_key == "inflation":
                pi_val = final_results.get('PI')
                if pi_val is not None: current_value = float(pi_val) * 100
            elif obj_key == "debt_gdp":
                gd_val = final_results.get('GD')
                y_val = final_results.get('Y')
                if gd_val is not None and y_val is not None and not np.isclose(float(y_val), 0):
                    current_value = (float(gd_val) / float(y_val)) * 100
                else:
                     logging.warning(f"Could not calculate Debt/GDP for objective '{label}'. GD: {gd_val}, Y: {y_val}")
            else:
                # Handle potential direct metric keys if added later
                direct_val = final_results.get(obj_key)
                if direct_val is not None:
                    current_value = float(direct_val)
                    # Adjust for percentage if needed based on target_type (heuristic)
                    if target_type == 'percent' and current_value <= 2: # Assume direct value needs scaling if small
                         current_value *= 100
                         logging.debug(f"Applied percentage scaling for direct metric '{obj_key}'")

        except (TypeError, ValueError) as e:
             logging.error(f"Error converting final result value for objective '{label}' ({obj_key}): {e}. Value: {final_results.get(obj_key)}")
             current_value = None # Ensure it's None if conversion fails

        # Check if objective met
        met = False
        if current_value is not None:
            try:
                target_float = float(target)
                if condition == ">=" and current_value >= target_float: met = True
                elif condition == "<=" and current_value <= target_float: met = True
                elif condition == ">" and current_value > target_float: met = True
                elif condition == "<" and current_value < target_float: met = True
                # Add == if needed, though less common for economic targets
                # elif condition == "==" and np.isclose(current_value, target_float): met = True
            except (TypeError, ValueError) as e:
                logging.error(f"Error comparing objective '{label}'. Current: {current_value}, Target: {target}. Error: {e}")
                met = False # Treat comparison error as not met

        if not met: all_met = False

        # Format for display
        current_str = "N/A"
        target_str = f"{target}" # Keep target as defined in character file
        if current_value is not None:
             # Use consistent formatting based on target_type
             if target_type == 'percent':
                 current_str = f"{current_value:.1f}%"; target_str += "%"
             elif target_type == 'index':
                 current_str = f"{current_value:.1f}"
             else: # Default or other types
                 current_str = f"{current_value:.1f}" # Adjust precision as needed

        summary.append({
            "Objective": label, "Target": f"{condition} {target_str}",
            "Actual": current_str, "Met?": "✅ Yes" if met else "❌ No"
        })

    logging.info(f"Objective evaluation complete. All met: {all_met}. Summary: {summary}")
    return all_met, summary