# src/ui_game_over.py
"""Handles rendering the Game Over screen."""

import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import quote
import altair as alt
import logging
from matrix_display import display_balance_sheet_matrix, display_revaluation_matrix, display_transaction_flow_matrix
from cards import POLICY_CARDS
from src.ui_plotting import create_kpi_plot
from src.simulation_logic import run_counterfactual_simulation


def get_achievement_html(title, desc, emoji):
    """Generates HTML for an achievement badge."""
    return f"""
    <div class="achievement">
        <div class="achievement-emoji">{emoji}</div>
        <div class="achievement-text">
            <div class="achievement-title">{title}</div>
            <div class="achievement-desc">{desc}</div>
        </div>
    </div>
    """


def get_history_metrics(history, current_year):
    """Extracts key metrics from history for the results summary."""
    metrics = {}
    if not history:
        return metrics
    
    # Create DataFrame for easier analysis
    history_df = pd.DataFrame(history)
    history_df = history_df.sort_values('year')
    
    # Get data from the first and last years
    start_year_data = history_df[history_df['year'] == 1].iloc[0] if 1 in history_df['year'].values else None
    end_year_data = history_df[history_df['year'] == current_year].iloc[0] if current_year in history_df['year'].values else None
    
    if start_year_data is not None and end_year_data is not None:
        # GDP growth over time
        metrics['gdp_growth'] = ((end_year_data.get('Yk_Index', 100) / start_year_data.get('Yk_Index', 100)) - 1) * 100
        
        # Average inflation rate
        metrics['avg_inflation'] = history_df['PI'].mean() if 'PI' in history_df else None
        
        # Average unemployment rate
        metrics['avg_unemployment'] = history_df['Unemployment'].mean() if 'Unemployment' in history_df else None
        
        # Debt-to-GDP ratio change
        metrics['debt_gdp_change'] = end_year_data.get('GD_GDP', 0) - start_year_data.get('GD_GDP', 0)
        
        # Total cards played
        total_cards = 0
        card_counts = {}
        for cards in history_df['played_cards'].values:
            if isinstance(cards, list):
                total_cards += len(cards)
                for card in cards:
                    card_counts[card] = card_counts.get(card, 0) + 1
        
        metrics['total_cards_played'] = total_cards
        metrics['card_counts'] = card_counts
        
        # Most used card type (Fiscal or Monetary)
        fiscal_count = 0
        monetary_count = 0
        for card in card_counts:
            card_type = POLICY_CARDS.get(card, {}).get('type')
            if card_type == 'Fiscal':
                fiscal_count += card_counts[card]
            elif card_type == 'Monetary':
                monetary_count += card_counts[card]
        
        metrics['fiscal_count'] = fiscal_count
        metrics['monetary_count'] = monetary_count
        metrics['most_used_type'] = 'Fiscal' if fiscal_count > monetary_count else 'Monetary' if monetary_count > fiscal_count else 'Equal'
    
    return metrics


def create_card_effect_comparison_chart(actual_data, counterfactual_data, metric, title, y_axis_title, y_format):
    """Creates a comparison chart between actual and counterfactual data."""
    # Combine the data
    actual_df = pd.DataFrame(actual_data)
    counterfactual_df = pd.DataFrame(counterfactual_data)
    
    # Keep only year and the metric
    actual_df = actual_df[['year', metric]].copy()
    counterfactual_df = counterfactual_df[['year', metric]].copy()
    
    # Add a scenario column
    actual_df['scenario'] = 'Actual'
    counterfactual_df['scenario'] = 'Without Selected Cards'
    
    # Combine the data
    combined_df = pd.concat([actual_df, counterfactual_df])
    
    # Convert to percentage for appropriate metrics
    if y_format.endswith('%'):
        combined_df[metric] = combined_df[metric] / 100.0
    
    # Create the chart
    chart = alt.Chart(combined_df).mark_line(point=True).encode(
        x=alt.X('year:Q', axis=alt.Axis(title='Year', format='d')),
        y=alt.Y(f'{metric}:Q', axis=alt.Axis(title=y_axis_title, format=y_format.replace('%', ''))),
        color=alt.Color('scenario:N', scale=alt.Scale(
            domain=['Actual', 'Without Selected Cards'],
            range=['#1FB25A', '#FF6347']  # Green for actual, Tomato for counterfactual
        )),
        tooltip=[
            alt.Tooltip('year:Q', title='Year'),
            alt.Tooltip(f'{metric}:Q', title=y_axis_title, format=y_format.replace('%', '')),
            alt.Tooltip('scenario:N', title='Scenario')
        ]
    ).properties(
        title=title,
        width=600,
        height=300
    ).interactive()
    
    return chart


