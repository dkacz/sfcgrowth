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
        ("omega1", "Parameter in wage equation (omega1)", 1.0, 0.9, 1.1),
        ("omega2", "Parameter in wage equation (omega2)", 2.0, 1.0, 3.0),
        ("omega3", "Speed of wage adjustment (omega3)", 0.45621, 0.1, 0.9),
        ("GRpr", "Growth rate of productivity (GRpr)", 0.03, 0.0, 0.1),
        ("BANDt", "Upper band of flat Phillips curve (BANDt)", 0.01, 0.0, 0.05),
        ("BANDb", "Lower band of flat Phillips curve (BANDb)", 0.01, 0.0, 0.05),
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
            baseline_ratio = [psbr/y for psbr, y in zip(baseline_psbr, baseline_y)]
            
            custom_psbr = get_model_data(custom_model, 'PSBR')
            custom_y = get_model_data(custom_model, 'Y')
            custom_ratio = [psbr/y for psbr, y in zip(custom_psbr, custom_y)]
            
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
            baseline_ratio = [gd/y for gd, y in zip(baseline_gd, baseline_y)]
            
            custom_gd = get_model_data(custom_model, 'GD')
            custom_y = get_model_data(custom_model, 'Y')
            custom_ratio = [gd/y for gd, y in zip(custom_gd, custom_y)]
            
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
                    relative_data = [c/b for c, b in zip(custom_data[:min_len], baseline_data[:min_len])]
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

