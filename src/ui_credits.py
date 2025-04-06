# src/ui_credits.py
"""Handles rendering the credits and model explanation section."""

import streamlit as st

def display_credits():
    """Displays the credits and model explanation expander."""
    st.divider()
    with st.expander("Credits and Model Explanation", expanded=False):
        st.markdown("""
        ### Code Credits
        Powered by:
        *   **pylinsolve**: [https://github.com/kennt/pylinsolve](https://github.com/kennt/pylinsolve)
        *   **monetary-economics**: [https://github.com/kennt/monetary-economics](https://github.com/kennt/monetary-economics)
        (Both by Kent Barber)

        ### About the Model Engine
        Uses pylinsolve for iterative equation solving (Gauss-Seidel, Newton-Raphson, Broyden) tailored for Stock-Flow Consistent (SFC) models.

        ### The GROWTH Model Explained
        Based on Chapter 11 of Godley & Lavoie's *"Monetary Economics"* (2007).

        #### Key Features
        *   **Stock-Flow Consistent**: Complete accounting consistency.
        *   **Exogenous Policy**: Gov spending growth, tax rates, bill rate set by policy.
        *   **Growing Economy**: Requires active policy for full employment without inflation.
        *   **Investment & Capital**: Endogenous pricing mark-up, self-financing targets.
        *   **Equity Markets**: Firms issue shares, households purchase.
        *   **Loan Dynamics**: Household & firm borrowing, default modeling.
        *   **Banking System**: Capital reserves, loan rate mark-up on deposit rate.

        #### Model Structure
        Five sectors (households, firms, banks, central bank, government) interacting via production, consumption, investment, saving, wage/price setting, portfolio allocation, lending, fiscal operations.
        """)