# Economic Simulator Cards and Events

This document maps the GROWTH model's exogenous variables and parameters to gameplay elements in the economic simulator.

## Policy Cards

### Monetary Policy Cards

| Card Name | Primary Effect | Secondary Effect |
|-----------|---------------|------------------|
| Interest Rate Hike | Rbbar: +0.5% | Higher lending rates, reduced investment |
| Forward Guidance | RA: ±0.2% | Affects expected sales and investment |
| Quantitative Easing | ADDbl: -0.3% | Lower long-term rates, higher asset prices |
| Reserve Requirements | ro: ±0.02 | Affects bank lending capacity |
| Bank Capital Requirements | NCAR: ±0.02 | Affects bank lending and risk-taking |
| Bank Liquidity Ratio Targets | bot/top: ±0.02 | Affects bank lending and deposit rates |

### Fiscal Policy Cards

| Card Name | Primary Effect | Secondary Effect |
|-----------|---------------|------------------|
| Government Spending | GRg: ±0.5% | Affects aggregate demand and employment |
| Tax Rate Change | theta: ±0.02 | Affects disposable income and consumption |
| Productivity Growth | GRpr: ±0.3% | Affects labor productivity and wages |

## Economic Events

### External Shocks

| Event Name | Primary Effect | Secondary Effect |
|------------|---------------|------------------|
| Global Recession | RA: -0.5% | Reduced investment and consumption |
| Trade Dispute | RA: -0.3% | Lower exports and investment |

### Domestic Economic Events

| Event Name | Primary Effect | Secondary Effect |
|------------|---------------|------------------|
| Banking Crisis | NPLk: +0.03 | Higher lending rates, reduced credit |

### Labor Market Events

| Event Name | Primary Effect | Secondary Effect |
|------------|---------------|------------------|
| Productivity Shock | GRpr: ±0.4% | Affects labor productivity |
| Labor Unrest | etan: -0.1 | Slower employment adjustment |

### Political/Social Events

| Event Name | Primary Effect | Secondary Effect |
|------------|---------------|------------------|
| Social Security Reform | alpha1: ±0.05 | Affects consumption behavior |
| Tax Policy Reform | theta: ±0.03 | Affects disposable income |
| Infrastructure Investment | gamma0: +0.002 | Higher capital accumulation |

### Natural Events

| Event Name | Primary Effect | Secondary Effect |
|------------|---------------|------------------|
| Natural Disaster | gamma0: -0.003 | Lower capital accumulation |
| Pandemic | etan: -0.15 | Slower employment adjustment |
| Agricultural/Energy Crisis | RA: -0.4% | Higher costs, lower investment | 