# Architectural Plan: SFC Model Economic Strategy Game

This document outlines the architectural design and implementation plan for transforming the existing Streamlit SFC model simulation into a turn-based economic strategy game.

**Target Repository:** `dkacz/sfcgrowth`

## 1. Version Control Strategy

*   **Goal:** Preserve the original application and establish a clean development environment targeting the `dkacz/sfcgrowth` repository.
*   **Prerequisites:**
    *   Ensure Git is configured with the correct user email (`omareth@gmail.com`) and name:
        ```bash
        git config --global user.email "omareth@gmail.com"
        git config --global user.name "<Your Name>" # Replace <Your Name>
        ```
    *   Ensure the local repository has a remote named `origin` pointing to `git@github.com:dkacz/sfcgrowth.git` or `https://github.com/dkacz/sfcgrowth.git`. If not, add it:
        ```bash
        # Example using SSH:
        git remote add origin git@github.com:dkacz/sfcgrowth.git
        # Or using HTTPS:
        # git remote add origin https://github.com/dkacz/sfcgrowth.git
        ```
*   **Steps:**
    1.  **Initialize Git (if not already):** Ensure the project directory is a Git repository.
    2.  **Commit Current State:** Commit any uncommitted changes on the current branch (likely `master` or `main`).
    3.  **Create `streamlit-base` Branch:** `git checkout -b streamlit-base`
    4.  **Push Base Branch:** `git push origin streamlit-base` (Pushes the preserved original state to the remote).
    5.  **Clean `.gitignore` Issues:**
        *   Ensure `.gitignore` includes standard Python/Streamlit ignores (e.g., `venv/`, `__pycache__/`, `*.pyc`).
        *   Use `git rm --cached <file>` for any files currently tracked that *should* be ignored.
        *   Commit the `.gitignore` changes and the results of `git rm --cached`. Push these changes to `streamlit-base`.
    6.  **Create `game-development` Branch:** `git checkout -b game-development streamlit-base` (Or use `game-loop-refactor` as decided).
    7.  **Development:** All new game development work will occur on the new branch. Push this branch to origin as well (`git push -u origin <branch-name>`).

## 2. Core Architecture

*   **Goal:** Design a modular and maintainable structure within Streamlit.
*   **Key Components:**
    *   **SFC Model Engine (`chapter_11_model_growth.py`):** Core `pysolve` model logic. Requires minor adaptations for turn-based interaction.
    *   **Game State Manager:** Utilizes `st.session_state` for all game-related data between turns (year, hand, economic state, model object, etc.).
    *   **Turn Manager:** Controls the flow through game turn phases (YEAR_START, SIMULATION).
    *   **Card/Event Engine:** Manages decks, hands, event triggers, and applies effects to model parameters.
    *   **UI Manager:** Renders Streamlit components for the current game phase.
    *   **Visualization Module:** Generates charts and displays data (including sector financials).
    *   **(Removed) Simulation Mode Controller:** The separate simulation mode is removed for now to focus on the core game loop.

*   **Data Flow (Simplified Turn - Merged YEAR_START/POLICY, No RESULTS Display):**
    ```mermaid
    graph TD
        A[Load App] --> B(Init Year 0);
        B --> C{YEAR_START (Year 0)};
        C -- Click 'Start Game' --> D{SIMULATION (Year 0->1)};
        D -- Update History & State --> F{YEAR_START (Year 1)};
        F -- Show Cards & Dashboard --> F;
        F -- Click 'Confirm & Run' --> G{SIMULATION (Year 1->2)};
        G -- Update History & State --> I{YEAR_START (Year 2)};
        I -- Show Cards & Dashboard --> I;
        I -- Click 'Confirm & Run' --> J{SIMULATION (Year 2->3)};
        J -- Update History & State --> L{YEAR_START (Year 3)};
        L --> L;
    ```

