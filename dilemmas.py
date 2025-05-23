# dilemmas.py

"""
Stores the definitions for the dilemmas presented to the player.
Each dilemma offers two options, each modifying the player's deck
by adding unique cards and removing standard cards.
"""

DILEMMAS = {
    # --- Austerity Apostle Dilemmas ---
    "austerity_apostle": {
        "AA_D1": {
            "title": "Labor Market Discipline",
            "flavor_text": "To truly control inflation and costs, the labor market needs discipline. Should we focus on weakening wage demands directly or reducing job security?",
            "option_a": {
                "name": "Curb Wage Aspirations",
                "add_cards": ["Wage Suppression Mandate", "Wage Suppression Mandate"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Time to tighten the screws on wages! It might cause some grumbling, but discipline is key to breaking this inflationary fever."
            },
            "option_b": {
                "name": "Increase 'Flexibility' (Precariousness)",
                "add_cards": ["Labor Market Flexibility Reform", "Labor Market Flexibility Reform"],
                "remove_cards": ["Make Tax System Less Progressive"],
                "choice_flavour": "Let's unleash 'flexibility'! Businesses love it, even if workers feel like they're on a permanent tightrope."
            }
        },
        "AA_D2": {
            "title": "Banking Sector Prudence",
            "flavor_text": "A stable financial system is paramount for austerity to work. Should we enforce stricter capital rules or encourage banks to hold more liquid assets?",
            "option_a": {
                "name": "Fortify Bank Capital",
                "add_cards": ["Bank Capital Fortification", "Bank Capital Fortification"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Banks need thicker walls! More capital means less chance of needing a bailout later, even if lending slows to a crawl."
            },
            "option_b": {
                "name": "Mandate Liquidity Hoarding",
                "add_cards": ["Bank Liquidity Mandate", "Bank Liquidity Mandate"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Make the banks hoard cash like dragons! They'll be safe, sure, but good luck getting a loan for anything less than a national treasure."
            }
        },
        "AA_D3": {
            "title": "Investment Climate for Austerity",
            "flavor_text": "Even during austerity, some investment is needed. Should we incentivize it through deregulation, hoping for efficiency gains, or accept lower growth as a price for stability?",
            "option_a": {
                "name": "Deregulate for Efficiency",
                "add_cards": ["Austerity Deregulation Package"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "Snip snip goes the red tape! Efficiency might bloom, or maybe just some creative risk-taking. Details!"
            },
            "option_b": {
                "name": "Prioritize Stability Over Growth",
                "add_cards": ["Investment Dampening Measures", "Investment Dampening Measures"],
                "remove_cards": ["Interest Rate Hike", "Interest Rate Hike"], # Removed 2 as 2 added
                "choice_flavour": "Growth is... nice, but stability is *essential*. Let's embrace the calm, steady pace of consolidation, even if it feels like wading through treacle."
            }
        },
        "AA_D4": {
            "title": "Public Sector Reform Strategy",
            "flavor_text": "The state apparatus itself is inefficient and costly. How best to impose fiscal discipline on the public sector?",
            "option_a": {
                "name": "Privatize State Assets",
                "add_cards": ["State Asset Privatization", "State Asset Privatization"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Sell the silverware! Quick cash and a smaller state. If a few monopolies pop up, well, that's the market finding efficiencies, right?"
            },
            "option_b": {
                "name": "Implement Deep Civil Service Cuts",
                "add_cards": ["Civil Service Rationalization", "Civil Service Rationalization"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "Time for the public sector haircut! Deep cuts mean real savings, even if finding a functioning service becomes a scavenger hunt."
            }
        },
        "AA_D5": {
            "title": "Managing Household Debt Burden",
            "flavor_text": "While not the primary focus, excessive household debt could destabilize the economy during austerity. Should we encourage faster repayment or simply let tighter credit handle it?",
            "option_a": {
                "name": "Promote Accelerated Deleveraging",
                "add_cards": ["Forced Deleveraging Initiative", "Forced Deleveraging Initiative"],
                "remove_cards": ["Raise Income Tax Rate"], # Placeholder removal
                "choice_flavour": "Force households to pay up! Stronger balance sheets tomorrow, even if they can't afford groceries today."
            },
            "option_b": {
                "name": "Rely on Credit Market Discipline",
                "add_cards": ["Credit Market Discipline", "Credit Market Discipline"],
                "remove_cards": ["Make Tax System Less Progressive"], # Placeholder removal
                "choice_flavour": "Let the credit markets work their magic. If people can't borrow, they can't spend. Simple, elegant, slightly brutal."
            }
        },
        "AA_D6": {
            "title": "Tax Structure for Fiscal Health",
            "flavor_text": "Raising revenue is necessary, but the structure matters. Should we focus on broad-based consumption taxes or ensure *everyone* contributes more via income taxes by simplifying the system?",
            "option_a": {
                "name": "Shift Towards Consumption Taxes",
                "add_cards": ["Consumption Tax Shift", "Consumption Tax Shift"],
                "remove_cards": ["Make Tax System Less Progressive"],
                "choice_flavour": "Tax what people *buy*, not what they *earn* (as much). Hits everyone, sure, but it's wonderfully efficient at raising cash."
            },
            "option_b": {
                "name": "Broaden the Income Tax Base",
                "add_cards": ["Income Tax Base Broadening", "Income Tax Base Broadening"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Simplify taxes so *everyone* pays their 'fair share'. Less paperwork, more revenue, even if it dampens enthusiasm for overtime."
            }
        },
        "AA_D7": {
            "title": "Inflation Expectations Management",
            "flavor_text": "Inflationary psychology is taking hold. Should we anchor expectations through aggressive monetary signals or by demonstrating unwavering fiscal resolve?",
            "option_a": {
                "name": "Monetary Shock & Awe",
                "add_cards": ["Monetary Credibility Shock", "Monetary Credibility Shock"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Monetary shock and awe! Jack up rates until inflation cries uncle. Recession? A small price to pay for credibility."
            },
            "option_b": {
                "name": "Fiscal Credibility Signal",
                "add_cards": ["Fiscal Resolve Signal", "Fiscal Resolve Signal"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Show unwavering fiscal resolve! Cut, cut, cut until expectations fall in line. It's the slow, grinding path to victory."
            }
        },
        "AA_D8": {
            "title": "Capital Investment vs. Debt Reduction",
            "flavor_text": "Even in austerity, some capital depreciates (`delta`). Should we allow minimal replacement investment, or prioritize debt reduction above all else?",
            "option_a": {
                "name": "Minimal Capital Maintenance",
                "add_cards": ["Austerity-Funded Capital Maintenance"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Fine, keep the lights on and patch the worst potholes. Minimal maintenance, maximum frugality."
            },
            "option_b": {
                "name": "Accelerate Capital Depreciation",
                "add_cards": ["Accelerated Capital Decay Savings", "Accelerated Capital Decay Savings"],
                "remove_cards": ["Make Tax System Less Progressive"],
                "choice_flavour": "Let it crumble! Immediate savings are paramount. We can worry about rebuilding... later. Much later."
            }
        },
        "AA_D9": {
            "title": "Response to External Shocks",
            "flavor_text": "An external shock threatens inflation and the deficit. Double down on austerity, or rely solely on the Central Bank to contain inflation?",
            "option_a": {
                "name": "Double Down on Austerity",
                "add_cards": ["Austerity Intensification Protocol"], # Special card, logic needed
                "remove_cards": ["Raise Income Tax Rate"], # Placeholder removal
                "choice_flavour": "Shock? What shock? Double down on the cuts! When in doubt, more austerity is always the answer."
            },
            "option_b": {
                "name": "Rely on Monetary Containment",
                "add_cards": ["Monetary Containment Response", "Monetary Containment Response"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Let the Money Monk handle this one. Fiscal policy needs to stay pure and unwavering."
            }
        },
        "AA_D10": {
            "title": "Financial Market Stability",
            "flavor_text": "Financial speculation seems detached from the real economy's adjustments. How do we ensure stability?",
            "option_a": {
                "name": "Impose Regulatory Constraints",
                "add_cards": ["Financial Regulation Tightening", "Financial Regulation Tightening"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "More rules for the financiers! Stability first, even if it means the markets become a bit... boring."
            },
            "option_b": {
                "name": "Let Monetary Policy Cool Markets",
                "add_cards": ["Market Cooling Rate Hikes", "Market Cooling Rate Hikes"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "Let the high rates cool their jets. If the whole economy freezes over a bit, so be it. Markets need discipline too."
            }
        },
        "AA_D11": {
            "title": "Long-Term Productivity vs. Short-Term Cuts",
            "flavor_text": "Stagnant productivity (`GRpr`) could undermine long-term fiscal health. Risk a small, targeted public investment, or maintain absolute fiscal discipline *now*?",
            "option_a": {
                "name": "Austere Investment in Productivity",
                "add_cards": ["Tax-Funded Productivity Initiative"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "A tiny, *austere* investment in productivity. Just a crumb, mind you, funded by finding 'efficiencies' elsewhere."
            },
            "option_b": {
                "name": "Unwavering Fiscal Discipline",
                "add_cards": ["Unwavering Fiscal Discipline", "Unwavering Fiscal Discipline"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Discipline! No deviations! Stick to the plan, even if productivity flatlines. Stability is the only goal."
            }
        },
        "AA_D12": {
            "title": "Managing Public Perception & Expectations",
            "flavor_text": "Public discontent with austerity is rising. Offer a minor, symbolic tax adjustment, or reinforce the message that austerity is non-negotiable?",
            "option_a": {
                "name": "Symbolic Tax Appeasement",
                "add_cards": ["Symbolic Tax Appeasement"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "A symbolic tax tweak. A tiny breadcrumb to quiet the masses, hopefully without compromising the mission."
            },
            "option_b": {
                "name": "Reinforce Austerity Resolve",
                "add_cards": ["Reinforce Austerity Resolve", "Reinforce Austerity Resolve"],
                "remove_cards": ["Make Tax System Less Progressive"],
                "choice_flavour": "Reinforce the message: Austerity is inevitable and non-negotiable! Steel yourselves, people!"
            }
        },
        "AA_D13": {
            "title": "Financing the Remaining Deficit",
            "flavor_text": "Compel banks to absorb government debt, or cut spending even deeper?",
            "option_a": {
                "name": "Mandate Bank Purchases of Gov. Debt",
                "add_cards": ["Forced Lending Mandate", "Forced Lending Mandate"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "'Encourage' banks to buy our debt. They won't like it, but needs must when the deficit drives."
            },
            "option_b": {
                "name": "Minimize Government Borrowing Needs",
                "add_cards": ["Emergency Fiscal Retrenchment", "Emergency Fiscal Retrenchment"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Cut deeper! Borrowing is weakness. We must minimize our needs, whatever the cost to services."
            }
        },
        "AA_D14": {
            "title": "Infrastructure Maintenance vs. Immediate Savings",
            "flavor_text": "Deferring infrastructure maintenance saves money now but increases long-term decay (`delta`). Is the immediate saving worth the long-term cost?",
            "option_a": {
                "name": "Slash Maintenance Budgets",
                "add_cards": ["Deferred Maintenance Savings", "Deferred Maintenance Savings"],
                "remove_cards": ["Make Tax System Less Progressive"],
                "choice_flavour": "Slash maintenance! Patch it later... maybe. Think of the immediate savings!"
            },
            "option_b": {
                "name": "Implement 'Efficiency Savings' in Maintenance",
                "add_cards": ["Restructured Maintenance Levy", "Restructured Maintenance Levy"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Find 'efficiency savings' in maintenance. Squeeze every penny, even if it means using duct tape."
            }
        },
        "AA_D15": {
            "title": "Political Capital Burn Rate",
            "flavor_text": "Push through the harshest reforms now, or adopt a slightly more gradual approach?",
            "option_a": {
                "name": "Rip Off the Band-Aid",
                "add_cards": ["Austerity Blitz"],
                "remove_cards": ["Raise Income Tax Rate"], # Placeholder removal
                "choice_flavour": "Rip the band-aid off! Maximum pain now for... well, for getting it over with. Brace for impact!"
            },
            "option_b": {
                "name": "Gradual Implementation (Relatively Speaking)",
                "add_cards": ["Sustained Fiscal Squeeze", "Sustained Fiscal Squeeze"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "The slow squeeze. Gradual, persistent tightening. Less shock, more of a long, drawn-out ache."
            }
        },
    },
    # --- Demand Side Devotee Dilemmas ---
    "demand_side_devotee": {
        "DSS_D1": {
             "title": "Fiscal Stimulus Delivery Mechanism",
             "flavor_text": "The economy needs a significant boost! Should we inject demand through large-scale public projects or by putting spending money directly into consumers' hands?",
             "option_a": {
                 "name": "Launch Major Public Works",
                 "add_cards": ["Shovel-Ready Infrastructure Projects", "Shovel-Ready Infrastructure Projects"],
                 "remove_cards": ["Cut Income Tax Rate"],
                 "choice_flavour": "Big projects! Shiny new bridges and roads! Creates jobs, looks impressive, even if it takes ages."
             },
             "option_b": {
                 "name": "Issue Consumer Stimulus Checks",
                 "add_cards": ["Direct Consumer Rebate", "Direct Consumer Rebate"],
                 "remove_cards": ["Increase Government Spending"],
                 "choice_flavour": "Money cannon! Fire cash directly at the people! Instant spending boost, let's hope they buy local."
             }
        },
        "DSS_D2": {
            "title": "Monetary Policy Focus",
            "flavor_text": "Credit isn't flowing freely. Should the Central Bank focus on slashing the main policy rate (`Rbbar`) or engage in aggressive asset purchases (QE) to lower long-term rates (`ADDbl`)?",
            "option_a": {
                "name": "Aggressive Policy Rate Cuts",
                "add_cards": ["Emergency Rate Cut Mandate", "Emergency Rate Cut Mandate"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Slash rates! Make borrowing cheap for everyone! Let the good times roll (on credit)!"
            },
            "option_b": {
                "name": "Unleash Quantitative Easing",
                "add_cards": ["QE Overdrive", "QE Overdrive"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "QE Overdrive! Flood the market with cash! Lower those long-term rates and watch investment (hopefully) soar!"
            }
        },
        "DSS_D3": {
            "title": "Encouraging Business Investment",
            "flavor_text": "Businesses seem hesitant to invest. Should we offer direct fiscal incentives or focus on making borrowing cheaper through monetary policy?",
            "option_a": {
                "name": "Implement Investment Tax Credits",
                "add_cards": ["Investment Tax Credit Bonanza", "Investment Tax Credit Bonanza"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Tax breaks for investors! Shower them with incentives! Surely they'll build factories now?"
            },
            "option_b": {
                "name": "Ensure Cheap Business Borrowing",
                "add_cards": ["Cheap Business Loans Initiative", "Cheap Business Loans Initiative"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Cheap loans for businesses! Make money almost free! They'd be fools not to borrow and expand!"
            }
        },
        "DSS_D4": {
            "title": "Supporting Household Spending",
            "flavor_text": "Households need more purchasing power! Directly boost incomes or make borrowing easier?",
            "option_a": {
                "name": "Direct Income Enhancement",
                "add_cards": ["Household Income Support Package", "Household Income Support Package"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "More money for the people! Tax cuts, benefits, whatever it takes to boost those paychecks!"
            },
            "option_b": {
                "name": "Facilitate Household Credit",
                "add_cards": ["Easy Household Credit Initiative", "Easy Household Credit Initiative"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Easy credit for households! Let them borrow their way to prosperity! What could go wrong?"
            }
        },
        "DSS_D5": {
            "title": "Addressing Potential Inflation Concerns",
            "flavor_text": "Some worry stimulus might overheat the economy. Ignore them or include a minor measure to ease potential supply bottlenecks?",
            "option_a": {
                "name": "Full Throttle Demand Stimulus",
                "add_cards": ["Damn the Torpedoes - Full Speed Ahead!"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Inflation? What inflation? Full speed ahead with the stimulus! We'll worry about that later!"
            },
            "option_b": {
                "name": "Demand Push with Supply Nudge",
                "add_cards": ["Stimulus with Efficiency Gains", "Stimulus with Efficiency Gains"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Stimulus with a side of efficiency! Boost demand AND maybe fix a supply bottleneck or two. Win-win?"
            }
        },
        "DSS_D6": {
            "title": "Nature of Government Spending Increase",
            "flavor_text": "More government spending needed, but focus on immediate public services/employment or longer-term public investments?",
            "option_a": {
                "name": "Expand Public Services & Employment",
                "add_cards": ["Public Service Expansion Program", "Public Service Expansion Program"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Hire more public servants! Expand services! Immediate jobs and happy citizens (mostly)!"
            },
            "option_b": {
                "name": "Invest in Future Growth Projects",
                "add_cards": ["Future Growth Public Investment", "Future Growth Public Investment"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Invest in the FUTURE! R&D, green tech! It'll pay off... eventually. Think long term!"
            }
        },
        "DSS_D7": {
            "title": "Wealth Effect vs. Direct Consumption Boost",
            "flavor_text": "Boost asset prices hoping for trickle-down, or directly target disposable income?",
            "option_a": {
                "name": "Stoke the Wealth Effect",
                "add_cards": ["Asset Price Inflation Target", "Asset Price Inflation Target"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Pump up asset prices! Make the rich feel richer, maybe they'll buy a yacht or two and stimulate something?"
            },
            "option_b": {
                "name": "Enhance Mass Consumption Power",
                "add_cards": ["Progressive Consumption Boost", "Progressive Consumption Boost"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Boost the masses! Put money in the hands of those who'll actually spend it! Real stimulus!"
            }
        },
        "DSS_D8": {
            "title": "Financing the Stimulus",
            "flavor_text": "Rely purely on government borrowing, or implement a progressive levy on higher incomes/wealth to partially offset the cost?",
            "option_a": {
                "name": "Pure Debt-Financed Stimulus",
                "add_cards": ["Unfunded Mandate Bonanza"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Borrow, borrow, borrow! Finance the stimulus now, figure out the debt later! Growth solves everything!"
            },
            "option_b": {
                "name": "Stimulus via Progressive Levy",
                "add_cards": ["Progressively Funded Growth", "Progressively Funded Growth"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Tax the rich (a bit) to pay for some of it! Makes the stimulus look responsible, right?"
            }
        },
        "DSS_D9": {
            "title": "Broad vs. Targeted Stimulus",
            "flavor_text": "Broad-based stimulus lifting all boats, or target specific strategic sectors like green energy?",
            "option_a": {
                "name": "Broad-Based Economic Flood",
                "add_cards": ["Universal Demand Injection", "Universal Demand Injection"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Flood the whole economy! A rising tide lifts all boats, even the leaky ones!"
            },
            "option_b": {
                "name": "Strategic Green Energy Push",
                "add_cards": ["Green New Deal Initiative", "Green New Deal Initiative"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Green stimulus! Save the planet AND the economy! Two birds, one massive government program!"
            }
        },
        "DSS_D10": {
            "title": "Boosting Consumer Confidence",
            "flavor_text": "Boost confidence through optimistic messaging, or make borrowing irresistible?",
            "option_a": {
                "name": "Launch \"Operation Optimism\"",
                "add_cards": ["Confidence Boosting Campaign", "Confidence Boosting Campaign"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Operation Optimism! Tell everyone how great things are! Confidence is contagious (and cheap)!"
            },
            "option_b": {
                "name": "Make Credit Irresistibly Cheap",
                "add_cards": ["Ultra-Low Interest Loans", "Ultra-Low Interest Loans"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Make borrowing irresistible! Rates so low, you'd have to be crazy not to take out a loan!"
            }
        },
        "DSS_D11": {
            "title": "International Trade Considerations",
            "flavor_text": "Implement \"Buy Domestic\" measures, or double down on stimulus magnitude to overwhelm import leakage?",
            "option_a": {
                "name": "\"Buy Domestic\" Campaign & Incentives",
                "add_cards": ["Patriotic Spending Initiative", "Patriotic Spending Initiative"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Buy Domestic! Keep the money here! A little patriotic nudging can't hurt."
            },
            "option_b": {
                "name": "Overwhelm Leakages with Raw Stimulus",
                "add_cards": ["Stimulus Tsunami"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Stimulus Tsunami! So much spending, who cares if some leaks abroad? Drown the problem in cash!"
            }
        },
        "DSS_D12": {
            "title": "Role of the Banking Sector in Stimulus",
            "flavor_text": "Encourage banks to lend more aggressively by loosening regulations, or bypass them via direct government programs?",
            "option_a": {
                "name": "Encourage Aggressive Bank Lending",
                "add_cards": ["Loosen the Lending Reins", "Loosen the Lending Reins"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Loosen the reins on banks! Let them lend, lend, lend! They know how to get money moving (into their pockets?)"
            },
            "option_b": {
                "name": "Direct Government Stimulus Channels",
                "add_cards": ["Direct Government Action Program", "Direct Government Action Program"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Bypass the banks! Direct government action! Faster, cleaner, no middleman."
            }
        },
        "DSS_D13": {
            "title": "Short-Term Jolt vs. Long-Term Foundation",
            "flavor_text": "Massive, immediate boost, or structural changes for sustained demand?",
            "option_a": {
                "name": "Economic Adrenaline Shot",
                "add_cards": ["Economic Adrenaline Shot"], # Temporary effect needs logic
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Adrenaline shot! A huge, temporary boost! Get the heart pumping again, worry about the crash later."
            },
            "option_b": {
                "name": "Foundation for Growth Act",
                "add_cards": ["Foundation for Growth Act", "Foundation for Growth Act"], # Permanent effect needs logic?
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Build a solid foundation! Structural changes for long-term growth. Slower, maybe, but sustainable."
            }
        },
        "DSS_D14": {
            "title": "Asset Market Froth Management",
            "flavor_text": "Ignore potential asset bubbles, or apply stimulus with a touch of macroprudential caution?",
            "option_a": {
                "name": "Ignore the Froth, Full Steam Ahead!",
                "add_cards": ["Damn the Bubbles - Full Expansion!"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Bubbles? Froth? Ignore it! Growth is paramount! Full steam ahead!"
            },
            "option_b": {
                "name": "Managed Boom Initiative",
                "add_cards": ["Managed Boom Initiative", "Managed Boom Initiative"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Managed boom! Stimulus with a safety net. Let's try not to blow everything up this time."
            }
        },
        "DSS_D15": {
            "title": "Consumption Engine vs. Investment Engine",
            "flavor_text": "Fuel consumer spending directly or spark business investment?",
            "option_a": {
                "name": "Fuel the Consumption Engine",
                "add_cards": ["Consumer Spending Spree", "Consumer Spending Spree"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Fuel consumption! Get people spending! That's the real engine of the economy!"
            },
            "option_b": {
                "name": "Spark the Investment Engine",
                "add_cards": ["Corporate Investment Drive", "Corporate Investment Drive"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Spark investment! Get businesses building! That's the *real* engine... no, wait, the other one?"
            }
        },
    },
    # --- Money Monk Dilemmas ---
    "money_monk": {
        "MM_D1": {
            "title": "Primary Inflation Control Tool",
            "flavor_text": "Inflation is ticking up! Rely on traditional short-term rate (`Rbbar`) hikes, or use quantitative tightening (QT) to drain liquidity (`ADDbl`)?",
            "option_a": {
                "name": "Orthodox Rate Hike",
                "add_cards": ["Steadfast Rate Increase", "Steadfast Rate Increase"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "The orthodox path: raise the policy rate. Clean, traditional, makes borrowing appropriately painful."
            },
            "option_b": {
                "name": "Aggressive Quantitative Tightening",
                "add_cards": ["Aggressive QT Mandate", "Aggressive QT Mandate"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Time for QT. Drain the swamp of excess liquidity directly. A more... thorough approach."
            }
        },
        "MM_D2": {
            "title": "Managing Inflation Expectations",
            "flavor_text": "Deliver a sharp, painful monetary shock now, or signal a prolonged period of tight money?",
            "option_a": {
                "name": "Short, Sharp Monetary Shock",
                "add_cards": ["Monetary Shock Therapy"], # Temporary effect needs logic
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Shock therapy. A sharp, decisive rate hike to shatter inflationary psychology. Expect turbulence."
            },
            "option_b": {
                "name": "Signal Prolonged Tightening",
                "add_cards": ["Persistent Tight Money Stance", "Persistent Tight Money Stance"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "The long game. Signal persistently high rates. Grind expectations down slowly, methodically."
            }
        },
        "MM_D3": {
            "title": "Fiscal Policy Alignment (or Lack Thereof)",
            "flavor_text": "Fiscal policy seems unhelpfully loose. Demand immediate fiscal consolidation, or simply tighten monetary policy even harder?",
            "option_a": {
                "name": "Demand Fiscal Support",
                "add_cards": ["Fiscal-Monetary Coordination Pact (Tight)"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Publicly chastise the fiscal authorities. Demand they get their house in order. Monetary policy requires a sensible partner."
            },
            "option_b": {
                "name": "Monetary Policy Goes It Alone",
                "add_cards": ["Compensatory Monetary Tightening", "Compensatory Monetary Tightening"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Fiscal fools won't listen? Fine. We'll tighten the screws ourselves, twice as hard if necessary."
            }
        },
        "MM_D4": {
            "title": "Addressing Wage Pressures",
            "flavor_text": "Use blunt monetary force to cool the labor market, or advocate for structural reforms to weaken worker bargaining power?",
            "option_a": {
                "name": "Monetary Hammer on Labor",
                "add_cards": ["Labor Market Cooling Rate Hikes", "Labor Market Cooling Rate Hikes"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "The monetary hammer falls on the labor market. Unfortunate, but necessary to cool wage demands."
            },
            "option_b": {
                "name": "Structural Reform Advocacy",
                "add_cards": ["Wage Discipline Initiative", "Wage Discipline Initiative"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Advocate for structural reforms. A more elegant solution than simply bludgeoning the economy with high rates."
            }
        },
        "MM_D5": {
            "title": "Managing Credit Growth",
            "flavor_text": "Rely purely on raising the price of credit (interest rates), or impose direct quantitative/regulatory limits?",
            "option_a": {
                "name": "Price Credit Appropriately (High!)",
                "add_cards": ["Punitive Interest Rate Policy", "Punitive Interest Rate Policy"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "Price dictates all. Make credit prohibitively expensive. Only the truly worthy (or desperate) will borrow."
            },
            "option_b": {
                "name": "Impose Credit Controls",
                "add_cards": ["Macroprudential Credit Limits", "Macroprudential Credit Limits"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Direct credit controls. A blunter instrument, perhaps, but sometimes necessary to curb excessive exuberance."
            }
        },
        "MM_D6": {
            "title": "Responding to Supply-Side Inflation Shock",
            "flavor_text": "Look through first-round effects, focusing on anchoring expectations, or attack all inflation head-on, ignoring output costs?",
            "option_a": {
                "name": "Attack Inflation Directly, Ignore Output Costs",
                "add_cards": ["Inflation Combat Overdrive"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Attack all inflation, regardless of source or cost. The mandate is price stability, full stop."
            },
            "option_b": {
                "name": "Anchor Expectations, Accommodate Slightly",
                "add_cards": ["Forward Guidance Tightening", "Forward Guidance Tightening"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Focus on anchoring expectations. Tolerate the first-round supply shock, but ensure it doesn't become embedded."
            }
        },
        "MM_D7": {
            "title": "Monetary Policy Transmission Channel",
            "flavor_text": "Focus on the traditional bank lending channel (`Rbbar`), or target asset prices more directly via QT (`ADDbl`)?",
            "option_a": {
                "name": "Squeeze the Lending Channel",
                "add_cards": ["Bank Lending Rate Squeeze", "Bank Lending Rate Squeeze"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Squeeze the traditional lending channel. Target bank borrowing costs directly."
            },
            "option_b": {
                "name": "Deflate Asset Prices",
                "add_cards": ["Asset Price Deflation Target", "Asset Price Deflation Target"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Deflate asset prices via QT. Reduce that troublesome 'wealth effect'."
            }
        },
        "MM_D8": {
            "title": "Tackling Government Debt",
            "flavor_text": "Explicitly demand immediate fiscal cuts, or rely on sustained monetary tightening to slow debt accumulation indirectly?",
            "option_a": {
                "name": "Demand Immediate Fiscal Cuts",
                "add_cards": ["Fiscal Austerity Mandate", "Fiscal Austerity Mandate"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Demand fiscal rectitude. The government's borrowing is complicating our mission."
            },
            "option_b": {
                "name": "Monetary Strangulation for Debt Control",
                "add_cards": ["Debt Control via Monetary Squeeze", "Debt Control via Monetary Squeeze"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Monetary strangulation. If they won't cut spending, we'll slow the economy until debt growth becomes untenable."
            }
        },
        "MM_D9": {
            "title": "Bolstering Policy Credibility",
            "flavor_text": "Double down with even more aggressive conventional tightening, or introduce an unconventional measure?",
            "option_a": {
                "name": "Overwhelming Conventional Tightening",
                "add_cards": ["Maximum Monetary Pressure"],
                "remove_cards": ["Raise Income Tax Rate"],
                "choice_flavour": "Maximum conventional pressure. Show the markets we are serious by pushing familiar levers to their limits."
            },
            "option_b": {
                "name": "Unconventional Credibility Shock",
                "add_cards": ["Monetary Base Control Shock"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "An unconventional shock. Something unexpected to demonstrate our unwavering resolve and regain credibility."
            }
        },
        "MM_D10": {
            "title": "Pace of Monetary Tightening",
            "flavor_text": "Sudden stop or gradual squeeze?",
            "option_a": {
                "name": "Swift & Decisive Rate Shock",
                "add_cards": ["Decisive Rate Adjustment"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Swift and decisive. A large rate hike now to establish dominance over inflation."
            },
            "option_b": {
                "name": "Gradual & Persistent Squeeze",
                "add_cards": ["Incremental Rate Nudge", "Incremental Rate Nudge", "Incremental Rate Nudge"],
                "remove_cards": ["Interest Rate Hike", "Interest Rate Hike"],
                "choice_flavour": "The gradual squeeze. Persistent, incremental hikes. Like water torture for inflation."
            }
        },
        "MM_D11": {
            "title": "Financial Stability During Tightening",
            "flavor_text": "Let inefficient institutions fail, or provide minimal liquidity backstops?",
            "option_a": {
                "name": "Enforce Market Discipline (Let Failures Happen)",
                "add_cards": ["Market Discipline Rate Hike", "Market Discipline Rate Hike"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Market discipline must prevail. Weak institutions should fail. It cleanses the system."
            },
            "option_b": {
                "name": "Targeted Liquidity Backstop (Reluctantly)",
                "add_cards": ["Sterilized Liquidity Facility"], # Special logic needed
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "A reluctant, sterilized backstop. Prevent outright collapse, but make it clear this is an exception, not the rule."
            }
        },
        "MM_D12": {
            "title": "Communication Strategy & Forward Guidance",
            "flavor_text": "Clear, hawkish forward guidance, or strategic ambiguity?",
            "option_a": {
                "name": "Hawkish Forward Guidance",
                "add_cards": ["Hawkish Guidance Signal", "Hawkish Guidance Signal"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Clear, hawkish guidance. Leave no room for doubt about our intentions. Certainty anchors expectations."
            },
            "option_b": {
                "name": "Strategic Ambiguity",
                "add_cards": ["Calculated Ambiguity"], # Special logic needed
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Strategic ambiguity. Keep them guessing. A little uncertainty can be a useful policy tool."
            }
        },
        "MM_D13": {
            "title": "Exchange Rate Considerations",
            "flavor_text": "Moderate tightening slightly to ease pressure on the exchange rate, or maintain domestic inflation focus regardless?",
            "option_a": {
                "name": "Moderate Tightening for Exchange Rate",
                "add_cards": ["Exchange Rate Conscious Tightening", "Exchange Rate Conscious Tightening"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "A slight moderation for the exchange rate. A pragmatic concession to external realities."
            },
            "option_b": {
                "name": "Domestic Focus Uber Alles",
                "add_cards": ["Domestic Inflation Target Priority", "Domestic Inflation Target Priority"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Domestic inflation is the sole target. The exchange rate is merely an outcome, not a goal."
            }
        },
        "MM_D14": {
            "title": "Impact on Savers vs. Borrowers",
            "flavor_text": "Structure tightening to primarily impact borrowing costs, or ensure deposit rates also rise significantly?",
            "option_a": {
                "name": "Focus Pain on Borrowers",
                "add_cards": ["Borrower Cost Squeeze", "Borrower Cost Squeeze"],
                "remove_cards": ["Quantitative Tightening"],
                "choice_flavour": "Focus the pain on borrowers. High loan rates are the primary transmission mechanism."
            },
            "option_b": {
                "name": "Reward Prudent Savers",
                "add_cards": ["Saver Reward Initiative", "Saver Reward Initiative"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "Ensure savers are rewarded. Higher deposit rates encourage prudence and reflect the true cost of money."
            }
        },
        "MM_D15": {
            "title": "Exit Strategy from Tightening",
            "flavor_text": "Signal a potential pause/easing soon, or maintain a firmly restrictive stance until inflation is definitively crushed?",
            "option_a": {
                "name": "Signal Potential Pivot (Cautiously)",
                "add_cards": ["Cautious Pivot Signal"],
                "remove_cards": ["Interest Rate Hike"],
                "choice_flavour": "A cautious hint of a pivot. Signal the peak *might* be near, but retain optionality."
            },
            "option_b": {
                "name": "Stay Restrictive Until Victory",
                "add_cards": ["Maintain Peak Restrictiveness", "Maintain Peak Restrictiveness"],
                "remove_cards": ["Decrease Government Spending"],
                "choice_flavour": "Maintain peak restrictiveness. No easing until inflation is well and truly vanquished. Victory requires vigilance."
            }
        },
    },
    # --- Class-Conscious Crusader Dilemmas ---
    "class_conscious_crusader": {
        "CCC_D1": {
            "title": "Achieving Universal Employment",
            "flavor_text": "Capitalism inherently creates unemployment! Should we guarantee jobs through direct state employment, or foster alternative, worker-controlled enterprises alongside demand stimulus?",
            "option_a": {
                "name": "Implement Universal Public Job Guarantee",
                "add_cards": ["Public Employment Corps Initiative", "Public Employment Corps Initiative"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "A job for everyone who wants one, guaranteed by the state! Unemployment is a capitalist disease; we are the cure!"
            },
            "option_b": {
                "name": "Support Worker Cooperatives & Social Economy",
                "add_cards": ["Worker Cooperative Development Fund", "Worker Cooperative Development Fund"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Worker co-ops! Build the new economy from below, owned and run by the people, not the bosses!"
            }
        },
        "CCC_D2": {
            "title": "Shifting Power in the Workplace",
            "flavor_text": "True progress requires shifting power away from capital! Should we mandate worker representation on corporate boards and strengthen unions, or focus on expropriating excess profits through radical taxation?",
            "option_a": {
                "name": "Mandate Workplace Democracy & Union Power",
                "add_cards": ["Codetermination & Union Rights Act", "Codetermination & Union Rights Act"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Workers on the boards! Strong unions! Give labor real power *inside* the beast!"
            },
            "option_b": {
                "name": "Expropriate Surplus Value via Taxation",
                "add_cards": ["Radical Profit & Wealth Tax", "Radical Profit & Wealth Tax"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Tax the parasites! Expropriate the surplus value they steal and use it for the people!"
            }
        },
        "CCC_D3": {
            "title": "Socializing Investment Decisions",
            "flavor_text": "Investment must serve the people, not profit! Should we massively expand public ownership and direct state investment, or channel funds through community-controlled banks and enterprises?",
            "option_a": {
                "name": "Nationalize Key Industries & Public Investment Drive",
                "add_cards": ["Public Ownership & Investment Authority", "Public Ownership & Investment Authority"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Nationalize it! Take control of the key industries! Investment must serve social needs, not private greed!"
            },
            "option_b": {
                "name": "Democratize Investment via Community Banks",
                "add_cards": ["Community Reinvestment & Banking Act", "Community Reinvestment & Banking Act"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Community banks! Let the people decide where investment goes in their own neighborhoods!"
            }
        },
        "CCC_D4": {
            "title": "Decommodifying Housing",
            "flavor_text": "Housing is a right, not a commodity! Should the state directly build and provide universal public housing, or implement strict rent controls and tenant protections?",
            "option_a": {
                "name": "Universal Public Housing Initiative",
                "add_cards": ["Mass Public Housing Construction", "Mass Public Housing Construction"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Housing for all, built by the state! Decommodify shelter, end landlordism!"
            },
            "option_b": {
                "name": "Radical Rent Control & Tenant Rights",
                "add_cards": ["Ironclad Rent Control & Tenant Power", "Ironclad Rent Control & Tenant Power"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Ironclad rent control! Protect tenants, squeeze the landlords until they squeak!"
            }
        },
        "CCC_D5": {
            "title": "Monetary Policy in Service of Labor",
            "flavor_text": "Monetary policy must serve the people! Mandate permanently low interest rates, or use targeted credit policies for socially useful projects?",
            "option_a": {
                "name": "Mandate Permanently Low Interest Rates",
                "add_cards": ["People's Interest Rate Mandate", "People's Interest Rate Mandate"],
                "remove_cards": ["Interest Rate Hike", "Quantitative Tightening"], # Remove both contractionary monetary cards
                "choice_flavour": "Permanently low interest rates! Cheap money for the people and worker enterprises, not for speculators!"
            },
            "option_b": {
                "name": "Socially Directed Credit Allocation",
                "add_cards": ["Social Investment Credit Channel", "Social Investment Credit Channel"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Direct credit where it's needed! Socially useful projects get priority, forget market whims!"
            }
        },
        "CCC_D6": {
            "title": "International Solidarity vs. National Focus",
            "flavor_text": "Dedicate resources to international worker solidarity, or focus all efforts on domestic workers first?",
            "option_a": {
                "name": "Prioritize Domestic Workers' Gains",
                "add_cards": ["Maximum Domestic Stimulus"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Focus here first! Strengthen the working class at home before taking on the world!"
            },
            "option_b": {
                "name": "Fund Global Worker Solidarity & Debt Relief",
                "add_cards": ["International Solidarity Levy", "International Solidarity Levy"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Workers of the world, unite! Fund solidarity abroad, fight global capital everywhere!"
            }
        },
        "CCC_D7": {
            "title": "Countering Capital Flight/Strike",
            "flavor_text": "Capitalists threaten to withhold investment! Impose strict capital controls, or nationalize assets of fleeing capital?",
            "option_a": {
                "name": "Impose Strict Capital Controls",
                "add_cards": ["Capital Control Mandate", "Capital Control Mandate"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Capital controls NOW! Trap their money here so they can't sabotage our progress!"
            },
            "option_b": {
                "name": "Nationalize Assets of Fleeing Capital",
                "add_cards": ["Expropriation of Capital Flight Assets"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "They want to flee with their stolen wealth? Seize it! Expropriate the expropriators!"
            }
        },
        "CCC_D8": {
            "title": "Expanding Social Welfare Provision",
            "flavor_text": "Implement Universal Basic Income (UBI), or focus on massively expanding free Universal Basic Services (UBS)?",
            "option_a": {
                "name": "Implement Universal Basic Income (UBI)",
                "add_cards": ["Universal Basic Income Act", "Universal Basic Income Act"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "UBI! Give everyone cash, empower individuals, bypass the bureaucracy!"
            },
            "option_b": {
                "name": "Implement Universal Basic Services",
                "add_cards": ["Universal Basic Services Expansion", "Universal Basic Services Expansion"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Universal Basic Services! Free healthcare, education, transport for all! Decommodify life itself!"
            }
        },
        "CCC_D9": {
            "title": "Managing Automation & Technological Change",
            "flavor_text": "Ensure benefits of automation are shared by all! Tax automation and fund worker transition/UBI, or socialize ownership of automated industries?",
            "option_a": {
                "name": "Tax Automation, Fund Worker Transition/UBI",
                "add_cards": ["Robot Tax & Worker Dividend", "Robot Tax & Worker Dividend"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Tax the robots! Use the funds to support workers displaced by automation!"
            },
            "option_b": {
                "name": "Socialize Ownership of Automated Industries",
                "add_cards": ["Public Ownership of Automation Initiative", "Public Ownership of Automation Initiative"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Socialize the robots! If machines do the work, let the people own the machines and share the benefits!"
            }
        },
        "CCC_D10": {
            "title": "Approach to Environmental Crisis",
            "flavor_text": "State lead a massive green transition, or empower local communities/workers to manage resources sustainably?",
            "option_a": {
                "name": "State-Led Green Transition",
                "add_cards": ["State Green Investment Fund", "State Green Investment Fund"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "State-led Green Transition! A massive public effort to save the planet from capitalist destruction!"
            },
            "option_b": {
                "name": "Empower Community Environmental Stewardship",
                "add_cards": ["Community Green Initiative Grants", "Community Green Initiative Grants"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Community power! Let local people and workers manage their environment sustainably!"
            }
        },
        "CCC_D11": {
            "title": "Education & Skills for the Working Class",
            "flavor_text": "Universal free higher education/training, or fund worker sabbaticals/lifelong learning through levies on capital?",
            "option_a": {
                "name": "Universal Free Education & Training",
                "add_cards": ["Free Education For All Act", "Free Education For All Act"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Free education for all! Knowledge is power, liberate it from the clutches of capital!"
            },
            "option_b": {
                "name": "Worker Sabbaticals & Lifelong Learning Levy",
                "add_cards": ["Worker Learning & Sabbatical Fund", "Worker Learning & Sabbatical Fund"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Worker sabbaticals! Tax capital to fund lifelong learning and development for the working class!"
            }
        },
        "CCC_D12": {
            "title": "Taming Finance Capital",
            "flavor_text": "Bring major banks under direct public ownership, or create a strong public banking network?",
            "option_a": {
                "name": "Nationalize the Commanding Heights of Finance",
                "add_cards": ["Major Banks Nationalization Act"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Nationalize the big banks! Break the power of finance capital over our economy!"
            },
            "option_b": {
                "name": "Build a Public Banking Network",
                "add_cards": ["Public Banking Network Initiative", "Public Banking Network Initiative"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Public banks everywhere! Create a democratic financial system that serves the people!"
            }
        },
        "CCC_D13": {
            "title": "Sharing Productivity Gains",
            "flavor_text": "Translate productivity gains into more leisure time (shorter work week), or into higher wages?",
            "option_a": {
                "name": "Implement Shorter Working Week",
                "add_cards": ["Four-Day Week Mandate", "Four-Day Week Mandate"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Shorter work week! More leisure, less toil! Share the gains of productivity as free time!"
            },
            "option_b": {
                "name": "Distribute Gains as Higher Wages",
                "add_cards": ["Productivity Dividend for Workers", "Productivity Dividend for Workers"],
                "remove_cards": ["Increase Government Spending"],
                "choice_flavour": "Higher wages! Share the gains as cold, hard cash in workers' pockets!"
            }
        },
        "CCC_D14": {
            "title": "Managing Inflationary Pressures from High Employment",
            "flavor_text": "Tolerate higher wage pressure as a sign of worker strength, or implement targeted measures to shield workers from rising costs?",
            "option_a": {
                "name": "Embrace Worker Bargaining Power",
                "add_cards": ["Empower Worker Wage Demands", "Empower Worker Wage Demands"],
                "remove_cards": ["Interest Rate Cut"],
                "choice_flavour": "Let wages rise! High employment means worker power, embrace it! Inflation is a capitalist scare tactic!"
            },
            "option_b": {
                "name": "Targeted Cost-of-Living Support",
                "add_cards": ["Targeted Relief Fund", "Targeted Relief Fund"],
                "remove_cards": ["Make Tax System More Progressive"],
                "choice_flavour": "Targeted support! Shield workers from rising costs caused by capitalist bottlenecks, don't punish them with austerity!"
            }
        },
        "CCC_D15": {
            "title": "Long-Term Economic Strategy",
            "flavor_text": "Boost domestic wages and consumption, or develop high-value public enterprises capable of competing internationally?",
            "option_a": {
                "name": "Focus on Domestic Wage-Led Growth",
                "add_cards": ["Domestic Wage & Consumption Drive", "Domestic Wage & Consumption Drive"],
                "remove_cards": ["Quantitative Easing"],
                "choice_flavour": "Wage-led growth! Boost domestic demand by empowering workers, build prosperity from the bottom up!"
            },
            "option_b": {
                "name": "Develop Public Export Champions",
                "add_cards": ["Public Export Champion Initiative", "Public Export Champion Initiative"],
                "remove_cards": ["Cut Income Tax Rate"],
                "choice_flavour": "Public champions! Build powerful, state-owned enterprises to challenge global capital on its own turf!"
            }
        },
    }
}