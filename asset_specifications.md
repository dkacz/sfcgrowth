# Asset Requirements for SFCGAME (Monopoly Theme)

This document lists the required visual assets for the SFCGAME application. The desired style is evocative of classic board games like Monopoly, suitable for a web application interface.

## General Style Guide

*   **Style:** Clean, clear, reminiscent of classic Monopoly elements. Avoid overly complex details that might clutter the UI. For cards, aim for a detailed illustrative or photorealistic style mimicking printed objects.
*   **Consistency:** All assets should share a consistent aesthetic.

## High-Fidelity Card Design Assets (Phase 6+)

*   **Goal:** Create card visuals that look like authentic, physical Monopoly cards.
*   **Required Elements (per card type - e.g., Monetary, Fiscal):**
    1.  **Card Base Image/Texture:** A background image representing the card's main body (e.g., parchment color `#FAFAD2` with subtle paper/linen texture). Should accommodate text overlay. (Format: PNG/JPG, potentially tileable).
    2.  **Colored Top Bar:** The distinct colored bar (e.g., Monopoly Blue `#0072BB` for Monetary, Green `#1FB25A` for Fiscal). This could be part of the base image or applied via CSS.
    3.  **Detailed Icon/Illustration:** A high-quality illustration relevant to the policy type (replacing the simple icons below). To be placed within the colored top bar. (Format: PNG with transparency, high resolution).
    4.  **Border:** A defined border style (e.g., simple black line, potentially with inner/outer styling) integrated into the card base image or applied via CSS.
*   **Typography:** Fonts for title (within top bar, likely white) and description (on card body, likely black) should match the Monopoly aesthetic (e.g., Oswald/Lato or similar).
*   **Implementation:** These assets will likely be used as background images or layered `<img>` tags within the card's HTML structure, combined with CSS for text overlay and positioning.

## Simple Icons (Alternative/Fallback or for Dashboard)

*   **Format:** **PNG** with a transparent background.
*   **Resolution:** Minimum **64x64 pixels**.
*   **Color:** Provide icons in **black** (`#000000`).
*   **Usage:** Displayed small (~20x20px) next to text labels (dashboard metrics) or potentially as simpler card icons if high-fidelity illustrations are not used.
*   **List:** (See detailed list below)

## Other Image Assets (Optional but Recommended)

1.  **Game Logo:**
    *   **Concept:** "SFCGAME" text in a style matching the Monopoly game logo (bold, potentially arched, white text on red background).
    *   **Usage:** Displayed prominently at the top.
    *   **Format:** PNG with transparent background (preferred) or SVG. High resolution needed.
2.  **Main Background Texture:**
    *   **Concept:** Subtle texture resembling the cream/parchment center of a Monopoly board.
    *   **Usage:** Tiled background for the main application area (`.stApp`).
    *   **Format:** Seamlessly tileable PNG or JPG. Keep file size reasonable.
3.  **Event Card Backgrounds (Future):**
    *   **Concept:** Background images mimicking "Community Chest" (Yellow) and "Chance" (Orange) cards, including borders/frames.
    *   **Usage:** For displaying game events if implemented as distinct popups/cards.
    *   **Format:** PNG or JPG.
4.  **UI Framing Elements (Optional):**
    *   **Concept:** Simple border graphics or corner elements inspired by Monopoly board squares.
    *   **Usage:** To visually frame main UI panels or sections.
    *   **Format:** PNG with transparency or SVG.

## Icon List Details (For Simple Icons)

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