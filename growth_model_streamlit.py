import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
import sys
import io
from contextlib import redirect_stdout
from chapter_11_model_growth import create_growth_model, growth_parameters, growth_exogenous, growth_variables
from pysolve.model import SolutionNotFoundError
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Suppress PDF generation output from the growth model
class NullIO(io.StringIO):
    def write(self, txt):
        pass

st.set_page_config(page_title="Growth Model Explorer", layout="wide")

# Set up the page
st.title("Growth Model Explorer")
st.markdown("""
This app allows you to experiment with exogenous variables in the monetary growth model from Chapter 11.
You can modify key parameters and compare the resulting model behavior against the baseline simulation.
""")

# Create sidebar for parameter selection
st.sidebar.header("Model Parameters")
st.sidebar.markdown("Adjust the exogenous variables below and click 'Run Simulation' to see the effects")

# Define categories of parameters for better organization
parameter_categories = {
    "Growth Parameters": [
        ("gamma0", "Base growth rate of real capital stock (gamma0)", 0.00122, 0.0, 0.01),
        ("gammar", "Effect of interest rate on capital growth (gammar)", 0.1, 0.0, 0.5),
        ("gammau", "Effect of utilization on capital growth (gammau)", 0.05, 0.0, 0.5),
        ("delta", "Rate of depreciation of fixed capital (delta)", 0.10667, 0.05, 0.2),
    ],
    "Consumption Parameters": [
        ("alpha1", "Propensity to consume out of income (alpha1)", 0.75, 0.5, 1.0),
        ("alpha2", "Propensity to consume out of wealth (alpha2)", 0.064, 0.01, 0.2),
        ("eps", "Speed of adjustment in income expectations (eps)", 0.5, 0.1, 1.0),
    ],
    "Government Parameters": [
        ("GRg", "Growth rate of government expenditures (GRg)", 0.03, -0.05, 0.1),
        ("theta", "Income tax rate (theta)", 0.22844, 0.1, 0.4),
    ],
    "Bank/Monetary Parameters": [
        ("Rbbar", "Interest rate on bills (Rbbar)", 0.035, 0.0, 0.1),
        ("ADDbl", "Spread between bonds and bills rate (ADDbl)", 0.02, 0.0, 0.05),
        ("NPLk", "Proportion of non-performing loans (NPLk)", 0.02, 0.0, 0.1),
        ("NCAR", "Normal capital adequacy ratio (NCAR)", 0.1, 0.05, 0.2),
        ("bot", "Bottom value for bank net liquidity ratio (bot)", 0.05, 0.0, 0.1),
        ("top", "Top value for bank net liquidity ratio (top)", 0.12, 0.1, 0.2),
        ("ro", "Reserve requirement parameter (ro)", 0.05, 0.01, 0.1),
        ("Rln", "Normal interest rate on loans (Rln)", 0.07, 0.02, 0.15),
    ],
    "Labor Market Parameters": [
        ("omega0", "Parameter affecting target real wage (omega0)", -0.20594, -0.5, 0.0),
 
        ("omega1", "Parameter in wage equation (omega1)", 1.005, 0.9, 1.1),
 # Default updated
        ("omega2", "Parameter in wage equation (omega2)", 2.0, 1.0, 3.0),
        ("omega3", "Speed of wage adjustment (omega3)", 0.45621, 0.1, 0.9),
        ("GRpr", "Growth rate of productivity (GRpr)", 0.03, 0.0, 0.1),
        ("BANDt", "Upper band of flat Phillips curve (BANDt)", 0.07, 0.0, 0.1), # Default updated
        ("BANDb", "Lower band of flat Phillips curve (BANDb)", 0.05, 0.0, 0.1), # Default updated
        ("etan", "Speed of employment adjustment (etan)", 0.6, 0.1, 1.0),
        ("Nfe", "Full employment level (Nfe)", 94.76, 80.0, 110.0),
    ],
    "Personal Loan Parameters": [
        ("eta0", "Base ratio of new loans to personal income (eta0)", 0.07416, 0.0, 0.2),
        ("etar", "Effect of real interest rate on loan ratio (etar)", 0.4, 0.0, 1.0),
        ("deltarep", "Ratio of loan repayments to stock (deltarep)", 0.1, 0.05, 0.2),
    ],
    "Firm Parameters": [
        ("beta", "Speed of adjustment in sales expectations (beta)", 0.5, 0.1, 1.0),
        ("gamma", "Speed of inventory adjustment (gamma)", 0.15, 0.0, 0.5),
        ("sigmat", "Target inventories to sales ratio (sigmat)", 0.2, 0.1, 0.3),
        ("sigman", "Param. influencing historic unit costs (sigman)", 0.1666, 0.1, 0.3),
        ("eps2", "Speed of markup adjustment (eps2)", 0.8, 0.1, 1.0),
        ("psid", "Ratio of dividends to gross profits (psid)", 0.15255, 0.1, 0.3),
        ("psiu", "Ratio of retained earnings to investments (psiu)", 0.92, 0.7, 1.0),
        ("RA", "Random shock to expectations on real sales (RA)", 0.0, -0.05, 0.05),
    ],
    "Portfolio Parameters": [
        ("lambda20", "Param in household demand for bills (lambda20)", 0.25, 0.1, 0.4),
        ("lambda30", "Param in household demand for bonds (lambda30)", -0.04341, -0.1, 0.1),
        ("lambda40", "Param in household demand for equities (lambda40)", 0.67132, 0.5, 0.9),
        ("lambdab", "Parameter determining bank dividends (lambdab)", 0.0153, 0.01, 0.03),
        ("lambdac", "Parameter in household demand for cash (lambdac)", 0.05, 0.01, 0.1),
    ],
}

