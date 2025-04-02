import subprocess
import numpy as np
import os
import sys

# --- Configuration ---
PARAMETERS_TO_TEST = [
    # ALL Exogenous variables AND growth parameters
    'ADDbl', 'BANDb', 'BANDt', 'GRg', 'GRpr', 'NCAR', 'NPLk', 'Nfe', 'RA',
    'Rbbar', 'Rln', 'alpha1', 'alpha2', 'beta', 'betab', 'bot', 'delta',
    'deltarep', 'eps', 'eps2', 'epsb', 'epsrb', 'eta', 'eta0', 'etan', 'etar',
    'gamma', 'gamma0', 'gammar', 'gammau', 'lambda20', 'lambda21', 'lambda22',
    'lambda23', 'lambda24', 'lambda25', 'lambda30', 'lambda31', 'lambda32',
    'lambda33', 'lambda34', 'lambda35', 'lambda40', 'lambda41', 'lambda42',
    'lambda43', 'lambda44', 'lambda45', 'lambdab', 'lambdac', 'omega0',
    'omega1', 'omega2', 'omega3', 'phi', 'phit', 'psid', 'psiu', 'ro',
    'sigman', 'sigmase', 'sigmat', 'theta', 'top', 'xim1', 'xim2'
]
# Reduced set of changes: +1% and +3%
CHANGES = np.array([0.01, 0.03])

OUTPUT_CSV = 'inflation_impact_simulations.csv' # Updated output filename
SIMULATOR_SCRIPT = 'scripts/parameter_impact_simulator.py'

# Ensure the simulator script exists
if not os.path.exists(SIMULATOR_SCRIPT):
    print(f"Error: Simulator script '{SIMULATOR_SCRIPT}' not found.")
    sys.exit(1)

# Clear the output file if it exists, or create the directory if needed
output_dir = os.path.dirname(OUTPUT_CSV)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)
if os.path.exists(OUTPUT_CSV):
    os.remove(OUTPUT_CSV)
    print(f"Removed existing output file: {OUTPUT_CSV}")

# --- Execution Loop ---
total_runs = len(PARAMETERS_TO_TEST) * len(CHANGES)
current_run = 0

print(f"Starting simulations. Total runs: {total_runs}")

for param in PARAMETERS_TO_TEST:
    print(f"\n--- Processing Parameter: {param} ---")
    for change in CHANGES:
        current_run += 1
        print(f"Run {current_run}/{total_runs}: Parameter={param}, Change={change:.6f}")

        command = [
            sys.executable, # Use the same python interpreter running this script
            SIMULATOR_SCRIPT,
            '--parameter', param,
            '--change', str(change),
            '--output', OUTPUT_CSV
        ]

        try:
            # Run the simulation script
            # Use capture_output=True to get stdout/stderr if needed for debugging
            # Use text=True for easier handling of output
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"  Success. Output:\n{result.stdout[-200:]}") # Print last few lines of output
            if result.stderr:
                 print(f"  Stderr:\n{result.stderr}")

        except subprocess.CalledProcessError as e:
            print(f"  *** FAILED ***")
            print(f"  Command: {' '.join(e.cmd)}")
            print(f"  Return Code: {e.returncode}")
            print(f"  Stdout:\n{e.stdout}")
            print(f"  Stderr:\n{e.stderr}")
            # Decide whether to continue or stop on failure
            # sys.exit(1) # Uncomment to stop on first failure
        except Exception as e:
            print(f"  *** An unexpected error occurred running the subprocess: {e} ***")
            # sys.exit(1) # Uncomment to stop on first failure

print("\n--- All simulations completed ---")
print(f"Results saved to: {OUTPUT_CSV}")