"""
Character definitions for the SFC Economic Strategy Game.
"""

CHARACTERS = {
    "demand_side_savior": {
        "name": "The Demand-Side Savior",
        "description": "Firm believer that demand creates its own supply—especially if the government foots the bill. Economic downturn? No worries, he's always ready to build another bridge to nowhere. His wallet is always open, and the printing press never stops spinning.",
        "image_path": "assets/characters/demand_side_savior.png",
        "starting_deck": [
            "Increase Government Spending", "Increase Government Spending", "Increase Government Spending",
            "Cut Income Tax Rate", "Cut Income Tax Rate",
            "Interest Rate Cut",
            "Quantitative Easing",
            "Make Tax System More Progressive"
        ],
        "bonus_criteria": [("expansionary", "Fiscal"), ("expansionary", "Monetary")], # List of (stance, type) tuples
        "bonus_multiplier": 1.20,
        "objectives": { # Objectives for Demand-Side Savior (Year 10)
            "gdp_index": {
                "label": "GDP Index", "condition": ">=", "target_value": 140, "target_type": "index"
            },
            "unemployment": {
                "label": "Unemployment", "condition": "<=", "target_value": 4, "target_type": "percent"
            },
            "inflation": {
                "label": "Inflation", "condition": "<=", "target_value": 5, "target_type": "percent"
            }
        }
    },
    "money_monk": {
        "name": "The Money Monk",
        "description": "Inflation keeps him awake at night, and nothing pleases him more than raising interest rates. Skeptical of government's fiscal escapades, he worships at the altar of stable money—usually by making everyone poorer first.",
        "image_path": "assets/characters/money_monk.png",
        "starting_deck": [
            "Interest Rate Hike", "Interest Rate Hike", "Interest Rate Hike",
            "Quantitative Tightening", "Quantitative Tightening",
            "Decrease Government Spending",
            "Raise Income Tax Rate",
            "Make Tax System Less Progressive"
        ],
        "bonus_criteria": [("contractionary", "Monetary")],
        "bonus_multiplier": 1.40,
        "objectives": { # Objectives for Money Monk (Year 10)
            "gdp_index": {
                "label": "GDP Index", "condition": ">=", "target_value": 130, "target_type": "index"
            },
            "inflation": {
                "label": "Inflation", "condition": "<=", "target_value": 2, "target_type": "percent"
            },
            "debt_gdp": {
                "label": "Gov Debt/GDP", "condition": "<=", "target_value": 60, "target_type": "percent"
            }
        }
    },
    "class_conscious_crusader": {
        "name": "The Class-Conscious Crusader",
        "description": "Understands that full employment isn't just an economic goal but a political battleground. Advocates for government intervention to maintain employment, fully aware that empowering workers might ruffle capitalist feathers. After all, a confident working class might start questioning who’s really in charge.",
        "image_path": "assets/characters/class_conscious_crusader.png",
        "starting_deck": [
            "Increase Government Spending", "Increase Government Spending", "Increase Government Spending",
            "Make Tax System More Progressive", "Make Tax System More Progressive",
            "Cut Income Tax Rate",
            "Interest Rate Cut",
            "Quantitative Easing"
        ],
        "bonus_criteria": [("expansionary", "Fiscal")],
        "bonus_multiplier": 1.40,
        "objectives": { # Objectives for Class-Conscious Crusader (Year 10)
            "gdp_index": {
                "label": "GDP Index", "condition": ">=", "target_value": 150, "target_type": "index"
            },
            "unemployment": {
                "label": "Unemployment", "condition": "<=", "target_value": 3, "target_type": "percent"
            }
        }
    },
    "austerity_apostle": {
        "name": "The Austerity Apostle",
        "description": "His economic strategy is straightforward: if it hurts, it’s working. Proudly wears the badge of budget cuts and belt-tightening. In his perfect world, prosperity is achieved through collective misery—spending less, earning less, smiling less.",
        "image_path": "assets/characters/austerity_apostle.png",
        "starting_deck": [
            "Decrease Government Spending", "Decrease Government Spending", "Decrease Government Spending",
            "Raise Income Tax Rate", "Raise Income Tax Rate",
            "Make Tax System Less Progressive",
            "Interest Rate Hike",
            "Quantitative Tightening"
        ],
        "bonus_criteria": [("contractionary", "Fiscal"), ("contractionary", "Monetary")],
        "bonus_multiplier": 1.20,
        "objectives": { # Objectives for Austerity Apostle (Year 10)
            "gdp_index": {
                "label": "GDP Index", "condition": ">=", "target_value": 120, "target_type": "index"
            },
            "inflation": {
                "label": "Inflation", "condition": "<=", "target_value": 2, "target_type": "percent"
            },
            "debt_gdp": {
                "label": "Gov Debt/GDP", "condition": "<=", "target_value": 50, "target_type": "percent"
            }
        }
    }
}