# Add a reset all button
if st.sidebar.button("Reset All Parameters", key="reset_all"):
    # Reset all parameters across all categories
    for category, params in parameter_categories.items():
        for param_key, param_name, default_val, min_val, max_val in params:
            # Reset to default value
            st.session_state[f"slider_{param_key}"] = float(default_val)

# Create a dictionary to store the selected parameters
selected_params = {}

# Create expandable sections for each parameter category
for category, params in parameter_categories.items():
    with st.sidebar.expander(category):
        # Add a reset button at the top of each category
        if st.button(f"Reset {category} to defaults", key=f"reset_{category}"):
            # Reset all parameters in this category to their default values
            for param_key, param_name, default_val, min_val, max_val in params:
                # Store the default value in session state
                st.session_state[f"slider_{param_key}"] = float(default_val)
        
        # Display sliders for each parameter
        for param_key, param_name, default_val, min_val, max_val in params:
            # Calculate an appropriate step size based on the range
            range_magnitude = max_val - min_val
            if range_magnitude <= 0.01:
                step_size = 0.0001  # Very fine control for tiny ranges
            elif range_magnitude <= 0.1:
                step_size = 0.0005  # Fine control for small ranges
            elif range_magnitude <= 1.0:
                step_size = 0.001   # Medium precision for moderate ranges
            elif range_magnitude <= 10.0:
                step_size = 0.005   # Less precision for larger ranges
            else:
                step_size = 0.01    # Coarse precision for very large ranges
                
            # Format the display to show appropriate decimal places
            if step_size < 0.001:
                format_spec = "%.5f"
            elif step_size < 0.01:
                format_spec = "%.4f"
            elif step_size < 0.1:
                format_spec = "%.3f"
            else:
                format_spec = "%.2f"
            
            # Initialize session state if not already done
            if f"slider_{param_key}" not in st.session_state:
                st.session_state[f"slider_{param_key}"] = float(default_val)
                
            # Use the slider without specifying value from session_state in the slider itself
            value = st.slider(
                param_name, 
                min_value=float(min_val), 
                max_value=float(max_val), 
                step=step_size,
                format=format_spec,
                key=f"slider_{param_key}"
            )
            
            # Update selected_params with the current value
            selected_params[param_key] = value

# Simulation settings
st.sidebar.header("Simulation Settings")
simulation_periods = st.sidebar.slider("Simulation Periods", 1, 30, 10)
# Remove warmup period slider and hardcode to 0
warmup_periods = 0

# Run simulation button
run_simulation = st.sidebar.button("Run Simulation")

# Function to run the model with selected parameters
def run_model(custom_params=None):
    # Create a clean model
    model = create_growth_model()
    
    # Set default parameters
    model.set_values(growth_parameters)
    model.set_values(growth_exogenous)
    model.set_values(growth_variables)
    
    # If custom parameters provided, override the defaults
    if custom_params:
        model.set_values(custom_params)
    
    # Suppress output from the model
    old_stdout = sys.stdout
    sys.stdout = NullIO()
    
    try:
        # No warmup periods ever - removed the warmup loop and run directly for simulation periods
        for _ in range(simulation_periods):
            model.solve(iterations=1000, threshold=1e-6)
    except SolutionNotFoundError as e:
        # Restore stdout before raising the exception
        sys.stdout = old_stdout
        # Re-raise the exception so it can be caught at a higher level
        raise e
    finally:
        # Restore stdout
        sys.stdout = old_stdout
    
    return model

# Create tabs for different outputs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Main Variables", "Advanced Charts", "Data Table", 
                               "Balance Sheet Matrix", "Revaluation Matrix", "Transaction Flow Matrix"])

# Model state management
if "baseline_model" not in st.session_state:
    with st.spinner("Running baseline simulation..."):
        try:
            st.session_state.baseline_model = run_model()
            st.success("Baseline model initialized!")
        except SolutionNotFoundError as e:
            st.error(f"Baseline model failed to converge. Error: {str(e)}")

