# -*- coding: utf-8 -*-
"""Chapter 11 Model GROWTH.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/kennt/monetary-economics/blob/master/Chapter%2011%20Model%20GROWTH.ipynb
"""

# pip install pysolve

"""# Monetary Economics: Chapter 11

### Preliminaries
"""

# Commented out IPython magic to ensure Python compatibility.
# Configure matplotlib to use non-interactive backend
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for headless operation
import matplotlib.pyplot as plt
import re

from pysolve.model import Model
from pysolve.utils import is_close,round_solution

# Simple function to close matplotlib figures
def plot_and_close(fig, caption=None):
    """Just close the figure without any graphical output"""
    plt.close(fig)

"""### Model GROWTH

> Changes to the model:
> In the GROWTH model, I've used the definition of the Tobin's Q from the INSOUT model in Chapter 10
>
> Original: Q = (Eks*Pe)/(K + IN + Lfd)
>
> Corrected : Q = (Eks*Pe + Lfd)/(K + IN)
"""

def create_growth_model():
    model = Model()

    model.set_var_default(0)
    model.var('ADDl', desc='Spread between interest rate on loans and rate on deposits')
    model.var('Bbd', desc='Government bills demanded by commercial banks')
    model.var('Bbs', desc='Government bills supplied to commercial banks')
    model.var('Bcbd', desc='Government bills demanded by Central bank')
    model.var('Bcbs', desc='Government bills supplied by Central bank')
    model.var('Bhd', desc='Demand for government bills from households')
    model.var('Bhs', desc='Government bills supplied to households')
    model.var('Bs', desc='Supply of government bills')
    model.var('BLd', desc='Demand for government bonds')
    model.var('BLs', desc='Supply of government bonds')
    model.var('BLR', desc='Gross bank liquidity ratio')
    model.var('BUR', desc='Burden of personal debt')
    model.var('Ck', desc='Real consumption')
    model.var('CAR', desc='Capital adequacy ratio of banks')
    model.var('CG', desc='Capital gains on government bonds')
    model.var('CONS', desc='Consumption at current prices')
    model.var('Ekd', desc='Number of equities demanded')
    model.var('Eks', desc='Number of equities supplied by firms')
    model.var('ER', desc='Employment rate')
    model.var('Fb', desc='Realized banks profits')
    model.var('Fbt', desc='Target profits of banks')
    model.var('Fcb', desc='Central bank "profits"')
    model.var('Ff', desc='Realized entrepreneurial profits')
    model.var('Fft', desc='Planned entrepreneurial profits')
    model.var('FDb', desc='Dividends of banks')
    model.var('FDf', desc='Dividends of firms')
    model.var('FUb', desc='Retained earnings of banks')
    model.var('FUbt', desc='Targt retained earnings of banks')
    model.var('FUf', desc='Retained earnings of firms')
    model.var('FUft', desc='Planned retained earnings of firms')
    model.var('G', desc='Government expenditures')
    model.var('Gk', desc='Real government expenditures')
    model.var('GD', desc='Government debt')
    model.var('GL', desc='Gross amount of new personal loans')
    model.var('GRk', desc='growth_mod of real capital stock')
    model.var('Hbd', desc='Cash required by banks')
    model.var('Hbs', desc='Cash supplied to banks')
    model.var('Hhd', desc='Households demand for cash')
    model.var('Hhs', desc='Cash supplied to households')
    model.var('Hs', desc='Total supply of cash')
    model.var('HCe', desc='Expected historical costs')
    model.var('INV', desc='Gross investment')
    model.var('Ik', desc='Gross investment in real terms')
    model.var('IN', desc='Stock of inventories at current costs')
    model.var('INk', desc='Real inventories')
    model.var('INke', desc='Expected real inventories')
    model.var('INkt', desc='Target level of real inventories')
    model.var('K', desc='Capital stock')
    model.var('Kk', desc='Real capital stock')
    model.var('Lfd', desc='Demand for loans by firms')
    model.var('Lfs', desc='Supply of loans to firms')
    model.var('Lhd', desc='Demand for loans by households')
    model.var('Lhs', desc='Loans supplied to households')
    model.var('Md', desc='Deposits demanded by households')
    model.var('Ms', desc='Deposits supplied by banks')
    model.var('N', desc='Employment level')
    model.var('Nt', desc='Desired employment level')
    model.var('NHUC', desc='Normal historic unit cost')
    model.var('NL', desc='Net flow of new loans to the household sector')
    model.var('NLk', desc='Real flow of new loans to the household sector')
    model.var('NPL', desc='Non-Performing loans')
    model.var('NPLke', desc='Expected proportion of Non-Performing Loans')
    model.var('NUC', desc='Normal unit cost')
    model.var('OFb', desc='Own funds of banks')
    model.var('OFbe', desc='Short-run target for banks own funds')
    model.var('OFbt', desc='Long-run target for banks own funds')
    model.var('omegat', desc='Target real wage for workers')
    model.var('P', desc='Price level')
    model.var('Pbl', desc='Price of government bonds')
    model.var('Pe', desc='Price of equities')
    model.var('PE', desc='Price earnings ratio')
    model.var('PI', desc='Price inflation')
    model.var('PR', desc='Lobor productivity')
    model.var('PSBR', desc='Government deficit')
    model.var('Q', desc="Tobin's Q")
    model.var('Rb', desc='Interest rate on government bills')
    model.var('Rbl', desc='Interest rate on bonds')
    model.var('Rk', desc='Dividend yield of firms')
    model.var('Rl', desc='Interest rate on loans')
    model.var('Rm', desc='Interest rate on deposits')
    model.var('REP', desc='Personal loans repayments')
    model.var('RRl', desc='Real interest rate on loans')
    model.var('S', desc='Sales at current prices')
    model.var('Sk', desc='Real sales')
    model.var('Ske', desc='Expected real sales')
    model.var('T', desc='Taxes')
    model.var('U', desc='Capital utilization proxy')
    model.var('UC', desc='Unit costs')
    model.var('V', desc='Wealth of households')
    model.var('Vk', desc='Real staock of wealth')
    model.var('Vfma', desc='Investible wealth of households')
    model.var('W', desc='Wage rate')
    model.var('WB', desc='The wage bill')
    model.var('Y', desc='Output at current prices (nominal GDP)')
    model.var('Yk', desc='Real output')
    model.var('YDhs', desc='Haig-Simons measure of disposable income')
    model.var('YDr', desc='Regular disposable income')
    model.var('YDkr', desc='Regular real disposable income')
    model.var('YDkre', desc='Expected regular real disposable income')
    model.var('YP', desc='Personal income')

    model.var('eta', desc='Ratio of new loans to personal income')
    model.var('phi', desc='Mark-up on unit costs')
    model.var('phit', desc='Ideal mark-up on unit costs')
    model.var('z1a', desc='Is one if bank liquidity ratio is below bottom range')
    model.var('z1b', desc='Is one if bank liquidity ratio is below bottom range')
    model.var('z2a', desc='Is one if bank liquidity ratio is above top range')
    model.var('z2b', desc='Is one if bank liquidity ratio is above top range')
    model.var('z3', desc='Parameter in wage aspiration equation')
    model.var('z4', desc='Parameter in wage aspiration equation')
    model.var('z5', desc='Parameter in wage aspiration equation')
    model.var('sigmase', desc='Opening inventories to expected sales ratio')

    model.param('alpha1', desc='Propensity to consume out of income')
    model.param('alpha2', desc='Propensity to consume out of wealth')
    model.param('beta', desc='Parameter in expectation formations on real sales')
    model.param('betab', desc='Spped of adjustment of banks own funds')
    model.param('bot', desc='Bottom value for bank net liquidity ratio')
    model.param('delta', desc='Rate of depreciation of fixed capital')
    model.param('deltarep', desc='Ratio of personal loans repayments to stock of loans')
    model.param('eps', desc='Parameter in expectation formations on real disposable income')
    model.param('eps2', desc='Speed of adjustment of mark-up')
    model.param('epsb', desc='Speed of adjustment in expected proportion of non-performing loans')
    model.param('epsrb', desc='Speed of adjustment in the real interest rate on bills')
    model.param('eta0', desc='Ratio of new loans to personal income - exogenous component')
    model.param('etan', desc='Speed of adjustment of actual employment to desired employment')
    model.param('etar', desc='Relation between the ratio of new loans to personal income and the interest rate on loans')
    model.param('gamma', desc='Speed of adjustment of inventories to the target level')
    model.param('gamma0', desc='Exogenous growth_mod in the real stock of capital')
    model.param('gammar', desc='Relation between the real interest rate and growth_mod in the stock of capital')
    model.param('gammau', desc='Relation between the utilization rate and growth_mod in the stock of capital')
    model.param('lambda20', desc='Parameter in households demand for bills')
    model.param('lambda21', desc='Parameter in households demand for bills')
    model.param('lambda22', desc='Parameter in households demand for bills')
    model.param('lambda23', desc='Parameter in households demand for bills')
    model.param('lambda24', desc='Parameter in households demand for bills')
    model.param('lambda25', desc='Parameter in households demand for bills')
    model.param('lambda30', desc='Parameter in households demand for bonds')
    model.param('lambda31', desc='Parameter in households demand for bonds')
    model.param('lambda32', desc='Parameter in households demand for bonds')
    model.param('lambda33', desc='Parameter in households demand for bonds')
    model.param('lambda34', desc='Parameter in households demand for bonds')
    model.param('lambda35', desc='Parameter in households demand for bonds')
    model.param('lambda40', desc='Parameter in households demand for equities')
    model.param('lambda41', desc='Parameter in households demand for equities')
    model.param('lambda42', desc='Parameter in households demand for equities')
    model.param('lambda43', desc='Parameter in households demand for equities')
    model.param('lambda44', desc='Parameter in households demand for equities')
    model.param('lambda45', desc='Parameter in households demand for equities')
    model.param('lambdab', desc='Parameter determining dividends of banks')
    model.param('lambdac', desc='Parameter in households demand for cash')
    model.param('psid', desc='Ratio of dividends to gross profits')
    model.param('psiu', desc='Ratio of retained earnings to investments')
    model.param('ro', desc='Reserve requirement parameter')
    model.param('sigman', desc='Parameter of influencing normal historic unit costs')
    model.param('theta', desc='Income tax rate')
    model.param('top', desc='Top value for bank net liquidity ratio')
    model.param('xim1', desc='Parameter in the equation for setting interest rate on deposits')
    model.param('xim2', desc='Parameter in the equation for setting interest rate on deposits')
    model.param('omega0', desc='Parameter influencing the target real wage for workers')
    model.param('omega1', desc='Parameter influencing the target real wage for workers')
    model.param('omega2', desc='Parameter influencing the target real wage for workers')
    model.param('omega3', desc='Speed of adjustment of wages to target value')


    model.param('ADDbl', desc='Spread between long-term interest rate and rate on bills')
    model.param('BANDb', desc='Lower range of the flat Phillips curve')
    model.param('BANDt', desc='Upper range of the flat Phillips curve')
    model.param('GRg', desc='growth_mod of real government expenditures')
    model.param('GRpr', desc='growth_mod rate of productivity')
    model.param('NCAR', desc='Normal capital adequacy ratio of banks')
    model.param('Nfe', desc='Full employment level')
    model.param('NPLk', desc='Proportion of Non-Performing loans')
    model.param('RA', desc='Random shock to expectations on real sales')
    model.param('Rbbar', desc='Interest rate on bills, set exogenously')
    model.param('Rln', desc='Normal interest rate on loans')
    model.param('RRb', desc='Real interest rate on bills')
    model.param('sigmas', desc='Realized inventories to sales ratio')
    model.param('sigmat', desc='Target inventories to sales ratio')


    # Box 11.1 : Firms' equations
    # ---------------------------
    model.add('Yk = Ske + INke - INk(-1)')          # 11.1 : Real output
    model.add('Ske = beta*Sk + (1-beta)*Sk(-1)*(1 + (GRpr + RA))') # 11.2 : Expected real sales
    model.add('INke = INk(-1) + gamma*(INkt - INk(-1))')  # 11.3 : Long-run inventory target
    model.add('INkt = sigmat*Ske')                  # 11.4 : Short-run inventory target
    model.add('INk - INk(-1) = Yk - Sk - NPL/UC')   # 11.5 : Actual real inventories
    model.add('Kk = Kk(-1)*(1 + GRk)')              # 11.6 : Real capital stock
    model.add('GRk = gamma0 + gammau*U(-1) - gammar*RRl')  # 11.7 : Growth of real capital stock
    model.add('U = Yk/Kk(-1)')                      # 11.8 : Capital utilization proxy
    model.add('RRl = ((1 + Rl)/(1 + PI)) - 1')      # 11.9 : Real interest rate on loans
    model.add('PI = (P - P(-1))/P(-1)')             # 11.10 : Rate of price inflation
    model.add('Ik = d(Kk) + delta*Kk(-1)')          # 11.11 : Real gross investment

    # Box 11.2 : Firms' equations
    # ---------------------------
    model.add('Sk = Ck + Gk + Ik')                  # 11.12 : Actual real sales
    model.add('S = Sk*P')                           # 11.13 : Value of realized sales
    model.add('IN = INk*UC')                        # 11.14 : Inventories valued at current cost
    model.add('INV = Ik*P')                         # 11.15 : Nominal gross investment
    model.add('K = Kk*P')                           # 11.16 : Nomincal value of fixed capital
    model.add('Y = Sk*P + d(INk)*UC')               # 11.17 : Nomincal GDP

    # Box 11.3 : Firms' equations
    # ---------------------------
    # 11.18 : Real wage aspirations
    model.add('omegat = exp(omega0 + omega1*log(PR) + omega2*log(ER + z3*(1 - ER) - z4*BANDt + z5*BANDb))')
    model.add('ER = N(-1)/Nfe(-1)')                 # 11.19 : Employment rate
    # 11.20 : Switch variables
    model.add('z3 = if_true(ER > (1-BANDb)) * if_true(ER <= (1+BANDt))')
    model.add('z4 = if_true(ER > (1+BANDt))')
    model.add('z5 = if_true(ER < (1-BANDb))')
    model.add('W - W(-1) = omega3*(omegat*P(-1) - W(-1))')  # 11.21 : Nominal wage
    model.add('PR = PR(-1)*(1 + GRpr)')             # 11.22 : Labor productivity
    model.add('Nt = Yk/PR')                         # 11.23 : Desired employment
    model.add('N - N(-1) = etan*(Nt - N(-1))')      # 11.24 : Actual employment
    model.add('WB = N*W')                           # 11.25 : Nominal wage bill
    model.add('UC = WB/Yk')                         # 11.26 : Actual unit cost
    model.add('NUC = W/PR')                         # 11.27 : Normal unit cost
    model.add('NHUC = (1 - sigman)*NUC + sigman*(1 + Rln(-1))*NUC(-1)')  # 11.28 : Normal historic unit cost

    # Box 11.4 : Firms' equations
    # ---------------------------
    model.add('P = (1 + phi)*NHUC')                 # 11.29 : Normal-cost pricing
    model.add('phi - phi(-1) = eps2*(phit(-1) - phi(-1))')  # 11.30 : Actual mark-up
    # 11.31 : Ideal mark-up
    model.add('phit = (FDf + FUft + Rl(-1)*(Lfd(-1) - IN(-1)))/((1 - sigmase)*Ske*UC + (1 + Rl(-1))*sigmase*Ske*UC(-1))')
    model.add('HCe = (1 - sigmase)*Ske*UC + (1 + Rl(-1))*sigmase*Ske*UC(-1)')  # 11.32 : Expected historical costs
    model.add('sigmase = INk(-1)/Ske')              # 11.33 : Opening inventories to expected sales ratio
    model.add('Fft = FUft + FDf + Rl(-1)*(Lfd(-1) - IN(-1))')  # 11.34 : Planned entrepeneurial profits of firmss
    model.add('FUft = psiu*INV(-1)')                # 11.35 : Planned retained earnings of firms
    model.add('FDf = psid*Ff(-1)')                  # 11.36 : Dividends of firms

    # Box 11.5 : Firms' equations
    # ---------------------------
    model.add('Ff = S - WB + d(IN) - Rl(-1)*IN(-1)')  # 11.37 : Realized entrepeneurial profits
    model.add('FUf = Ff - FDf - Rl(-1)*(Lfd(-1) - IN(-1)) + Rl(-1)*NPL')  # 11.38 : Retained earnings of firms
    # 11.39 : Demand for loans by firms
    model.add('Lfd - Lfd(-1) = INV + d(IN) - FUf - d(Eks)*Pe - NPL')
    model.add('NPL = NPLk*Lfs(-1)')                 # 11.40 : Defaulted loans
    model.add('Eks - Eks(-1) = ((1 - psiu)*INV(-1))/Pe')  # 11.41 : Supply of equities issued by firms
    model.add('Rk = FDf/(Pe(-1)*Ekd(-1))')          # 11.42 : Dividend yield of firms
    model.add('PE = Pe/(Ff/Eks(-1))')               # 11.43 : Price earnings ratio
    model.add('Q = (Eks*Pe + Lfd)/(K + IN)')        # 11.44 : Tobin's Q ratio

    # Box 11.6 : Households' equations
    # --------------------------------
    model.add('YP = WB + FDf + FDb + Rm(-1)*Md(-1) + Rb(-1)*Bhd(-1) + BLs(-1)')  # 11.45 : Personal income
    model.add('T = theta*YP')                       # 11.46 : Income taxes
    model.add('YDr = YP - T - Rl(-1)*Lhd(-1)')      # 11.47 : Regular disposable income
    model.add('YDhs = YDr + CG')                    # 11.48 : Haig-Simons disposable income
    # !1.49 : Capital gains
    model.add('CG = d(Pbl)*BLd(-1) + d(Pe)*Ekd(-1) + d(OFb)')
    # 11.50 : Wealth
    model.add('V - V(-1) = YDr - CONS + d(Pe)*Ekd(-1) + d(Pbl)*BLs(-1) + d(OFb)')
    model.add('Vk = V/P')                           # 11.51 : Real staock of wealth
    model.add('CONS = Ck*P')                        # 11.52 : Consumption
    model.add('Ck = alpha1*(YDkre + NLk) + alpha2*Vk(-1)')  # 11.53 : Real consumption
    model.add('YDkre = eps*YDkr + (1 - eps)*YDkr(-1)*(1 + GRpr)')  # 11.54 : Expected real regular disposable income
    model.add('YDkr = YDr/P - d(P)*Vk(-1)/P')  # 11.55 : Real regular disposable income

    # Box 11.7 : Households' equations
    # --------------------------------
    model.add('GL = eta*YDr')                       # 11.56 : Gross amount of new personal loans
    model.add('eta = eta0 - etar*RRl')              # 11.57 : New loans to personal income ratio
    model.add('NL = GL - REP')                      # 11.58 : Net amount of new personal loans
    model.add('REP = deltarep*Lhd(-1)')             # 11.59 : Personal loans repayments
    model.add('Lhd - Lhd(-1) = GL - REP')           # 11.60 : Demand for personal loans
    model.add('NLk = NL/P')                         # 11.61 : Real amount of new personal loans
    model.add('BUR = (REP + Rl(-1)*Lhd(-1))/YDr(-1)')  # 11.62 : Burden of personal debt

    # Box 11.8 : Households equations - portfolio decisions
    # -----------------------------------------------------

    # 11.64 : Demand for bills
    model.add('Bhd = Vfma(-1)*(lambda20 + lambda22*Rb(-1) - lambda21*Rm(-1) - lambda24*Rk(-1) - lambda23*Rbl(-1) - lambda25*YDr/V)')
    # 11.65 : Demand for bonds
    model.add('BLd = Vfma(-1)*(lambda30 - lambda32*Rb(-1) - lambda31*Rm(-1) - lambda34*Rk(-1) + lambda33*Rbl(-1) - lambda35*YDr/V)/Pbl')
    # 11.66 : Demand for equities - normalized to get the price of equitities
    model.add('Pe = Vfma(-1)*(lambda40 - lambda42*Rb(-1) - lambda41*Rm(-1) + lambda44*Rk(-1) - lambda43*Rbl(-1) - lambda45*YDr/V)/Ekd')
    model.add('Md = Vfma - Bhd - Pe*Ekd - Pbl*BLd + Lhd')  # 11.67 : Money deposits - as a residual
    model.add('Vfma = V - Hhd - OFb')               # 11.68 : Investible wealth
    model.add('Hhd = lambdac*CONS')                 # 11.69 : Households' demand for cash
    model.add('Ekd = Eks')                          # 11.70 : Stock market equilibrium

    # Box 11.9 : Government's equations
    # ---------------------------------
    model.add('G = Gk*P')                           # 11.71 : Pure government expenditures
    model.add('Gk = Gk(-1)*(1 + GRg)')              # 11.72 : Real government expenditures
    model.add('PSBR = G + BLs(-1) + Rb(-1)*(Bbs(-1) + Bhs(-1)) - T')  # 11.73 : Government deficit
    # 11.74 : New issues of bills
    model.add('Bs - Bs(-1) = G - T - d(BLs)*Pbl + Rb(-1)*(Bhs(-1) + Bbs(-1)) + BLs(-1)')
    model.add('GD = Bbs + Bhs + BLs*Pbl + Hs')      # 11.75 : Government debt

    # Box 11.10 : The Central bank's equations
    # ----------------------------------------
    model.add('Fcb = Rb(-1)*Bcbd(-1)')              # 11.76 : Central bank profits
    model.add('BLs = BLd')                          # 11.77 : Bonds are supplied on demand
    model.add('Bhs = Bhd')                          # 11.78 : Household bills supplied on demand
    model.add('Hhs = Hhd')                          # 11.79 : Cash supplied on demand
    model.add('Hbs = Hbd')                          # 11.80 : Reserves supplied on demand
    model.add('Hs = Hbs + Hhs')                     # 11.81 : Total supply of cash
    model.add('Bcbd = Hs')                          # 11.82 : Central bankd
    model.add('Bcbs = Bcbd')                        # 11.83 : Supply of bills to Central bank
    model.add('Rb = Rbbar')                         # 11.84 : Interest rate on bills set exogenously
    model.add('Rbl = Rb + ADDbl')                   # 11.85 : Long term interest rate
    model.add('Pbl = 1/Rbl')                        # 11.86 : Price of long-term bonds

    # Box 11.11 : Commercial Bank's equations
    # ---------------------------------------
    model.add('Ms = Md')                            # 11.87 : Bank deposits supplied on demand
    model.add('Lfs = Lfd')                          # 11.88 : Loans to firms supplied on demand
    model.add('Lhs = Lhd')                          # 11.89 : Personal loans supplied on demand
    model.add('Hbd = ro*Ms')                        # 11.90 : Reserve requirements of banks
    # 11.91 : Bills supplied to banks
    model.add('Bbs - Bbs(-1) = d(Bs) - d(Bhs) - d(Bcbs)')
    # 11.92 : Balance sheet constraint of banks
    model.add('Bbd = Ms + OFb - Lfs - Lhs - Hbd')
    model.add('BLR = Bbd/Ms')                       # 11.93 : Bank liquidity ratio
    # 11.94 : Deposit interest rate
    model.add('Rm - Rm(-1) = z1a*xim1 + z1b*xim2 - z2a*xim1 - z2b*xim2')
    # 11.95-97 : Mechanism for determining changes to the interest rate on deposits
    model.add('z2a = if_true(BLR(-1) > (top + .05))')
    model.add('z2b = if_true(BLR(-1) > top)')
    model.add('z1a = if_true(BLR(-1) <= bot)')
    model.add('z1b = if_true(BLR(-1) <= (bot -.05))')

    # Box 11.12 : Commercial bank's equations
    # ---------------------------------------
    model.add('Rl = Rm + ADDl')                     # 11.98 : Loan interest rate
    model.add('OFbt = NCAR*(Lfs(-1) + Lhs(-1))')    # 11.99 : Long-run own funds target
    model.add('OFbe = OFb(-1) + betab*(OFbt - OFb(-1))')  # 11.100 : Short-run own funds target
    model.add('FUbt = OFbe - OFb(-1) + NPLke*Lfs(-1)')  # 11.101 : Target retained earnings of banks
    model.add('NPLke = epsb*NPLke(-1) + (1 - epsb)*NPLk(-1)')  # 11.102 : Expected proportion of non-performaing loans
    model.add('FDb = Fb - FUb')                     # 11.103 : Dividends of banks
    model.add('Fbt = lambdab*Y(-1) + (OFbe - OFb(-1) + NPLke*Lfs(-1))')  # 11.104 : Target profits of banks
    # 11.105 : Actual profits of banks
    model.add('Fb = Rl(-1)*(Lfs(-1) + Lhs(-1) - NPL) + Rb(-1)*Bbd(-1) - Rm(-1)*Ms(-1)')
    # 11.106 : Lending mark-up over deposit rate
    model.add('ADDl = (Fbt - Rb(-1)*Bbd(-1) + Rm*(Ms(-1) - (1 - NPLke)*Lfs(-1) - Lhs(-1)))/((1 - NPLke)*Lfs(-1) + Lhs(-1))')
    model.add('FUb = Fb - lambdab*Y(-1)')           # 11.107 : Actual retained earnings
    model.add('OFb - OFb(-1) = FUb - NPL')          # 11.108 : Own funds of banks
    model.add('CAR = OFb/(Lfs + Lhs)')              # 11.109 : Actual capital capacity ratio

    return model

