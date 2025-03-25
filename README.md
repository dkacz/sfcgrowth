# Growth Model Explorer

This Streamlit application allows you to experiment with exogenous variables in a monetary growth model and compare the effects against a baseline scenario.

## Features

- Interactive parameter adjustment for key exogenous variables
- Visual comparison between baseline and modified scenarios
- Multiple visualization tabs showing different economic indicators
- Data tables with downloadable CSV exports

## Installation

1. Make sure you have Python 3.8+ installed on your system
2. Clone this repository or download the files
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the App

To run the app, execute:

```bash
streamlit run growth_model_streamlit.py
```

This will start the Streamlit server and open the app in your default web browser.

## How to Use

1. The sidebar contains expandable sections for different categories of exogenous variables
2. Adjust the sliders to modify parameter values
3. Set simulation settings (periods, warmup)
4. Click "Run Simulation" to execute the model with your parameters
5. View the results in the different tabs:
   - **Main Variables**: Key economic indicators like output, consumption, and inflation
   - **Advanced Charts**: Financial indicators including interest rates and debt metrics
   - **Data Table**: Tabular data that can be downloaded as CSV

## Understanding the Model

The growth model is a Stock-Flow Consistent (SFC) model that represents a modern monetary economy with:

- Firms that make production and pricing decisions
- Households that consume, save, and make portfolio decisions
- A government sector with fiscal policy
- A banking sector that sets interest rates and manages loans
- A central bank that sets the policy rate

The parameters you can adjust are exogenous variables that drive the model's behavior.

## Examples of Experiments

Here are some interesting experiments you can try:

1. **Interest Rate Shock**: Increase `Rbbar` to simulate a monetary policy tightening
2. **Fiscal Stimulus**: Increase `GRg` to simulate higher government spending
3. **Tax Cut**: Decrease `theta` to simulate a tax cut
4. **Credit Crisis**: Increase `NPLk` to simulate a rise in non-performing loans
5. **Wage Pressure**: Adjust `omega0` to simulate changes in wage demands

For each experiment, observe how the variables respond over time and compare to the baseline scenario. 