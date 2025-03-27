"""
Card definitions for the SFC Economic Strategy Game.
"""

# Structure: { 'Card Name': {'type': 'Monetary'/'Fiscal', 'param': 'param_name', 'effect': value_change, 'desc': 'Description'} }
# Note: 'effect' is the direct change applied (e.g., +0.005 for +0.5%). Needs careful implementation.

POLICY_CARDS = {
    # Monetary Policy
    "Interest Rate Hike": {
        "type": "Monetary",
        "param": "Rbbar",
        "effect": 0.005, # +0.5%
        "desc": "Increase the central bank policy rate. Secondary: Higher lending rates, reduced investment."
    },
    "Interest Rate Cut": { # Added counterpart for balance
        "type": "Monetary",
        "param": "Rbbar",
        "effect": -0.005, # -0.5%
        "desc": "Decrease the central bank policy rate. Secondary: Lower lending rates, potential for increased investment."
    },
    "Forward Guidance (Expansionary)": {
        "type": "Monetary",
        "param": "RA", # Affects expectations
        "effect": 0.002, # +0.2% (proxy effect on expectations)
        "desc": "Signal lower future rates. Secondary: Affects expected sales and investment positively."
    },
     "Forward Guidance (Contractionary)": {
        "type": "Monetary",
        "param": "RA", # Affects expectations
        "effect": -0.002, # -0.2% (proxy effect on expectations)
        "desc": "Signal higher future rates. Secondary: Affects expected sales and investment negatively."
    },
    "Quantitative Easing": {
        "type": "Monetary",
        "param": "ADDbl", # Spread between long/short rates
        "effect": -0.003, # -0.3% spread reduction
        "desc": "Central bank buys assets. Secondary: Lower long-term rates, higher asset prices."
    },
    "Quantitative Tightening": { # Added counterpart
        "type": "Monetary",
        "param": "ADDbl", # Spread between long/short rates
        "effect": 0.003, # +0.3% spread increase
        "desc": "Central bank sells assets/lets them mature. Secondary: Higher long-term rates, lower asset prices."
    },
    "Lower Reserve Requirements": {
        "type": "Monetary",
        "param": "ro",
        "effect": -0.02, # -2% points
        "desc": "Decrease bank reserve requirements. Secondary: Increases bank lending capacity."
    },
    "Raise Reserve Requirements": {
        "type": "Monetary",
        "param": "ro",
        "effect": 0.02, # +2% points
        "desc": "Increase bank reserve requirements. Secondary: Reduces bank lending capacity."
    },
    "Ease Bank Capital Requirements": {
        "type": "Monetary",
        "param": "NCAR", # Normal Capital Adequacy Ratio
        "effect": -0.02, # -2% points
        "desc": "Lower the required capital banks must hold. Secondary: Affects bank lending and risk-taking (potentially increases)."
    },
    "Tighten Bank Capital Requirements": {
        "type": "Monetary",
        "param": "NCAR", # Normal Capital Adequacy Ratio
        "effect": 0.02, # +2% points
        "desc": "Raise the required capital banks must hold. Secondary: Affects bank lending and risk-taking (potentially decreases)."
    },
    # Note: Bank Liquidity Ratio Targets (bot/top) affect Rm adjustment speed (xim1/xim2), not a direct param change in the same way.
    # This requires modifying the Rm equation logic or adjusting xim1/xim2, which is more complex. Deferring for now.

    # Fiscal Policy
    "Increase Government Spending": {
        "type": "Fiscal",
        "param": "GRg", # Growth rate of real gov spending
        "effect": 0.005, # +0.5% growth rate
        "desc": "Boost government expenditure growth. Secondary: Affects aggregate demand and employment."
    },
    "Decrease Government Spending": {
        "type": "Fiscal",
        "param": "GRg", # Growth rate of real gov spending
        "effect": -0.005, # -0.5% growth rate
        "desc": "Reduce government expenditure growth. Secondary: Affects aggregate demand and employment."
    },
    "Cut Income Tax Rate": {
        "type": "Fiscal",
        "param": "theta",
        "effect": -0.02, # -2% points
        "desc": "Lower the income tax rate. Secondary: Affects disposable income and consumption."
    },
    "Raise Income Tax Rate": {
        "type": "Fiscal",
        "param": "theta",
        "effect": 0.02, # +2% points
        "desc": "Increase the income tax rate. Secondary: Affects disposable income and consumption."
    },
    "Boost Productivity Growth": { # Renamed from card doc for clarity
        "type": "Fiscal", # Often result of fiscal policy (R&D, education)
        "param": "GRpr", # Growth rate of productivity
        "effect": 0.003, # +0.3% growth rate
        "desc": "Implement policies to enhance productivity growth. Secondary: Affects labor productivity and wages."
    },
     "Productivity Slowdown Policy": { # Added counterpart
        "type": "Fiscal", # Can be policy induced (bad regulation etc)
        "param": "GRpr", # Growth rate of productivity
        "effect": -0.003, # -0.3% growth rate
        "desc": "Policies hindering productivity growth take effect. Secondary: Affects labor productivity and wages."
    },
}