# Define functions to display the matrices
def display_balance_sheet_matrix():
    st.markdown("""
    ## Table 11.1: The balance sheet of Model GROWTH
    
    This matrix displays the assets (+) and liabilities (-) of each sector in the economy.
    
    **Hover over cells** to see detailed explanations.
    """)
    
    # Use actual model if available, otherwise use initial values
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        # Add period selection
        available_periods = list(range(1, periods + 1))
        selected_period = st.selectbox(
            "Select period to display:", 
            available_periods,
            index=len(available_periods) - 1,  # Default to last period
            key="balance_sheet_period"
        )
        
        # Get the selected solution (adjust index since solutions are 0-indexed)
        solution = model.solutions[selected_period - 1]
        
        # Extract values from the model
        IN_val = round(solution.get('IN'), 0)
        K_val = round(solution.get('K'), 0)
        Hh_val = round(solution.get('Hhd'), 0)
        H_val = round(solution.get('Hs'), 0)
        Hb_val = round(solution.get('Hbd'), 0)
        M_val = round(solution.get('Md'), 0)
        Bh_val = round(solution.get('Bhd'), 0)
        B_val = round(solution.get('Bs'), 0)
        Bcb_val = round(solution.get('Bcbd'), 0)
        Bb_val = round(solution.get('Bbd'), 0)
        BL_val = round(solution.get('BLd'), 0)
        Pbl_val = round(solution.get('Pbl'), 0)
        BL_Pbl_val = round(BL_val * Pbl_val, 0)
        Lh_val = round(solution.get('Lhd'), 0)
        Lf_val = round(solution.get('Lfd'), 0)
        L_val = round(solution.get('Lfs') + solution.get('Lhs'), 0)
        e_val = round(solution.get('Ekd'), 0)
        Pe_val = round(solution.get('Pe'), 0)
        e_Pe_val = round(e_val * Pe_val, 0)
        OFb_val = round(solution.get('OFb'), 0)
        
        st.write(f"Showing balance sheet for period {selected_period} of {periods}")
    else:
        # Use initial values from the growth_variables
        # These are from growth_variables in the chapter_11_model_growth.py file
        IN_val = 11585400
        K_val = 127444000
        Hh_val = 2630150
        Hb_val = 2025540
        H_val = Hh_val + Hb_val  # Hs = Hbd + Hhd
        M_val = 40510800
        Bh_val = 33396900
        B_val = 42484800
        Bcb_val = 4655690
        Bb_val = 4388930
        BL_val = 840742
        Pbl_val = 18.182  # Default from the model
        BL_Pbl_val = round(BL_val * Pbl_val, 0)
        Lh_val = 21606600
        Lf_val = 15962900
        L_val = Lh_val + Lf_val
        e_val = 5112.6001
        Pe_val = 17937  # Default from the model
        e_Pe_val = round(e_val * Pe_val, 0)
        OFb_val = 3473280
        
        st.write("Showing initial balance sheet values")
    
    # Calculate net worth for each sector
    # Assets - liabilities in each column
    h_assets = Hh_val + M_val + Bh_val + BL_Pbl_val + e_Pe_val + OFb_val
    h_liabilities = Lh_val
    h_net_worth = h_assets - h_liabilities
    
    f_assets = IN_val + K_val
    f_liabilities = Lf_val + e_Pe_val
    f_net_worth = f_assets - f_liabilities
    
    g_assets = 0
    g_liabilities = B_val + BL_Pbl_val
    g_net_worth = g_assets - g_liabilities
    
    # Central bank and banks should balance to zero
    cb_net_worth = 0
    b_net_worth = 0
    
    # Total real assets (should equal negative of total net worth)
    total_real_assets = IN_val + K_val
    
    # Define tooltips with detailed calculations
    # Note: The keys need to be shifted one column to the left to fix the alignment
    # The correct mapping should be (row, column-1)
    tooltips = {
        # Inventories row
        (0, 0): f"Stock of inventories at current costs: {IN_val:,.0f}",
        (0, 1): "",
        (0, 2): "",
        (0, 3): "",
        (0, 4): "",
        (0, 5): f"Sum of all inventories across sectors: {IN_val:,.0f}",
        
        # Fixed capital row
        (1, 0): f"Capital stock at replacement cost: {K_val:,.0f}",
        (1, 1): "",
        (1, 2): "",
        (1, 3): "",
        (1, 4): "",
        (1, 5): f"Sum of all fixed capital across sectors: {K_val:,.0f}",
        
        # HPM row
        (2, 0): f"Households' cash holdings: {Hh_val:,.0f}",
        (2, 1): "",
        (2, 2): "",
        (2, 3): f"Total high-powered money issued by central bank (negative as liability): {-H_val:,.0f}",
        (2, 4): f"Banks' reserves at central bank: {Hb_val:,.0f}",
        (2, 5): "Sum equals zero as all HPM issued must be held",
        
        # Money row
        (3, 0): f"Deposits held by households: {M_val:,.0f}",
        (3, 1): "",
        (3, 2): "",
        (3, 3): "",
        (3, 4): f"Deposits issued by banks (negative as liability): {-M_val:,.0f}",
        (3, 5): "Sum equals zero as all deposits issued must be held",
        
        # Bills row
        (4, 0): f"Treasury bills held by households: {Bh_val:,.0f}",
        (4, 1): "",
        (4, 2): f"Treasury bills issued by government (negative as liability): {-B_val:,.0f}",
        (4, 3): f"Treasury bills held by central bank: {Bcb_val:,.0f}",
        (4, 4): f"Treasury bills held by banks: {Bb_val:,.0f}",
        (4, 5): "Sum equals zero as all bills issued must be held",
        
        # Bonds row
        (5, 0): f"Bonds held by households: {BL_val:,.0f} bonds × {Pbl_val:.2f} price = {BL_Pbl_val:,.0f}",
        (5, 1): "",
        (5, 2): f"Bonds issued by government (negative as liability): {BL_val:,.0f} bonds × {Pbl_val:.2f} price = {-BL_Pbl_val:,.0f}",
        (5, 3): "",
        (5, 4): "",
        (5, 5): "Sum equals zero as all bonds issued must be held",
        
        # Loans row
        (6, 0): f"Loans taken by households (negative as liability): {-Lh_val:,.0f}",
        (6, 1): f"Loans taken by firms (negative as liability): {-Lf_val:,.0f}",
        (6, 2): "",
        (6, 3): "",
        (6, 4): f"Total loans issued by banks: {Lh_val:,.0f} (households) + {Lf_val:,.0f} (firms) = {L_val:,.0f}",
        (6, 5): "Sum equals zero as all loans issued must be borrowed",
        
        # Equities row
        (7, 0): f"Equities held by households: {e_val:,.0f} equities × {Pe_val:.2f} price = {e_Pe_val:,.0f}",
        (7, 1): f"Equities issued by firms (negative as liability): {-e_val:,.0f} equities × {Pe_val:.2f} price = {-e_Pe_val:,.0f}",
        (7, 2): "",
        (7, 3): "",
        (7, 4): "",
        (7, 5): "Sum equals zero as all equities issued must be held",
        
        # Bank capital row
        (8, 0): f"Banks' capital as an asset for households: {OFb_val:,.0f}",
        (8, 1): "",
        (8, 2): "",
        (8, 3): "",
        (8, 4): f"Banks' capital as a liability for banks: {-OFb_val:,.0f}",
        (8, 5): "Sum equals zero as bank capital is both an asset and liability",
        
        # Balance row
        (9, 0): f"Net worth of households = Assets ({h_assets:,.0f}) - Liabilities ({h_liabilities:,.0f}) = {-h_net_worth:,.0f}",
        (9, 1): f"Net worth of firms = Assets ({f_assets:,.0f}) - Liabilities ({f_liabilities:,.0f}) = {-f_net_worth:,.0f}",
        (9, 2): f"Net worth of government = Assets (0) - Liabilities ({g_liabilities:,.0f}) = {abs(g_net_worth):,.0f}",
        (9, 3): "Net worth of central bank (should be zero)",
        (9, 4): "Net worth of banks (should be zero)",
        (9, 5): f"Total real assets = Inventories ({IN_val:,.0f}) + Fixed capital ({K_val:,.0f}) = {-total_real_assets:,.0f}",
        
        # Sum row
        (10, 0): "Column sum (should be zero as all assets = liabilities + net worth)",
        (10, 1): "Column sum (should be zero as all assets = liabilities + net worth)",
        (10, 2): "Column sum (should be zero as all assets = liabilities + net worth)",
        (10, 3): "Column sum (should be zero as all assets = liabilities + net worth)",
        (10, 4): "Column sum (should be zero as all assets = liabilities + net worth)",
        (10, 5): "Column sum (should be zero as all assets = liabilities + net worth)",
    }
    
    # Row labels and data for the matrix
    row_labels = [
        "Inventories",
        "Fixed capital",
        "HPM",
        "Money",
        "Bills",
        "Bonds",
        "Loans",
        "Equities",
        "Bank capital",
        "Balance",
        "Σ"
    ]
    
    # Format data for display (without duplicate first column)
    data = [
        ["", f"+{IN_val:,.0f}", "", "", "", f"+{IN_val:,.0f}"],
        ["", f"+{K_val:,.0f}", "", "", "", f"+{K_val:,.0f}"],
        [f"+{Hh_val:,.0f}", "", "", f"-{H_val:,.0f}", f"+{Hb_val:,.0f}", "0"],
        [f"+{M_val:,.0f}", "", "", "", f"-{M_val:,.0f}", "0"],
        [f"+{Bh_val:,.0f}", "", f"-{B_val:,.0f}", f"+{Bcb_val:,.0f}", f"+{Bb_val:,.0f}", "0"],
        [f"+{BL_Pbl_val:,.0f}", "", f"-{BL_Pbl_val:,.0f}", "", "", "0"],
        [f"-{Lh_val:,.0f}", f"-{Lf_val:,.0f}", "", "", f"+{L_val:,.0f}", "0"],
        [f"+{e_Pe_val:,.0f}", f"-{e_Pe_val:,.0f}", "", "", "", "0"],
        [f"+{OFb_val:,.0f}", "", "", "", f"-{OFb_val:,.0f}", "0"],
        [f"-{h_net_worth:,.0f}", f"-{f_net_worth:,.0f}", f"+{abs(g_net_worth):,.0f}", "0", "0", f"-{total_real_assets:,.0f}"],
        ["0", "0", "0", "0", "0", "0"]
    ]
    
    # Column headers
    headers = ["Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]
    
    # Convert to numpy arrays for heatmap
    z_values = np.zeros((len(data), len(headers)))
    text_values = [['' for _ in range(len(headers))] for _ in range(len(data))]
    hover_texts = [['' for _ in range(len(headers))] for _ in range(len(data))]
    
    for i in range(len(data)):
        for j in range(len(headers)):
            cell_value = data[i][j]
            text_values[i][j] = cell_value
            
            # Set numeric value for color
            if isinstance(cell_value, str):
                if cell_value.startswith('+'):
                    z_values[i][j] = 1  # Positive values
                elif cell_value.startswith('-'):
                    z_values[i][j] = -1  # Negative values
                else:
                    z_values[i][j] = 0  # Zero or text
            
            # Set hover text - use the value itself as tooltip if empty
            tooltip = tooltips.get((i, j), "")
            if tooltip:
                hover_texts[i][j] = tooltip
            elif cell_value:  # If no tooltip but has a value, use the value
                hover_texts[i][j] = cell_value
            else:
                hover_texts[i][j] = ""
    
    # Create custom colorscale
    colorscale = [
        [0, '#FF9999'],  # Red for negative
        [0.5, '#1E1E1E'],  # Dark background for zero/text
        [1, '#8FD14F']   # Green for positive
    ]
    
    # Create heatmap with properly aligned tooltips
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=headers,
        y=row_labels,
        colorscale=colorscale,
        showscale=False,
        text=text_values,
        hovertext=hover_texts,
        hoverinfo='text',
        texttemplate="%{text}",
    ))
    
    # Update layout for better appearance
    fig.update_layout(
        height=550,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white'),
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            side='top',
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
        )
    )
    
    # Display the heatmap
    st.plotly_chart(fig, use_container_width=True)

