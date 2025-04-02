# Parameter Sensitivity Analysis Report (5-Turn Horizon)

This report analyzes the sensitivity of Real GDP (Yk) to changes in various model parameters over a 5-turn simulation horizon. The goal is to determine appropriate effect sizes for policy cards and events to achieve target GDP impacts.

**Target Impacts:**
*   Policy Cards: 2.5% absolute change in Real GDP after 5 turns.
*   Events: 5.0% absolute change in Real GDP after 5 turns.

**Methodology:**
*   For each parameter, 20 simulations were run with absolute changes ranging from +/- 0.5% to +/- 5.0% (in 0.5% steps).
*   Sensitivity was calculated as: `Average(|% GDP Change at Turn 5|) / Average(|Absolute Parameter Change|)`.
*   Required changes were calculated as: `Target % GDP Impact / Sensitivity`.
*   Results are based only on successful simulation runs (some runs failed due to model convergence issues, especially for large parameter changes).

## Analysis Results Summary

parameter|avg_sensitivity|required_change_card|required_change_event
:---|:---|:---|:---
ADDbl|141.284401|0.017695|0.035390
GRg|91.920273|0.027197|0.054395
GRpr|298.195377|0.008384|0.016768
NCAR|9.868458|0.253332|0.506665
NPLk|30.288287|0.082540|0.165080
RA|39.233937|0.063720|0.127441
Rbbar|103.572063|0.024138|0.048276
Rln|26.391874|0.094726|0.189452
alpha1|72.931279|0.034279|0.068558
beta|0.002617|955.247417|1910.494833
delta|62.092721|0.040262|0.080525
eta0|37.461285|0.066736|0.133471
etan|0.101955|24.520514|49.041028
gamma0|113.151678|0.022094|0.044188
omega3|8.722768|0.286606|0.573213
ro|4.087253|0.611658|1.223315
theta|114.236494|0.021884|0.043769

## Parameter Details and Realism Assessment

### ADDbl
*   **Description:** Spread between long-term interest rate and rate on bills
*   **Avg. Sensitivity:** 141.2844
*   **Required Change (Card ~2.5%):** 0.0177
*   **Required Change (Event ~5.0%):** 0.0354
*   **Realism Comment:** Changes (~1.8-3.5 pp spread) seem plausible.

### GRg
*   **Description:** growth_mod of real government expenditures
*   **Avg. Sensitivity:** 91.9203
*   **Required Change (Card ~2.5%):** 0.0272
*   **Required Change (Event ~5.0%):** 0.0544
*   **Realism Comment:** Changes (~2.7-5.4 pp growth rate) seem plausible, maybe slightly large but usable.

### GRpr
*   **Description:** growth_mod rate of productivity
*   **Avg. Sensitivity:** 298.1954
*   **Required Change (Card ~2.5%):** 0.0084
*   **Required Change (Event ~5.0%):** 0.0168
*   **Realism Comment:** Changes (~0.8-1.7 pp growth rate) seem plausible, maybe slightly large but usable.

### NCAR
*   **Description:** Normal capital adequacy ratio of banks
*   **Avg. Sensitivity:** 9.8685
*   **Required Change (Card ~2.5%):** 0.2533
*   **Required Change (Event ~5.0%):** 0.5067
*   **Realism Comment:** Changes (~25-51 pp capital ratio) are unrealistically large. Exclude.

### NPLk
*   **Description:** Proportion of Non-Performing loans
*   **Avg. Sensitivity:** 30.2883
*   **Required Change (Card ~2.5%):** 0.0825
*   **Required Change (Event ~5.0%):** 0.1651
*   **Realism Comment:** Changes (~8-17 pp NPL ratio) are very large. Use with caution or scale down.

### RA
*   **Description:** Random shock to expectations on real sales
*   **Avg. Sensitivity:** 39.2339
*   **Required Change (Card ~2.5%):** 0.0637
*   **Required Change (Event ~5.0%):** 0.1274
*   **Realism Comment:** Changes (~6-13 pp expectations proxy) seem plausible.

### Rbbar
*   **Description:** Interest rate on bills, set exogenously
*   **Avg. Sensitivity:** 103.5721
*   **Required Change (Card ~2.5%):** 0.0241
*   **Required Change (Event ~5.0%):** 0.0483
*   **Realism Comment:** Changes (~2.4-4.8 pp policy rate) are large but potentially plausible.

### Rln
*   **Description:** Normal interest rate on loans
*   **Avg. Sensitivity:** 26.3919
*   **Required Change (Card ~2.5%):** 0.0947
*   **Required Change (Event ~5.0%):** 0.1895
*   **Realism Comment:** Changes (~9-19 pp normal loan rate) are unrealistically large. Exclude.

### alpha1
*   **Description:** Propensity to consume out of income
*   **Avg. Sensitivity:** 72.9313
*   **Required Change (Card ~2.5%):** 0.0343
*   **Required Change (Event ~5.0%):** 0.0686
*   **Realism Comment:** Changes (~3-7 pp consumption propensity) seem plausible.

### beta
*   **Description:** Parameter in expectation formations on real sales
*   **Avg. Sensitivity:** 0.0026
*   **Required Change (Card ~2.5%):** 955.2474
*   **Required Change (Event ~5.0%):** 1910.4948
*   **Realism Comment:** Changes (~955-1910) are unrealistically large for expectation parameter. Exclude.

### delta
*   **Description:** Rate of depreciation of fixed capital
*   **Avg. Sensitivity:** 62.0927
*   **Required Change (Card ~2.5%):** 0.0403
*   **Required Change (Event ~5.0%):** 0.0805
*   **Realism Comment:** Changes (~4-8 pp depreciation rate) seem plausible.

