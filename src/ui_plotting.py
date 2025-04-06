# src/ui_plotting.py
"""Handles the creation of KPI plots using Altair."""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import altair as alt

# Import project modules
# Import get_sparkline_data locally within the function to avoid potential circular dependency issues
# if ui_sidebar also needs plotting functions in the future.

def create_kpi_plot(metric_key, y_axis_title):
    """Creates an Altair chart for a Key Performance Indicator."""
    logging.debug(f"Entering create_kpi_plot for metric: {metric_key}")
    # Import get_sparkline_data locally to avoid circular dependency if moved later
    from src.ui_sidebar import get_sparkline_data
    # Fetch full history starting from Year 1 for KPI plots
    plot_df = get_sparkline_data(metric_key, st.session_state.current_year, fetch_full_history=True)
    logging.debug(f"create_kpi_plot({metric_key}) - plot_df from get_sparkline_data:\n{plot_df}")
    if plot_df is not None and not plot_df.empty:
        # Define colors based on metric_key
        if metric_key == 'Yk_Index': plot_color = "#1FB25A" # Green
        elif metric_key == 'PI': plot_color = "#000000" # Black
        elif metric_key == 'Unemployment': plot_color = "#0072BB" # Blue
        elif metric_key == 'GD_GDP': plot_color = "#555555" # Dark Grey
        else: plot_color = "#1FB25A" # Default Green

        # Determine axis format
        y_axis_format = ".1f" # Default format for index
        if metric_key in ['PI', 'Unemployment', 'GD_GDP']:
            y_axis_format = ".1%" # Percentage format

        # Correct data for percentage scaling in Altair
        plot_df_corrected = plot_df.copy()
        if y_axis_format.endswith('%'):
            plot_df_corrected[metric_key] = plot_df_corrected[metric_key] / 100.0

        # Base chart
        base = alt.Chart(plot_df_corrected.reset_index()).encode(
            x=alt.X('Year:Q',
                    axis=alt.Axis(orient='bottom', title='Year', format='d', labelAngle=-45, grid=False),
                    scale=alt.Scale(domain=[plot_df.index.min(), plot_df.index.max()], paddingOuter=0.1)
                   ),
            tooltip=[
                alt.Tooltip('Year:O', title='Simulation Year'),
                alt.Tooltip(f'{metric_key}:Q', format=y_axis_format, title=y_axis_title)
            ]
        )

        # Handle single data point or line chart
        if len(plot_df_corrected) == 1:
            single_value = plot_df_corrected[metric_key].iloc[0]
            padding = abs(single_value) * 0.15 if not np.isclose(single_value, 0) else 0.01
            y_domain = [single_value - padding, single_value + padding]
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']:
                 y_domain[0] = max(0, y_domain[0])
            y_axis_scale = alt.Scale(domain=y_domain, zero=False)
            chart = base.mark_point(size=100, filled=True, color=plot_color).encode(
                 y=alt.Y(f'{metric_key}:Q',
                         axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                         scale=y_axis_scale)
            )
        else:
            min_val = plot_df_corrected[metric_key].min()
            max_val = plot_df_corrected[metric_key].max()
            data_range = max_val - min_val
            padding = data_range * 0.15 if not np.isclose(data_range, 0) else (abs(max_val) * 0.15 if not np.isclose(max_val, 0) else 0.01)
            y_domain = [min_val - padding, max_val + padding]
            if metric_key in ['Unemployment', 'GD_GDP', 'Yk_Index']:
                 y_domain[0] = max(0, y_domain[0])
            y_axis_scale = alt.Scale(domain=y_domain, zero=False)

            line = base.mark_line(
                point=alt.OverlayMarkDef(color=plot_color), color=plot_color, strokeWidth=2
            ).encode(
                y=alt.Y(f'{metric_key}:Q',
                        axis=alt.Axis(title=y_axis_title, format=y_axis_format, grid=True, titlePadding=10),
                        scale=y_axis_scale)
            )
            last_point_df_corrected = plot_df_corrected.reset_index().iloc[[-1]]
            labels = alt.Chart(last_point_df_corrected).mark_text(
                align='left', baseline='middle', dx=7, fontSize=11
            ).encode(
                x=alt.X('Year:O'), y=alt.Y(f'{metric_key}:Q'),
                text=alt.Text(f'{metric_key}:Q', format=y_axis_format),
                color=alt.value(plot_color)
            )
            chart_layers = [line, labels]
            if y_domain[0] <= 0 <= y_domain[1]:
                 zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                     color='grey', strokeDash=[2,2], size=1
                 ).encode(y='y')
                 chart_layers.append(zero_line)
            chart = alt.layer(*chart_layers)

        # Common Chart Configuration
        chart = chart.properties(
            height=200,
            padding={"top": 10, "right": 20, "bottom": 10, "left": 20}
        ).configure_view(
            fill=None, stroke='#cccccc'
        ).configure_axis(
            labelFont='Lato', titleFont='Oswald', titleFontSize=12, labelFontSize=11
        ).interactive()
        return chart
    else:
        logging.warning(f"create_kpi_plot({metric_key}) - Returning None because plot_df is None or empty.")
        return None