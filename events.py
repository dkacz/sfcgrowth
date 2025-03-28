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
        "effect": -0.005, # -0.5%
        "desc": "A major global downturn occurs. Secondary: Reduced investment and consumption expectations."
        # Potential Trigger: Low global growth indicator (if added) or random chance
    },
    "Trade Dispute": {
        "type": "External",
        "param": "RA", # Random shock to expectations
        "effect": -0.003, # -0.3%
        "desc": "International trade tensions escalate. Secondary: Lower exports (implicit) and investment expectations."
        # Potential Trigger: Random chance, specific policy card plays
    },
    # Domestic Economic Events
    "Banking Sector Stress": { # Renamed from Crisis for variable impact
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": 0.03, # +3% points
        "desc": "Increased stress in the banking sector leads to more non-performing loans. Secondary: Higher lending rates, reduced credit availability."
        # Potential Trigger: High BUR, low CAR, low growth
    },
     "Banking Sector Calm": { # Added counterpart
        "type": "Domestic",
        "param": "NPLk", # Proportion of Non-Performing Loans
        "effect": -0.01, # -1% points (improvement)
        "desc": "Banking sector conditions improve, reducing non-performing loans. Secondary: Potentially lower lending rates, increased credit."
        # Potential Trigger: Low BUR, high CAR, high growth
    },
    # Labor Market Events
    "Productivity Boom": { # Renamed from Shock
        "type": "Labor",
        "param": "GRpr",
        "effect": 0.004, # +0.4%
        "desc": "Unexpected surge in labor productivity. Secondary: Affects wages and potential output."
        # Potential Trigger: Random chance, high investment levels
    },
    "Productivity Bust": { # Added counterpart
        "type": "Labor",
        "param": "GRpr",
        "effect": -0.004, # -0.4%
        "desc": "Unexpected drop in labor productivity. Secondary: Affects wages and potential output."
        # Potential Trigger: Random chance, low investment levels
    },
    "Labor Unrest": {
        "type": "Labor",
        "param": "etan", # Speed of employment adjustment
        "effect": -0.1, # Slower adjustment
        "desc": "Increased labor disputes slow down hiring/firing adjustments. Secondary: Employment levels adjust more slowly to desired levels."
        # Potential Trigger: Low wage growth, high inflation, low ER
    },
    "Flexible Labor Market": { # Added counterpart
        "type": "Labor",
        "param": "etan", # Speed of employment adjustment
        "effect": 0.1, # Faster adjustment
        "desc": "Labor market becomes more flexible. Secondary: Employment levels adjust more quickly to desired levels."
        # Potential Trigger: High wage growth, low inflation, high ER
    },
    # Political/Social Events
    "Social Security Reform (Expansion)": { # More specific
        "type": "Political",
        "param": "alpha1", # Propensity to consume out of income
        "effect": 0.05, # Increased consumption propensity (simplification)
        "desc": "Reforms increase social security benefits/coverage. Secondary: Affects consumption behavior."
        # Potential Trigger: Random chance, election cycle (if added)
    },
    "Social Security Reform (Contraction)": { # More specific
        "type": "Political",
        "param": "alpha1", # Propensity to consume out of income
        "effect": -0.05, # Decreased consumption propensity (simplification)
        "desc": "Reforms decrease social security benefits/coverage. Secondary: Affects consumption behavior."
        # Potential Trigger: Random chance, high government debt
    },
    "Tax Policy Reform (Lower Burden)": { # More specific
        "type": "Political",
        "param": "theta",
        "effect": -0.03, # -3% points
        "desc": "Major tax reform reduces the overall tax burden. Secondary: Affects disposable income."
        # Potential Trigger: Random chance, election cycle
    },
    "Tax Policy Reform (Higher Burden)": { # More specific
        "type": "Political",
        "param": "theta",
        "effect": 0.03, # +3% points
        "desc": "Major tax reform increases the overall tax burden. Secondary: Affects disposable income."
        # Potential Trigger: Random chance, high government debt
    },
    "Infrastructure Investment Boom": {
        "type": "Political",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": 0.002, # +0.2% boost
        "desc": "Large-scale infrastructure projects commence. Secondary: Higher capital accumulation baseline."
        # Potential Trigger: Specific policy card, random chance
    },
    # Natural Events
    "Natural Disaster": {
        "type": "Natural",
        "param": "gamma0", # Exogenous growth in capital stock
        "effect": -0.003, # -0.3% reduction (representing capital destruction)
        "desc": "A significant natural disaster impacts infrastructure. Secondary: Lower capital accumulation baseline."
        # Potential Trigger: Random chance
    },
    "Pandemic": {
        "type": "Natural",
        "param": "etan", # Speed of employment adjustment
        "effect": -0.15, # Much slower adjustment
        "desc": "A pandemic disrupts the labor market significantly. Secondary: Slower employment adjustment."
        # Potential Trigger: Random chance (low probability)
    },
    "Energy Crisis": { # Renamed from Agricultural/Energy
        "type": "Natural", # Or Geopolitical
        "param": "RA", # Affects expectations (proxy for cost shock impact)
        "effect": -0.004, # -0.4%
        "desc": "Sudden spike in energy prices impacts the economy. Secondary: Higher costs, lower investment expectations."
        # Potential Trigger: Random chance, geopolitical events (if added)
    },
}