### eta0
*   **Description:** Ratio of new loans to personal income - exogenous component
*   **Avg. Sensitivity:** 37.4613
*   **Required Change (Card ~2.5%):** 0.0667
*   **Required Change (Event ~5.0%):** 0.1335
*   **Realism Comment:** Changes (~7-13 pp base loan ratio) seem plausible.

### etan
*   **Description:** Speed of adjustment of actual employment to desired employment
*   **Avg. Sensitivity:** 0.1020
*   **Required Change (Card ~2.5%):** 24.5205
*   **Required Change (Event ~5.0%):** 49.0410
*   **Realism Comment:** Changes (~25-49) are unrealistically large for speed parameter. Exclude.

### gamma0
*   **Description:** Exogenous growth_mod in the real stock of capital
*   **Avg. Sensitivity:** 113.1517
*   **Required Change (Card ~2.5%):** 0.0221
*   **Required Change (Event ~5.0%):** 0.0442
*   **Realism Comment:** Changes (~2-4 pp exogenous capital growth) seem plausible, maybe slightly large but usable.

### omega3
*   **Description:** Speed of adjustment of wages to target value
*   **Avg. Sensitivity:** 8.7228
*   **Required Change (Card ~2.5%):** 0.2866
*   **Required Change (Event ~5.0%):** 0.5732
*   **Realism Comment:** Changes (~29-57 pp wage adjustment speed) are large for speed parameter. Use with caution or scale down.

### ro
*   **Description:** Reserve requirement parameter
*   **Avg. Sensitivity:** 4.0873
*   **Required Change (Card ~2.5%):** 0.6117
*   **Required Change (Event ~5.0%):** 1.2233
*   **Realism Comment:** Changes (~61-122 pp reserve ratio) are unrealistically large. Exclude.

### theta
*   **Description:** Income tax rate
*   **Avg. Sensitivity:** 114.2365
*   **Required Change (Card ~2.5%):** 0.0219
*   **Required Change (Event ~5.0%):** 0.0438
*   **Realism Comment:** Changes (~2-4 pp tax rate) seem plausible.

## Proposed Effect Variants

Based on the analysis and realism assessment, here are three variants for the `effect` magnitudes. The sign (+/-) should be set according to the specific card/event's intended stance (expansionary/contractionary).

### Variant 1: Calculated & Rounded

Uses calculated required changes (rounded to 4 decimal places) for parameters deemed plausible or usable with caution.

| Parameter | Card Effect (Magnitude, ~2.5% GDP) | Event Effect (Magnitude, ~5.0% GDP) | Notes          |
| :-------- | :--------------------------------- | :---------------------------------- | :------------- |
| ADDbl     | 0.0177                             | 0.0354                              |                |
| GRg       | 0.0272                             | 0.0544                              |                |
| GRpr      | 0.0084                             | 0.0168                              |                |
| NPLk      | 0.0825                             | 0.1651                              | Use w/ Caution |
| RA        | 0.0637                             | 0.1274                              |                |
| Rbbar     | 0.0241                             | 0.0483                              |                |
| alpha1    | 0.0343                             | 0.0686                              |                |
| delta     | 0.0403                             | 0.0805                              |                |
| eta0      | 0.0667                             | 0.1335                              |                |
| gamma0    | 0.0221                             | 0.0442                              |                |
| omega3    | 0.2866                             | 0.5732                              | Use w/ Caution |
| theta     | 0.0219                             | 0.0438                              |                |

*Excluded Parameters: NCAR, Rln, beta, etan, ro*

### Variant 2: Simplified & Practical

Rounds required changes to 'nicer' numbers (e.g., nearest 0.005 or 0.001). Uses small fixed values for highly sensitive parameters. Excludes parameters requiring unrealistically large changes.

| Parameter | Card Effect (Magnitude, ~2.5% GDP) | Event Effect (Magnitude, ~5.0% GDP) | Notes          |
| :-------- | :--------------------------------- | :---------------------------------- | :------------- |
| ADDbl     | 0.018                              | 0.035                               |                |
| GRg       | 0.027                              | 0.054                               |                |
| GRpr      | 0.008                              | 0.017                               |                |
| NPLk      | 0.083                              | 0.165                               | Use w/ Caution |
| RA        | 0.064                              | 0.127                              |                |
| Rbbar     | 0.024                              | 0.048                               |                |
| alpha1    | 0.034                              | 0.069                              |                |
| delta     | 0.040                              | 0.081                              |                |
| eta0      | 0.067                              | 0.133                              |                |
| gamma0    | 0.022                              | 0.044                              |                |
| omega3    | 0.287                              | 0.573                              | Use w/ Caution |
| theta     | 0.022                              | 0.044                              |                |

*Excluded Parameters: NCAR, Rln, beta, etan, ro*

### Variant 3: Selective & Stable

Focuses only on parameters with moderate sensitivity and plausible required changes based on the realism assessment.

| Parameter | Card Effect (Magnitude, ~2.5% GDP) | Event Effect (Magnitude, ~5.0% GDP) |
| :-------- | :--------------------------------- | :---------------------------------- |
| ADDbl     | 0.018                              | 0.035                               |
| GRg       | 0.027                              | 0.054                               |
| GRpr      | 0.008                              | 0.017                               |
| RA        | 0.064                              | 0.127                               |
| Rbbar     | 0.024                              | 0.048                               |
| alpha1    | 0.034                              | 0.069                               |
| delta     | 0.040                              | 0.081                               |
| eta0      | 0.067                              | 0.133                               |
| gamma0    | 0.022                              | 0.044                               |
| theta     | 0.022                              | 0.044                               |

*Excluded Parameters: NCAR, Rln, beta, etan, ro, NPLk, omega3*