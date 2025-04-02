"""
Card definitions for the SFC Economic Strategy Game.
"""

# Structure: { 'Card Name': {'type': 'Monetary'/'Fiscal', 'param': 'param_name', 'effect': value_change, 'desc': 'Description'} }
# Note: 'effect' is the direct change applied (e.g., +0.005 for +0.5%). Needs careful implementation.

POLICY_CARDS = {
    # Monetary Policy
    "Interest Rate Hike": {
        "type": "Monetary",
        "stance": "contractionary",
        "param": "Rbbar",
        "effect": 0.015, # Boosted from 0.010
        "desc": "The central bank raises its target bill rate (Rbbar) to combat inflation or cool an overheating economy. Expect higher borrowing costs (Rl) and reduced investment (Ik)."
    },
    "Interest Rate Cut": { # Added counterpart for balance
        "type": "Monetary",
        "param": "Rbbar",
        "stance": "expansionary",
        "effect": -0.015, # Boosted from -0.010
        "desc": "The central bank lowers its target bill rate (Rbbar) to stimulate growth or fight deflation. Expect lower borrowing costs (Rl) and potentially increased investment (Ik)."
    },
    "Quantitative Easing": {
        "type": "Monetary",
        "param": "ADDbl", # Spread between long/short rates
        "stance": "expansionary",
        "effect": -0.01, # Boosted from -0.005, rounded
        "desc": "The central bank injects liquidity by purchasing long-term bonds, aiming to reduce the yield spread (ADDbl) and lower long-term borrowing costs, potentially boosting asset prices (Pe)."
    },
    "Quantitative Tightening": { # Added counterpart
        "type": "Monetary",
        "param": "ADDbl", # Spread between long/short rates
        "stance": "contractionary",
        "effect": 0.01, # Boosted from 0.005, rounded
        "desc": "The central bank withdraws liquidity by selling assets or letting them mature, widening the yield spread (ADDbl). Aims to increase long-term borrowing costs and moderate asset prices (Pe)."
    },
    # Note: Bank Liquidity Ratio Targets (bot/top) affect Rm adjustment speed (xim1/xim2), not a direct param change in the same way.
    # This requires modifying the Rm equation logic or adjusting xim1/xim2, which is more complex. Deferring for now.

    # Fiscal Policy
    "Increase Government Spending": {
        "type": "Fiscal",
        "stance": "expansionary",
        "param": "GRg", # Growth rate of real gov spending
        "effect": 0.015, # Boosted from 0.010
        "desc": "Boost the growth rate of real government spending (GRg). This fiscal stimulus directly increases aggregate demand (Yk) and tends to raise employment (N)."
    },
    "Decrease Government Spending": {
        "type": "Fiscal",
        "param": "GRg", # Growth rate of real gov spending
        "stance": "contractionary",
        "effect": -0.015, # Boosted from -0.010
        "desc": "Reduce the growth rate of real government spending (GRg). This fiscal consolidation directly dampens aggregate demand (Yk) and tends to lower employment (N)."
    },
    "Cut Income Tax Rate": {
        "type": "Fiscal",
        "param": "theta",
        "stance": "expansionary",
        "effect": -0.02, # Boosted from -0.0125, rounded
        "desc": "Implement a broad cut in the average income tax rate (theta). This increases household disposable income (YDr) and typically stimulates consumption (Ck)."
    },
    "Raise Income Tax Rate": {
        "type": "Fiscal",
        "param": "theta",
        "stance": "contractionary",
        "effect": 0.02, # Boosted from 0.0125, rounded
        "desc": "Implement a broad increase in the average income tax rate (theta). This reduces household disposable income (YDr) and typically dampens consumption (Ck)."
    },
    "Make Tax System More Progressive": { # Renamed, uses alpha1 as proxy
        "type": "Fiscal",
        "param": "alpha1", # Propensity to consume
        "stance": "expansionary",
        "effect": 0.025, # Boosted from 0.015, rounded
        "desc": "Restructure the tax system to increase the burden on higher incomes relative to lower incomes. This tends to increase the overall propensity to consume (alpha1), boosting aggregate demand."
    },
    "Make Tax System Less Progressive": { # Renamed, uses alpha1 as proxy
        "type": "Fiscal",
        "param": "alpha1", # Propensity to consume
        "stance": "contractionary",
        "effect": -0.025, # Boosted from -0.015, rounded
        "desc": "Restructure the tax system to decrease the burden on higher incomes relative to lower incomes. This tends to decrease the overall propensity to consume (alpha1), dampening aggregate demand."
    },
}