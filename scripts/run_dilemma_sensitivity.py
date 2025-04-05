# scripts/run_dilemma_sensitivity.py
import subprocess
import os
import sys

# Define parameters and their corresponding absolute shock values (+/-)
# Based on the plan discussed in Architect mode
parameter_shocks = {
    'omega0': 0.002,
    'omega2': 0.02,
    'NCAR': 0.001,
    'bot': 0.001,
    'top': 0.001,
    'gammar': 0.001,
    'gammau': 0.001,
    'delta': 0.001,
    'deltarep': 0.001,
    'etar': 0.004,
    'eps': 0.005,
    'ro': 0.001,
    'xim1': 0.0001,
    'xim2': 0.0001,
    'alpha2': 0.001,
}

# Define the target script and output file
simulator_script = os.path.join("scripts", "parameter_impact_simulator.py")
output_csv = "dilemma_parameter_sensitivity.csv"
python_executable = sys.executable # Use the same python interpreter running this script

# Remove existing output file to start fresh
if os.path.exists(output_csv):
    print(f"Removing existing output file: {output_csv}")
    os.remove(output_csv)

print(f"Starting dilemma parameter sensitivity simulations...")
print(f"Output will be saved to: {output_csv}")
print("-" * 30)

run_count = 0
error_count = 0

# Loop through each parameter and run simulations for positive and negative shocks
for param, shock_value in parameter_shocks.items():
    for sign in [1, -1]:
        change = shock_value * sign
        run_count += 1
        print(f"\n[{run_count}/30] Running simulation for: Parameter={param}, Change={change:.6f}")

        command = [
            python_executable,
            simulator_script,
            "--parameter", param,
            "--change", str(change),
            "--output", output_csv
        ]

        try:
            # Execute the command
            # Capture output to check for errors reported by the simulator script
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"Successfully completed run for {param} with change {change:.6f}.")
            # Print simulator's stdout for user visibility
            print("Simulator Output:\n---")
            print(result.stdout)
            print("---\n")


        except subprocess.CalledProcessError as e:
            error_count += 1
            print(f"!!! Error running simulation for: Parameter={param}, Change={change:.6f}")
            print(f"Command failed with exit code {e.returncode}")
            print("Stderr:")
            print(e.stderr)
            print("Stdout:")
            print(e.stdout)
            print("Continuing with next simulation...\n")
        except Exception as e:
            error_count += 1
            print(f"!!! An unexpected error occurred for: Parameter={param}, Change={change:.6f}")
            print(f"Error: {e}")
            print("Continuing with next simulation...\n")


print("-" * 30)
print(f"Completed {run_count} simulation runs.")
if error_count > 0:
    print(f"!!! Encountered {error_count} errors during execution.")
else:
    print("All simulations completed successfully.")
print(f"Results saved in: {output_csv}")