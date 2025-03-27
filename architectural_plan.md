# Architectural Plan: SFC Model Economic Strategy Game (Revised v2)

This document outlines the architectural design and implementation plan for transforming the existing Streamlit SFC model simulation into a turn-based economic strategy game. **Note:** This revised plan removes the separate Simulation Mode, adds an option for initial parameter adjustment, and modifies the simulation logic to run one step per turn without a separate t=0 equilibrium solve.

**Target Repository:** `dkacz/sfcgrowth`

## 1. Version Control Strategy

*   **Goal:** Preserve the original application and establish a clean development environment targeting the `dkacz/sfcgrowth` repository.
*   **Prerequisites:**
    *   Ensure Git is configured with the correct user email (`omareth@gmail.com`) and name.
    *   Ensure the local repository has a remote named `origin` pointing to `dkacz/sfcgrowth`.
*   **Steps:**
    1.  Initialize Git (if not already).
    2.  Commit Current State.
    3.  Create `streamlit-base` Branch: `git checkout -b streamlit-base`.
    4.  Push Base Branch: `git push origin streamlit-base`.
    5.  Clean `.gitignore` Issues (using `git rm --cached` for previously tracked files). Commit cleanup and push to `streamlit-base`.
    6.  Create `game-development` Branch: `git checkout -b game-development streamlit-base`.
    7.  Development occurs on `game-development`. Push branch (`git push -u origin game-development`).

## 2. Core Architecture

*   **Goal:** Design a modular and maintainable structure within Streamlit for the game.
*   **Key Components:**
    *   **SFC Model Engine (`chapter_11_model_growth.py`):** Core `pysolve` model logic.
    *   **Game State Manager:** Utilizes `st.session_state` for all game-related data between turns (year, phase, hand, events, model object, history).
    *   **Turn Manager:** Controls the flow through game turn phases (Year Start, Policy, Simulation, Results).
    *   **Card/Event Engine:** Manages decks, hands, event triggers, and applies effects to model parameters.
    *   **UI Manager:** Renders Streamlit components for the current game phase.
    *   **Visualization Module:** Generates charts and displays data (dashboard, financial matrices).
    *   **Initial Parameter Adjuster:** UI component (e.g., expander) shown only before Year 1 starts.

*   **Data Flow (Simplified Turn - Revised Simulation):**
    ```mermaid
    graph TD
        A[Start Turn / Previous State in st.session_state] --> B{Year Start Phase};
        B -- If Year > 0: Generate Events/Draw Cards --> C[Game State Updated];
        B -- If Year == 0: Allow Initial Param Adjust --> C;
        C --> D{Policy Implementation Phase};
        D -- Player Plays Cards --> E[Calculate Final Params for Turn];
        E --> F{Simulation Phase};
        F -- Create Fresh Model --> G[Set Initial Values (t-1 state)];
        G -- Apply Final Params --> H[Run model.solve() ONCE];
        H --> I[Get New Economic Results (t state)];
        I --> J{Results & Analysis Phase};
        J -- Display Results/Update History --> K[Update Game State (Model Object with t state, Year++)];
        K --> A;
    ```

*   **State Management:**
    *   `st.session_state` is primary.
    *   Key variables: `current_year`, `game_phase`, `player_hand`, `deck`, `active_events_this_year`, `cards_selected_this_year`, `sfc_model_object`, `history`.
    *   `sfc_model_object` stored is the result of the *previous* turn's simulation (or the initial state at the very beginning).

## 3. SFC Model Refactoring (`chapter_11_model_growth.py`)

*   **Goal:** Ensure turn-based compatibility and parameter access.
*   **Steps:**
    1.  Confirm `pysolve` uses the last solution in `model.solutions` as the `t-1` state for the next `solve()` call. (Verified - this is standard behavior).
    2.  Confirm `model.set_values()` is sufficient for parameter modification by cards/events/initial adjustments. (Verified).
    3.  Confirm single `model.solve()` advances one year. (Verified).

## 4. Game Mechanics Implementation (Revised Simulation Logic)

