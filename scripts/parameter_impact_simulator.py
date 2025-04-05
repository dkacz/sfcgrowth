import argparse
import csv
import os
import copy
import sys
import matplotlib # Import matplotlib before pysolve potentially imports pyplot
matplotlib.use('Agg') # Use Agg backend for headless operation
import numpy # Import numpy for ndarray check

# Add project root to path to allow importing chapter_11_model_growth
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from chapter_11_model_growth import (
        create_growth_model,
        growth_parameters,
        growth_exogenous,
        growth_variables
    )
    from pysolve.model import Model # Ensure Model is accessible
    from pysolve.utils import is_close, round_solution # If needed later
except ImportError as e:
    print(f"Error importing from chapter_11_model_growth: {e}")
    print("Ensure the script is run from the project root or the path is correctly set.")
    sys.exit(1)

# --- Simulation Parameters ---
# Run for exactly 5 turns as requested
TOTAL_TURNS = 5
 # Keep at 5 turns
TARGET_VARIABLES = ['PI', 'Yk'] # Track both Inflation and Real GDP
OUTPUT_COLUMNS = {
    'PI': 'inflation_change_abs_turn5',
    'Yk': 'gdp_change_pct_turn5'
}

def run_and_get_final_values(params, exogenous, variables, turns, target_vars):
    """
    Creates a model instance, sets values, solves for 'turns' steps,
    and returns a dictionary of final values for the target variables.
    """
    model = create_growth_model()
    # Use deep copies to avoid modifying the original dicts/lists
    # Set initial values (t=0)
    model.set_values(copy.deepcopy(params))
    model.set_values(copy.deepcopy(exogenous))
    model.set_values(copy.deepcopy(variables))

    # Need to store the initial state (t=0) before solving
    # The pysolve library automatically stores the initial state as index 0
    # when solve() is first called.

    # Solve the model for the required number of turns
    solve_successful = True
    for t in range(turns): # This will run solve() turns times (0 to turns-1)
        try:
            # The solve method calculates the values for the *next* step (t+1)
            # based on the current state (t)
            model.solve(iterations=200, threshold=1e-6)
        except Exception as e:
            print(f"Error solving model at turn {t+1}: {e}")
            solve_successful = False
            break # Exit loop on solver error

    if not solve_successful:
        print("Solver failed to complete all turns.")
        return None

    # Extract final values for target variables only if solve completed
    final_values = {}
    try:
        # Access model.solutions as a list of dictionaries
        # Index for the final turn (turn 5) is 4 (0-based)
        iteration_index = turns - 1

        # Check if solutions attribute exists and is a list
        if not hasattr(model, 'solutions') or not isinstance(model.solutions, list):
             print(f"Error: model.solutions is not a list or does not exist after solve.")
             return None

        # Check if the list has enough elements (needs turns+1 elements for index 'turns')
        # The list stores initial state (index 0) + results for turns 1 to 'turns'
        if len(model.solutions) <= iteration_index:
             print(f"Error: Iteration {iteration_index} out of range for solutions list (length {len(model.solutions)}). Expected length {turns}.")
             return None

        # Access the dictionary for the specific iteration
        solution_dict = model.solutions[iteration_index]
        if not isinstance(solution_dict, dict):
            print(f"Error: Element at index {iteration_index} in model.solutions is not a dictionary (type: {type(solution_dict)}).")
            return None

        # Extract values for all target variables
        for target_var in target_vars:
            if target_var not in solution_dict:
                print(f"Error: Target variable '{target_var}' not found in solutions dictionary for iteration {iteration_index}.")
                 # Return None or partial results? Returning None for simplicity.
                return None

            value = solution_dict[target_var]

            # Ensure it's a float or can be converted
            if value is None:
                print(f"Warning: Final value for '{target_var}' at iteration {iteration_index} is None.")
                # Return None or partial results? Returning None for simplicity.
                return None
            final_values[target_var] = float(value)

        return final_values

    except Exception as e:
        # Catch any other unexpected error during extraction
        print(f"Unexpected error extracting solutions: {e}")
        # Also print type/value of model.solutions if possible
        try:
            print(f"DEBUG: Type of model.solutions during error: {type(model.solutions)}")
            print(f"DEBUG: Value of model.solutions during error: {str(model.solutions)[:200]}")
        except:
            print("DEBUG: Could not inspect model.solutions during error.")
        return None