# ... All parameter definitions stay the same ...
growth_parameters = {'alpha1': 0.75,
                     'alpha2': 0.064,
                     'beta': 0.5,
                     'betab': 0.4,
                     'gamma': 0.15,
                     'gamma0': 0.00122,
                     'gammar': 0.1,
                     'gammau': 0.05,
                     'delta': 0.10667,
                     'deltarep': 0.1,
                     'eps': 0.5,
                     'eps2': 0.8,
                     'epsb': 0.25,
                     'epsrb': 0.9,
                     'eta': 0.04918,
                     'eta0': 0.07416,
                     'etan': 0.6,
                     'etar': 0.4,
                     'theta': 0.22844,
                     'lambda20': 0.25,
                     'lambda21': 2.2,
                     'lambda22': 6.6,
                     'lambda23': 2.2,
                     'lambda24': 2.2,
                     'lambda25': 0.1,
                     'lambda30': -0.04341,
                     'lambda31': 2.2,
                     'lambda32': 2.2,
                     'lambda33': 6.6,
                     'lambda34': 2.2,
                     'lambda35': 0.1,
                     'lambda40': 0.67132,
                     'lambda41': 2.2,
                     'lambda42': 2.2,
                     'lambda43': 2.2,
                     'lambda44': 6.6,
                     'lambda45': 0.1,
                     'lambdab': 0.0153,
                     'lambdac': 0.05,
                     'xim1': 0.0008,
                     'xim2': 0.0007,
                     'ro': 0.05,
                     'sigman': 0.1666,
                     'sigmase': 0.16667,
                     'sigmat': 0.2,
                     'phi': 0.26417,
                     'phit': 0.26417,
                     'psid': 0.15255,
                     'psiu': 0.92,
                     'omega0': -0.20594,
                     'omega1': 1,
                     'omega2': 2,
                     'omega3': 0.45621
                     }