*   **State Management:**
    *   `st.session_state` is primary.
    *   Key variables: `current_year`, `game_phase`, `player_hand`, `active_events`, `sfc_model_object`, `historical_data`, `initial_state_dict`.
    *   `sfc_model_object` stored is the result of the *previous* turn.

    *   **Initialization:** The initial `sfc_model_object` is created, populated using `set_values` from initial lists, but **not solved**. Its `.solutions` list is empty. This object and the `initial_state_dict` are stored in session state. Game starts at `current_year = 0`.
    *   **Simulation:** Each turn creates a fresh model, applies parameters, explicitly copies the full `.solutions` history from the previous turn's stored object (if `current_year > 0`), sets `.current_solution` (if `current_year > 0`), then runs `solve()` once.

## 3. SFC Model Refactoring (`chapter_11_model_growth.py`)

*   **Goal:** Ensure turn-based compatibility and dynamic variable updates.
*   **Steps:**
    1.  Ensure model file does **not** perform a warm-up solve on import.
    2.  Modify purely lagged equations (e.g., `ER`, `PR`, `phi`, `NPLke`) to include a trivial dependency on a current variable (e.g., `+ 0*N`) to force recalculation when history is set externally.
    3.  Confirm single `model.solve()` advances one year (verified).

## 4. Game Mechanics Implementation

*   **Goal:** Implement the turn structure, card, and event systems.
*   **Turn Structure:**
    *   Use `st.session_state['game_phase']` to control UI rendering.
    *   **Year Start (Year 0):** Display initial setup message. Allow optional parameter adjustment. Provide "Start Game" button which triggers the first `SIMULATION` phase.
    *   **Year Start (Year > 0):** Draw cards and check events. Display card selection UI *first*, then the dashboard (in sidebar) comparing the *just completed* year (`current_year`) to the year before that. Provide "Confirm Policies & Run Simulation" button.
    *   **(Removed) Policy Phase:** Logic merged into `YEAR_START` for Year > 0.
    *   **Simulation:** Get previous model state, apply parameter changes (from selected cards/active events) to a *fresh* model instance, copy history from previous model (if `current_year > 0`), set current solution (if `current_year > 0`), run `model.solve()` once, store new model object, update history, update hand, increment `current_year`, set `game_phase = "YEAR_START"`. Handle `SolutionNotFoundError`.
    *   **(Removed) Results Phase:** Display logic moved to `YEAR_START` sidebar. Auto-advance logic moved to end of `SIMULATION`.
*   **Card/Event System:**
    *   **Data Representation:** Store definitions mapping names to effects (parameter changes) based on `economic_simulator_cards_events.md`.
    *   **Card Management:** Implement deck, shuffling, drawing, hand management in `st.session_state`. Card selection UI integrated into `YEAR_START` (Year > 0).
    *   **Event Triggering:** Define conditions based on previous results to trigger events.
    *   **Effect Application:** Function to modify parameters before Simulation Phase.

## 5. UI/UX Design