if run_simulation:
    with st.spinner("Running custom simulation..."):
        try:
            st.session_state.custom_model = run_model(selected_params)
            st.success("Custom simulation complete!")
        except SolutionNotFoundError as e:
            st.error(f"The model failed to converge with the selected parameters. Try different values. Error: {str(e)}")

# Helper function to get model data
def get_model_data(model, variable):
    data = []
    for solution in model.solutions:
        data.append(solution.get(variable))
    return data

# Create comparison charts
if run_simulation and "custom_model" in st.session_state:
    baseline_model = st.session_state.baseline_model
    custom_model = st.session_state.custom_model
    
    # Create time range for x-axis
    time_range = list(range(len(baseline_model.solutions)))
    
    with tab1:
        st.header("Comparison of Key Variables")
        
        # Create 2x3 grid of plots for main variables
        col1, col2 = st.columns(2)
        
        # Plot variables in columns
        with col1:
            # Real Output
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'Yk')
            custom_data = get_model_data(custom_model, 'Yk')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Real Output (Yk)')
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Real Consumption
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'Ck')
            custom_data = get_model_data(custom_model, 'Ck')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Real Consumption (Ck)')
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Unemployment Rate (1-ER)
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_er = get_model_data(baseline_model, 'ER')
            custom_er = get_model_data(custom_model, 'ER')
            # Convert to unemployment rate (percentage)
            baseline_ur = [(1-er)*100 for er in baseline_er]
            custom_ur = [(1-er)*100 for er in custom_er]
            
            # Ensure both arrays are the same length
            min_len = min(len(baseline_ur), len(custom_ur), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_ur[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_ur[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Unemployment Rate (1-ER)')
            ax.set_ylabel('Rate (%)')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
        
        with col2:
            # Price Inflation
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = [d*100 for d in get_model_data(baseline_model, 'PI')]
            custom_data = [d*100 for d in get_model_data(custom_model, 'PI')]
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Price Inflation (PI)')
            ax.set_ylabel('Inflation Rate (%)')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Real Investment
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'Ik')
            custom_data = get_model_data(custom_model, 'Ik')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Real Investment (Ik)')
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Growth Rate of Capital
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = [d*100 for d in get_model_data(baseline_model, 'GRk')]
            custom_data = [d*100 for d in get_model_data(custom_model, 'GRk')]
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Growth Rate of Capital (GRk)')
            ax.set_ylabel('Growth Rate (%)')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
    
    with tab2:
        st.header("Advanced Financial and Fiscal Indicators")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Interest Rates
            fig, ax = plt.subplots(figsize=(10, 6))
            min_len = min(len(time_range), len(get_model_data(baseline_model, 'Rb')), 
                           len(get_model_data(custom_model, 'Rb')))
            time_range_x = time_range[:min_len]
            
            # Show baseline rates
            for rate_var, label, style in [('Rb', 'Bill Rate', '-'), ('Rl', 'Loan Rate', '--'), 
                                          ('Rm', 'Deposit Rate', ':')]:
                baseline_data = [d*100 for d in get_model_data(baseline_model, rate_var)]
                custom_data = [d*100 for d in get_model_data(custom_model, rate_var)]
                # Ensure consistency in array lengths
                var_min_len = min(min_len, len(baseline_data), len(custom_data))
                ax.plot(time_range_x[:var_min_len], baseline_data[:var_min_len], style, color='r', linewidth=1.5, 
                       label=f'{label} (Baseline)')
                ax.plot(time_range_x[:var_min_len], custom_data[:var_min_len], style, color='b', linewidth=2, 
                       label=f'{label} (Modified)')
            
            ax.set_title('Interest Rates')
            ax.set_ylabel('Rate (%)')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Government Deficit (PSBR)
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'PSBR')
            custom_data = get_model_data(custom_model, 'PSBR')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Government Deficit (PSBR)')
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Government Deficit to GDP Ratio
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_psbr = get_model_data(baseline_model, 'PSBR')
            baseline_y = get_model_data(baseline_model, 'Y')
            baseline_ratio = [psbr/y if y != 0 else 0 for psbr, y in zip(baseline_psbr, baseline_y)] # Avoid division by zero
            
            custom_psbr = get_model_data(custom_model, 'PSBR')
            custom_y = get_model_data(custom_model, 'Y')
            custom_ratio = [psbr/y if y != 0 else 0 for psbr, y in zip(custom_psbr, custom_y)] # Avoid division by zero
            
            # Ensure both arrays are the same length
            min_len = min(len(baseline_ratio), len(custom_ratio), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_ratio[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_ratio[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Government Deficit to GDP Ratio')
            ax.set_ylabel('Ratio')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Government Debt to GDP Ratio 
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Debt to GDP ratio
            baseline_gd = get_model_data(baseline_model, 'GD')
            baseline_y = get_model_data(baseline_model, 'Y')
            baseline_ratio = [gd/y if y != 0 else 0 for gd, y in zip(baseline_gd, baseline_y)] # Avoid division by zero
            
            custom_gd = get_model_data(custom_model, 'GD')
            custom_y = get_model_data(custom_model, 'Y')
            custom_ratio = [gd/y if y != 0 else 0 for gd, y in zip(custom_gd, custom_y)] # Avoid division by zero
            
            # Ensure both arrays are the same length
            min_len = min(len(baseline_ratio), len(custom_ratio), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_ratio[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_ratio[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Government Debt to GDP Ratio')
            ax.set_ylabel('Ratio')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
        
        with col2:
            # Tobin's Q
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'Q')
            custom_data = get_model_data(custom_model, 'Q')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title("Tobin's Q Ratio")
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
            
            # Burden of Personal Debt
            fig, ax = plt.subplots(figsize=(10, 6))
            baseline_data = get_model_data(baseline_model, 'BUR')
            custom_data = get_model_data(custom_model, 'BUR')
            # Ensure both arrays are the same length
            min_len = min(len(baseline_data), len(custom_data), len(time_range))
            
            ax.plot(time_range[:min_len], baseline_data[:min_len], 'r--', linewidth=2, label='Baseline')
            ax.plot(time_range[:min_len], custom_data[:min_len], 'b-', linewidth=2, label='Modified')
            ax.set_title('Burden of Personal Debt (BUR)')
            ax.set_ylabel('Value')
            ax.set_xlabel('Time Period')
            ax.legend()
            st.pyplot(fig)
    
    with tab3:
        st.header("Data Table")
        
        # Select which variables to display
        selected_vars = st.multiselect(
            "Select variables to display", 
            ['Yk', 'Ck', 'ER', 'PI', 'Ik', 'GRk', 'Rb', 'Rl', 'Rm', 'Q', 'BUR', 'GD', 'PSBR'],
            default=['Yk', 'Ck', 'ER', 'PI', 'Ik', 'GRk']
        )
        
        if selected_vars:
            # Create DataFrame for data table
            data_dict = {}
            
            for var in selected_vars:
                baseline_data = get_model_data(baseline_model, var)
                custom_data = get_model_data(custom_model, var)
                
                # Ensure all arrays have the same length
                min_len = min(len(baseline_data), len(custom_data), len(time_range))
                
                # Format based on variable type
                if var == 'PI':
                    baseline_data = [d*100 for d in baseline_data[:min_len]]  # Convert to percentage
                    custom_data = [d*100 for d in custom_data[:min_len]]
                    data_dict[f'{var}_baseline (%)'] = baseline_data
                    data_dict[f'{var}_modified (%)'] = custom_data
                elif var in ['Rb', 'Rl', 'Rm', 'GRk']:
                    baseline_data = [d*100 for d in baseline_data[:min_len]]  # Convert to percentage
                    custom_data = [d*100 for d in custom_data[:min_len]]
                    data_dict[f'{var}_baseline (%)'] = baseline_data
                    data_dict[f'{var}_modified (%)'] = custom_data
                else:
                    data_dict[f'{var}_baseline'] = baseline_data[:min_len]
                    data_dict[f'{var}_modified'] = custom_data[:min_len]
                
                # Add ratio where appropriate
                if var not in ['PI', 'Rb', 'Rl', 'Rm', 'GRk']:
                    # Avoid division by zero for ratio calculation
                    relative_data = [c/b if b != 0 else 0 for c, b in zip(custom_data[:min_len], baseline_data[:min_len])]
                    data_dict[f'{var}_ratio'] = relative_data
            
            df = pd.DataFrame(data_dict)
            df.index = time_range[:min_len]
            
            # Display the data table
            st.dataframe(df)
            
            # Download button
            csv = df.to_csv().encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="growth_model_data.csv",
                mime="text/csv",
            )
else:
    with tab1:
        st.info("👈 Adjust parameters in the sidebar and click 'Run Simulation' to see results.")
    
    with tab2:
        st.info("👈 Adjust parameters in the sidebar and click 'Run Simulation' to see results.")
    
    with tab3:
        st.info("👈 Adjust parameters in the sidebar and click 'Run Simulation' to see results.")

# Add an explanation section at the bottom
st.markdown("""
## About the Growth Model

This interactive app uses the GROWTH model from Chapter 11 of Monetary Economics, which is a Stock-Flow Consistent (SFC) model 
of a modern monetary economy. The model includes:

- Firms that make production and pricing decisions
- Households that consume, save, and make portfolio allocation decisions
- A government sector with fiscal policy
- A banking sector that sets interest rates and manages loans
- A central bank that sets the policy rate

### Key Exogenous Variables

The parameters you can adjust in the sidebar represent exogenous variables in the model:

- **Growth Parameters**: Control the baseline growth rate of capital and how it responds to utilization and interest rates
- **Consumption Parameters**: Determine how households consume out of income and wealth
- **Government Parameters**: Set fiscal policy through government spending growth and taxation
- **Bank/Monetary Parameters**: Influence interest rates and banking sector behavior
- **Labor Market Parameters**: Affect wage setting and employment dynamics
- **Personal Loan Parameters**: Determine household borrowing behavior

### Interpreting Results

The charts show how changing these parameters affects the economy compared to the baseline scenario:
- Values above 1.0 on relative charts indicate an increase compared to baseline
- Values below 1.0 indicate a decrease
- The red dashed line represents the baseline value
""")

# --- Refactored display_balance_sheet_matrix function using Pandas ---
def display_balance_sheet_matrix():
    st.markdown("""
    ## Table 11.1: The balance sheet of Model GROWTH
    
    This matrix displays the assets (+) and liabilities (-) of each sector in the economy.
    """)
    
    # Helper function to format values
    def format_value(val, include_sign=True):
        if abs(val) < 0.1: return "0"
        sign = "+" if val > 0 else "-"
        return f"{sign}{abs(val):,.0f}" if include_sign else f"{val:,.0f}"

    # Use actual model if available, otherwise use initial values
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        available_periods = list(range(1, periods + 1))
        selected_period = st.selectbox(
            "Select period to display:", 
            available_periods,
            index=len(available_periods) - 1,
            key="balance_sheet_period_pd" # Use a different key
        )
        solution = model.solutions[selected_period - 1]
        
        # Extract values
        IN_val = round(solution.get('IN', 0.0), 0)
        K_val = round(solution.get('K', 0.0), 0)
        Hh_val = round(solution.get('Hhd', 0.0), 0)
        H_val = round(solution.get('Hs', 0.0), 0)
        Hb_val = round(solution.get('Hbd', 0.0), 0)
        M_val = round(solution.get('Md', 0.0), 0)
        Bh_val = round(solution.get('Bhd', 0.0), 0)
        B_val = round(solution.get('Bs', 0.0), 0)
        Bcb_val = round(solution.get('Bcbd', 0.0), 0)
        Bb_val = round(solution.get('Bbd', 0.0), 0)
        BL_val = round(solution.get('BLd', 0.0), 0)
        Pbl_val = round(solution.get('Pbl', 0.0), 0)
        BL_Pbl_val = round(BL_val * Pbl_val, 0)
        Lh_val = round(solution.get('Lhd', 0.0), 0)
        Lf_val = round(solution.get('Lfd', 0.0), 0)
        L_val = round(solution.get('Lfs', 0.0) + solution.get('Lhs', 0.0), 0)
        e_val = round(solution.get('Ekd', 0.0), 0)
        Pe_val = round(solution.get('Pe', 0.0), 0)
        e_Pe_val = round(e_val * Pe_val, 0)
        OFb_val = round(solution.get('OFb', 0.0), 0)
        
        st.write(f"Showing balance sheet for period {selected_period} of {periods}")
    else:
        # Use initial values 
        IN_val, K_val, Hh_val, Hb_val, H_val, M_val, Bh_val, B_val, Bcb_val, Bb_val, BL_val, Pbl_val, BL_Pbl_val, Lh_val, Lf_val, L_val, e_val, Pe_val, e_Pe_val, OFb_val = (11585400, 127444000, 2630150, 2025540, 4655690, 40510800, 33396900, 42484800, 4655690, 4388930, 840742, 18.182, 15286984, 21606600, 15962900, 37569500, 5112.6001, 17937, 91704168, 3473280)
        st.write("Showing initial balance sheet values")
    
    # Calculate net worth
    h_assets = Hh_val + M_val + Bh_val + BL_Pbl_val + e_Pe_val + OFb_val
    h_liabilities = Lh_val
    h_net_worth = h_assets - h_liabilities
    f_assets = IN_val + K_val
    f_liabilities = Lf_val + e_Pe_val
    f_net_worth = f_assets - f_liabilities
    g_liabilities = B_val + BL_Pbl_val
    g_net_worth = -g_liabilities
    total_real_assets = IN_val + K_val

    # Define index and columns in correct order
    index = [
        "Inventories", "Fixed capital", "HPM", "Money", "Bills", 
        "Bonds", "Loans", "Equities", "Bank capital", "Balance", "Σ"
    ]
    columns = ["Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]

    # Create data array in the correct order
    data_array = [
        # Households, Firms, Govt., CB, Banks, Σ
        ["", format_value(IN_val), "", "", "", format_value(IN_val)],                     # Inventories
        ["", format_value(K_val), "", "", "", format_value(K_val)],                      # Fixed capital
        [format_value(Hh_val), "", "", format_value(-H_val), format_value(Hb_val), "0"],      # HPM
        [format_value(M_val), "", "", "", format_value(-M_val), "0"],                      # Money
        [format_value(Bh_val), "", format_value(-B_val), format_value(Bcb_val), format_value(Bb_val), "0"], # Bills
        [format_value(BL_Pbl_val), "", format_value(-BL_Pbl_val), "", "", "0"],             # Bonds
        [format_value(-Lh_val), format_value(-Lf_val), "", "", format_value(L_val), "0"],      # Loans
        [format_value(e_Pe_val), format_value(-e_Pe_val), "", "", "", "0"],                 # Equities
        [format_value(OFb_val), "", "", "", format_value(-OFb_val), "0"],                 # Bank capital
        [format_value(-h_net_worth), format_value(-f_net_worth), format_value(g_net_worth), "0", "0", format_value(-total_real_assets)], # Balance (Net Worth)
        ["0", "0", "0", "0", "0", "0"]                                              # Sum
    ]

    # Create DataFrame
    df = pd.DataFrame(data_array, index=index, columns=columns)

    # Display using st.dataframe
    st.dataframe(df)

# --- Refactored display_revaluation_matrix function using Pandas ---
def display_revaluation_matrix():
    st.markdown("""
    ## Table 11.2: The revaluation account (matrix) of Model GROWTH
    
    This matrix displays capital gains or losses due to changes in asset prices between periods.
    """)
    
    # Helper function to format values
    def format_value(val, include_sign=True):
        if abs(val) < 0.1: return "0"
        sign = "+" if val > 0 else "-"
        return f"{sign}{abs(val):,.0f}" if include_sign else f"{val:,.0f}"

    # Check if we have a model with solutions
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        # Need at least 2 periods to show revaluation
        if periods >= 2:
            available_periods = list(range(2, periods + 1))
            selected_period = st.selectbox(
                "Select period to display:", 
                available_periods,
                index=len(available_periods) - 1,
                key="revaluation_period_pd" # Use different key
            )
            
            solution = model.solutions[selected_period - 1]
            prev_solution = model.solutions[selected_period - 2]
            
            st.write(f"Showing revaluation matrix for period {selected_period} (changes from period {selected_period-1})")
            
            # Extract and calculate values
            Pbl_curr = solution.get('Pbl', 0.0)
            Pbl_prev = prev_solution.get('Pbl', 0.0)
            delta_Pbl = Pbl_curr - Pbl_prev
            BLd_curr = solution.get('BLd', 0.0)
            Pe_curr = solution.get('Pe', 0.0)
            Pe_prev = prev_solution.get('Pe', 0.0)
            delta_Pe = Pe_curr - Pe_prev
            Ekd_curr = solution.get('Ekd', 0.0)
            Eks_curr = solution.get('Eks', 0.0)
            
            bonds_hl = BLd_curr * delta_Pbl
            equity_hl = Ekd_curr * delta_Pe
            total_h = bonds_hl + equity_hl
            equity_fl = -Eks_curr * delta_Pe
            bonds_gl = -BLd_curr * delta_Pbl
            
            # Define index and columns
            index = ["Bonds", "Equities", "Bank equity", "Fixed capital", "Balance", "Σ"]
            # Note: First column header is intentionally blank for alignment in st.dataframe
            columns = ["", "Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"] 

            # Format data for display
            data_array = [
                ["Bonds", format_value(bonds_hl), "", format_value(bonds_gl), "", "", "0"],
                ["Equities", format_value(equity_hl), format_value(equity_fl), "", "", "", "0"],
                ["Bank equity", "0", "", "", "", "0", "0"], # Bank equity revaluation not modeled
                ["Fixed capital", "", "0", "", "", "", "0"], # Fixed capital revaluation not modeled
                ["Balance", format_value(-total_h), format_value(-equity_fl), format_value(-bonds_gl), "0", "0", "0"], # Balance
                ["Σ", "0", "0", "0", "0", "0", "0"] # Sum
            ]
            
            # Create DataFrame
            df = pd.DataFrame(data_array, columns=columns)
            df = df.set_index(columns[0]) # Set first column as index

            # Display using st.dataframe
            st.dataframe(df)
            
        else:
            st.info("Revaluation matrix requires at least two periods of data. Run a simulation with multiple periods to view revaluation effects.")
    else:
        st.info("No model data available. Run a simulation with multiple periods to view the revaluation matrix.")

# --- Refactored display_transaction_flow_matrix function using Pandas ---
def display_transaction_flow_matrix():
    st.markdown("""
    ## Table 11.3: The transaction flow matrix of Model GROWTH
    
    This matrix displays all the transactions between sectors in the economy for a given period.
    """)
    
    # Helper function to format values
    def format_value(val, include_sign=True):
        if abs(val) < 0.1: return "0"
        sign = "+" if val > 0 else "-"
        return f"{sign}{abs(val):,.0f}" if include_sign else f"{val:,.0f}"

    # Use actual model if available
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        available_periods = list(range(1, periods + 1))
        selected_period = st.selectbox(
            "Select period to display:", 
            available_periods,
            index=len(available_periods) - 1,
            key="transaction_flow_period_pd" # Use different key
        )
        
        solution = model.solutions[selected_period - 1]
        
        if selected_period == 1:
             st.info("Transaction Flow Matrix requires data from the previous period. Select period 2 or later.")
             return 
        prev_solution = model.solutions[selected_period - 2] 

        st.write(f"Showing transaction flow matrix for period {selected_period} of {periods}")
        
        # --- Extract values ---
        C_val = round(solution.get('CONS', 0.0), 0)
        G_val = round(solution.get('G', 0.0), 0)
        I_val = round(solution.get('INV', 0.0), 0) 
        WB_val = round(solution.get('WB', 0.0), 0)
        T_val = round(solution.get('T', 0.0), 0)
        r_val = solution.get('Rb', 0.0) 
        rm_val = solution.get('Rm', 0.0)
        rl_val = solution.get('Rl', 0.0)
        Md_prev = prev_solution.get('Md', 0.0) 
        Bhd_prev = prev_solution.get('Bhd', 0.0)
        Bbd_prev = prev_solution.get('Bbd', 0.0)
        Bcbd_prev = prev_solution.get('Bcbd', 0.0)
        Bs_prev = prev_solution.get('Bs', 0.0)
        Lhd_prev = prev_solution.get('Lhd', 0.0)
        Lfd_prev = prev_solution.get('Lfd', 0.0)
        IN_prev = prev_solution.get('IN', 0.0)
        r_Bhd_val = round(r_val * Bhd_prev, 0)
        r_Bbd_val = round(r_val * Bbd_prev, 0)
        r_Bcbd_val = round(r_val * Bcbd_prev, 0)
        r_Bs_val = round(r_val * Bs_prev, 0) 
        rm_Md_val = round(rm_val * Md_prev, 0)
        rl_Lhd_val = round(rl_val * Lhd_prev, 0)
        rl_Lfd_val = round(rl_val * Lfd_prev, 0)
        InvFinCost_val = round(rl_val * IN_prev, 0) 
        BL_prev = prev_solution.get('BLs', 0.0) 
        coupon_val = solution.get('Rbl', 0.0) 
        coupons_val = round(coupon_val * BL_prev, 0)
        Ff_val = round(solution.get('Ff', 0.0), 0) 
        Fb_val = round(solution.get('Fb', 0.0), 0) 
        Fcb_val = round(solution.get('Fcb', 0.0), 0) 
        FDf_val = round(solution.get('FDf', 0.0), 0) 
        FDb_val = round(solution.get('FDb', 0.0), 0) 
        FUf_val = round(solution.get('FUf', 0.0), 0) 
        FUb_val = round(solution.get('FUb', 0.0), 0) 
        delta_H_h_val = round(solution.get('Hhd', 0.0) - prev_solution.get('Hhd', 0.0), 0)
        delta_H_b_val = round(solution.get('Hbd', 0.0) - prev_solution.get('Hbd', 0.0), 0)
        delta_H_val = round(solution.get('Hs', 0.0) - prev_solution.get('Hs', 0.0), 0)
        delta_M_h_val = round(solution.get('Md', 0.0) - prev_solution.get('Md', 0.0), 0)
        delta_M_b_val = round(solution.get('Ms', 0.0) - prev_solution.get('Ms', 0.0), 0)
        delta_Bh_val = round(solution.get('Bhd', 0.0) - prev_solution.get('Bhd', 0.0), 0)
        delta_Bb_val = round(solution.get('Bbd', 0.0) - prev_solution.get('Bbd', 0.0), 0)
        delta_Bcb_val = round(solution.get('Bcbd', 0.0) - prev_solution.get('Bcbd', 0.0), 0)
        delta_B_val = round(solution.get('Bs', 0.0) - prev_solution.get('Bs', 0.0), 0)
        delta_BL_val = round(solution.get('BLs', 0.0) - prev_solution.get('BLs', 0.0), 0) 
        Pbl_val = solution.get('Pbl', 0.0)
        delta_BL_Pbl_val = round(delta_BL_val * Pbl_val, 0) 
        delta_Lh_val = round(solution.get('Lhd', 0.0) - prev_solution.get('Lhd', 0.0), 0)
        delta_Lf_val = round(solution.get('Lfd', 0.0) - prev_solution.get('Lfd', 0.0), 0)
        delta_L_val = round((solution.get('Lhs', 0.0) - prev_solution.get('Lhs', 0.0)) + (solution.get('Lfs', 0.0) - prev_solution.get('Lfs', 0.0)), 0)
        Pe_val = solution.get('Pe', 0.0) 
        delta_e_val = round(solution.get('Ekd', 0.0) - prev_solution.get('Ekd', 0.0), 0) 
        delta_e_Pe_val = round(delta_e_val * Pe_val, 0) 
        NPL_val = round(solution.get('NPL', 0.0), 0) 
        delta_IN_val = round(solution.get('IN', 0.0) - prev_solution.get('IN', 0.0), 0) 

        # --- Define Multi-Level Headers ---
        headers = pd.MultiIndex.from_tuples([
            ("", ""), ("Households", ""), ("Firms", "Current"), ("Firms", "Capital"), 
            ("Govt.", ""), ("Central bank", "Current"), ("Central bank", "Capital"), 
            ("Banks", "Current"), ("Banks", "Capital"), ("Σ", "")
        ], names=['Sector', 'Flow'])
        
        # --- Define Row Index ---
        index = [
            "Consumption", "Government expenditures", "Investment", "Inventory accumulation", 
            "--- Income/Costs ---", 
            "Wages", "Inventory financing cost", "Taxes", "Entrepreneurial Profits", "Bank profits", "Central bank profits", 
            "--- Interest Flows ---", 
            "Interest on bills", "Interest on deposits", "Interest on loans", "Bond coupon payments", 
            "--- Change in Stocks ---", 
            "ΔLoans", "ΔCash", "ΔMoney deposits", "ΔBills", "ΔBonds", "ΔEquities", "Loan defaults", 
            "--- Balance Check ---", 
            "Σ"
        ]

        # --- Format data for display (10 columns) ---
        # Using a dictionary for easier column mapping
        data_dict = {
            ("Households", ""): [
                format_value(-C_val), "", "", "", "", 
                format_value(WB_val), "", format_value(-T_val), format_value(FDf_val), format_value(FDb_val), "", "",
                format_value(r_Bhd_val), format_value(rm_Md_val), format_value(-rl_Lhd_val), format_value(coupons_val), "",
                format_value(delta_Lh_val), format_value(-delta_H_h_val), format_value(-delta_M_h_val), format_value(-delta_Bh_val), format_value(-delta_BL_Pbl_val), format_value(-delta_e_Pe_val), "", "",
                "0"
            ],
            ("Firms", "Current"): [
                format_value(C_val), format_value(G_val), "", format_value(delta_IN_val), "",
                format_value(-WB_val), format_value(-InvFinCost_val), "", format_value(-Ff_val), "", "", "",
                "", "", format_value(-rl_Lfd_val), "", "",
                "", "", "", "", "", "", "", "",
                "0"
            ],
            ("Firms", "Capital"): [
                "", "", format_value(-I_val), format_value(-delta_IN_val), "",
                "", "", "", format_value(FUf_val), "", "", "",
                "", "", "", "", "",
                format_value(delta_Lf_val), "", "", "", "", format_value(delta_e_Pe_val), format_value(NPL_val), "",
                "0"
            ],
            ("Govt.", ""): [
                "", format_value(-G_val), "", "", "",
                "", "", format_value(T_val), "", "", format_value(Fcb_val), "",
                format_value(-r_Bs_val), "", "", format_value(-coupons_val), "",
                "", "", "", format_value(delta_B_val), format_value(delta_BL_Pbl_val), "", "", "",
                "0"
            ],
            ("Central bank", "Current"): [
                "", "", "", "", "",
                "", "", "", "", "", format_value(-Fcb_val), "",
                format_value(r_Bcbd_val), "", "", "", "",
                "", "", "", "", "", "", "", "",
                "0"
            ],
            ("Central bank", "Capital"): [
                "", "", "", "", "",
                "", "", "", "", "", "", "",
                "", "", "", "", "",
                "", format_value(-delta_H_val), "", format_value(-delta_Bcb_val), "", "", "", "",
                "0"
            ],
            ("Banks", "Current"): [
                "", "", "", "", "",
                "", format_value(InvFinCost_val), "", "", format_value(-Fb_val), "", "",
                format_value(r_Bbd_val), format_value(-rm_Md_val), format_value(rl_Lhd_val + rl_Lfd_val), "", "",
                "", "", "", "", "", "", "", "",
                "0"
            ],
            ("Banks", "Capital"): [
                "", "", "", "", "",
                "", "", "", "", format_value(FUb_val), "", "",
                "", "", "", "", "",
                format_value(-delta_L_val), format_value(-delta_H_b_val), format_value(delta_M_b_val), format_value(-delta_Bb_val), "", "", format_value(-NPL_val), "",
                "0"
            ],
            ("Σ", ""): [ # Corrected Sum Column
                "0", "0", "0", "0", "", 
                "0", "0", "0", "0", "0", "0", "", 
                "0", "0", "0", "0", "", 
                "0", "0", "0", "0", "0", "0", "0", "", # All stock changes sum to 0
                format_value(delta_IN_val)
            ]
        }
        
        # Create DataFrame
        df = pd.DataFrame(data_dict, index=index) # Use index list directly
        df.index.name = "Flow" # Name the index

        # Display using st.dataframe
        st.dataframe(df)

    else:
        st.info("No model data available. Run a simulation to view the transaction flow matrix.")

# Display matrix tabs content even if simulation hasn't run (Correctly outside function)
with tab4:
    display_balance_sheet_matrix()
    
with tab5:
    display_revaluation_matrix()
    
with tab6:
    display_transaction_flow_matrix()
