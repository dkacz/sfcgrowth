# Icon Requirements for SFCGAME (Monopoly Theme)

This document lists the required icons for the SFCGAME application. The desired style is simple, clear, and evocative of classic board games like Monopoly, suitable for use at small sizes.

## General Requirements

*   **Style:** Simple, easily recognizable silhouette or line-art. Avoid excessive detail. Icons should render clearly at small sizes (target viewable area ~20x20 pixels).
*   **Format:** **PNG** with a transparent background.
*   **Resolution:** Please provide PNGs at a minimum resolution of **64x64 pixels** to allow for good quality when scaled down.
*   **Color:** Icons should be provided in **black** (`#000000`). We may attempt to re-color them via CSS filters if needed for specific contexts (like white on card bars), but a black version is the most versatile base.
*   **Consistency:** All icons should share a consistent line weight and level of detail.
*   **Usage Context:** Icons will be displayed small, next to text labels (dashboard metrics) or card titles. Clarity at small sizes is paramount.
*   **State Variations:** No hover or active state variations are needed for the icons themselves; these effects will be handled by CSS on the parent elements.

## Icon List

### Policy Card Types

1.  **Monetary Policy:**
    *   **Concept:** Banking, money supply, interest rates.
    *   **Suggested Visual:** Simple bank building facade OR a currency symbol (e.g., '$').
    *   **Filename Suggestion:** `monetary_icon.png`
2.  **Fiscal Policy:**
    *   **Concept:** Government spending, taxation, budgets.
    *   **Suggested Visual:** Simple government building facade (distinct from bank) OR scales of justice.
    *   **Filename Suggestion:** `fiscal_icon.png`

### Dashboard Metrics (Sidebar)

3.  **Real GDP (Yk):**
    *   **Concept:** Overall economic output/production.
    *   **Suggested Visual:** Simple factory outline OR an upward trending line graph.
4.  **Inflation (PI):**
    *   **Concept:** Rising prices.
    *   **Suggested Visual:** Simple flame icon OR an upward arrow.
5.  **Unemployment Rate:**
    *   **Concept:** Labor force status.
    *   **Suggested Visual:** Simple group of people/figures OR a 'factory closed' symbol.
6.  **Capital Growth (GRk):**
    *   **Concept:** Investment, building up capital.
    *   **Suggested Visual:** Simple building/construction icon OR an upward arrow with a gear/cog.
7.  **Bill Rate (Rb):**
    *   **Concept:** Government bond interest rate.
    *   **Suggested Visual:** Simple scroll/document icon OR a percentage sign ('%').
8.  **Loan Rate (Rl):**
    *   **Concept:** Bank lending interest rate.
    *   **Suggested Visual:** Simple handshake icon OR a percentage sign ('%').
9.  **Deposit Rate (Rm):**
    *   **Concept:** Bank deposit interest rate.
    *   **Suggested Visual:** Simple piggy bank icon OR a percentage sign ('%').
10. **Tobin's Q:**
    *   **Concept:** Asset valuation ratio.
    *   **Suggested Visual:** Simple balanced scales icon OR a stylized 'Q'.
11. **Debt Burden (BUR):**
    *   **Concept:** Household debt relative to income.
    *   **Suggested Visual:** Simple icon of a figure carrying a weight OR a house with a downward arrow/weight.
12. **Capital Adequacy (CAR):**
    *   **Concept:** Bank stability/reserves.
    *   **Suggested Visual:** Simple shield icon OR a bank building with a plus sign.
13. **Gov Deficit (PSBR):**
    *   **Concept:** Government spending exceeding revenue.
    *   **Suggested Visual:** Simple downward arrow OR a money bag with a minus sign.
14. **Gov Debt / GDP:**
    *   **Concept:** Government debt relative to economy size.
    *   **Suggested Visual:** Simple government building icon next to a percentage sign ('%').