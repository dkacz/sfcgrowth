# cards.py
"""
Card definitions for the SFC Economic Strategy Game.
"""

# Structure: { 'Card Name': {'type': 'Monetary'/'Fiscal'/'Mixed'/'Meta', 'stance': 'expansionary'/'contractionary'/'neutral', 'effects': [{'param': 'param_name', 'effect': value_change}, ...], 'desc': 'Description'} }
# Note: 'effect' is the direct absolute change applied to the parameter.
# Some cards might have special logic handled elsewhere (e.g., temporary effects, transformations).

POLICY_CARDS = {
    # === Standard Monetary Policy ===
    "Interest Rate Hike": {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}],
        "desc": "The central bank raises its target bill rate (Rbbar) to combat inflation or cool an overheating economy."
    },
    "Interest Rate Cut": {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.010}],
        "desc": "The central bank lowers its target bill rate (Rbbar) to stimulate growth or fight deflation."
    },
    "Quantitative Easing": {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'ADDbl', 'effect': -0.005}],
        "desc": "The central bank injects liquidity by purchasing long-term bonds, aiming to reduce the yield spread (ADDbl)."
    },
    "Quantitative Tightening": {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'ADDbl', 'effect': 0.005}],
        "desc": "The central bank withdraws liquidity by selling assets or letting them mature, widening the yield spread (ADDbl)."
    },

    # === Standard Fiscal Policy ===
    "Increase Government Spending": {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}],
        "desc": "Boost the growth rate of real government spending (GRg)."
    },
    "Decrease Government Spending": {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}],
        "desc": "Reduce the growth rate of real government spending (GRg)."
    },
    "Cut Income Tax Rate": {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.010}],
        "desc": "Implement a broad cut in the average income tax rate (theta)."
    },
    "Raise Income Tax Rate": {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'theta', 'effect': 0.010}],
        "desc": "Implement a broad increase in the average income tax rate (theta)."
    },
    "Make Tax System More Progressive": {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.015}], # Proxy effect
        "desc": "Restructure taxes to increase the burden on higher incomes, boosting overall propensity to consume (alpha1)."
    },
    "Make Tax System Less Progressive": {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'alpha1', 'effect': -0.015}], # Proxy effect
        "desc": "Restructure taxes to decrease the burden on higher incomes, dampening overall propensity to consume (alpha1)."
    },

    # === Dilemma Cards ===

    # --- Austerity Apostle Cards ---
    'Wage Suppression Mandate': {
        "type": "Fiscal", # Affects wage params, closer to structural/fiscal
        "stance": "contractionary",
        "effects": [{'param': 'omega1', 'effect': -0.005}, {'param': 'omega2', 'effect': -0.010}],
        "desc": "Weakens worker wage demands by reducing sensitivity to productivity and employment."
    },
    'Labor Market Flexibility Reform': {
        "type": "Fiscal", # Structural reform
        "stance": "contractionary",
        "effects": [{'param': 'BANDt', 'effect': 0.005}, {'param': 'BANDb', 'effect': 0.005}],
        "desc": "Increases labor market 'flexibility' by widening the range where employment changes don't strongly affect wage demands."
    },
    'Bank Capital Fortification': {
        "type": "Monetary", # Regulatory, affects banks
        "stance": "contractionary",
        "effects": [{'param': 'NCAR', 'effect': 0.005}],
        "desc": "Forces banks to hold more capital, potentially restricting lending."
    },
    'Bank Liquidity Mandate': {
        "type": "Monetary", # Regulatory, affects banks
        "stance": "contractionary",
        "effects": [{'param': 'bot', 'effect': 0.005}],
        "desc": "Forces banks to hold more liquid assets, potentially restricting lending (subtle effect)."
    },
    'Austerity Deregulation Package': {
        "type": "Fiscal", # Mixed effects
        "stance": "neutral", # Productivity boost vs NPL increase
        "effects": [{'param': 'GRpr', 'effect': 0.005}, {'param': 'NPLk', 'effect': 0.005}],
        "desc": "Attempts to boost productivity through deregulation, but increases the risk of bad loans."
    },
    'Investment Dampening Measures': {
        "type": "Fiscal", # Affects investment parameters
        "stance": "contractionary",
        "effects": [{'param': 'gamma0', 'effect': 0.000}, {'param': 'gammau', 'effect': -0.005}],
        "desc": "Reduces baseline investment and its sensitivity to economic activity to enforce stability."
    },
    'State Asset Privatization': {
        "type": "Fiscal",
        "stance": "contractionary", # Spending cut outweighs tax relief
        "effects": [{'param': 'GRg', 'effect': -0.005}, {'param': 'theta', 'effect': -0.005}],
        "desc": "Sells state assets to reduce spending needs, allowing minor tax relief."
    },
    'Civil Service Rationalization': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'omega0', 'effect': 0.005}],
        "desc": "Implements deep cuts to public sector jobs, risking unrest."
    },
    'Forced Deleveraging Initiative': {
        "type": "Fiscal", # Affects household behavior
        "stance": "contractionary",
        "effects": [{'param': 'deltarep', 'effect': 0.005}, {'param': 'alpha1', 'effect': -0.005}],
        "desc": "Encourages faster household debt repayment, dampening consumption."
    },
    'Credit Market Discipline': {
        "type": "Monetary", # Affects credit parameters
        "stance": "contractionary",
        "effects": [{'param': 'eta0', 'effect': -0.005}, {'param': 'etar', 'effect': 0.005}],
        "desc": "Tightens credit conditions by reducing the base impulse and increasing rate sensitivity."
    },
    'Consumption Tax Shift': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'theta', 'effect': 0.010}, {'param': 'alpha1', 'effect': -0.015}],
        "desc": "Shifts tax burden towards consumption, significantly reducing spending propensity."
    },
    'Income Tax Base Broadening': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'theta', 'effect': 0.015}, {'param': 'alpha1', 'effect': -0.010}],
        "desc": "Increases overall income tax take by simplifying deductions, moderately reducing spending propensity."
    },
    'Monetary Credibility Shock': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Aggressively hikes short and long-term rates to anchor inflation expectations."
    },
    'Fiscal Resolve Signal': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'theta', 'effect': 0.010}, {'param': 'eps', 'effect': -0.005}],
        "desc": "Demonstrates unwavering fiscal discipline through spending cuts and tax hikes, dampening expectations."
    },
    'Austerity-Funded Capital Maintenance': {
        "type": "Fiscal",
        "stance": "contractionary", # Tax hike likely outweighs productivity boost short-term
        "effects": [{'param': 'GRpr', 'effect': 0.005}, {'param': 'theta', 'effect': 0.005}],
        "desc": "Allows minimal capital upkeep funded by tax increases."
    },
    'Accelerated Capital Decay Savings': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'delta', 'effect': 0.005}],
        "desc": "Slashes maintenance spending, accepting faster capital depreciation for immediate savings."
    },
    'Austerity Intensification Protocol': { # Placeholder - Needs special logic
        "type": "Meta",
        "stance": "contractionary",
        "effects": [],
        "desc": "Transforms the next two contractionary cards played into more potent versions."
    },
    'Monetary Containment Response': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}, {'param': 'ADDbl', 'effect': 0.010}, {'param': 'eta0', 'effect': -0.005}],
        "desc": "Relies solely on monetary tightening (rates and credit) to counter an external inflationary shock."
    },
    'Financial Regulation Tightening': {
        "type": "Monetary", # Regulatory
        "stance": "contractionary",
        "effects": [{'param': 'NCAR', 'effect': 0.005}, {'param': 'ro', 'effect': 0.005}],
        "desc": "Tightens bank regulations by increasing capital and reserve requirements."
    },
    'Market Cooling Rate Hikes': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Uses interest rate hikes across the board to cool potentially speculative markets."
    },
    'Tax-Funded Productivity Initiative': {
        "type": "Fiscal",
        "stance": "contractionary", # Tax hike likely outweighs productivity boost short-term
        "effects": [{'param': 'GRpr', 'effect': 0.005}, {'param': 'theta', 'effect': 0.005}],
        "desc": "A small, tax-funded attempt to boost long-term productivity during austerity."
    },
    'Unwavering Fiscal Discipline': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'GRpr', 'effect': -0.005}],
        "desc": "Prioritizes immediate spending cuts above all, even at the cost of lower productivity."
    },
    'Symbolic Tax Appeasement': {
        "type": "Fiscal",
        "stance": "contractionary", # Regressive cut likely contractionary overall
        "effects": [{'param': 'theta', 'effect': -0.005}, {'param': 'alpha1', 'effect': -0.005}],
        "desc": "Offers a minor, likely regressive tax cut to manage public perception."
    },
    'Reinforce Austerity Resolve': {
        "type": "Monetary", # Uses monetary signal
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'eps', 'effect': -0.005}],
        "desc": "Uses a rate hike to signal unwavering commitment to austerity, dampening expectations."
    },
    'Forced Lending Mandate': { # Placeholder - Needs special logic for temporary effect
        "type": "Monetary", # Affects bank behavior
        "stance": "contractionary", # Crowds out private credit
        "effects": [{'param': 'bot', 'effect': 0.005}, {'param': 'top', 'effect': -0.005}, {'param': 'eta0', 'effect': -0.005}],
        "desc": "Temporarily compels banks to hold more government debt, potentially reducing private credit."
    },
    'Emergency Fiscal Retrenchment': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.015}, {'param': 'theta', 'effect': 0.010}],
        "desc": "Implements extreme spending cuts and tax hikes to minimize borrowing needs."
    },
    'Deferred Maintenance Savings': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'delta', 'effect': 0.005}],
        "desc": "Achieves savings by deferring infrastructure maintenance, increasing long-term decay."
    },
    'Restructured Maintenance Levy': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.005}, {'param': 'theta', 'effect': 0.005}, {'param': 'GRpr', 'effect': -0.005}],
        "desc": "Funds reduced maintenance through taxes, masking cuts as 'efficiency savings'."
    },
    'Austerity Blitz': { # Placeholder - Needs special logic for combined effect
        "type": "Mixed",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'theta', 'effect': 0.010}, {'param': 'Rbbar', 'effect': 0.010}, {'param': 'eps', 'effect': -0.010}],
        "desc": "Applies harsh fiscal and monetary tightening simultaneously to front-load austerity."
    },
    'Sustained Fiscal Squeeze': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.005}, {'param': 'theta', 'effect': 0.005}, {'param': 'omega3', 'effect': 0.005}],
        "desc": "Applies moderate, ongoing fiscal tightening while slightly slowing wage adjustments."
    },

    # --- Demand Side Devotee Cards ---
    'Shovel-Ready Infrastructure Projects': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Launches major public works, boosting spending and potentially long-term productivity."
    },
    'Direct Consumer Rebate': { # Placeholder - Needs special logic for temporary effect
        "duration": 1, # Temporary effect
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.015}, {'param': 'alpha1', 'effect': 0.010}],
        "desc": "Issues temporary stimulus checks, cutting taxes and boosting consumption propensity."
    },
    # ... (other cards remain persistent unless specified) ...
    'Emergency Rate Cut Mandate': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.010}, {'param': 'etar', 'effect': -0.005}],
        "desc": "Aggressively cuts the policy rate, making credit less sensitive to rate changes."
    },
    'QE Overdrive': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'ADDbl', 'effect': -0.010}, {'param': 'alpha2', 'effect': 0.005}],
        "desc": "Massively expands quantitative easing, lowering long-term rates and boosting wealth effects."
    },
    'Investment Tax Credit Bonanza': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.010}, {'param': 'gamma0', 'effect': 0.005}],
        "desc": "Provides tax credits to incentivize business investment."
    },
    'Cheap Business Loans Initiative': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.005}, {'param': 'ADDbl', 'effect': -0.005}, {'param': 'gammar', 'effect': -0.005}],
        "desc": "Uses monetary policy to ensure cheap borrowing costs for businesses."
    },
    'Household Income Support Package': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.015}, {'param': 'alpha1', 'effect': 0.010}],
        "desc": "Directly boosts household incomes through tax cuts and increased consumption propensity."
    },
    'Easy Household Credit Initiative': {
        "type": "Monetary", # Affects credit parameters
        "stance": "expansionary",
        "effects": [{'param': 'eta0', 'effect': 0.010}, {'param': 'etar', 'effect': -0.005}],
        "desc": "Makes household borrowing easier and less sensitive to interest rates."
    },
    'Damn the Torpedoes - Full Speed Ahead!': {
        "type": "Mixed",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'Rbbar', 'effect': -0.010}],
        "desc": "Applies maximum fiscal and monetary stimulus simultaneously, ignoring potential risks."
    },
    'Stimulus with Efficiency Gains': {
        "type": "Mixed",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'Rbbar', 'effect': -0.005}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Combines strong demand stimulus with measures aimed at slightly boosting productivity."
    },
    'Public Service Expansion Program': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}],
        "desc": "Significantly increases government spending focused on public services and hiring."
    },
    'Future Growth Public Investment': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'gamma0', 'effect': 0.005}],
        "desc": "Increases government spending focused on long-term capital projects."
    },
    'Asset Price Inflation Target': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'ADDbl', 'effect': -0.010}, {'param': 'alpha2', 'effect': 0.005}],
        "desc": "Uses monetary policy (QE) to boost asset prices and stimulate wealth effects."
    },
    'Progressive Consumption Boost': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.015}, {'param': 'theta', 'effect': -0.010}],
        "desc": "Targets stimulus towards those with higher propensity to consume via tax structure."
    },
    'Unfunded Mandate Bonanza': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}],
        "desc": "Massively increases government spending without immediate tax offsets."
    },
    'Progressively Funded Growth': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.01}, {'param': 'theta', 'effect': 0.005}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Funds government spending increases through progressive taxation."
    },
    'Universal Demand Injection': {
        "type": "Mixed",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'theta', 'effect': -0.005}, {'param': 'Rbbar', 'effect': -0.005}],
        "desc": "Applies moderate stimulus across fiscal and monetary channels."
    },
    'Green New Deal Initiative': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Targets government spending towards green energy projects, boosting productivity."
    },
    'Confidence Boosting Campaign': {
        "type": "Fiscal", # Includes spending
        "stance": "expansionary",
        "effects": [{'param': 'eps', 'effect': 0.010}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Attempts to boost consumer confidence through messaging and minor spending."
    },
    'Ultra-Low Interest Loans': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.010}, {'param': 'ADDbl', 'effect': -0.010}],
        "desc": "Makes borrowing extremely cheap by slashing short and long-term rates."
    },
    'Patriotic Spending Initiative': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'theta', 'effect': -0.005}],
        "desc": "Encourages domestic consumption through spending and targeted tax relief."
    },
    'Stimulus Tsunami': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.020}, {'param': 'theta', 'effect': -0.015}],
        "desc": "Unleashes an overwhelming fiscal stimulus via spending hikes and tax cuts."
    },
    'Loosen the Lending Reins': {
        "type": "Monetary", # Regulatory
        "stance": "expansionary",
        "effects": [{'param': 'NCAR', 'effect': -0.005}, {'param': 'bot', 'effect': -0.005}, {'param': 'top', 'effect': 0.005}, {'param': 'eta0', 'effect': 0.005}],
        "desc": "Encourages bank lending by loosening capital/liquidity rules and boosting credit impulse."
    },
    'Direct Government Action Program': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'theta', 'effect': -0.010}],
        "desc": "Bypasses banks, using direct government spending and tax cuts for stimulus."
    },
    'Economic Adrenaline Shot': { # Placeholder - Needs special logic for temporary effect
        "duration": 1, # Temporary effect
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.015}, {'param': 'GRg', 'effect': 0.015}],
        "desc": "Provides a massive, but temporary, fiscal jolt to the economy."
    },
    'Foundation for Growth Act': { # Placeholder - Needs special logic for permanent effect?
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.010}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Implements structural changes for sustained demand via consumption propensity and baseline spending."
    },
    'Damn the Bubbles - Full Expansion!': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.015}, {'param': 'ADDbl', 'effect': -0.010}],
        "desc": "Applies extreme monetary easing, ignoring potential asset bubbles."
    },
    'Managed Boom Initiative': {
        # Persistent effect with a regulatory component
        "type": "Monetary", # Mixed regulatory/monetary
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.010}, {'param': 'ADDbl', 'effect': -0.005}, {'param': 'NCAR', 'effect': 0.005}],
        "desc": "Combines significant monetary easing with a slight increase in bank caution (capital ratio)."
    },
    'Consumer Spending Spree': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.015}, {'param': 'theta', 'effect': -0.010}],
        "desc": "Directly fuels consumption through tax cuts and boosting spending propensity."
    },
    'Corporate Investment Drive': {
        "type": "Fiscal", # Mixed fiscal/investment params
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.005}, {'param': 'gamma0', 'effect': 0.005}, {'param': 'gammau', 'effect': 0.005}],
        "desc": "Sparks business investment through targeted tax relief (theta) and by boosting baseline investment (gamma0) and its sensitivity to economic activity (gammau)."
    },

    # --- Money Monk Cards ---
    'Steadfast Rate Increase': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}],
        "desc": "A standard, significant increase in the policy interest rate."
    },
    'Aggressive QT Mandate': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Significantly drains liquidity via quantitative tightening, widening the yield spread."
    },
    'Monetary Shock Therapy': { # Placeholder - Needs special logic for temporary effect
        "duration": 1, # Temporary effect
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Applies a very large, temporary hike to both short and long-term rates."
    },
    'Persistent Tight Money Stance': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'eps', 'effect': -0.005}],
        "desc": "Signals a prolonged period of tight money via moderate rate hikes and dampening expectations."
    },
    'Fiscal-Monetary Coordination Pact (Tight)': {
        "type": "Mixed",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'GRg', 'effect': -0.005}],
        "desc": "Coordinates monetary tightening with fiscal consolidation."
    },
    'Compensatory Monetary Tightening': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}],
        "desc": "Applies extra-strong rate hikes to counteract loose fiscal policy."
    },
    'Labor Market Cooling Rate Hikes': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}],
        "desc": "Uses very significant rate hikes specifically aimed at cooling wage pressures."
    },
    'Wage Discipline Initiative': {
        "type": "Mixed", # Monetary + Structural wage params
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'omega1', 'effect': -0.005}, {'param': 'omega2', 'effect': -0.010}],
        "desc": "Combines moderate rate hikes with measures to reduce worker wage sensitivity."
    },
    'Punitive Interest Rate Policy': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Raises the price of credit sharply across the board."
    },
    'Macroprudential Credit Limits': {
        "type": "Monetary", # Regulatory
        "stance": "contractionary",
        "effects": [{'param': 'eta0', 'effect': -0.010}, {'param': 'NCAR', 'effect': 0.005}],
        "desc": "Imposes direct limits on credit growth via regulation and capital requirements."
    },
    'Inflation Combat Overdrive': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}],
        "desc": "Applies an extremely large rate hike to attack inflation regardless of output costs."
    },
    'Forward Guidance Tightening': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'eps', 'effect': -0.010}],
        "desc": "Uses moderate rate hikes combined with strong forward guidance to anchor expectations."
    },
    'Bank Lending Rate Squeeze': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}],
        "desc": "Focuses tightening impact on the bank lending channel via policy rate hikes."
    },
    'Asset Price Deflation Target': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'ADDbl', 'effect': 0.010}, {'param': 'alpha2', 'effect': -0.005}],
        "desc": "Uses quantitative tightening to target asset prices and curb wealth effects."
    },
    'Fiscal Austerity Mandate': {
        "type": "Fiscal",
        "stance": "contractionary",
        "effects": [{'param': 'GRg', 'effect': -0.010}, {'param': 'theta', 'effect': 0.010}],
        "desc": "Demands immediate fiscal cuts and tax hikes to reduce government debt."
    },
    'Debt Control via Monetary Squeeze': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Relies on sustained, strong monetary tightening to slow the economy and debt growth."
    },
    'Maximum Monetary Pressure': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}, {'param': 'ADDbl', 'effect': 0.010}],
        "desc": "Applies overwhelming conventional monetary tightening."
    },
    'Monetary Base Control Shock': {
        "type": "Monetary", # Unconventional
        "stance": "contractionary",
        "effects": [{'param': 'eta0', 'effect': -0.010}, {'param': 'ro', 'effect': 0.005}, {'param': 'Rbbar', 'effect': 0.005}],
        "desc": "Introduces unconventional measures to drastically reduce credit availability."
    },
    'Decisive Rate Adjustment': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.015}],
        "desc": "Implements a single, very large rate hike for immediate impact."
    },
    'Incremental Rate Nudge': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}],
        "desc": "Applies a small rate hike, signaling a gradual but persistent tightening path."
    },
    'Market Discipline Rate Hike': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}, {'param': 'NPLk', 'effect': 0.005}],
        "desc": "Raises rates significantly while accepting potential bank failures as market discipline."
    },
    'Sterilized Liquidity Facility': { # Placeholder - Needs special logic
        "duration": 1, # Assume liquidity facility is temporary intervention
        "type": "Monetary",
        "stance": "neutral", # Aims to be neutral on overall stance
        "effects": [{'param': 'NCAR', 'effect': 0.005}],
        "desc": "Provides targeted liquidity to prevent contagion without easing overall policy, slightly raising capital requirements."
    },
    'Hawkish Guidance Signal': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'eps', 'effect': -0.010}],
        "desc": "Uses clear, hawkish forward guidance alongside moderate rate hikes to manage expectations."
    },
    'Calculated Ambiguity': { # Placeholder - Needs special logic for random shock
        "duration": 1, # Ambiguity effect lasts one turn for the shock
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}],
        "desc": "Maintains strategic ambiguity about future policy, potentially increasing market volatility (adds random shock to ADDbl)."
    },
    'Exchange Rate Conscious Tightening': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}],
        "desc": "Moderates the pace of rate hikes to lessen pressure on the exchange rate."
    },
    'Domestic Inflation Target Priority': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}],
        "desc": "Focuses rate hikes solely on domestic inflation, ignoring exchange rate impacts."
    },
    'Borrower Cost Squeeze': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.010}],
        "desc": "Ensures rate hikes primarily impact borrowing costs."
    },
    'Saver Reward Initiative': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.005}, {'param': 'xim1', 'effect': 0.000}, {'param': 'xim2', 'effect': 0.000}],
        "desc": "Structures tightening to ensure deposit rates rise, rewarding savers (subtle effect)."
    },
    'Cautious Pivot Signal': {
        "type": "Monetary",
        "stance": "expansionary", # Relative to tight stance
        "effects": [{'param': 'Rbbar', 'effect': -0.005}, {'param': 'eps', 'effect': 0.005}],
        "desc": "Signals a potential end to tightening with a small rate cut, slightly boosting expectations."
    },
    'Maintain Peak Restrictiveness': {
        "type": "Monetary",
        "stance": "contractionary",
        "effects": [{'param': 'Rbbar', 'effect': 0.0}, {'param': 'ADDbl', 'effect': 0.005}],
        "desc": "Keeps policy rates at their peak while continuing slight quantitative tightening."
    },

    # --- Class-Conscious Crusader Cards ---
    'Public Employment Corps Initiative': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'omega0', 'effect': 0.005}],
        "desc": "Creates public jobs via massive government spending, boosting base wage pressure."
    },
    'Worker Cooperative Development Fund': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'theta', 'effect': -0.005}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Funds worker cooperatives through spending and tax breaks, aiming for productivity gains."
    },
    'Codetermination & Union Rights Act': {
        "type": "Fiscal", # Structural reform w/ spending
        "stance": "expansionary", # Boosts wages
        "effects": [{'param': 'omega1', 'effect': 0.005}, {'param': 'omega2', 'effect': 0.020}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Mandates worker representation and strengthens unions, significantly boosting wage sensitivity."
    },
    'Radical Profit & Wealth Tax': {
        "type": "Fiscal",
        "stance": "expansionary", # Redistributive effect
        "effects": [{'param': 'alpha1', 'effect': 0.015}, {'param': 'theta', 'effect': 0.015}],
        "desc": "Implements highly progressive taxes on profits/wealth, boosting consumption propensity."
    },
    'Public Ownership & Investment Authority': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'gamma0', 'effect': 0.000}],
        "desc": "Expands public ownership via state investment, boosting baseline capital growth."
    },
    'Community Reinvestment & Banking Act': {
        "type": "Mixed", # Fiscal spending + credit effect
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'eta0', 'effect': 0.010}, {'param': 'gammar', 'effect': -0.005}],
        "desc": "Channels funds through community banks, boosting targeted credit and reducing investment rate sensitivity."
    },
    'Mass Public Housing Construction': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Builds universal public housing via massive state spending, slightly boosting consumption long-term."
    },
    'Ironclad Rent Control & Tenant Power': {
        "type": "Fiscal", # Regulatory effect on consumption
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.010}, {'param': 'gamma0', 'effect': 0.000}, {'param': 'gammau', 'effect': -0.005}],
        "desc": "Implements strict rent controls, boosting consumption propensity (alpha1) but potentially deterring private housing investment by reducing baseline investment (gamma0) and its sensitivity to economic activity (gammau)."
    },
    'People\'s Interest Rate Mandate': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.010}, {'param': 'ADDbl', 'effect': -0.010}],
        "desc": "Mandates permanently low interest rates to support labor, accepting inflation risks."
    },
    'Social Investment Credit Channel': {
        "type": "Monetary",
        "stance": "expansionary",
        "effects": [{'param': 'Rbbar', 'effect': -0.005}, {'param': 'ADDbl', 'effect': -0.005}, {'param': 'eta0', 'effect': 0.010}],
        "desc": "Uses targeted credit policies alongside moderate easing to fund socially useful projects."
    },
    'Maximum Domestic Stimulus': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'alpha1', 'effect': 0.015}],
        "desc": "Applies extreme fiscal stimulus focused entirely on domestic workers and consumption."
    },
    'International Solidarity Levy': {
        "type": "Fiscal",
        "stance": "expansionary", # Net effect likely expansionary despite levy
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'theta', 'effect': 0.005}],
        "desc": "Funds international worker solidarity through a small domestic tax levy."
    },
    'Capital Control Mandate': {
        "type": "Fiscal", # Regulatory w/ spending
        "stance": "neutral", # Mixed effects on investment/spending
        "effects": [{'param': 'gammar', 'effect': -0.005}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Imposes strict capital controls to counter capital flight, slightly reducing investment rate sensitivity."
    },
    'Expropriation of Capital Flight Assets': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'gamma0', 'effect': 0.005}],
        "desc": "Nationalizes assets of fleeing capital, funding public investment."
    },
    'Universal Basic Income Act': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'theta', 'effect': -0.015}, {'param': 'alpha1', 'effect': 0.015}],
        "desc": "Implements a UBI through significant tax cuts (negative taxes), boosting consumption."
    },
    'Universal Basic Services Expansion': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.015}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Massively expands free public services, boosting consumption as household costs fall."
    },
    'Robot Tax & Worker Dividend': {
        "type": "Fiscal",
        "stance": "expansionary", # Redistributive
        "effects": [{'param': 'theta', 'effect': 0.010}, {'param': 'alpha1', 'effect': 0.010}],
        "desc": "Taxes automation to fund a worker dividend, boosting consumption propensity."
    },
    'Public Ownership of Automation Initiative': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Socializes ownership of automated industries via public investment, boosting productivity."
    },
    'State Green Investment Fund': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Funds a state-led green transition through public investment."
    },
    'Community Green Initiative Grants': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Empowers local communities for environmental projects via grants."
    },
    'Free Education For All Act': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Provides universal free education/training via government spending, boosting long-term productivity."
    },
    'Worker Learning & Sabbatical Fund': {
        "type": "Fiscal",
        "stance": "expansionary", # Spending likely outweighs tax drag
        "effects": [{'param': 'theta', 'effect': 0.005}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Funds worker sabbaticals and lifelong learning through a levy on capital."
    },
    'Major Banks Nationalization Act': {
        "type": "Mixed", # Fiscal spending + regulatory change
        "stance": "expansionary", # Social goals prioritized
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'eta0', 'effect': 0.005}, {'param': 'NCAR', 'effect': 0.005}],
        "desc": "Brings major banks under public ownership, redirecting lending towards social goals."
    },
    'Public Banking Network Initiative': {
        "type": "Mixed", # Fiscal spending + credit effect
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'eta0', 'effect': 0.010}],
        "desc": "Creates a public banking network to compete with private finance and boost social lending."
    },
    'Four-Day Week Mandate': {
        "type": "Fiscal", # Labor regulation
        "stance": "expansionary", # Boosts wage pressure
        "effects": [{'param': 'omega0', 'effect': 0.005}, {'param': 'GRpr', 'effect': 0.000}],
        "desc": "Mandates a shorter working week, increasing base wage pressure but potentially slightly reducing productivity initially."
    },
    'Productivity Dividend for Workers': {
        "type": "Fiscal", # Affects wage sensitivity
        "stance": "expansionary",
        "effects": [{'param': 'omega1', 'effect': 0.005}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Ensures productivity gains are shared as higher wages, boosting consumption."
    },
    'Empower Worker Wage Demands': {
        "type": "Fiscal", # Affects wage parameters
        "stance": "expansionary",
        "effects": [{'param': 'omega0', 'effect': 0.005}, {'param': 'omega1', 'effect': 0.005}, {'param': 'omega2', 'effect': 0.010}],
        "desc": "Strengthens worker bargaining power across the board, increasing wage pressure."
    },
    'Targeted Relief Fund': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.005}, {'param': 'theta', 'effect': 0.005}, {'param': 'alpha1', 'effect': 0.005}],
        "desc": "Provides targeted cost-of-living support funded through progressive taxes."
    },
    'Domestic Wage & Consumption Drive': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'alpha1', 'effect': 0.015}, {'param': 'GRg', 'effect': 0.005}],
        "desc": "Focuses economic strategy on boosting domestic wages and consumption."
    },
    'Public Export Champion Initiative': {
        "type": "Fiscal",
        "stance": "expansionary",
        "effects": [{'param': 'GRg', 'effect': 0.010}, {'param': 'GRpr', 'effect': 0.005}],
        "desc": "Develops high-value public enterprises for international competition via investment and productivity boosts."
    },
}