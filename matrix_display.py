import streamlit as st
import pandas as pd
import numpy as np

# --- Helper Function (Copied from growth_model_streamlit.py) ---
# Note: format_percent remains in main file as it's used by dashboard too.
def format_value(value, include_sign=False):
    """Formats a number for display, handling large/small values and optional sign."""
    # Check for NaN or infinite values
    if not np.isfinite(value):
        return "N/A"
    if abs(value) < 0.01 and value != 0: # Use higher precision for very small non-zero numbers
        formatted_val = f"{value:.3f}"
    elif abs(value) >= 1000:
        formatted_val = f"{value:,.0f}"
    else:
        formatted_val = f"{value:.2f}" # Default to 2 decimal places otherwise

    if include_sign:
        sign = "+" if value > 0 else "-" if value < 0 else ""
        # Avoid double negative sign
        if formatted_val.startswith('-'):
             formatted_val = formatted_val[1:]
        return f"{sign}{formatted_val}"
    else:
        return formatted_val

# --- Matrix Display Functions (Copied from growth_model_streamlit.py) ---

def display_balance_sheet_matrix(solution):
    """Displays the balance sheet matrix for a given solution state."""
    st.markdown("#### Table 11.1: Balance Sheet")
    st.caption("Assets (+) and liabilities (-) of each sector.")

    # Extract values
    IN_val = round(solution.get('IN', 0.0), 0)
    K_val = round(solution.get('K', 0.0), 0)
    Hh_val = round(solution.get('Hhd', 0.0), 0)
    H_val = round(solution.get('Hs', 0.0), 0)
    Hb_val = round(solution.get('Hbd', 0.0), 0)
    M_val = round(solution.get('Md', 0.0), 0)
    Bh_val = round(solution.get('Bhd', 0.0), 0)
    B_val = round(solution.get('Bs', 0.0), 0)
    Bcb_val = round(solution.get('Bcbd', 0.0), 0)
    Bb_val = round(solution.get('Bbd', 0.0), 0)
    BL_val = round(solution.get('BLd', 0.0), 0)
    Pbl_val = solution.get('Pbl', 1.0) # Avoid division by zero if Pbl is 0
    BL_Pbl_val = round(BL_val * Pbl_val, 0) if Pbl_val != 0 else 0
    Lh_val = round(solution.get('Lhd', 0.0), 0)
    Lf_val = round(solution.get('Lfd', 0.0), 0)
    L_val = round(solution.get('Lfs', 0.0) + solution.get('Lhs', 0.0), 0)
    e_val = round(solution.get('Ekd', 0.0), 0)
    Pe_val = round(solution.get('Pe', 0.0), 0)
    e_Pe_val = round(e_val * Pe_val, 0)
    OFb_val = round(solution.get('OFb', 0.0), 0)

    # Calculate net worth
    h_assets = Hh_val + M_val + Bh_val + BL_Pbl_val + e_Pe_val + OFb_val
    h_liabilities = Lh_val
    h_net_worth = h_assets - h_liabilities
    f_assets = IN_val + K_val
    f_liabilities = Lf_val + e_Pe_val
    f_net_worth = f_assets - f_liabilities
    # Government net worth is negative of its liabilities (excluding HPM held by CB)
    g_liabilities = (B_val - Bcb_val) + BL_Pbl_val # Bills held outside CB + Bonds
    g_net_worth = -g_liabilities
    total_real_assets = IN_val + K_val

    # Define index and columns
    index = [
        "Inventories", "Fixed capital", "HPM", "Money", "Bills",
        "Bonds", "Loans", "Equities", "Bank capital", "Balance (Net Worth)", "Σ"
    ]
    columns = ["Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]

    # Create data array
    data_array = [
        # Households, Firms, Govt., CB, Banks, Σ
        ["", format_value(IN_val, True), "", "", "", format_value(IN_val, True)],                     # Inventories
        ["", format_value(K_val, True), "", "", "", format_value(K_val, True)],                      # Fixed capital
        [format_value(Hh_val, True), "", "", format_value(-H_val, True), format_value(Hb_val, True), "0"],      # HPM
        [format_value(M_val, True), "", "", "", format_value(-M_val, True), "0"],                      # Money
        [format_value(Bh_val, True), "", format_value(-(B_val-Bcb_val), True), format_value(Bcb_val, True), format_value(Bb_val, True), "0"], # Bills (Govt only shows net bills held outside CB)
        [format_value(BL_Pbl_val, True), "", format_value(-BL_Pbl_val, True), "", "", "0"],             # Bonds
        [format_value(-Lh_val, True), format_value(-Lf_val, True), "", "", format_value(L_val, True), "0"],      # Loans
        [format_value(e_Pe_val, True), format_value(-e_Pe_val, True), "", "", "", "0"],                 # Equities
        [format_value(OFb_val, True), "", "", "", format_value(-OFb_val, True), "0"],                 # Bank capital
        [format_value(-h_net_worth, True), format_value(-f_net_worth, True), format_value(g_net_worth, True), "0", "0", format_value(-total_real_assets, True)], # Balance
        ["0", "0", "0", "0", "0", "0"]                                              # Sum
    ]

    df = pd.DataFrame(data_array, index=index, columns=columns)
    st.dataframe(df)


def display_revaluation_matrix(solution, prev_solution):
    """Displays the revaluation matrix comparing solution to prev_solution."""
    st.markdown("#### Table 11.2: Revaluation Account")
    st.caption("Capital gains (+) or losses (-) due to changes in asset prices.")

    # Extract and calculate values
    Pbl_curr = solution.get('Pbl', 0.0)
    Pbl_prev = prev_solution.get('Pbl', 0.0)
    delta_Pbl = Pbl_curr - Pbl_prev
    BLd_prev = prev_solution.get('BLd', 0.0) # Use previous holding for gain calc

    Pe_curr = solution.get('Pe', 0.0)
    Pe_prev = prev_solution.get('Pe', 0.0)
    delta_Pe = Pe_curr - Pe_prev
    Ekd_prev = prev_solution.get('Ekd', 0.0) # Use previous holding
    Eks_prev = prev_solution.get('Eks', 0.0) # Use previous holding

    bonds_hl = BLd_prev * delta_Pbl
    equity_hl = Ekd_prev * delta_Pe
    total_h = bonds_hl + equity_hl
    equity_fl = -Eks_prev * delta_Pe # Loss for firms is negative of household gain on same shares
    bonds_gl = -BLd_prev * delta_Pbl # Loss for govt is negative of household gain on same bonds

    # Define index and columns
    index = ["Bonds", "Equities", "Bank equity", "Fixed capital", "Balance", "Σ"]
    columns = ["", "Households", "Firms", "Govt.", "Central bank", "Banks", "Σ"]

    # Format data
    data_array = [
        ["Bonds", format_value(bonds_hl, True), "", format_value(bonds_gl, True), "", "", "0"],
        ["Equities", format_value(equity_hl, True), format_value(equity_fl, True), "", "", "", "0"],
        ["Bank equity", "0", "", "", "", "0", "0"], # Not modeled here
        ["Fixed capital", "", "0", "", "", "", "0"], # Not modeled here
        ["Balance", format_value(-total_h, True), format_value(-equity_fl, True), format_value(-bonds_gl, True), "0", "0", "0"], # Balance
        ["Σ", "0", "0", "0", "0", "0", "0"] # Sum
    ]

    df = pd.DataFrame(data_array, columns=columns).set_index(columns[0])
    st.dataframe(df)


def display_transaction_flow_matrix(solution, prev_solution):
    """Displays the transaction flow matrix comparing solution to prev_solution."""
    st.markdown("#### Table 11.3: Transaction Flow Matrix")
    st.caption("Transactions between sectors for the period.")

    # --- Extract values ---
    C_val = round(solution.get('CONS', 0.0), 0)
    G_val = round(solution.get('G', 0.0), 0)
    I_val = round(solution.get('INV', 0.0), 0)
    WB_val = round(solution.get('WB', 0.0), 0)
    T_val = round(solution.get('T', 0.0), 0)
    r_val = prev_solution.get('Rb', 0.0) # Interest rates from start of period
    rm_val = prev_solution.get('Rm', 0.0)
    rl_val = prev_solution.get('Rl', 0.0)
    Md_prev = prev_solution.get('Md', 0.0)
    Bhd_prev = prev_solution.get('Bhd', 0.0)
    Bbd_prev = prev_solution.get('Bbd', 0.0)
    Bcbd_prev = prev_solution.get('Bcbd', 0.0)
    Bs_prev = prev_solution.get('Bs', 0.0) # Total bills supply
    Lhd_prev = prev_solution.get('Lhd', 0.0)
    Lfd_prev = prev_solution.get('Lfd', 0.0)
    IN_prev = prev_solution.get('IN', 0.0)
    r_Bhd_val = round(r_val * Bhd_prev, 0)
    r_Bbd_val = round(r_val * Bbd_prev, 0)
    r_Bcbd_val = round(r_val * Bcbd_prev, 0)
    # Govt interest payment is on total bills supplied (excl CB holdings?) - Model uses Bbs(-1)+Bhs(-1)
    r_Bs_paid_val = round(r_val * (prev_solution.get('Bbs', 0.0) + prev_solution.get('Bhs', 0.0)), 0)
    rm_Md_val = round(rm_val * Md_prev, 0)
    rl_Lhd_val = round(rl_val * Lhd_prev, 0)
    rl_Lfd_val = round(rl_val * Lfd_prev, 0)
    InvFinCost_val = round(rl_val * IN_prev, 0) # Financing cost on previous inventories
    BL_prev = prev_solution.get('BLs', 0.0)
    # Coupon payment is based on stock of bonds at start of period (BLs(-1))
    coupons_val = round(BL_prev, 0) # Model uses BLs(-1) directly in YP and PSBR, representing coupon payment
    Ff_val = round(solution.get('Ff', 0.0), 0)
    Fb_val = round(solution.get('Fb', 0.0), 0)
    Fcb_val = round(solution.get('Fcb', 0.0), 0)
    FDf_val = round(solution.get('FDf', 0.0), 0)
    FDb_val = round(solution.get('FDb', 0.0), 0)
    FUf_val = round(solution.get('FUf', 0.0), 0)
    FUb_val = round(solution.get('FUb', 0.0), 0)
    delta_H_h_val = round(solution.get('Hhd', 0.0) - prev_solution.get('Hhd', 0.0), 0)
    delta_H_b_val = round(solution.get('Hbd', 0.0) - prev_solution.get('Hbd', 0.0), 0)
    delta_H_val = round(solution.get('Hs', 0.0) - prev_solution.get('Hs', 0.0), 0)
    delta_M_h_val = round(solution.get('Md', 0.0) - prev_solution.get('Md', 0.0), 0)
    delta_M_b_val = round(solution.get('Ms', 0.0) - prev_solution.get('Ms', 0.0), 0)
    delta_Bh_val = round(solution.get('Bhd', 0.0) - prev_solution.get('Bhd', 0.0), 0)
    delta_Bb_val = round(solution.get('Bbd', 0.0) - prev_solution.get('Bbd', 0.0), 0)
    delta_Bcb_val = round(solution.get('Bcbd', 0.0) - prev_solution.get('Bcbd', 0.0), 0)
    delta_B_val = round(solution.get('Bs', 0.0) - prev_solution.get('Bs', 0.0), 0) # Change in total supply
    delta_BL_val = round(solution.get('BLs', 0.0) - prev_solution.get('BLs', 0.0), 0)
    Pbl_val = solution.get('Pbl', 1.0) # Use current price for valuing flow
    delta_BL_Pbl_val = round(delta_BL_val * Pbl_val, 0) if Pbl_val != 0 else 0
    delta_Lh_val = round(solution.get('Lhd', 0.0) - prev_solution.get('Lhd', 0.0), 0)
    delta_Lf_val = round(solution.get('Lfd', 0.0) - prev_solution.get('Lfd', 0.0), 0)
    delta_L_val = round((solution.get('Lhs', 0.0) - prev_solution.get('Lhs', 0.0)) + (solution.get('Lfs', 0.0) - prev_solution.get('Lfs', 0.0)), 0)
    Pe_val = solution.get('Pe', 0.0) # Use current price
    delta_e_val = round(solution.get('Ekd', 0.0) - prev_solution.get('Ekd', 0.0), 0)
    delta_e_Pe_val = round(delta_e_val * Pe_val, 0)
    NPL_val = round(solution.get('NPL', 0.0), 0)
    delta_IN_val = round(solution.get('IN', 0.0) - prev_solution.get('IN', 0.0), 0)

    # --- Define Multi-Level Headers ---
    headers = pd.MultiIndex.from_tuples([
        ("", ""), ("Households", ""), ("Firms", "Current"), ("Firms", "Capital"),
        ("Govt.", ""), ("Central bank", "Current"), ("Central bank", "Capital"),
        ("Banks", "Current"), ("Banks", "Capital"), ("Σ", "")
    ], names=['Sector', 'Flow'])

    # --- Define Row Index ---
    index = [
        "Consumption", "Government expenditures", "Investment", "Inventory accumulation",
        "--- Income/Costs ---",
        "Wages", "Inventory financing cost", "Taxes", "Entrepreneurial Profits", "Bank profits", "Central bank profits",
        "--- Interest Flows ---",
        "Interest on bills", "Interest on deposits", "Interest on loans", "Bond coupon payments",
        "--- Change in Stocks ---",
        "ΔLoans", "ΔCash", "ΔMoney deposits", "ΔBills", "ΔBonds", "ΔEquities", "Loan defaults",
        "--- Balance Check ---",
        "Σ"
    ]

    # --- Format data for display (10 columns) ---
    data_dict = {
        # Households
        ("Households", ""): [
            format_value(-C_val, True), "", "", "", "",
            format_value(WB_val, True), "", format_value(-T_val, True), format_value(FDf_val, True), format_value(FDb_val, True), "", "",
            format_value(r_Bhd_val, True), format_value(rm_Md_val, True), format_value(-rl_Lhd_val, True), format_value(coupons_val, True), "",
            format_value(delta_Lh_val, True), format_value(-delta_H_h_val, True), format_value(-delta_M_h_val, True), format_value(-delta_Bh_val, True), format_value(-delta_BL_Pbl_val, True), format_value(-delta_e_Pe_val, True), "", "",
            "0" # Sum check
        ],
        # Firms Current
        ("Firms", "Current"): [
            format_value(C_val, True), format_value(G_val, True), "", format_value(delta_IN_val, True), "",
            format_value(-WB_val, True), format_value(-InvFinCost_val, True), "", format_value(-Ff_val, True), "", "", "",
            "", "", format_value(-rl_Lfd_val, True), "", "",
            "", "", "", "", "", "", "", "",
            "0" # Sum check
        ],
        # Firms Capital
        ("Firms", "Capital"): [
            "", "", format_value(-I_val, True), format_value(-delta_IN_val, True), "",
            "", "", "", format_value(FUf_val, True), "", "", "",
            "", "", "", "", "",
            format_value(delta_Lf_val, True), "", "", "", "", format_value(delta_e_Pe_val, True), format_value(NPL_val, True), "",
            "0" # Sum check
        ],
         # Govt
        ("Govt.", ""): [
            "", format_value(-G_val, True), "", "", "",
            "", "", format_value(T_val, True), "", "", format_value(Fcb_val, True), "", # CB profits paid to Govt
            format_value(-r_Bs_paid_val, True), "", "", format_value(-coupons_val, True), "",
            "", "", "", format_value(delta_B_val, True), format_value(delta_BL_Pbl_val, True), "", "", "",
            "0" # Sum check
        ],
        # CB Current
        ("Central bank", "Current"): [
            "", "", "", "", "",
            "", "", "", "", "", format_value(-Fcb_val, True), "",
            format_value(r_Bcbd_val, True), "", "", "", "",
            "", "", "", "", "", "", "", "",
            "0" # Sum check
        ],
        # CB Capital
        ("Central bank", "Capital"): [
            "", "", "", "", "",
            "", "", "", "", "", "", "",
            "", "", "", "", "",
            "", format_value(-delta_H_val, True), "", format_value(-delta_Bcb_val, True), "", "", "", "",
            "0" # Sum check
        ],
        # Banks Current
        ("Banks", "Current"): [
            "", "", "", "", "",
            "", format_value(InvFinCost_val, True), "", "", format_value(-Fb_val, True), "", "",
            format_value(r_Bbd_val, True), format_value(-rm_Md_val, True), format_value(rl_Lhd_val + rl_Lfd_val, True), "", "",
            "", "", "", "", "", "", "", "",
            "0" # Sum check
        ],
        # Banks Capital
        ("Banks", "Capital"): [
            "", "", "", "", "",
            "", "", "", "", format_value(FUb_val, True), "", "",
            "", "", "", "", "",
            format_value(-delta_L_val, True), format_value(-delta_H_b_val, True), format_value(delta_M_b_val, True), format_value(-delta_Bb_val, True), "", "", format_value(-NPL_val, True), "",
            "0" # Sum check
        ],
        # Sum Column
        ("Σ", ""): [
            "0", "0", "0", "0", "", # Expenditures sum to 0
            "0", "0", "0", "0", "0", "0", "", # Incomes sum to 0
            "0", "0", "0", "0", "", # Interest flows sum to 0
            "0", "0", "0", "0", "0", "0", "0", "", # Changes in stocks sum to 0
            "0" # Final balance check
        ]
    }

    df = pd.DataFrame(data_dict, index=index)
    df.index.name = "Flow"
    st.dataframe(df)