growth_exogenous = [('ADDbl', 0.02),
                    ('BANDt', 0.01),
                    ('BANDb', 0.01),
                    ('bot', 0.05),
                    ('GRg', 0.03),
                    ('GRpr', 0.03),
                    ('Nfe', 94.76),
                    ('NCAR', 0.1),
                    ('NPLk', 0.02),
                    ('Rbbar', 0.035),
                    ('Rln', 0.07),
                    ('RA', 0),
                    ('top', 0.12),

                    ('ADDl', 0.04592),
                    ('BLR', 0.1091),
                    ('BUR', 0.06324),
                    ('Ck', 7334240),
                    ('CAR', 0.09245),
                    ('CONS', 52603100),
                    ('ER', 0.92),  # Changed from 1 to 0.92
                    ('Fb', 1744130),
                    ('Fbt', 1744140),
                    ('Ff', 18081100),
                    ('Fft', 18013600),
                    ('FDb', 1325090),
                    ('FDf', 2670970),
                    ('FUb', 419039),
                    ('FUf', 15153800),
                    ('FUft', 15066200),
                    ('G', 16755600),
                    ('Gk', 2336160),
                    ('GL', 2775900),
                    ('GRk', 0.03001),
                    ('INV', 16911600),
                    ('Ik', 2357910),
                    ('N', 87.181),
                    ('Nt', 87.181),
                    ('NHUC', 5.6735),
                    ('NL', 683593),
                    ('NLk', 95311),
                    ('NPL', 309158),
                    ('NPLke', 0.02),
                    ('NUC', 5.6106),
                    ('omegat', 112852),
                    ('P', 7.1723),
                    ('Pbl', 18.182),
                    ('Pe', 17937),
                    ('PE', 5.07185),
                    ('PI', 0.0026),
                    ('PR', 138659),
                    ('PSBR', 1894780),
                    ('Q', 0.77443),
                    ('Rb', 0.035),
                    ('Rbl', 0.055),
                    ('Rk', 0.03008),
                    ('Rl', 0.06522),
                    ('Rm', 0.0193),
                    ('REP', 2092310),
                    ('RRb', 0.03232),
                    ('RRl', 0.06246),
                    ('S', 86270300),
                    ('Sk', 12028300),
                    ('Ske', 'Sk'),
                    ('T', 17024100),
                    ('U', 0.70073),
                    ('UC', 5.6106),
                    ('W', 777968),
                    ('WB', 67824000),
                    ('Y', 86607700),
                    ('Yk', 12088400),
                    ('YDr', 56446400),
                    ('YDkr', 7813270),
                    ('YDkre', 7813290),
                    ('YP', 73158700),
                    ('z1a', 0),
                    ('z1b', 0),
                    ('z2a', 0),
                    ('z2b', 0),
                    ]

