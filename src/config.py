# src/config.py
"""Configuration constants and mappings for the SFC Game."""

# --- Constants ---
INITIAL_HAND_SIZE = 5
CARDS_TO_DRAW_PER_YEAR = 4 # Draw 4 cards per year as requested
MAX_CARDS_PLAYED_PER_YEAR = 2 # Max policies player can confirm

MAX_CARDS_PER_ROW = 4 # For card display layout
ICON_DIR = "assets/icons" # Define icon directory
SPARKLINE_YEARS = 10 # Number of years for sparkline history
GAME_END_YEAR = 10 # Define the final year

# --- Icon Mapping ---
# Maps internal keys/types to filenames in ICON_DIR
ICON_FILENAME_MAP = {
    # Card Types
    "monetary": "monetary_icon.png",
    "fiscal": "fiscal_icon.png",
    # Dashboard Metrics (using keys from history/solution dicts)
    "Yk": "factory.png",
    "PI": "inflation_icon.png",
    "ER": "people.png", # Note: We calculate unemployment from ER
    "GRk": "buildingouparrow.png",
    "Rb": "percentagescroll.png",
    "Rl": "percentagescroll.png", # Reusing bill rate icon for loan rate
    "Rm": "pig.png",
    "Q": "tobins_q_icon.png",
    "BUR": "bendingman.png",
    "CAR": "plusshield.png",
    "PSBR": "dollardownarrow.png",
    "GD_GDP": "fiscal_icon.png" # Reusing fiscal icon for Gov Debt/GDP ratio
}

# --- Variable Descriptions (Keep for potential future use) ---
VARIABLE_DESCRIPTIONS = {
    "Yk": "Real Gross Domestic Product: Total value of goods and services produced, adjusted for inflation.",
    "PI": "Inflation Rate: Percentage increase in the general price level.",
    "Unemployment": "Unemployment Rate: Percentage of the labor force that is jobless and looking for work.",
    "GRk": "Capital Growth Rate: Percentage change in the stock of physical capital.",
    "Rb": "Bill Rate: Interest rate on short-term government debt (Treasury Bills).",
    "Rl": "Loan Rate: Interest rate charged by banks on loans to firms and households.",
    "Rm": "Deposit Rate: Interest rate paid by banks on deposits.",
    "Q": "Tobin's Q: Ratio of the market value of firms' capital to its replacement cost.",
    "K": "Capital Stock: The total value of physical capital (machinery, buildings, etc.) used in production.",
    "INV": "Investment: Spending by firms on new capital goods.",
    "CONS": "Consumption: Spending by households on goods and services.",
    "BUR": "Debt Burden Ratio: Ratio of household debt service payments to disposable income.",
    "W": "Wage Rate: The nominal wage paid to labor.",
    "CAR": "Capital Adequacy Ratio: Ratio of a bank's capital to its risk-weighted assets.",
    "Lhs": "Loans to Households: Outstanding loan balances held by the household sector.",
    "PSBR": "Public Sector Borrowing Requirement: The government's budget deficit.",
    "GD_GDP": "Government Debt to GDP Ratio: Ratio of total government debt to nominal GDP.",
    "GovBalance_GDP": "Government Balance as % of GDP: Surplus (+) or Deficit (-)."
}

# Helper dict for parameter descriptions (extracted from chapter_11_model_growth.py)
PARAM_DESCRIPTIONS = {
    'Rbbar': 'Interest rate on bills, set exogenously',
    'RA': 'Random shock to expectations on real sales',
    'ADDbl': 'Spread between long-term interest rate and rate on bills',
    'ro': 'Reserve requirement parameter',
    'NCAR': 'Normal capital adequacy ratio of banks',
    'GRg': 'Growth rate of real government expenditures',
    'theta': 'Income tax rate',
    'GRpr': 'Growth rate of productivity',
    'NPLk': 'Proportion of Non-Performing loans',
    'etan': 'Speed of adjustment of actual employment to desired employment',
    'alpha1': 'Propensity to consume out of income',
    'gamma0': 'Exogenous growth in the real stock of capital',
    'Rln': 'Normal interest rate on loans',
    'eta0': 'Ratio of new loans to personal income - exogenous component',
    'delta': 'Rate of depreciation of fixed capital',
    'beta': 'Parameter in expectation formations on real sales',
    'omega3': 'Speed of adjustment of wages to target value',
    'omega0': 'Constant term in wage Phillips curve',
    'omega1': 'Coefficient on expected inflation in wage Phillips curve',
    'omega2': 'Coefficient on unemployment gap in wage Phillips curve',
    'alpha2': 'Propensity to consume out of wealth',
    'bot': 'Bottom value for bank net liquidity ratio',
    # Add others if needed by cards/events
    'eps': 'Sensitivity of exchange rate expectations to deviations',
    'gammar': 'Sensitivity of investment (capital growth) to the real interest rate',

    'deltarep': 'Change in Political Reputation',
}