def display_revaluation_matrix():
    st.markdown("""
    ## Table 11.2: The revaluation account (matrix) of Model GROWTH
    
    This matrix displays capital gains or losses due to changes in asset prices between periods.
    
    **Note**: Detailed explanations of each value are shown in the cells as text.
    """)
    
    # Check if we have a model with solutions
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        # Need at least 2 periods to show revaluation
        if periods >= 2:
            # Add period selection
            available_periods = list(range(2, periods + 1))  # Start from period 2 since we need previous period data
            selected_period = st.selectbox(
                "Select period to display:", 
                available_periods,
                index=len(available_periods) - 1,  # Default to last period
                key="revaluation_period"
            )
            
            # Get the selected solution and previous period (adjust index since solutions are 0-indexed)
            solution = model.solutions[selected_period - 1]
            prev_solution = model.solutions[selected_period - 2]
            
            st.write(f"Showing revaluation matrix for period {selected_period} (changes from period {selected_period-1})")
            
            # Helper function to format values and avoid small decimals displaying as "+0" or "-0"
            def format_value(val, include_sign=True):
                # If the value is very small, just return 0
                if abs(val) < 0.1:
                    return "0"
                
                if include_sign:
                    sign = "+" if val > 0 else "-"
                    return f"{sign}{abs(val):,.0f}"
                else:
                    return f"{val:,.0f}"
            
            # Extract and calculate values for revaluation matrix
            # Change in bond prices
            Pbl_curr = solution.get('Pbl')
            Pbl_prev = prev_solution.get('Pbl')
            delta_Pbl = Pbl_curr - Pbl_prev
            
            # Extract bond quantities
            BLd_curr = solution.get('BLd')
            
            # Change in equity prices
            Pe_curr = solution.get('Pe')
            Pe_prev = prev_solution.get('Pe')
            delta_Pe = Pe_curr - Pe_prev
            
            # Extract equity quantities
            Ekd_curr = solution.get('Ekd')
            Eks_curr = solution.get('Eks')
            
            # Calculations for revaluation gains/losses
            # Households bonds gain/loss
            bonds_hl = BLd_curr * delta_Pbl
            
            # Households equity gain/loss
            equity_hl = Ekd_curr * delta_Pe
            
            # Households total gain/loss
            total_h = bonds_hl + equity_hl
            
            # Firms equity loss/gain (opposite of households)
            equity_fl = -Eks_curr * delta_Pe
            
            # Government bonds loss/gain (opposite of households)
            bonds_gl = -BLd_curr * delta_Pbl
            
            # Store calculation details for tooltip display
            calculations = {
                "bonds_hl": f"BLd × ΔPbl = {BLd_curr:,.0f} × {delta_Pbl:,.2f} = {bonds_hl:,.0f}",
                "equity_hl": f"Ekd × ΔPe = {Ekd_curr:,.0f} × {delta_Pe:,.2f} = {equity_hl:,.0f}",
                "equity_fl": f"-Eks × ΔPe = -{Eks_curr:,.0f} × {delta_Pe:,.2f} = {equity_fl:,.0f}",
                "bonds_gl": f"-BLd × ΔPbl = -{BLd_curr:,.0f} × {delta_Pbl:,.2f} = {bonds_gl:,.0f}",
            }
            
            # Define tooltips for each cell
            tooltips = {
                # Bonds row
                (0, 0): "Government bonds",
                (0, 1): f"Capital gain on household's bond holdings: {calculations['bonds_hl']}",
                (0, 2): "",
                (0, 3): f"Capital loss on government's bond liabilities: {calculations['bonds_gl']}",
                (0, 4): "",
                (0, 5): "",
                (0, 6): "Net change in bond values (should be zero as gains equal losses)",
                
                # Equities row
                (1, 0): "Firm equities",
                (1, 1): f"Capital gain on household's equity holdings: {calculations['equity_hl']}",
                (1, 2): f"Capital loss on firm's equity liabilities: {calculations['equity_fl']}",
                (1, 3): "",
                (1, 4): "",
                (1, 5): "",
                (1, 6): "Net change in equity values (should be zero as gains equal losses)",
                
                # Bank equity row - zero since model doesn't track bank equity price changes
                (2, 0): "Bank equity",
                (2, 1): "Capital gain on household's bank equity holdings (zero in this model)",
                (2, 2): "",
                (2, 3): "",
                (2, 4): "",
                (2, 5): "Capital loss on bank's equity liabilities (zero in this model)",
                (2, 6): "Net change in bank equity values (zero in this model)",
                
                # Fixed capital row - should be zero since model doesn't track fixed capital price changes
                (3, 0): "Fixed capital",
                (3, 1): "",
                (3, 2): "Capital gain on firm's fixed capital (zero in this model)",
                (3, 3): "",
                (3, 4): "",
                (3, 5): "",
                (3, 6): "Net change in fixed capital values (zero in this model)",
                
                # Balance row - shows total revaluation gains/losses by sector
                (4, 0): "Revaluation balances",
                (4, 1): f"Total revaluation gains for households: Bonds ({format_value(bonds_hl)}) + Equities ({format_value(equity_hl)}) = {format_value(total_h)}",
                (4, 2): f"Total revaluation losses for firms (from equities): {format_value(equity_fl)}",
                (4, 3): f"Total revaluation losses for government (from bonds): {format_value(bonds_gl)}",
                (4, 4): "Revaluation for central bank (zero in this model)",
                (4, 5): "Revaluation for banks (zero in this model)",
                (4, 6): "Sum of all revaluation gains/losses (should be zero)",
                
                # Sum row - should be all zeros as each column should sum to zero
                (5, 0): "Column sum",
                (5, 1): "Sum of all revaluation items for households (should be zero)",
                (5, 2): "Sum of all revaluation items for firms (should be zero)",
                (5, 3): "Sum of all revaluation items for government (should be zero)",
                (5, 4): "Sum of all revaluation items for central bank (should be zero)",
                (5, 5): "Sum of all revaluation items for banks (should be zero)",
                (5, 6): "Total sum of all revaluation items (should be zero)",
            }
            
            # Format data for display
            data = [
                ["Bonds", format_value(bonds_hl), "", format_value(bonds_gl), "", "", "0"],
                ["Equities", format_value(equity_hl), format_value(equity_fl), "", "", "", "0"],
                ["Bank equity", "0", "", "", "", "0", "0"],
                ["Fixed capital", "", "0", "", "", "", "0"]
            ]
            
            # Add revaluation balances row
            data.append(["Balance", format_value(-total_h), format_value(-equity_fl), format_value(-bonds_gl), "0", "0", "0"])
            
            # Final row should be all zeros because each column balances
            data.append(["Σ", "0", "0", "0", "0", "0", "0"])
            
            # Column headers
            headers = ["", "Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]
            
            # Convert data to format needed for Plotly
            cell_values = [[] for _ in range(len(headers))]
            for i in range(len(data)):
                for j in range(len(headers)):
                    cell_values[j].append(data[i][j])
            
            # Create hover text matrix with tooltips
            hover_text = []
            for i in range(len(data)):
                row_hover = []
                for j in range(len(headers)):
                    tooltip = tooltips.get((i, j), "")
                    if tooltip:
                        row_hover.append(tooltip)
                    else:
                        row_hover.append("")
                hover_text.append(row_hover)
            
            # Create cell colors
            cell_colors = []
            for i in range(len(data)):
                row_colors = []
                for j in range(len(headers)):
                    val = data[i][j]
                    if isinstance(val, str):
                        if val.startswith('+'):
                            row_colors.append('#8FD14F')  # Darker green
                        elif val.startswith('-'):
                            row_colors.append('#FF9999')  # Darker red
                        else:
                            row_colors.append('#1E1E1E')  # Dark background
                    else:
                        row_colors.append('#1E1E1E')  # Dark background
                cell_colors.append(row_colors)
            
            # Create Plotly table
            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=headers,
                    fill_color='#0E1117',
                    align='center',
                    font=dict(color='white', size=14)
                ),
                cells=dict(
                    values=cell_values,
                    fill_color=[cell_colors[i] for i in range(len(cell_colors))],
                    align='right',
                    font=dict(color='white', size=12),
                    height=30,
                    text=hover_text
                ))
            ])
            
            # Update layout
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=400,
                paper_bgcolor='#0E1117',
                plot_bgcolor='#0E1117'
            )
            
            # Display the table
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Revaluation matrix requires at least two periods of data. Run a simulation with multiple periods to view revaluation effects.")
    else:
        st.info("No model data available. Run a simulation with multiple periods to view the revaluation matrix.")