growth_variables = [('Bbd', 4388930),
                    ('Bbs', 4389790),
                    ('Bcbd', 4655690),
                    ('Bcbs', 4655690),
                    ('Bhd', 33396900),
                    ('Bhs', 'Bhd'),
                    ('Bs', 42484800),
                    ('BLd', 840742),
                    ('BLs', 'BLd'),
                    ('GD', 57728700),
                    ('Ekd', 5112.6001),
                    ('Eks', 'Ekd'),
                    ('Hbd', 2025540),
                    ('Hbs', 'Hbd'),
                    ('Hhd', 2630150),
                    ('Hhs', 'Hhd'),
                    ('Hs', 'Hbd + Hhd'),
                    ('IN', 11585400),
                    ('INk', 2064890),
                    ('INke', 2405660),
                    ('INkt', 'INk'),
                    ('K', 127444000),
                    ('Kk', 17768900),
                    ('Lfd', 15962900),
                    ('Lfs', 'Lfd'),
                    ('Lhd', 21606600),
                    ('Lhs', 'Lhd'),
                    ('Md', 40510800),
                    ('Ms', 'Md'),
                    ('OFb', 3473280),
                    ('OFbe', 3782430),
                    ('OFbt', 3638100),
                    ('V', 165395000),
                    ('Vfma', 159291000),
                    ('Vk', 22576100),
                    ]

# No PDF generation when run directly - just define baseline model for import
if __name__ == "__main__":
    # Create and run the baseline model
    baseline = create_growth_model()
    baseline.set_values(growth_parameters)
    baseline.set_values(growth_exogenous)
    baseline.set_values(growth_variables)

    for _ in range(100):
        baseline.solve(iterations=200, threshold=1e-6)

    print("Baseline model solved successfully")

# These lines outside the if block will be executed on import
baseline = create_growth_model()
baseline.set_values(growth_parameters)
baseline.set_values(growth_exogenous)
baseline.set_values(growth_variables)

for _ in range(100):
    baseline.solve(iterations=200, threshold=1e-6)
