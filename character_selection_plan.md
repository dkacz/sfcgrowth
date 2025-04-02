# Character Selection Screen Implementation Plan

**Goal:** Replace the initial "Start Game" button with a character selection screen featuring four economist archetypes, each with a unique portrait, description, fixed starting deck, and a specific card bonus.

## Character Details

*   **Mapping (Left-to-Right in `assets/economists.png`):**
    1.  The Demand-Side Savior
    2.  The Money Monk
    3.  The Class-Conscious Crusader
    4.  The Austerity Apostle
*   **Starting Decks (Fixed Lists - 8 cards each):**
    *   **Demand-Side Savior:** 3x "Increase Government Spending", 2x "Cut Income Tax Rate", 1x "Interest Rate Cut", 1x "Quantitative Easing", 1x "Make Tax System More Progressive"
    *   **Money Monk:** 3x "Interest Rate Hike", 2x "Quantitative Tightening", 1x "Decrease Government Spending", 1x "Raise Income Tax Rate", 1x "Make Tax System Less Progressive"
    *   **Class-Conscious Crusader:** 3x "Increase Government Spending", 2x "Make Tax System More Progressive", 1x "Cut Income Tax Rate", 1x "Interest Rate Cut", 1x "Quantitative Easing"
    *   **Austerity Apostle:** 3x "Decrease Government Spending", 2x "Raise Income Tax Rate", 1x "Make Tax System Less Progressive", 1x "Interest Rate Hike", 1x "Quantitative Tightening"
*   **Bonus:** Apply a `* 1.20` multiplier to the `effect` value of any played card that matches *both* the character's preferred stance (Expansionary/Contractionary) and type (Fiscal/Monetary).
    *   Demand-Side Savior: Boosts Expansionary Fiscal & Expansionary Monetary cards.
    *   Money Monk: Boosts Contractionary Monetary cards.
    *   Class-Conscious Crusader: Boosts Expansionary Fiscal cards.
    *   Austerity Apostle: Boosts Contractionary Fiscal & Contractionary Monetary cards.

## Detailed Plan

**Phase 1: Data Definition & Asset Preparation**

1.  **Create `characters.py`:** Define a new file to hold the character data dictionary (`CHARACTERS`) mapping IDs to attributes (name, description, image_path, starting_deck list, bonus_criteria list of tuples, bonus_multiplier).
2.  **Split Character Portraits:** Create/modify a script (`scripts/split_characters.py`) to split `assets/economists.png` into individual files (e.g., `demand_side_savior.png`) saved in `assets/characters/`. Update `image_path` in `characters.py`. Assume roughly equal width splitting initially.
3.  **Import Characters:** Import `CHARACTERS` from `characters.py` into `growth_model_streamlit.py` and `game_mechanics.py`.

**Phase 2: Core Logic Modifications**

4.  **Modify `game_mechanics.py`:**
    *   **`create_deck(character_id=None)`:** If `character_id` is provided, return a shuffled copy of the `starting_deck` list from `CHARACTERS`. Otherwise, use default logic.
    *   **`apply_effects(..., character_id=None)`:** Add `character_id` parameter. Inside the effect application loop, if `character_id` is present, check if the card's `(stance, type)` matches the character's `bonus_criteria`. If yes, multiply the card's `effect` by `bonus_multiplier` before applying. Log the bonus application.
5.  **Modify `growth_model_streamlit.py`:**
    *   **Add New Game Phase:** Define `CHARACTER_SELECTION` and set as initial phase.
    *   **Character Selection UI (in `CHARACTER_SELECTION` phase):** Display title, use `st.columns(4)` for characters (image, name, description, "Select" button). Store chosen `char_id` in `st.session_state.selected_character_id`. Show enabled "Confirm Character & Start Game" button when a character is selected.
    *   **Update Game Initialization:** On "Confirm", transition phase to `YEAR_START`. Call `create_deck(character_id=st.session_state.selected_character_id)`.
    *   **Update Simulation Logic:** Pass `character_id=st.session_state.get('selected_character_id')` to `apply_effects`.

**Phase 3: Styling & Refinement**

6.  **CSS Styling:** Add CSS rules in `growth_model_streamlit.py` for character columns, images, and selection highlighting.

## Visual Plan (Mermaid Flowchart)

```mermaid
graph TD
    A[App Start] --> B{Game Phase?};

    subgraph Pre-Game Setup
        direction LR
        B -- Initial Load --> CS[CHARACTER_SELECTION: Display Characters];
        CS --> CS_Select{Select Character};
        CS_Select -- Character Chosen --> CS_Store[Store selected_character_id];
        CS_Store --> CS_Confirm{Confirm & Start?};
        CS_Confirm -- Yes --> YS0[Transition to YEAR_START (Year 0)];
        CS_Confirm -- No --> CS_Select;
    end

    subgraph Game Initialization (Year 0)
        direction LR
        YS0 --> YS0_InitModel[Initialize Model State];
        YS0_InitModel --> YS0_CreateDeck[Create Deck (using selected_character_id)];
        YS0_CreateDeck --> YS0_Wait[Wait for 'Proceed' (Implicitly after deck creation)];
         YS0_Wait --> SIM0[Transition to SIMULATION (Year 0 -> 1)];
    end

    subgraph Gameplay Loop (Year > 0)
        direction TB
        YS_Next[YEAR_START (Year > 0)] --> Draw[Draw Cards (Standard Logic)];
        Draw --> Display[Display KPIs, Events, Hand];
        Display --> SelectCards{Select Policies};
        SelectCards -- Confirm --> SIM_Next[Transition to SIMULATION];
        SIM_Next --> ApplyFx[Apply Effects (using selected_character_id for bonus)];
        ApplyFx --> Solve[Run Model Solve];
        Solve --> Update[Update History, Discard Hand];
        Update --> IncYear[Increment Year];
        IncYear --> YS_Next;
    end

    B -- CHARACTER_SELECTION --> CS;
    B -- YEAR_START (Year 0) --> YS0;
    B -- YEAR_START (Year > 0) --> YS_Next;
    B -- SIMULATION --> ApplyFx; % Connect simulation phase

    style CS fill:#f9f,stroke:#333,stroke-width:2px
    style YS0_CreateDeck fill:#ccf,stroke:#333,stroke-width:2px
    style ApplyFx fill:#ccf,stroke:#333,stroke-width:2px