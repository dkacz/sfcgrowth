"""
Event definitions for the SFC Economic Strategy Game.
"""

# Structure: { 'Event Name': {'type': 'External'/'Domestic'/'Labor'/'Political'/'Natural', 'param': 'param_name', 'effect': value_change, 'desc': 'Description', 'indirect_effects': 'Commentary', 'probability': float (0-1)} }
# 'trigger_condition' (optional) could be added later for state-dependent triggers.

ECONOMIC_EVENTS = {
    # External Shocks
    "Global Recession": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": -0.025,
        "desc": "A significant slowdown in the global economy negatively impacts domestic confidence. Businesses may postpone investment projects, and households could reduce spending due to increased uncertainty.",
        "indirect_effects": "Reduced confidence typically dampens investment (INV) and consumption (CONS).",
        "probability": 0.15
    },
    "Global Boom": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": 0.025,
        "desc": "A strong upswing in the global economy boosts domestic confidence. Businesses may increase investment, and households could raise spending due to improved outlooks.",
        "indirect_effects": "Improved confidence typically boosts investment (INV) and consumption (CONS).",
        "probability": 0.15
    },
    "Trade Dispute": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": -0.025,
        "desc": "Rising international trade tensions create uncertainty and disrupt trade flows. This can negatively impact business confidence, potentially leading to lower investment.",
        "indirect_effects": "Increased uncertainty often leads to reduced investment (INV).",
        "probability": 0.10
    },
    # Domestic Economic Events
    "Banking Sector Stress": {
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": 0.015, # Temporary, Floor 0
        "desc": "Growing stress within the banking system leads to an increase in bad loans. This can tighten credit conditions, potentially raising borrowing costs and reducing credit availability.",
        "indirect_effects": "Higher NPLs can increase bank risk aversion, potentially raising loan rates (Rl) and impacting the Capital Adequacy Ratio (CAR).",
        "probability": 0.10
        ,"duration": 1 # Effect lasts 1 turn
    },
     "Banking Sector Calm": {
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": -0.015, # Temporary, Floor 0
        "desc": "Conditions in the banking sector improve, leading to a decrease in bad loans. This can ease credit conditions, potentially lowering borrowing costs and increasing credit availability.",
        "indirect_effects": "Lower NPLs can decrease bank risk aversion, potentially lowering loan rates (Rl) and improving the Capital Adequacy Ratio (CAR).",
        "probability": 0.10
        ,"duration": 1 # Effect lasts 1 turn
    },
    "Financial Market Stress": {
        "type": "Domestic",
        "param": "ADDbl", # Spread between long/short rates
        "effect": 0.010,
        "desc": "Heightened volatility and risk aversion in financial markets cause investors to demand higher premiums for holding long-term assets relative to short-term ones. This can increase long-term borrowing costs, potentially dampening investment.",
        "indirect_effects": "A wider yield spread (higher ADDbl) increases long-term borrowing costs, which can reduce investment (INV).",
        "probability": 0.15
    },
    "Financial Market Rally": {
        "type": "Domestic",
        "param": "ADDbl", # Spread between long/short rates
        "effect": -0.010,
        "desc": "Reduced volatility and increased risk appetite in financial markets cause the gap between long-term and short-term asset yields to narrow. This can lower long-term borrowing costs, potentially stimulating investment.",
        "indirect_effects": "A narrower yield spread (lower ADDbl) reduces long-term borrowing costs, which can encourage investment (INV).",
        "probability": 0.15
    },
    # Labor Market Events
    "Productivity Boom": {
        "type": "Labor",
        "param": "GRpr",
        "effect": 0.005,
        "desc": "An unexpected surge in labor productivity means workers are producing more output per hour. This can lead to higher potential economic output and may influence wages and inflation.",
        "indirect_effects": "Higher productivity growth (GRpr) can lead to higher real wages (W/P), potentially lower inflation (PI), and higher potential output (Yk).",
        "probability": 0.10
    },
    "Productivity Bust": {
        "type": "Labor",
        "param": "GRpr",
        "effect": -0.005,
        "desc": "An unexpected decline in labor productivity means workers are producing less output per hour. This can lower potential economic output and may influence wages and inflation.",
        "indirect_effects": "Lower productivity growth (GRpr) can suppress real wages (W/P), potentially increase inflation (PI), and lower potential output (Yk).",
        "probability": 0.10
    },
    # Political/Social Events
    "Infrastructure Investment Boom": {
        "type": "Political",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": 0.015, # Temporary
        "desc": "The government initiates large-scale public infrastructure projects. This directly boosts investment and increases the economy's capital stock, potentially raising long-term potential output.",
        "indirect_effects": "Higher exogenous capital growth (gamma0) directly boosts the capital stock (K) and investment (INV), increasing potential output (Yk).",
        "probability": 0.05
        ,"duration": 1 # Effect lasts 1 turn
    },
    # Natural Events
    "Natural Disaster": {
        "type": "Natural",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": -0.015, # Temporary
        "desc": "A significant natural disaster damages infrastructure and disrupts economic activity. This reduces the economy's capital stock and can negatively impact investment and potential output in the short term.",
        "indirect_effects": "Lower exogenous capital growth (gamma0) directly reduces the capital stock (K) and investment (INV), decreasing potential output (Yk).",
        "probability": 0.05
       ,"duration": 1 # Effect lasts 1 turn
    },
    "Energy Crisis": {
        "type": "Natural", # Or Geopolitical
        "param": "RA", # Affects expectations (proxy for cost shock impact)
        "effect": -0.025,
        "desc": "A sudden, sharp increase in energy prices raises costs for businesses and households. This can fuel inflation and negatively impact confidence, potentially leading to lower investment and consumption.",
        "indirect_effects": "Higher costs and lower confidence (via RA) can increase inflation (PI) while reducing investment (INV) and consumption (CONS).",
        "probability": 0.10
    },
    "Credit Boom": {
        "type": "Domestic",
        "param": "eta0", # Exogenous loan ratio component
        "effect": 0.025,
        "desc": "An environment of easy credit and strong household borrowing appetite leads to a rapid expansion of household debt. This can fuel consumption in the short term but increases vulnerability to future shocks.",
        "indirect_effects": "A higher propensity to borrow (eta0) increases household loans (Lhs) and consumption (CONS), but also raises the debt burden ratio (BUR).",
        "probability": 0.10
    },
    "Credit Crunch": {
        "type": "Domestic",
        "param": "eta0", # Exogenous loan ratio component
        "effect": -0.025,
        "desc": "Banks tighten lending standards and households become more reluctant to borrow. This restricts the flow of credit, likely leading to lower household spending and an increased debt burden relative to income.",
        "indirect_effects": "A lower propensity to borrow (eta0) decreases household loans (Lhs) and consumption (CONS), potentially lowering the debt burden ratio (BUR) over time.",
        "probability": 0.10
    },
    # New Inflation Events based on Simulation Results
    "Worker Militancy Surge": {
        "type": "Labor",
        "param": "omega1", # Parameter influencing target real wage sensitivity to productivity
        "effect": 0.000, # Positive shock increases wage pressure (adjust magnitude as needed)
        "desc": "Increased union activity and worker bargaining power lead to wages becoming more sensitive to productivity gains, potentially pushing inflation higher.",
        "indirect_effects": "Higher omega1 increases target real wage (omegat), potentially leading to higher nominal wages (W) and inflation (PI).",
        "probability": 0.08
    },
    "Consumer Confidence Boom": {
        "type": "Domestic",
        "param": "alpha1", # Propensity to consume out of income
        "effect": 0.010, # Positive shock increases consumption propensity (adjust magnitude)
        "desc": "A wave of optimism sweeps through households, leading to a higher propensity to spend out of current income.",
        "indirect_effects": "Higher alpha1 directly boosts consumption (Ck), increasing aggregate demand (Sk) and potentially leading to demand-pull inflation (PI).",
        "probability": 0.10
        # Consider making temporary? "duration": 1
    },
}

