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
    6.  **Create `game-development` Branch:** `git checkout -b game-development streamlit-base`
    7.  **Development:** All new game development work will occur on the `game-development` branch. Push this branch to origin as well (`git push -u origin game-development`).

## 2. Core Architecture

*   **Goal:** Design a modular and maintainable structure within Streamlit.
*   **Key Components:**
    *   **SFC Model Engine (`chapter_11_model_growth.py`):** Core `pysolve` model logic. Requires minor adaptations for turn-based interaction.
    *   **Game State Manager:** Utilizes `st.session_state` for all game-related data between turns (year, hand, economic state, model object, etc.).
    *   **Turn Manager:** Controls the flow through game turn phases (Year Start, Policy, Simulation, Results).
    *   **Card/Event Engine:** Manages decks, hands, event triggers, and applies effects to model parameters.
    *   **UI Manager:** Renders Streamlit components for the current game phase and mode (Game vs. Simulation).
    *   **Visualization Module:** Generates charts and displays data (including sector financials) with thematic styling and animations.
    *   **Simulation Mode Controller:** Manages the separate simulation sandbox environment.

*   **Data Flow (Simplified Turn):**
    ```mermaid
    graph TD
        A[Start Turn / Previous State in st.session_state] --> B{Year Start Phase};
        B -- Generate Events/Draw Cards --> C[Game State Updated];
        C --> D{Policy Implementation Phase};
        D -- Player Plays Cards --> E[Modify Model Params in State];
        E --> F{Simulation Phase};
        F -- Run model.solve() once --> G[Get New Economic Results];
        G --> H{Results & Analysis Phase};
        H -- Display Results/Calculate Consequences --> I[Update Game State for Next Turn];
        I --> A;
    ```

*   **State Management:**
    *   `st.session_state` is primary.
    *   Key variables: `current_year`, `game_phase`, `player_hand`, `active_events`, `sfc_model_object`, `historical_data`, `ui_mode` (Game/Simulation).
    *   `sfc_model_object` stored is the result of the *previous* turn.

## 3. SFC Model Refactoring (`chapter_11_model_growth.py`)

*   **Goal:** Ensure turn-based compatibility.
*   **Steps:**
    1.  Review model initialization from previous state.
    2.  Create a clear interface for getting/setting model parameters.
    3.  Confirm single `model.solve()` advances one year.
    4.  Isolate the baseline model run.

## 4. Game Mechanics Implementation

*   **Goal:** Implement the turn structure, card, and event systems.
*   **Turn Structure:**
    *   Use `st.session_state['game_phase']` to control UI rendering.
    *   **Year Start:** Display dashboard, trigger event checks, draw cards.
    *   **Policy:** Allow card selection, display projected parameter changes, confirm choices.
    *   **Simulation:** Apply parameter changes, run `model.solve()`, store new model object. Handle `SolutionNotFoundError`.
    *   **Results:** Display outcomes, calculate consequences, update history, transition to next turn.
*   **Card/Event System:**
    *   **Data Representation:** Store definitions mapping names to effects (parameter changes) based on `economic_simulator_cards_events.md`.
    *   **Card Management:** Implement deck, shuffling, drawing, hand management in `st.session_state`.
    *   **Event Triggering:** Define conditions based on previous results to trigger events.
    *   **Effect Application:** Function to modify `sfc_model_object` parameters before Simulation Phase.

## 5. UI/UX Design

*   **Goal:** Create an engaging, retro/stylized interface within Streamlit.
*   **Game Mode UI:**
    *   **Dashboard:** Columns/containers for indicators, charts, news feed.
    *   **Card Display:** Custom HTML/CSS (`st.markdown`) or component for stylized cards. Buttons for playing.
    *   **Event Notifications:** `st.toast`, `st.warning`, or custom containers.
    *   **Styling:** Custom CSS and Streamlit Theming for retro/stylized look.
    *   **Sector Financials:** `st.expander` or modal for detailed matrices.
    *   **Simulation Mode Access:** Button/link in `st.sidebar` or settings `st.expander`.
*   **Simulation Mode UI:**
    *   Reuse existing layout (sliders, comparison charts).
    *   Operate on a *copy* of game state.
    *   Clear sandbox indicators.
*   **Visualizations:**
    *   Use Plotly.
    *   Simulate animations (indicator changes, highlights).
    *   Basic chart transitions (re-rendering).

## 6. Development Phases

1.  **Phase 1: Setup & Model Prep:** Version Control (incl. Git config/remote setup), Model parameter access, Basic app structure.
2.  **Phase 2: Basic Game Loop & State:** Turn progression, Model object persistence, Single-step execution.
3.  **Phase 3: Card & Event Systems:** Data structures, Card logic, Event logic, Effect application.
4.  **Phase 4: UI/UX - Game Mode:** Dashboard, Card/Event display, Financials display, Styling, Basic animations.
5.  **Phase 5: Simulation Mode Integration:** Integrate UI, Implement state copying, Add access point.
6.  **Phase 6: Testing, Balancing & Polish:** Implement tests, Balance gameplay, Refine UI, Optimize.

## 7. Testing Strategy

*   **Model Integrity:** Scripts verifying outputs for known inputs over turns.
*   **Card/Event Effects:** Test parameter modification and resulting economic impact.
*   **Gameplay:** Play through scenarios, test strategies, check edge cases.
*   **UI/State:** Test navigation, phase transitions, state persistence/isolation.
*   **Balancing:** Iterative playtesting for challenge and fairness.