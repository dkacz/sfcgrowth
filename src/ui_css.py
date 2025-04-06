# src/ui_css.py
"""Handles custom CSS injection for the Streamlit app."""

import streamlit as st

def display_css():
    """Injects custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* --- Monopoly Theme --- */
        /* --- Fonts --- */
        @import url('https://fonts.googleapis.com/css2?family=Passion+One:wght@700&family=Oswald:wght@700&family=Lato&display=swap');
        /* --- Base Styles --- */
        html, body, [class*="st-"], button, input, textarea, select {
            font-family: 'Lato', sans-serif !important;
            color: #000000 !important; /* Black text */
        }
        .stApp {
            background-color: #F7F1E3 !important; /* Cream background */
        }
        [data-testid="stSidebar"] {
            background-color: #e9e4d9 !important; /* Slightly darker cream for sidebar */
            border-right: 2px solid #000000 !important;
        }
        /* Reduce default top padding in sidebar */
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem !important;
            margin-top: 0rem !important; /* Added to remove potential margin */
        }
        /* Hide default Streamlit header */
        [data-testid="stHeader"] {
            background-color: #F7F1E3 !important; /* Match background */
            box-shadow: none !important;
            border-bottom: none !important;
            height: 0px !important; /* Attempt to hide */
            visibility: hidden !important;
        }
        /* --- Title Area --- */
        .title-container {
            padding: 0.2rem 1rem; /* Reduced vertical padding */
            margin-bottom: 2rem;
            border-radius: 5px;
            display: inline-block; /* Fit content width */
            margin-left: auto; /* Center align block */
            margin-right: auto; /* Center align block */
            text-align: center; /* Center text inside */
        }
        .title-container h1 {
            font-family: 'Passion One', sans-serif !important; /* Monopoly-like font */
            color: #FFFFFF !important; /* White text */
            text-align: center;
            margin-bottom: 0 !important;
            font-size: 2.5em !important; /* Adjust size as needed */
            line-height: 1.2 !important; /* Adjust line height */
        }
        /* --- Other Headers --- */
        h2, h3 {
            font-family: 'Oswald', sans-serif !important; /* Bold sans-serif */
            color: #000000 !important;
            margin-bottom: 1rem !important;
            border-bottom: 1px solid #000000 !important; /* Underline headers */
            padding-bottom: 0.25rem;
        }
        /* --- Character Selection (Table Layout) --- */
        .character-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 10px 0; /* Add horizontal spacing between cells */
            /* table-layout: fixed; */ /* Removed to allow natural column sizing */
        }
        .character-table td {
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 1rem;
            background-color: rgba(255, 255, 255, 0.5);
            vertical-align: top;
            text-align: center;
            transition: border-color 0.3s ease-in-out, background-color 0.3s ease-in-out;
            height: 100%; /* Try to make cells fill height - might not work perfectly */
        }
        .character-table td.selected-character {
             border-color: #DAA520 !important; /* Gold border */
             background-color: rgba(250, 250, 210, 0.8) !important; /* Light yellow tint */
        }
        .character-table h5 { /* Target name heading */
             margin-bottom: 0.5rem !important; /* Adjusted gap below name */
             font-size: 1.2em !important; /* Increased font size */
             line-height: 1.2 !important; /* Adjust line height */
        }
        .character-table img {
             max-width: 140px; /* Reset image size */
             height: auto;
             margin-bottom: 0.5rem;
        }
        .character-table ul {
            list-style-type: none;
            padding-left: 0;
            text-align: left;
            margin-top: 0.5rem;
        }
         .character-table li {
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
        }
        /* Sidebar headers */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
             font-family: 'Oswald', sans-serif !important;
             color: #000000 !important;
             border-bottom: none !important; /* No underline in sidebar */
        }
        /* Objective List Styling */
        .character-column ul { /* Keep this class for now if needed elsewhere, or remove */
            list-style-type: none; /* Remove default bullets */
            padding-left: 5px; /* Adjust left padding */
            margin-top: 0.5rem; /* Add some space above the list */
            text-align: left; /* Align text to the left */
            padding-bottom: 0.5rem; /* Add some padding below objectives */
        }
        .character-column li {
            margin-bottom: 0.3rem; /* Space between objectives */
            display: flex; /* Use flexbox for alignment */
            align-items: center; /* Vertically align icon and text */
        }
        /* Make description take available space, pushing objectives down */
        .character-column .description-wrapper { /* Target the new wrapper div */
            flex-grow: 1; /* Allow description wrapper to grow */
            margin-bottom: 0.5rem; /* Add space below description */
        }
        /* --- Dashboard Metrics (Sidebar) --- */
        .stMetric {
            background-color: #FFFFFF !important; /* White background for metrics */
            border: 1px solid #000000 !important;
            border-radius: 4px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stMetric > label { /* Label */
            font-family: 'Oswald', sans-serif !important;
            color: #000000 !important;
        }
        .stMetric > div > div > div { /* Value */
            font-family: 'Lato', sans-serif !important;
            font-weight: bold;
            color: #000000 !important;
        }
        .stMetric > div > div > p { /* Delta */
             font-family: 'Lato', sans-serif !important;
             color: #555555 !important; /* Grey delta */
        }
        /* Icon Styling for Sidebar */
        .metric-icon {
            height: 1.5em; /* Adjust size */
            width: 1.5em;
            display: block;
            margin: 0.2em auto 0 auto; /* Center and add some top margin */
        }
        /* --- Cards --- */
        .card-container {
            border: 1px solid #000000;
            border-radius: 8px;
            margin-bottom: 15px;
            background-color: #FAFAD2; /* Parchment background */
            height: 300px; /* Increased height for cards */
            display: flex;
            flex-direction: column;
            padding: 0; /* Remove padding from container */
            overflow: hidden;
            transition: border 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        }
        .card-container.selected {
            border: 3px solid #DAA520 !important;
            box-shadow: 0 0 10px 2px #DAA520 !important;
        }
        .card-top-bar {
            min-height: 3.5em;
            margin-bottom: 10px;
            padding: 6px 8px; /* Reduced padding */
            display: flex;
            align-items: center;
            flex-shrink: 0;
            color: #FFFFFF !important; /* White text for title */
        }
        .card-top-bar.monetary { background-color: #0072BB; } /* Monopoly Blue */
        .card-top-bar.fiscal { background-color: #A0522D; } /* Sienna Brown for Fiscal */
        .card-top-bar.default { background-color: #8B4513; } /* Brown */
        .card-title {
            font-family: 'Oswald', sans-serif !important;
            font-weight: bold;
            font-size: 1.1em;
            text-align: left;
            margin-bottom: 0;
            margin-left: 0.5em; /* Space after stance icon */
            line-height: 1.3;
            word-wrap: break-word;
            overflow-wrap: break-word;
            color: inherit; /* Inherit color from parent (.card-top-bar) */
        }
        .card-icon {
            height: 1.1em;
            width: 1.1em;
            vertical-align: middle;
            filter: brightness(0) invert(1);
            margin-right: 0.4em;
            flex-shrink: 0;
        }
        .stance-icon {
            height: 1em;
            width: 1em;
            vertical-align: middle;
            filter: brightness(0) invert(1);
            margin-left: 0.5em;
            flex-shrink: 0;
        }
        .card-main-content {
            padding: 0 10px 8px 10px; /* Reduced padding */
            flex-grow: 1; /* Allow content area to grow */
            overflow-y: auto; /* Allow scrolling if needed */
            min-height: 0; /* Allow shrinking for flexbox */
            display: flex;
            flex-direction: column;
            justify-content: space-between; /* Push button to bottom */
        }
        .card-desc {
            font-family: 'Lato', sans-serif !important;
            font-size: 0.9em;
            color: #000000 !important;
            margin-bottom: 10px;
        }
        .card-main-content .stExpander {
            padding: 0 !important;
            margin-top: auto; /* Push expander towards bottom before button */
            margin-bottom: 5px; /* Space before button */
        }
         .card-main-content .stExpander p { /* Style caption inside expander */
            font-size: 0.8em;
            color: #555555;
        }
        .card-stance-bar {
            height: 16px; /* Increased height */
            width: 100%;
            margin-top: auto; /* Push to bottom */
            margin-bottom: 5px; /* Space before button */
            border-radius: 2px;
            text-align: center;
            color: white;
            font-size: 0.8em; /* Slightly larger text */
            line-height: 16px; /* Match height for vertical centering */
            font-weight: bold;
        }
        .expansionary-bar { background-color: #4CAF50; } /* Green */
        .contractionary-bar { background-color: #f44336; } /* Red */
        /* --- Event Cards --- */
        .event-card {
            border: 1px solid #cccccc; /* Lighter border than policy cards */
            border-radius: 5px;
            padding: 10px 15px; /* Add padding */
            margin-bottom: 10px;
            background-color: #ffffff; /* White background */
        }
        .event-card-title {
            font-family: 'Oswald', sans-serif !important;
            font-weight: bold;
            font-size: 1.1em;
            color: #000000 !important;
            margin-bottom: 5px;
        }
        .event-card-desc {
            font-family: 'Lato', sans-serif !important;
            font-size: 0.95em;
            color: #333333 !important;
            margin-bottom: 8px;
        }
        .event-card .stExpander {
            border: none !important;
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }
         .event-card .stExpander p { /* Style caption inside expander */
            font-size: 0.85em;
            color: #555555;
        }
        /* --- Buttons --- */
        .stButton > button {
            font-family: 'Oswald', sans-serif !important;
            border: 1px solid #000000 !important;
            border-radius: 3px !important;
            background-color: #FFFFFF !important;
            color: #000000 !important;
            width: 100%;
            margin-top: 10px; /* Space above button */
            padding: 0.5rem 1rem !important; /* Adjust padding */
            transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out, transform 0.1s ease-in-out; /* Smooth transition including transform */
            flex-shrink: 0; /* Prevent button from shrinking */
        }
        .stButton > button:hover {
            background-color: #cccccc !important; /* Slightly darker grey hover */
            color: #000000 !important;
            border-color: #000000 !important;
            transform: scale(1.02); /* Slight scale up on hover */
        }
         .stButton > button[kind="primary"] { /* Selected button */
            background-color: #aaaaaa !important; /* Lighter grey for selected */
            color: #000000 !important; /* Black text for selected */
            border-color: #000000 !important;
        }
        /* --- Dividers --- */
        hr {
            border-top: 1px solid #000000 !important;
            margin-top: 1rem !important;
            margin-bottom: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)