def display_transaction_flow_matrix():
    st.markdown("""
    ## Table 11.3: The transaction flow matrix of Model GROWTH
    
    This matrix displays all the transactions between sectors in the economy for a given period.
    
    **Note**: Detailed explanations of each value are shown in the cells as text.
    """)
    
    # Use actual model if available
    if "custom_model" in st.session_state:
        model = st.session_state.custom_model
        periods = len(model.solutions)
        
        # Add period selection
        available_periods = list(range(1, periods + 1))
        selected_period = st.selectbox(
            "Select period to display:", 
            available_periods,
            index=len(available_periods) - 1,  # Default to last period
            key="transaction_flow_period"
        )
        
        # Get the selected solution (adjust index since solutions are 0-indexed)
        solution = model.solutions[selected_period - 1]
        
        st.write(f"Showing transaction flow matrix for period {selected_period} of {periods}")
        
        # Helper function to format values and avoid small decimals displaying as "+0" or "-0"
        def format_value(val, include_sign=True):
            # If the value is very small, just return 0
            if abs(val) < 0.1:
                return "0"
            
            if include_sign:
                sign = "+" if val > 0 else "-"
                return f"{sign}{abs(val):,.0f}"
            else:
                return f"{val:,.0f}"
        
        # Extract values from the solution
        # Consumption
        C_val = round(solution.get('CONS'), 0)
        
        # Government expenditures
        G_val = round(solution.get('G'), 0)
        
        # Investment
        I_val = round(solution.get('INV'), 0)
        
        # Firms
        N_val = round(solution.get('N'), 0)
        WB_val = round(solution.get('WB'), 0)
        INV_val = round(solution.get('INV'), 0)
        
        # Interest flows
        r_val = solution.get('r')
        rm_val = solution.get('rm')
        rl_val = solution.get('rl')
        Md_val = solution.get('Md')
        Bhd_val = solution.get('Bhd')
        Bbd_val = solution.get('Bbd')
        Bcbd_val = solution.get('Bcbd')
        Bs_val = solution.get('Bs')
        Lhd_val = solution.get('Lhd')
        Lfd_val = solution.get('Lfd')
        
        # Calculate interest amounts
        r_Bhd_val = round(r_val * Bhd_val, 0)
        r_Bbd_val = round(r_val * Bbd_val, 0)
        r_Bcbd_val = round(r_val * Bcbd_val, 0)
        r_Bs_val = round(r_val * Bs_val, 0)
        rm_Md_val = round(rm_val * Md_val, 0)
        rl_Lhd_val = round(rl_val * Lhd_val, 0)
        rl_Lfd_val = round(rl_val * Lfd_val, 0)
        
        # Bond coupon payments
        BL_val = solution.get('BLd')
        coupon_val = solution.get('coupon')
        coupons_val = round(coupon_val * BL_val, 0)
        
        # Dividends
        Ff_val = round(solution.get('Ff'), 0)
        Fb_val = round(solution.get('Fb'), 0)
        Fcb_val = round(solution.get('Fcb'), 0)
        
        # Taxes
        T_val = round(solution.get('T'), 0)
        
        # Changes in assets
        delta_H_h_val = round(solution.get('Hhd') - solution.get('Hhd_1'), 0)
        delta_H_b_val = round(solution.get('Hbd') - solution.get('Hbd_1'), 0)
        delta_H_val = round(solution.get('Hs') - solution.get('Hs_1'), 0)
        
        delta_M_h_val = round(solution.get('Md') - solution.get('Md_1'), 0)
        delta_M_b_val = round(solution.get('Ms') - solution.get('Ms_1'), 0)
        
        delta_Bh_val = round(solution.get('Bhd') - solution.get('Bhd_1'), 0)
        delta_Bb_val = round(solution.get('Bbd') - solution.get('Bbd_1'), 0)
        delta_Bcb_val = round(solution.get('Bcbd') - solution.get('Bcbd_1'), 0)
        delta_B_val = round(solution.get('Bs') - solution.get('Bs_1'), 0)
        
        delta_BL_val = round(solution.get('BLd') - solution.get('BLd_1'), 0)
        
        delta_Lh_val = round(solution.get('Lhd') - solution.get('Lhd_1'), 0)
        delta_Lf_val = round(solution.get('Lfd') - solution.get('Lfd_1'), 0)
        delta_L_val = round((solution.get('Lhs') - solution.get('Lhs_1')) + (solution.get('Lfs') - solution.get('Lfs_1')), 0)
        
        Pe_val = solution.get('Pe')
        delta_e_val = round(solution.get('Ekd') - solution.get('Ekd_1'), 0)
        delta_e_Pe_val = round(delta_e_val * Pe_val, 0)
        
        # Create calculation details for tooltips
        calculations = {
            "C": f"Consumption: {C_val:,.0f}",
            "G": f"Government spending: {G_val:,.0f}",
            "I": f"Investment: {I_val:,.0f}",
            "WB": f"Wage bill: {WB_val:,.0f}",
            "T": f"Taxes: {T_val:,.0f}",
            "r_Bhd": f"Interest on bills (households): r × Bhd = {r_val:.4f} × {Bhd_val:,.0f} = {r_Bhd_val:,.0f}",
            "r_Bbd": f"Interest on bills (banks): r × Bbd = {r_val:.4f} × {Bbd_val:,.0f} = {r_Bbd_val:,.0f}",
            "r_Bcbd": f"Interest on bills (central bank): r × Bcbd = {r_val:.4f} × {Bcbd_val:,.0f} = {r_Bcbd_val:,.0f}",
            "r_Bs": f"Interest on bills (government): r × Bs = {r_val:.4f} × {Bs_val:,.0f} = {r_Bs_val:,.0f}",
            "rm_Md": f"Interest on deposits: rm × Md = {rm_val:.4f} × {Md_val:,.0f} = {rm_Md_val:,.0f}",
            "rl_Lhd": f"Interest on loans (households): rl × Lhd = {rl_val:.4f} × {Lhd_val:,.0f} = {rl_Lhd_val:,.0f}",
            "rl_Lfd": f"Interest on loans (firms): rl × Lfd = {rl_val:.4f} × {Lfd_val:,.0f} = {rl_Lfd_val:,.0f}",
            "coupons": f"Bond coupon payments: coupon × BLd = {coupon_val:.4f} × {BL_val:,.0f} = {coupons_val:,.0f}",
            "Ff": f"Firms' profits distributed as dividends: {Ff_val:,.0f}",
            "Fb": f"Banks' profits distributed: {Fb_val:,.0f}",
            "Fcb": f"Central bank profits distributed to government: {Fcb_val:,.0f}",
            "delta_H_h": f"Change in cash (households): ΔHhd = {delta_H_h_val:,.0f}",
            "delta_H_b": f"Change in reserves (banks): ΔHbd = {delta_H_b_val:,.0f}",
            "delta_H": f"Change in high-powered money (central bank): ΔHs = {delta_H_val:,.0f}",
            "delta_M_h": f"Change in deposits (households): ΔMd = {delta_M_h_val:,.0f}",
            "delta_M_b": f"Change in deposit liabilities (banks): ΔMs = {delta_M_b_val:,.0f}",
            "delta_Bh": f"Change in bills (households): ΔBhd = {delta_Bh_val:,.0f}",
            "delta_Bb": f"Change in bills (banks): ΔBbd = {delta_Bb_val:,.0f}",
            "delta_Bcb": f"Change in bills (central bank): ΔBcbd = {delta_Bcb_val:,.0f}",
            "delta_B": f"Change in bill issuance (government): ΔBs = {delta_B_val:,.0f}",
            "delta_e_Pe": f"Change in equity value: ΔEkd × Pe = {delta_e_val:,.0f} × {Pe_val:,.0f} = {delta_e_Pe_val:,.0f}",
        }
        
        # Define tooltips for each cell
        tooltips = {
            # Current transactions
            (0, 0): "Current account transactions",
            (0, 1): "",
            (0, 2): "",
            (0, 3): "",
            (0, 4): "",
            (0, 5): "",
            (0, 6): "",
            
            # Consumption row
            (1, 0): "Consumption",
            (1, 1): f"Consumption expenditure by households (negative outflow): {calculations['C']}",
            (1, 2): f"Sales of consumption goods by firms (positive inflow): {calculations['C']}",
            (1, 3): "",
            (1, 4): "",
            (1, 5): "",
            (1, 6): "Sum of consumption flows (should be zero)",
            
            # Government spending row
            (2, 0): "Government expenditures",
            (2, 1): "",
            (2, 2): f"Sales of goods to government (positive inflow): {calculations['G']}",
            (2, 3): f"Government spending (negative outflow): {calculations['G']}",
            (2, 4): "",
            (2, 5): "",
            (2, 6): "Sum of government expenditure flows (should be zero)",
            
            # Investment row
            (3, 0): "Investment",
            (3, 1): "",
            (3, 2): f"Investment expenditure recorded as both outflow and inflow for firms: {calculations['I']}",
            (3, 3): "",
            (3, 4): "",
            (3, 5): "",
            (3, 6): "Sum of investment flows (should be zero)",
            
            # Wages row
            (4, 0): "Wages",
            (4, 1): f"Wage income for households (positive inflow): {calculations['WB']}",
            (4, 2): f"Wage payments by firms (negative outflow): {calculations['WB']}",
            (4, 3): "",
            (4, 4): "",
            (4, 5): "",
            (4, 6): "Sum of wage flows (should be zero)",
            
            # Inventories row
            (5, 0): "Inventories",
            (5, 1): "",
            (5, 2): f"Change in inventories for firms (could be positive or negative): {format_value(INV_val)}",
            (5, 3): "",
            (5, 4): "",
            (5, 5): "",
            (5, 6): f"Total change in inventories: {format_value(INV_val)}",
            
            # Taxes row
            (6, 0): "Taxes",
            (6, 1): f"Tax payments by households (negative outflow): {calculations['T']}",
            (6, 2): "",
            (6, 3): f"Tax receipts by government (positive inflow): {calculations['T']}",
            (6, 4): "",
            (6, 5): "",
            (6, 6): "Sum of tax flows (should be zero)",
            
            # Interest on bills row
            (7, 0): "Interest on bills",
            (7, 1): f"Interest received by households (positive inflow): {calculations['r_Bhd']}",
            (7, 2): "",
            (7, 3): f"Interest paid by government (negative outflow): {calculations['r_Bs']}",
            (7, 4): f"Interest received by central bank (positive inflow): {calculations['r_Bcbd']}",
            (7, 5): f"Interest received by banks (positive inflow): {calculations['r_Bbd']}",
            (7, 6): "Sum of interest on bills flows (should be zero)",
            
            # Interest on deposits row
            (8, 0): "Interest on deposits",
            (8, 1): f"Interest received by households (positive inflow): {calculations['rm_Md']}",
            (8, 2): "",
            (8, 3): "",
            (8, 4): "",
            (8, 5): f"Interest paid by banks (negative outflow): {calculations['rm_Md']}",
            (8, 6): "Sum of interest on deposits flows (should be zero)",
            
            # Interest on loans row
            (9, 0): "Interest on loans",
            (9, 1): f"Interest paid by households (negative outflow): {calculations['rl_Lhd']}",
            (9, 2): f"Interest paid by firms (negative outflow): {calculations['rl_Lfd']}",
            (9, 3): "",
            (9, 4): "",
            (9, 5): f"Interest received by banks (positive inflow): {calculations['rl_Lhd']} + {calculations['rl_Lfd']} = {format_value(rl_Lhd_val + rl_Lfd_val)}",
            (9, 6): "Sum of interest on loans flows (should be zero)",
            
            # Bond coupon row
            (10, 0): "Bond coupon payments",
            (10, 1): f"Coupon payments received by households (positive inflow): {calculations['coupons']}",
            (10, 2): "",
            (10, 3): f"Coupon payments paid by government (negative outflow): {calculations['coupons']}",
            (10, 4): "",
            (10, 5): "",
            (10, 6): "Sum of bond coupon payment flows (should be zero)",
            
            # Dividends row
            (11, 0): "Dividends",
            (11, 1): f"Dividends received by households (positive inflow): {calculations['Ff']} + {calculations['Fb']} = {format_value(Ff_val + Fb_val)}",
            (11, 2): f"Dividends paid by firms (negative outflow): {calculations['Ff']}",
            (11, 3): f"Dividends received by government (positive inflow): {calculations['Fcb']}",
            (11, 4): f"Dividends paid by central bank (negative outflow): {calculations['Fcb']}",
            (11, 5): f"Dividends paid by banks (negative outflow): {calculations['Fb']}",
            (11, 6): "Sum of dividend flows (should be zero)",
            
            # Current balance row
            (12, 0): "Current account balance",
            (12, 1): "Current balance for households (sum of all current transactions)",
            (12, 2): "Current balance for firms (sum of all current transactions)",
            (12, 3): "Current balance for government (sum of all current transactions)",
            (12, 4): "Current balance for central bank (sum of all current transactions)",
            (12, 5): "Current balance for banks (sum of all current transactions)",
            (12, 6): "Sum of all current balances (should equal change in inventories)",
            
            # Capital transactions header
            (13, 0): "Capital account transactions",
            (13, 1): "",
            (13, 2): "",
            (13, 3): "",
            (13, 4): "",
            (13, 5): "",
            (13, 6): "",
            
            # Cash row
            (14, 0): "ΔCash",
            (14, 1): f"Change in cash holdings by households (negative for increase): {calculations['delta_H_h']}",
            (14, 2): "",
            (14, 3): "",
            (14, 4): f"Change in cash issuance by central bank (positive for increase): {calculations['delta_H']}",
            (14, 5): f"Change in reserve holdings by banks (negative for increase): {calculations['delta_H_b']}",
            (14, 6): "Sum of cash/reserves changes (should be zero)",
            
            # Deposits row
            (15, 0): "ΔDeposits",
            (15, 1): f"Change in deposit holdings by households (negative for increase): {calculations['delta_M_h']}",
            (15, 2): "",
            (15, 3): "",
            (15, 4): "",
            (15, 5): f"Change in deposit liabilities by banks (positive for increase): {calculations['delta_M_b']}",
            (15, 6): "Sum of deposit changes (should be zero)",
            
            # Bills row
            (16, 0): "ΔBills",
            (16, 1): f"Change in bill holdings by households (negative for increase): {calculations['delta_Bh']}",
            (16, 2): "",
            (16, 3): f"Change in bill issuance by government (positive for increase): {calculations['delta_B']}",
            (16, 4): f"Change in bill holdings by central bank (negative for increase): {calculations['delta_Bcb']}",
            (16, 5): f"Change in bill holdings by banks (negative for increase): {calculations['delta_Bb']}",
            (16, 6): "Sum of bill changes (should be zero)",
            
            # Bonds row
            (17, 0): "ΔBonds",
            (17, 1): f"Change in bond holdings by households (negative for increase): {calculations['delta_BL']}",
            (17, 2): "",
            (17, 3): f"Change in bond issuance by government (positive for increase): {calculations['delta_BL']}",
            (17, 4): "",
            (17, 5): "",
            (17, 6): "Sum of bond changes (should be zero)",
            
            # Loans row
            (18, 0): "ΔLoans",
            (18, 1): f"Change in loans taken by households (positive for increase): {calculations['delta_Lh']}",
            (18, 2): f"Change in loans taken by firms (positive for increase): {calculations['delta_Lf']}",
            (18, 3): "",
            (18, 4): "",
            (18, 5): f"Change in loans issued by banks (negative for increase): {calculations['delta_L']}",
            (18, 6): "Sum of loan changes (should be zero)",
            
            # Equities row
            (19, 0): "ΔEquities",
            (19, 1): f"Change in equity holdings by households (negative for increase): {calculations['delta_e_Pe']}",
            (19, 2): f"Change in equity issuance by firms (positive for increase): {calculations['delta_e_Pe']}",
            (19, 3): "",
            (19, 4): "",
            (19, 5): "",
            (19, 6): "Sum of equity changes (should be zero)",
            
            # Capital balance row
            (20, 0): "Capital account balance",
            (20, 1): "Capital balance for households (sum of all capital transactions)",
            (20, 2): "Capital balance for firms (sum of all capital transactions)",
            (20, 3): "Capital balance for government (sum of all capital transactions)",
            (20, 4): "Capital balance for central bank (sum of all capital transactions)",
            (20, 5): "Capital balance for banks (sum of all capital transactions)",
            (20, 6): "Sum of all capital balances (should equal zero)",
            
            # Total sum row
            (21, 0): "Current + Capital balance",
            (21, 1): "Total balance for households (should be zero)",
            (21, 2): "Total balance for firms (should be zero)",
            (21, 3): "Total balance for government (should be zero)",
            (21, 4): "Total balance for central bank (should be zero)",
            (21, 5): "Total balance for banks (should be zero)",
            (21, 6): "Sum of all balances (should equal change in inventories)",
        }
        
        # Calculate current account balances
        h_current = -C_val + WB_val - T_val + r_Bhd_val + rm_Md_val - rl_Lhd_val + coupons_val + Ff_val + Fb_val
        f_current = C_val + G_val - WB_val + INV_val - rl_Lfd_val - Ff_val
        g_current = -G_val + T_val - r_Bs_val - coupons_val + Fcb_val
        cb_current = r_Bcbd_val - Fcb_val
        b_current = r_Bbd_val - rm_Md_val + rl_Lhd_val + rl_Lfd_val - Fb_val
        
        # Calculate capital account balances (excluding current balances)
        h_capital = delta_H_h_val + delta_M_h_val + delta_Bh_val + delta_BL_val - delta_Lh_val + delta_e_Pe_val
        f_capital = -delta_Lf_val - delta_e_Pe_val
        g_capital = delta_B_val + delta_BL_val
        cb_capital = -delta_H_val + delta_Bcb_val
        b_capital = delta_H_b_val - delta_M_b_val + delta_Bb_val + delta_L_val
        
        # Format data for display
        data = [
            ["1. Current", "", "", "", "", "", ""],
            ["Consumption", format_value(-C_val), format_value(C_val), "", "", "", "0"],
            ["Government expenditures", "", format_value(G_val), format_value(-G_val), "", "", "0"],
            ["Investment", "", format_value(I_val) + " / " + format_value(-I_val), "", "", "", "0"],
            ["Wages", format_value(WB_val), format_value(-WB_val), "", "", "", "0"],
            ["Change in inventories", "", format_value(INV_val), "", "", "", format_value(INV_val)],
            ["Taxes", format_value(-T_val), "", format_value(T_val), "", "", "0"],
            ["Interest on bills", format_value(r_Bhd_val), "", format_value(-r_Bs_val), format_value(r_Bcbd_val), format_value(r_Bbd_val), "0"],
            ["Interest on deposits", format_value(rm_Md_val), "", "", "", format_value(-rm_Md_val), "0"],
            ["Interest on loans", format_value(-rl_Lhd_val), format_value(-rl_Lfd_val), "", "", format_value(rl_Lhd_val + rl_Lfd_val), "0"],
            ["Bond coupon payments", format_value(coupons_val), "", format_value(-coupons_val), "", "", "0"],
            ["Dividends", format_value(Ff_val + Fb_val), format_value(-Ff_val), format_value(Fcb_val), format_value(-Fcb_val), format_value(-Fb_val), "0"],
            ["Current balance", format_value(h_current), format_value(f_current), format_value(g_current), format_value(cb_current), format_value(b_current), format_value(INV_val)],
            ["2. Capital", "", "", "", "", "", ""],
            ["ΔCash", format_value(-delta_H_h_val), "", "", format_value(delta_H_val), format_value(-delta_H_b_val), "0"],
            ["ΔDeposits", format_value(-delta_M_h_val), "", "", "", format_value(delta_M_b_val), "0"],
            ["ΔBills", format_value(-delta_Bh_val), "", format_value(delta_B_val), format_value(-delta_Bcb_val), format_value(-delta_Bb_val), "0"],
            ["ΔBonds", format_value(-delta_BL_val), "", format_value(delta_BL_val), "", "", "0"],
            ["ΔLoans", format_value(delta_Lh_val), format_value(delta_Lf_val), "", "", format_value(-delta_L_val), "0"],
            ["ΔEquities", format_value(-delta_e_Pe_val), format_value(delta_e_Pe_val), "", "", "", "0"],
            ["Capital balance", format_value(-h_capital), format_value(-f_capital), format_value(-g_capital), format_value(-cb_capital), format_value(-b_capital), "0"],
            ["Σ", "0", "0", "0", "0", "0", format_value(INV_val)]
        ]
        
        # Column headers
        headers = ["", "Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]
        
        # Convert data to format needed for Plotly
        cell_values = [[] for _ in range(len(headers))]
        for i in range(len(data)):
            for j in range(len(headers)):
                cell_values[j].append(data[i][j])
        
        # Create hover text matrix with tooltips
        hover_text = []
        for i in range(len(data)):
            row_hover = []
            for j in range(len(headers)):
                tooltip = tooltips.get((i, j), "")
                if tooltip:
                    row_hover.append(tooltip)
                else:
                    row_hover.append("")
            hover_text.append(row_hover)
        
        # Create cell colors
        cell_colors = []
        for i in range(len(data)):
            row_colors = []
            for j in range(len(headers)):
                val = data[i][j]
                # Section headers
                if i == 0 or i == 13:
                    row_colors.append('#2C3E50')  # Dark blue for headers
                # Special handling for investment cell which has two values
                elif i == 3 and j == 2:
                    row_colors.append('#8FD14F')  # Green for the investment cell
                elif isinstance(val, str):
                    if val.startswith('+'):
                        row_colors.append('#8FD14F')  # Darker green
                    elif val.startswith('-'):
                        row_colors.append('#FF9999')  # Darker red
                    else:
                        row_colors.append('#1E1E1E')  # Dark background
                else:
                    row_colors.append('#1E1E1E')  # Dark background
            cell_colors.append(row_colors)
        
        # Create Plotly table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                fill_color='#0E1117',
                align='center',
                font=dict(color='white', size=14)
            ),
            cells=dict(
                values=cell_values,
                fill_color=[cell_colors[i] for i in range(len(cell_colors))],
                align='right',
                font=dict(color='white', size=12),
                height=30,
                text=hover_text
            ))
        ])
        
        # Update layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=720,  # Taller for this larger matrix
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117'
        )
        
        # Display the table
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No model data available. Run a simulation to view the transaction flow matrix.")

# Display matrix tabs content even if simulation hasn't run
with tab4:
    display_balance_sheet_matrix()
    
with tab5:
    display_revaluation_matrix()
    
with tab6:
    display_transaction_flow_matrix() 