def modify_parameter(param_name, change_value, params_dict, exogenous_list):
    """
    Modifies the specified parameter in the copied parameter/exogenous sets.
    Handles both parameters (dict) and exogenous variables (list of tuples).
    Returns the modified copies.
    """
    params_copy = copy.deepcopy(params_dict)
    exogenous_copy = copy.deepcopy(exogenous_list)
    found = False

    # Check in parameters dictionary
    if param_name in params_copy:
        params_copy[param_name] += change_value
        print(f"Modified parameter '{param_name}' in params_dict from {params_dict[param_name]:.6f} to {params_copy[param_name]:.6f}")
        found = True
    else:
        # Check in exogenous list (handle potential multiple entries - use last?)
        # Find index of the parameter in the exogenous list
        indices = [i for i, item in enumerate(exogenous_copy) if item[0] == param_name]
        if indices:
            # Modify the last occurrence if multiple exist (typical pysolve behavior)
            idx_to_modify = indices[-1]
            original_value = exogenous_copy[idx_to_modify][1]
            # Ensure value is numeric before adding
            if isinstance(original_value, (int, float)):
                 new_value = original_value + change_value
                 exogenous_copy[idx_to_modify] = (param_name, new_value)
                 print(f"Modified parameter '{param_name}' in exogenous_list from {original_value:.6f} to {new_value:.6f}")
                 found = True
            else:
                 print(f"Warning: Parameter '{param_name}' in exogenous_list is not numeric ('{original_value}'). Cannot apply change.")

    if not found:
        print(f"Error: Parameter '{param_name}' not found in parameters or exogenous variables.")
        # Optionally raise an error or return None to signal failure
        raise ValueError(f"Parameter '{param_name}' not found.")

    return params_copy, exogenous_copy


def main():
    parser = argparse.ArgumentParser(description="Run economic model simulation with parameter changes.")
    parser.add_argument('--parameter', required=True, help="Name of the parameter/exogenous variable to change.")
    parser.add_argument('--change', required=True, type=float, help="Absolute change to apply to the parameter.")
    parser.add_argument('--output', required=True, help="Path to the output CSV file.")

    args = parser.parse_args()

    print(f"Running simulation for parameter: {args.parameter}, change: {args.change:.6f}")

    # --- Run Baseline Simulation ---
    print("Running baseline simulation...")
    # Run baseline for TOTAL_TURNS, get final values for target variables
    baseline_final_values = run_and_get_final_values(growth_parameters, growth_exogenous, growth_variables, TOTAL_TURNS, TARGET_VARIABLES)
    if baseline_final_values is None:
        print("Baseline simulation failed or did not complete. Exiting.")
        sys.exit(1) # Exit this specific subprocess run
    print(f"Baseline values at turn {TOTAL_TURNS}:")
    for var, val in baseline_final_values.items():
        print(f"  {var}: {val:.6f}")


    # --- Run Modified Simulation ---
    print("Running modified simulation...")
    try:
        modified_params, modified_exogenous = modify_parameter(
            args.parameter, args.change, growth_parameters, growth_exogenous
        )
    except ValueError as e:
        print(e)
        sys.exit(1) # Exit if parameter not found

    # Run modified simulation for TOTAL_TURNS
    modified_final_values = run_and_get_final_values(modified_params, modified_exogenous, growth_variables, TOTAL_TURNS, TARGET_VARIABLES)

    if modified_final_values is None:
        print("Modified simulation failed or did not complete. Exiting.")
        sys.exit(1) # Exit this specific subprocess run
    print(f"Modified values at turn {TOTAL_TURNS}:")
    for var, val in modified_final_values.items():
        print(f"  {var}: {val:.6f}")

     # --- Calculate Changes ---
    results = {}
     # PI: Absolute change
    pi_change_abs = modified_final_values['PI'] - baseline_final_values['PI']
    results[OUTPUT_COLUMNS['PI']] = f"{pi_change_abs:.8f}"
    print(f"Absolute change in PI at turn {TOTAL_TURNS}: {pi_change_abs*100:.4f} p.p.")

     # Yk: Percentage change
    if baseline_final_values['Yk'] != 0: # Avoid division by zero
        yk_change_pct = ((modified_final_values['Yk'] - baseline_final_values['Yk']) / baseline_final_values['Yk'])
        results[OUTPUT_COLUMNS['Yk']] = f"{yk_change_pct:.8f}"
        print(f"Percentage change in Yk at turn {TOTAL_TURNS}: {yk_change_pct*100:.4f}%")
    else:
        results[OUTPUT_COLUMNS['Yk']] = "N/A (baseline Yk is zero)"
        print(f"Percentage change in Yk at turn {TOTAL_TURNS}: N/A (baseline Yk is zero)")


    # --- Append Result to CSV ---
    file_exists = os.path.isfile(args.output)
    try:
        with open(args.output, 'a', newline='') as csvfile:
             # Define fieldnames including the new GDP column
            fieldnames = ['parameter', 'change'] + list(OUTPUT_COLUMNS.values())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'parameter': args.parameter,
                'change': f"{args.change:.6f}", # Store change with precision
                **results # Unpack the results dictionary into the row
            })
        print(f"Result appended to {args.output}")
    except IOError as e:
        print(f"Error writing to output file {args.output}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()