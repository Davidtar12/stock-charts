import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# List of tickers
tickers = [
    'UTHR'
]

# Function to calculate P/FCF
def calculate_p_fcf(ticker):
    try:
        stock = yf.Ticker(ticker)
        market_price = stock.info['currentPrice']
        cf = stock.cashflow
        operating_cash_flow = cf.loc['Operating Cash Flow'].iloc[0]
        capital_expenditure = cf.loc['Capital Expenditure'].iloc[0]
        free_cash_flow = operating_cash_flow - capital_expenditure
        p_fcf = market_price / (free_cash_flow / stock.info['sharesOutstanding'])
        return p_fcf
    except Exception as e:
        print(f"Error calculating P/FCF for {ticker}: {e}")
        return None

# Function to calculate FCF Yield
def calculate_fcf_yield(ticker):
    try:
        stock = yf.Ticker(ticker)
        market_cap = stock.info['marketCap']
        cf = stock.cashflow
        operating_cash_flow = cf.loc['Operating Cash Flow'].iloc[0]
        capital_expenditure = cf.loc['Capital Expenditure'].iloc[0]
        free_cash_flow = operating_cash_flow - capital_expenditure
        fcf_yield = (free_cash_flow / market_cap) * 100
        return fcf_yield
    except Exception as e:
        print(f"Error calculating FCF Yield for {ticker}: {e}")
        return None

# Function to calculate P/E Ratio
def calculate_pe_ratio(ticker):
    try:
        stock = yf.Ticker(ticker)
        pe_ratio = stock.info.get('trailingPE', None)
        return pe_ratio
    except Exception as e:
        print(f"Error calculating P/E Ratio for {ticker}: {e}")
        return None

# Function to calculate ROIC
def calculate_roic(ticker):
    try:
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        fin = stock.financials
        net_income = fin.loc['Net Income'].iloc[0]
        total_debt = bs.loc['Total Debt'].iloc[0]
        total_equity = bs.loc['Stockholders Equity'].iloc[0]
        invested_capital = total_debt + total_equity
        roic = (net_income / invested_capital) * 100
        return roic
    except Exception as e:
        print(f"Error calculating ROIC for {ticker}: {e}")
        return None

# Function to calculate Debt to Equity Ratio
def calculate_debt_to_equity(ticker):
    try:
        stock = yf.Ticker(ticker)
        bs = stock.balance_sheet
        total_debt = bs.loc['Total Debt'].iloc[0]
        total_equity = bs.loc['Stockholders Equity'].iloc[0]
        debt_equity_ratio = total_debt / total_equity
        return debt_equity_ratio
    except Exception as e:
        print(f"Error calculating Debt to Equity Ratio for {ticker}: {e}")
        return None

# Collect data for each indicator
p_fcf_data = []
fcf_yield_data = []
pe_ratio_data = []
roic_data = []
debt_equity_data = []

for ticker in tickers:
    p_fcf = calculate_p_fcf(ticker)
    fcf_yield = calculate_fcf_yield(ticker)
    pe_ratio = calculate_pe_ratio(ticker)
    roic = calculate_roic(ticker)
    debt_equity = calculate_debt_to_equity(ticker)

    if p_fcf is not None:
        p_fcf_data.append({'Ticker': ticker, 'P/FCF': p_fcf})
    if fcf_yield is not None:
        fcf_yield_data.append({'Ticker': ticker, 'FCF Yield (%)': fcf_yield})
    if pe_ratio is not None:
        pe_ratio_data.append({'Ticker': ticker, 'P/E Ratio': pe_ratio})
    if roic is not None:
        roic_data.append({'Ticker': ticker, 'ROIC (%)': roic})
    if debt_equity is not None:
        debt_equity_data.append({'Ticker': ticker, 'Debt to Equity Ratio': debt_equity})

# Create DataFrames for each indicator
df_p_fcf = pd.DataFrame(p_fcf_data)
df_fcf_yield = pd.DataFrame(fcf_yield_data)
df_pe_ratio = pd.DataFrame(pe_ratio_data)
df_roic = pd.DataFrame(roic_data)
df_debt_equity = pd.DataFrame(debt_equity_data)

# Create bar charts for each indicator
def create_bar_chart(df, title, x_col, y_col, filename):
    fig = go.Figure([go.Bar(x=df[x_col], y=df[y_col])])
    fig.update_layout(title=title, xaxis_title=x_col, yaxis_title=y_col)
    fig.write_html(filename)

create_bar_chart(df_p_fcf, 'P/FCF Comparison', 'Ticker', 'P/FCF', '../../p_fcf_chart.html')
create_bar_chart(df_fcf_yield, 'FCF Yield Comparison', 'Ticker', 'FCF Yield (%)', '../../fcf_yield_chart.html')
create_bar_chart(df_pe_ratio, 'P/E Ratio Comparison', 'Ticker', 'P/E Ratio', '../../pe_ratio_chart.html')
create_bar_chart(df_roic, 'ROIC Comparison', 'Ticker', 'ROIC (%)', '../../roic_chart.html')
create_bar_chart(df_debt_equity, 'Debt to Equity Ratio Comparison', 'Ticker', 'Debt to Equity Ratio',
                 '../../debt_equity_chart.html')

print("Charts generated and saved to HTML files.")