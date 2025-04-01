"""
Event definitions for the SFC Economic Strategy Game.
"""

# Structure: { 'Event Name': {'type': 'External'/'Domestic'/'Labor'/'Political'/'Natural', 'param': 'param_name', 'effect': value_change, 'desc': 'Description', 'trigger_condition': function/lambda (optional)} }
# 'trigger_condition' would take the model state and return True if the event should be considered.

ECONOMIC_EVENTS = {
    # External Shocks
    "Global Recession": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": -0.050, # Reverted: Halved from -0.10
        "desc": "A significant slowdown in the global economy negatively impacts domestic confidence. Businesses may postpone investment projects, and households could reduce spending due to increased uncertainty."
,
        "affected_vars": ["INV", "CONS"] # Via expectations
        # Potential Trigger: Low global growth indicator (if added) or random chance
    },
    "Global Boom": { # Added counterpart
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": 0.050, # Reverted: Halved from 0.10
        "desc": "A strong upswing in the global economy boosts domestic confidence. Businesses may increase investment, and households could raise spending due to improved outlooks."
,
        "affected_vars": ["INV", "CONS"] # Via expectations
        # Potential Trigger: High global growth indicator (if added) or random chance
    },
    "Trade Dispute": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": -0.050, # Reverted: Halved from -0.10
        "desc": "Rising international trade tensions create uncertainty and disrupt trade flows. This can negatively impact business confidence, potentially leading to lower investment."
,
        "affected_vars": ["INV"] # Via expectations, exports implicit
        # Potential Trigger: Random chance, specific policy card plays
    },
    # Domestic Economic Events
    "Banking Sector Stress": { # Renamed from Crisis for variable impact
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": 0.025, # Reverted: Halved from 0.050 (Temporary, Floor 0)
        "desc": "Growing stress within the banking system leads to an increase in bad loans. This can tighten credit conditions, potentially raising borrowing costs and reducing credit availability."
,
        "affected_vars": ["Rl", "CAR"] # Non-performing loans affect bank health and lending
        # Potential Trigger: High BUR, low CAR, low growth
        # NOTE: Implement as temporary (1 turn) and ensure NPLk >= 0
    },
     "Banking Sector Calm": { # Added counterpart
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": -0.025, # Reverted: Halved from -0.050 (Temporary, Floor 0)
        "desc": "Conditions in the banking sector improve, leading to a decrease in bad loans. This can ease credit conditions, potentially lowering borrowing costs and increasing credit availability."
,
        "affected_vars": ["Rl", "CAR"] # Non-performing loans affect bank health and lending
        # Potential Trigger: Low BUR, high CAR, high growth
        # NOTE: Implement as temporary (1 turn) and ensure NPLk >= 0
    },
    "Financial Market Stress": { # New event using ADDbl
        "type": "Domestic",
        "param": "ADDbl", # Spread between long/short rates
        "effect": 0.015, # Reverted: Halved from 0.030
        "desc": "Heightened volatility and risk aversion in financial markets cause investors to demand higher premiums for holding long-term assets relative to short-term ones. This can increase long-term borrowing costs, potentially dampening investment."
,
        "affected_vars": ["INV"] # Spread affects long-term rates impacting investment
        # Potential Trigger: Low Q, high BUR, external shocks
    },
    "Financial Market Rally": { # New event using ADDbl
        "type": "Domestic",
        "param": "ADDbl", # Spread between long/short rates
        "effect": -0.015, # Reverted: Halved from -0.030
        "desc": "Reduced volatility and increased risk appetite in financial markets cause the gap between long-term and short-term asset yields to narrow. This can lower long-term borrowing costs, potentially stimulating investment."
,
        "affected_vars": ["INV"] # Spread affects long-term rates impacting investment
        # Potential Trigger: High Q, low BUR, positive external shocks
    },
    # Labor Market Events
    "Productivity Boom": { # Renamed from Shock
        "type": "Labor",
        "param": "GRpr",
        "effect": 0.005, # Reverted: Halved from 0.0105
        "desc": "An unexpected surge in labor productivity means workers are producing more output per hour. This can lead to higher potential economic output and may influence wages and inflation."
,
        "affected_vars": ["W", "PI", "Yk"] # Productivity affects wages, inflation, potential GDP
        # Potential Trigger: Random chance, high investment levels
    },
    "Productivity Bust": { # Added counterpart
        "type": "Labor",
        "param": "GRpr",
        "effect": -0.005, # Reverted: Halved from -0.0105
        "desc": "An unexpected decline in labor productivity means workers are producing less output per hour. This can lower potential economic output and may influence wages and inflation."
,
        "affected_vars": ["W", "PI", "Yk"] # Productivity affects wages, inflation, potential GDP
        # Potential Trigger: Random chance, low investment levels
    },
    # Political/Social Events
    "Infrastructure Investment Boom": {
        "type": "Political",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": 0.025, # Reverted: Halved from 0.050 (Temporary)
        "desc": "The government initiates large-scale public infrastructure projects. This directly boosts investment and increases the economy's capital stock, potentially raising long-term potential output."
,
        "affected_vars": ["K", "INV", "Yk"] # Affects capital stock, investment, potential GDP
        # Potential Trigger: Specific policy card, random chance
        # NOTE: Implement as temporary (1 turn)
    },
    # Natural Events
    "Natural Disaster": {
        "type": "Natural",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": -0.025, # Reverted: Halved from -0.050 (Temporary)
        "desc": "A significant natural disaster damages infrastructure and disrupts economic activity. This reduces the economy's capital stock and can negatively impact investment and potential output in the short term."
,
        "affected_vars": ["K", "INV", "Yk"] # Affects capital stock, investment, potential GDP
        # Potential Trigger: Random chance
       # NOTE: Implement as temporary (1 turn)
    },
    "Energy Crisis": { # Renamed from Agricultural/Energy
        "type": "Natural", # Or Geopolitical
        "param": "RA", # Affects expectations (proxy for cost shock impact)
        "effect": -0.050, # Reverted: Halved from -0.10
        "desc": "A sudden, sharp increase in energy prices raises costs for businesses and households. This can fuel inflation and negatively impact confidence, potentially leading to lower investment and consumption."
,
        "affected_vars": ["PI", "INV", "CONS"] # Energy prices affect inflation and expectations
        # Potential Trigger: Random chance, geopolitical events (if added)
    },
    "Credit Boom": { # New event using eta0
        "type": "Domestic",
        "param": "eta0", # Exogenous loan ratio component
        "effect": 0.050, # Reverted: Halved from 0.10
        "desc": "An environment of easy credit and strong household borrowing appetite leads to a rapid expansion of household debt. This can fuel consumption in the short term but increases vulnerability to future shocks."
,
        "affected_vars": ["Lhs", "CONS", "BUR"] # Affects household loans, consumption, debt burden
        # Potential Trigger: Low interest rates, high confidence
    },
    "Credit Crunch": { # New event using eta0
        "type": "Domestic",
        "param": "eta0", # Exogenous loan ratio component
        "effect": -0.050, # Reverted: Halved from -0.10
        "desc": "Banks tighten lending standards and households become more reluctant to borrow. This restricts the flow of credit, likely leading to lower household spending and an increased debt burden relative to income."
,
        "affected_vars": ["Lhs", "CONS", "BUR"] # Affects household loans, consumption, debt burden
        # Potential Trigger: High interest rates, low confidence, banking stress
    },
}