*   **Goal:** Create an engaging and informative interface within Streamlit, aiming for a "Monopoly" board game aesthetic.
*   **Game Mode UI Refinements (Phase 4 Plan):**
    *   **`YEAR_START` Phase (Year > 0) Layout:**
        *   Display Card Selection UI *first* in the main area. **(Done)**
        *   **(Moved)** Economic Dashboard displayed in the `st.sidebar`. **(Done)**
    *   **Dashboard Enhancement (Sidebar):**
        *   **Location:** Move dashboard display logic into the `st.sidebar` section. **(Done)**
        *   **Data Source:** Always display results from the *latest* entry in `st.session_state.sfc_model_object.solutions`, comparing to the second-to-last entry or `initial_state_dict` for deltas. **(Done)**
        *   **Layout:** Use `st.sidebar.metric` and potentially `st.sidebar.columns` if needed for organization within the sidebar. **(Done)**
        *   **Completeness:** Add missing metrics (e.g., `Rm`, `CAR`). Fix root cause of "N/A" values. **(Done)**
        *   **Clarity:** Ensure consistent formatting (`format_value`, `format_percent`). Use clear labels. Add relevant emojis/Unicode icons (e.g., 📈, 📉, 💰, 🏦) next to metric labels for visual appeal. **(Done)**
        *   **Styling:** Sidebar metrics might require less styling adjustment.
        *   **Delta Handling:**
            *   Modify `get_delta` helper function to calculate and return **percentage change** (e.g., `((curr - prev) / prev) * 100`), handling potential division by zero. **(Done)**
            *   Modify `get_delta_percent` helper function to calculate and return **percentage point change** (e.g., `(curr - prev) * 100`). Ensure conditional logic correctly handles `None` values for `prev_val` before calling `np.isfinite`. **(Done)**
            *   Update `st.metric` calls in the dashboard to use the appropriate delta function (`get_delta` for levels like GDP, `get_delta_percent` for rates/ratios like inflation). **(Done)**
            *   Ensure deltas are explicitly omitted (passed as `None`) for Year 1 results display (when comparing to initial state). **(Done)**
    *   **Card Display (`YEAR_START` Phase for Year > 0):**
        *   **Visuals:** Improve card appearance beyond simple containers. Consider using HTML/CSS within `st.markdown(..., unsafe_allow_html=True)` for better styling (borders, icons, colors based on type?). **(Basic CSS Done)**
        *   **Layout:** Ensure `MAX_CARDS_PER_ROW` logic works well. Consider responsiveness. **(Done)**
        *   **Information:** Clearly display card type, cost (if implemented later), description, and potentially the direct parameter effect. **(Done)**
        *   **Functionality:** Ensure selection/deselection works reliably. **(Done)**
    *   **Event Display (Sidebar / Main Area):**
        *   **Clarity:** Improve how active events are shown. Maybe use `st.warning` or dedicated containers in the main area during `YEAR_START` instead of just the sidebar.
        *   **Details:** Show event type and description clearly. **(Done in Sidebar)**
    *   **Financial Matrices (Moved to `YEAR_START` or separate view):**
        *   Consider placing matrices within an expander in the `YEAR_START` phase below the card selection, or creating a separate "Reports" page/view. **(Done - In Expander)**
        *   **Review `matrix_display.py`:** Ensure the formatting and calculations within the display functions are correct and robust.
        *   **Clarity:** Improve labels, potentially add explanations or tooltips for matrix entries.
        *   **Error Handling:** Ensure graceful handling if `prev_solution` is missing for revaluation/transaction matrices (Use `model.solutions[0]` for Year 1 comparison). **(Done)**
    *   **General Styling & Flow:**
        *   **Consistency:** Ensure consistent styling across phases.
        *   **Feedback:** Use `st.toast` or `st.spinner` appropriately during transitions or long operations (like simulation). **(Done)**
        *   **Navigation:** Ensure button placement and phase transitions are intuitive. Rename initial button to "Start Game". Remove `RESULTS` phase display. **(Done)**
        *   **Responsiveness:** Check layout on different screen sizes.
        *   **Reliability:** Test game loop transitions for stability. **(Done)**
*   **(Removed) Simulation Mode UI:** Focus is on the core game loop.
*   **Visualizations:**
    *   Use Streamlit's native charts (`st.line_chart`) or Plotly for historical trends based on `st.session_state.history`. Place within an expander in `YEAR_START` or a separate view. **(Done - In Expander)**
    *   Ensure matrix displays handle the first year gracefully (when no previous data exists). **(Done)**
    *   **Requirement:** Include plots/charts of key historical variables (e.g., Real GDP, Inflation, Unemployment Rate).