# Character-Specific Events
CHARACTER_EVENTS = {
    "Consumer Confidence Craze": {
        "character": "Demand Side Devotee",
        "desc": "Your latest speech was SO inspiring, people are spending like there's no tomorrow (especially on imports)!",
        "param": "alpha1",
        "effect": 0.025,
        "duration": 1,
        "probability": 0.1,
        "type": "Character",
        "indirect_effects": "Increased consumption propensity might boost GDP but worsen trade balance."
    },
    "Surplus Surprise": {
        "character": "Austerity Apostle",
        "desc": "You cut so much, the government accidentally ran a surplus! Markets are... confused, and autonomous investment sentiment dips.",
        "param": "gamma0",
        "effect": -0.01,
        "duration": 2,
        "probability": 0.1,
        "type": "Character",
        "indirect_effects": "Reduced investment could hinder long-term growth despite the surplus."
    },
    "Inflationary Epiphany": {
        "character": "Money Monk",
        "desc": "Meditating on price stability, you briefly misjudged how strongly inflation expectations influence wages.",
        "param": "omega1",
        "effect": 0.025,
        "duration": 1,
        "probability": 0.1,
        "type": "Character",
        "indirect_effects": "Higher wage sensitivity to inflation expectations could make inflation stickier."
    },
    "Productivity Puzzle": {
        "character": "Class Conscious Crusader",
        "desc": "Empowered workers rearranged the factory floor for 'better vibes'. Output temporarily dipped while they figured out the new layout.",
        "param": "eta0",
        "effect": -0.01,
        "duration": 1,
        "probability": 0.1,
        "type": "Character",
        "indirect_effects": "Short-term productivity dip might be offset by long-term morale boost (or not)."
    }
}
