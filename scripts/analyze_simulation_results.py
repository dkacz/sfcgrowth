import pandas as pd
import numpy as np
import os

# --- Configuration ---
RESULTS_CSV = 'simulation_results.csv'
TARGET_GDP_IMPACT_CARD = 2.5  # New Target % GDP impact for cards
TARGET_GDP_IMPACT_EVENT = 5.0 # New Target % GDP impact for events
OUTPUT_COLUMN_NAME = 'gdp_change_pct_turn5' # Match the simulator script

# --- Analysis ---
def analyze_results(filepath):
    """
    Reads simulation results, calculates sensitivity, and required changes.
    """
    if not os.path.exists(filepath):
        print(f"Error: Results file not found at {filepath}")
        return None

    try:
        df = pd.read_csv(filepath)
        # Convert columns to numeric, coercing errors to NaN
        df['change'] = pd.to_numeric(df['change'], errors='coerce')
        df[OUTPUT_COLUMN_NAME] = pd.to_numeric(df[OUTPUT_COLUMN_NAME], errors='coerce')

        # Drop rows with NaN values that resulted from conversion errors or failed runs
        df.dropna(subset=['change', OUTPUT_COLUMN_NAME], inplace=True)

        if df.empty:
            print("Error: No valid simulation results found after cleaning.")
            return None

        # Calculate absolute values
        df['abs_change'] = df['change'].abs()
        df['abs_gdp_change_pct'] = df[OUTPUT_COLUMN_NAME].abs()

        # Calculate sensitivity: average absolute % GDP change per unit absolute parameter change
        # Avoid division by zero for 'change'
        df_filtered = df[df['abs_change'] > 1e-9] # Filter out near-zero changes
        if df_filtered.empty:
             print("Error: No valid non-zero changes found to calculate sensitivity.")
             return None

        df_filtered['sensitivity_ratio'] = df_filtered['abs_gdp_change_pct'] / df_filtered['abs_change']

        # Group by parameter and calculate average sensitivity
        sensitivity_results = df_filtered.groupby('parameter')['sensitivity_ratio'].mean().reset_index()
        sensitivity_results.rename(columns={'sensitivity_ratio': 'avg_sensitivity'}, inplace=True)

        # Calculate required changes
        # Handle potential division by zero if sensitivity is zero
        sensitivity_results['required_change_card'] = np.where(
            np.abs(sensitivity_results['avg_sensitivity']) > 1e-9,
            TARGET_GDP_IMPACT_CARD / sensitivity_results['avg_sensitivity'],
            np.inf # Assign infinity if sensitivity is near zero
        )
        sensitivity_results['required_change_event'] = np.where(
            np.abs(sensitivity_results['avg_sensitivity']) > 1e-9,
            TARGET_GDP_IMPACT_EVENT / sensitivity_results['avg_sensitivity'],
            np.inf # Assign infinity if sensitivity is near zero
        )

        return sensitivity_results

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: File {filepath} is empty.")
        return None
    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    analysis = analyze_results(RESULTS_CSV)

    if analysis is not None:
        print("\n--- Simulation Analysis Results ---")
        # Format output for better readability
        pd.set_option('display.float_format', '{:.6f}'.format)
        print(analysis.to_string(index=False))

        print(f"\nNotes:")
        print(f"- Sensitivity = Average(|% GDP Change|) / Average(|Parameter Change|)")
        print(f"- Required Change (Card) = {TARGET_GDP_IMPACT_CARD}% / Sensitivity")
        print(f"- Required Change (Event) = {TARGET_GDP_IMPACT_EVENT}% / Sensitivity")
        print(f"- 'inf' indicates near-zero sensitivity, implying extremely large changes needed.")
        print(f"- Results based only on successful simulation runs.")

    else:
        print("\nAnalysis could not be completed due to errors.")