*   **"Monopoly" Theme Visual Enhancements (Revised Plan):**
    *   **Phase 5: Monopoly Foundation (Layout, Core Styles, Readability & Simplification)**
        *   **Goal:** Apply basic "Monopoly" styling, prioritizing readability and creating a distinct, simplified game-like structure.
        *   **Overall Layout & Background:**
            *   Use `st.container()` with custom CSS classes for distinct panels.
            *   Main Background: Light Cream/Beige (`#F7F1E3`).
            *   Style sidebar (`[data-testid="stSidebar"]`) with border/different background.
            *   Fix/Hide Top Bar: Investigate black bar at the top (`[data-testid="stHeader"]`?) and hide or restyle it.
        *   **Color Palette:**
            *   Primary: Cream/Beige (`#F7F1E3`), Black (`#000000`) for text.
            *   Accents: Monopoly Red (`#ED1B24`), Green (`#1FB25A`), Yellow (`#FFF200`), Blue (`#0072BB`), Orange (`#F7941D`), Magenta (`#EC008C`), Light Blue (`#A9E1F7`), Brown (`#9E5B3A`).
            *   Title Area: Red background (`#ED1B24`) with White text (`#FFFFFF`).
        *   **Typography:**
            *   Main Title: Text: "SFCGAME". Font: Monopoly-like font ("Passion One"). Color: White on Red background.
            *   Headers (`h2`, `h3`, Sidebar Headers): Font: "Oswald". Color: Black.
            *   Card Titles: Font: "Oswald". Color: Black.
            *   Body Text: Readable serif ("Georgia") or sans-serif ("Lato"). Color: Black.
            *   Numerical Values: Body font or clean monospace. Color: Black.
            *   *Action:* Define font stacks in CSS. Use `@import` for web fonts.
        *   **Basic Elements Styling:**
            *   **Cards:** Style like property cards (White/Light background `#FAFAD2`, black text). Add colored bar at top (`border-top: 20px solid <color>;`) based on policy type. Enforce uniform size (`min-height`). Add simple black border. Define `.selected` style (e.g., gold border).
            *   **Buttons:** Simple black borders, white/light background, black text. Hover state: Light grey background (`#DDDDDD`) or accent border, keep text black.
            *   **Dividers:** Simple black lines (`hr`).
            *   **Spacing:** Increase margins/padding.
        *   **UI Simplification (Python Code Changes):**
            *   Modify `st.set_page_config` to dynamically include the current year in the `page_title`.
            *   Remove the `st.markdown("Manage the economy...")` subtitle.
            *   Remove the `st.header(f"Year: ...")` call.
            *   Remove the `st.subheader(f"Phase: ...")` call.
            *   Remove instructional `st.write(...)` calls in `YEAR_START`.
    *   **Phase 6: Monopoly Polish & Game Elements (Future)**
        *   **Goal:** Add more specific board game elements and visual flair.
        *   **Icons:** Simple black/white icons (Font Awesome?) for dashboard/cards.
        *   **Board Elements:** Explore background textures or framing.
        *   **Visual Feedback:** Refine hover/selection states.
        *   **Custom Elements:** Style expanders, etc.

## 6. Development Phases

1.  **Phase 1: Setup & Model Prep:** Version Control, Modify model equations, Ensure model compatibility (no warm-up solve). **(Complete)**
2.  **Phase 2: Basic Game Loop & State:** Implement turn progression, state management (`st.session_state`), Initialization logic (no initial solve), Simulation logic (history copy, single solve), basic phase transitions. **(Complete)**
3.  **Phase 3: Card & Event Systems:** Data structures (`cards.py`, `events.py`), Card logic (deck, hand), Event logic (triggering), Effect application (`game_mechanics.py`). **(Partially Complete - Core logic done)**
4.  **Phase 4: UI/UX Refinement & Core Functionality:** Implement UI for merged `YEAR_START`. Move dashboard to sidebar. Fix N/A value display. Implement basic card selection UI. Ensure core game loop functions reliably. **(Complete)**
5.  **Phase 5: Monopoly Theme Foundation & Simplification:** Implement styling and Python changes focusing on the Monopoly aesthetic (layout, colors, fonts, basic card/button styles, simplified text). **(Next)**
6.  **Phase 6: Monopoly Polish & Game Elements:** Implement icons, advanced styling, and potentially subtle effects (lower priority).
7.  **Phase 7: Testing, Balancing & Final Polish:** Implement tests, Balance gameplay, Refine UI, Optimize.

## 7. Testing Strategy

*   **Model Integrity:** Verify single-step simulation results show dynamic behavior for lagged variables.
*   **State Transfer:** Ensure history copying and `current_solution` setting work correctly between turns.
*   **Card/Event Effects:** Test parameter modification and resulting economic impact.
*   **Gameplay:** Play through scenarios, test strategies, check edge cases.
*   **UI/State:** Test navigation, phase transitions, state persistence.
*   **Balancing:** Iterative playtesting for challenge and fairness.