*   **Goal:** Implement the turn structure, card, and event systems using the revised simulation approach.
*   **Initialization (`if "game_initialized" not in st.session_state`):**
    *   Create `initial_model_object`.
    *   Construct `initial_state_dict` (parameters, exogenous, initial variables).
    *   **Manually calculate and add necessary derived variables (e.g., `Sk`) to `initial_state_dict` based on their defining equations and the initial values.**
    *   Call `initial_model_object.set_values(initial_state_dict)`.
    *   **Do NOT call `initial_model_object.solve()` here.**
    *   Set the t=0 state:
        *   `t0_state = copy.copy(initial_state_dict)`
        *   `initial_model_object.solutions = [t0_state]`
        *   `initial_model_object.current_solution = t0_state`
    *   Store `initial_model_object` in `st.session_state.sfc_model_object`.
*   **Turn Structure:**
    *   Use `st.session_state['game_phase']` for UI control.
    *   **Year Start:** Display dashboard based on `st.session_state.sfc_model_object.solutions[-1]`. If `current_year == 0`, show Initial Parameter Adjuster. If `current_year > 0`, draw cards & check events.
    *   **Policy:** Allow card selection.
    *   **Simulation:**
        *   Get `previous_solution_dict` from `st.session_state.sfc_model_object.solutions[-1]`.
        *   Create a *fresh* `model_to_simulate`.
        *   Set defaults (`growth_parameters`, etc.) on `model_to_simulate`.
        *   Calculate `final_numerical_params` based on policies/events.
        *   Apply `final_numerical_params` via `model_to_simulate.set_values()`.
        *   Set history for the solver:
            *   `model_to_simulate.solutions = [copy.copy(previous_solution_dict)]`
            *   `model_to_simulate.current_solution = copy.copy(previous_solution_dict)`
        *   Run **exactly one** step: `model_to_simulate.solve(iterations=1000, threshold=1e-6)`.
        *   Store the updated model: `st.session_state.sfc_model_object = model_to_simulate`.
        *   Handle `SolutionNotFoundError`.
    *   **Results:** Display outcomes based on `st.session_state.sfc_model_object.solutions[-1]`, update history, transition to next turn.
*   **Card/Event System:** (No changes from previous plan)
    *   Data Representation, Card Management, Event Triggering, Effect Application.
*   **Initial Parameter Adjustment:** (No changes from previous plan)
    *   Availability (Year 0 only), UI (Expander), Functionality (Sliders update initial model state), Lock-in.

## 5. UI/UX Design (Enhanced)

*   **Goal:** Create an engaging, retro/stylized game interface within Streamlit.
*   **Game UI:** (No changes from previous plan)
    *   Layout & Grouping (Dashboard & Results)
    *   Styling (Retro Theme)
    *   Card Visuals (Policy Phase)
    *   Historical Charts (Results Phase)
    *   Event Notifications
    *   Sector Financials
    *   Initial Parameters

## 6. Development Phases (Revised)

1.  **Phase 1: Setup & Model Prep:** Version Control, Confirm parameter access.
2.  **Phase 2: Basic Game Loop & State (Revised Sim):** Implement turn progression, model persistence, **single-step execution without initial solve**, add Initial Parameter Adjuster UI.
3.  **Phase 3: Card & Event Systems:** Data structures, Card logic, Event logic, Effect application.
4.  **Phase 4: UI/UX Enhancements:** Implement presentation improvements.
5.  **Phase 5: Testing, Balancing & Polish:** Implement tests, Balance gameplay, Refine UI, Optimize.

## 7. Testing Strategy

*   **Model Integrity:** Verify outputs for known inputs over turns, ensuring single-step simulation behaves as expected.
*   **Card/Event/Initial Param Effects:** Test parameter modification and resulting economic impact.
*   **Gameplay:** Play through scenarios, test strategies, check edge cases.
*   **UI/State:** Test navigation, phase transitions, state persistence, visual presentation.
*   **Balancing:** Iterative playtesting.