def display_game_over_screen():
    """Renders the Game Over screen with a summary of the game."""
    st.header("Game Over - Economic Summary")
    
    # Get current year from session state
    current_year = st.session_state.current_year
    history = st.session_state.history
    
    # Extract KPI information
    if history:
        # Extract metrics for summary
        metrics = get_history_metrics(history, current_year)
        
        # Display summary stats in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("GDP Growth", f"{metrics.get('gdp_growth', 0):.1f}%", delta=None)
        
        with col2:
            st.metric("Avg. Inflation", f"{metrics.get('avg_inflation', 0):.1f}%", delta=None)
        
        with col3:
            st.metric("Avg. Unemployment", f"{metrics.get('avg_unemployment', 0):.1f}%", delta=None)
        
        with col4:
            debt_gdp_change = metrics.get('debt_gdp_change', 0)
            delta = f"{debt_gdp_change:.1f}%" if debt_gdp_change is not None else None
            delta_color = "inverse" if debt_gdp_change is not None else None
            st.metric("Debt-to-GDP Change", delta, delta_color=delta_color)
        
        # Display KPI charts
        st.subheader("Economic Performance Over Time")
        tab1, tab2, tab3, tab4 = st.tabs(["GDP", "Inflation", "Unemployment", "Debt-to-GDP"])
        
        with tab1:
            gdp_chart = create_kpi_plot('Yk_Index', 'GDP Index (Year 1 = 100)')
            if gdp_chart:
                st.altair_chart(gdp_chart, use_container_width=True)
            else:
                st.write("GDP data not available.")
        
        with tab2:
            inflation_chart = create_kpi_plot('PI', 'Inflation Rate (%)')
            if inflation_chart:
                st.altair_chart(inflation_chart, use_container_width=True)
            else:
                st.write("Inflation data not available.")
        
        with tab3:
            unemployment_chart = create_kpi_plot('Unemployment', 'Unemployment Rate (%)')
            if unemployment_chart:
                st.altair_chart(unemployment_chart, use_container_width=True)
            else:
                st.write("Unemployment data not available.")
        
        with tab4:
            debt_chart = create_kpi_plot('GD_GDP', 'Debt-to-GDP Ratio (%)')
            if debt_chart:
                st.altair_chart(debt_chart, use_container_width=True)
            else:
                st.write("Debt-to-GDP data not available.")
        
        # Card Analysis Section
        st.subheader("Policy Card Analysis")
        
        # Get all years where cards were played
        history_df = pd.DataFrame(history)
        years_with_cards = {}
        for _, row in history_df.iterrows():
            year = row.get('year')
            cards = row.get('played_cards', [])
            if year and isinstance(cards, list) and len(cards) > 0:
                years_with_cards[year] = cards
        
        # Create a selection box for the year
        if years_with_cards:
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_year = st.selectbox(
                    "Select Year to Analyze",
                    options=sorted(years_with_cards.keys()),
                    format_func=lambda x: f"Year {x}: {', '.join(years_with_cards[x])}"
                )
            
            # Get the cards played in that year
            cards_in_year = years_with_cards.get(selected_year, [])
            
            # Create multiselect for the cards
            with col2:
                selected_cards = st.multiselect(
                    "Select Cards to Analyze Impact",
                    options=cards_in_year,
                    default=cards_in_year,
                    help="Select cards to see the economy's trajectory without them"
                )
            
            # Button to run counterfactual simulation
            if selected_cards and st.button("Analyze Card Effects"):
                with st.spinner("Running counterfactual simulation..."):
                    # Run the counterfactual simulation
                    counterfactual_results = run_counterfactual_simulation(selected_year, selected_cards)
                    
                    if counterfactual_results:
                        st.success(f"Analysis complete! Showing 10-year actual vs. what would have happened without the selected card(s) in Year {selected_year}.")
                        
                        # Create comparison charts
                        st.subheader(f"Impact of {'Card' if len(selected_cards) == 1 else 'Cards'}: {', '.join(selected_cards)}")
                        
                        # Filter the actual history to match counterfactual years
                        counterfactual_years = [result.get('year') for result in counterfactual_results]
                        actual_data = [entry for entry in history if entry.get('year') in counterfactual_years]
                        
                        # Create tabs for different metrics
                        tab1, tab2, tab3, tab4 = st.tabs(["GDP Impact", "Inflation Impact", "Unemployment Impact", "Debt-to-GDP Impact"])
                        
                        with tab1:
                            gdp_chart = create_card_effect_comparison_chart(
                                actual_data, counterfactual_results, 'Yk_Index', 
                                f"GDP Trajectory With vs. Without {'Card' if len(selected_cards) == 1 else 'Cards'}", 
                                'GDP Index (Year 1 = 100)', '.1f'
                            )
                            st.altair_chart(gdp_chart, use_container_width=True)
                        
                        with tab2:
                            inflation_chart = create_card_effect_comparison_chart(
                                actual_data, counterfactual_results, 'PI', 
                                f"Inflation Trajectory With vs. Without {'Card' if len(selected_cards) == 1 else 'Cards'}", 
                                'Inflation Rate', '.1%'
                            )
                            st.altair_chart(inflation_chart, use_container_width=True)
                        
                        with tab3:
                            unemployment_chart = create_card_effect_comparison_chart(
                                actual_data, counterfactual_results, 'Unemployment', 
                                f"Unemployment Trajectory With vs. Without {'Card' if len(selected_cards) == 1 else 'Cards'}", 
                                'Unemployment Rate', '.1%'
                            )
                            st.altair_chart(unemployment_chart, use_container_width=True)
                        
                        with tab4:
                            debt_chart = create_card_effect_comparison_chart(
                                actual_data, counterfactual_results, 'GD_GDP', 
                                f"Debt-to-GDP Trajectory With vs. Without {'Card' if len(selected_cards) == 1 else 'Cards'}", 
                                'Debt-to-GDP Ratio', '.1%'
                            )
                            st.altair_chart(debt_chart, use_container_width=True)
                        
                        # Summary of the impact
                        st.subheader("Impact Summary")
                        
                        # Calculate differences in the final year
                        final_year = max(counterfactual_years)
                        actual_final = next((entry for entry in actual_data if entry.get('year') == final_year), None)
                        counterfactual_final = next((entry for entry in counterfactual_results if entry.get('year') == final_year), None)
                        
                        if actual_final and counterfactual_final:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            # GDP difference
                            gdp_diff = actual_final.get('Yk_Index', 0) - counterfactual_final.get('Yk_Index', 0)
                            gdp_diff_pct = (gdp_diff / counterfactual_final.get('Yk_Index', 100)) * 100
                            with col1:
                                st.metric(
                                    "Final GDP Impact", 
                                    f"{actual_final.get('Yk_Index', 0):.1f}", 
                                    f"{gdp_diff_pct:+.1f}% vs. without",
                                    delta_color="normal" if gdp_diff > 0 else "inverse"
                                )
                            
                            # Inflation difference
                            infl_diff = actual_final.get('PI', 0) - counterfactual_final.get('PI', 0)
                            with col2:
                                st.metric(
                                    "Final Inflation Impact", 
                                    f"{actual_final.get('PI', 0):.1f}%", 
                                    f"{infl_diff:+.1f}pp vs. without",
                                    delta_color="inverse" if infl_diff > 0 else "normal"
                                )
                            
                            # Unemployment difference
                            unemp_diff = actual_final.get('Unemployment', 0) - counterfactual_final.get('Unemployment', 0)
                            with col3:
                                st.metric(
                                    "Final Unemployment Impact", 
                                    f"{actual_final.get('Unemployment', 0):.1f}%", 
                                    f"{unemp_diff:+.1f}pp vs. without",
                                    delta_color="inverse" if unemp_diff > 0 else "normal"
                                )
                            
                            # Debt-to-GDP difference
                            debt_diff = actual_final.get('GD_GDP', 0) - counterfactual_final.get('GD_GDP', 0)
                            with col4:
                                st.metric(
                                    "Final Debt-to-GDP Impact", 
                                    f"{actual_final.get('GD_GDP', 0):.1f}%", 
                                    f"{debt_diff:+.1f}pp vs. without",
                                    delta_color="inverse" if debt_diff > 0 else "normal"
                                )
                    else:
                        st.error("Failed to run counterfactual simulation. Please check the logs for details.")
        else:
            st.info("No policy cards were played during the game.")
        
        # Final data display
        with st.expander("View Final Economic State Details"):
            if st.session_state.sfc_model_object and hasattr(st.session_state.sfc_model_object, 'solutions') and st.session_state.sfc_model_object.solutions:
                final_state = st.session_state.sfc_model_object.solutions[-1]
                prev_state = st.session_state.sfc_model_object.solutions[-2] if len(st.session_state.sfc_model_object.solutions) > 1 else None
                
                display_balance_sheet_matrix(final_state)
                st.divider()
                if prev_state:
                    display_revaluation_matrix(final_state, prev_state)
                    st.divider()
                    display_transaction_flow_matrix(final_state, prev_state)
                else:
                    st.caption("Additional matrices require previous period data.")
            else:
                st.caption("Final state details not available.")
    else:
        st.error("No simulation history found.")
    
    # Placeholder for sharing results
    st.divider()
    st.subheader("Share Your Results")
    
    # Create a shareable message
    if 'metrics' in locals() and metrics:
        share_text = f"In my SFC Economic Simulator game, I achieved {metrics.get('gdp_growth', 0):.1f}% GDP growth with {metrics.get('avg_inflation', 0):.1f}% avg inflation and {metrics.get('avg_unemployment', 0):.1f}% avg unemployment over {current_year} years!"
        twitter_url = f"https://twitter.com/intent/tweet?text={quote(share_text)}&hashtags=SFCGame,EconomicSimulation"
        
        st.markdown(f"""
        <a href="{twitter_url}" target="_blank" style="text-decoration:none;">
            <div style="display:inline-block; background-color:#1DA1F2; color:white; padding:8px 16px; border-radius:4px; margin-right:10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-twitter" viewBox="0 0 16 16" style="vertical-align:middle; margin-right:5px;">
                    <path d="M5.026 15c6.038 0 9.341-5.003 9.341-9.334 0-.14 0-.282-.006-.422A6.685 6.685 0 0 0 16 3.542a6.658 6.658 0 0 1-1.889.518 3.301 3.301 0 0 0 1.447-1.817 6.533 6.533 0 0 1-2.087.793A3.286 3.286 0 0 0 7.875 6.03a9.325 9.325 0 0 1-6.767-3.429 3.289 3.289 0 0 0 1.018 4.382A3.323 3.323 0 0 1 .64 6.575v.045a3.288 3.288 0 0 0 2.632 3.218 3.203 3.203 0 0 1-.865.115 3.23 3.23 0 0 1-.614-.057 3.283 3.283 0 0 0 3.067 2.277A6.588 6.588 0 0 1 .78 13.58a6.32 6.32 0 0 1-.78-.045A9.344 9.344 0 0 0 5.026 15z"/>
                </svg>
                Share on Twitter
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    # Button to start a new game
    if st.button("Start New Game", type="primary"):
        st.session_state.action_trigger = ("new_game", None)
        st.rerun()