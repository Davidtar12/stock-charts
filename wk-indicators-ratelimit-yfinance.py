import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
from functools import wraps

# Rate limit decorator: pauses for 1 second after each API call.
def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        time.sleep(1)  # Wait 1 second after each call
        return result
    return wrapper

# Retry decorator with exponential backoff for handling 429 errors.
def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_attempts = 3
        sleep_time = 1
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if the error message indicates a 429 error.
                if "429" in str(e):
                    print(f"429 error on attempt {attempt+1}. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    sleep_time *= 2  # Exponential backoff
                else:
                    print(f"Error in {func.__name__}: {e}")
                    return None
        print(f"Max retry attempts reached for {func.__name__}.")
        return None
    return wrapper

# List of tickers
tickers = ['BABA', 'BRK-B', 'AZN', 'KO']

# Create a dictionary of Ticker objects (one per ticker) to avoid multiple API calls per ticker.
stocks = {ticker: yf.Ticker(ticker) for ticker in tickers}

# Calculate P/FCF using a single Ticker object.
@rate_limit
@retry
def calculate_p_fcf(stock):
    ticker = stock.ticker
    try:
        info = stock.info
        market_price = info.get('currentPrice')
        cf = stock.cashflow
        operating_cash_flow = cf.loc['Operating Cash Flow'].iloc[0]
        capital_expenditure = cf.loc['Capital Expenditure'].iloc[0]
        free_cash_flow = operating_cash_flow - capital_expenditure
        shares = info.get('sharesOutstanding')
        if free_cash_flow == 0 or shares is None:
            raise ValueError("Invalid free cash flow or shares outstanding")
        p_fcf = market_price / (free_cash_flow / shares)
        return p_fcf
    except Exception as e:
        print(f"Error calculating P/FCF for {ticker}: {e}")
        return None

# Calculate FCF Yield.
@rate_limit
@retry
def calculate_fcf_yield(stock):
    ticker = stock.ticker
    try:
        info = stock.info
        market_cap = info.get('marketCap')
        cf = stock.cashflow
        operating_cash_flow = cf.loc['Operating Cash Flow'].iloc[0]
        capital_expenditure = cf.loc['Capital Expenditure'].iloc[0]
        free_cash_flow = operating_cash_flow - capital_expenditure
        if market_cap == 0:
            raise ValueError("Invalid market cap")
        fcf_yield = (free_cash_flow / market_cap) * 100
        return fcf_yield
    except Exception as e:
        print(f"Error calculating FCF Yield for {ticker}: {e}")
        return None

# Calculate P/E Ratio.
@rate_limit
@retry
def calculate_pe_ratio(stock):
    ticker = stock.ticker
    try:
        info = stock.info
        pe_ratio = info.get('trailingPE', None)
        return pe_ratio
    except Exception as e:
        print(f"Error calculating P/E Ratio for {ticker}: {e}")
        return None

# Calculate ROIC.
@rate_limit
@retry
def calculate_roic(stock):
    ticker = stock.ticker
    try:
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

# Calculate Debt to Equity Ratio.
@rate_limit
@retry
def calculate_debt_to_equity(stock):
    ticker = stock.ticker
    try:
        bs = stock.balance_sheet
        total_debt = bs.loc['Total Debt'].iloc[0]
        total_equity = bs.loc['Stockholders Equity'].iloc[0]
        if total_equity == 0:
            raise ValueError("Total equity is zero, cannot calculate ratio")
        debt_equity_ratio = total_debt / total_equity
        return debt_equity_ratio
    except Exception as e:
        print(f"Error calculating Debt to Equity Ratio for {ticker}: {e}")
        return None

# Collect data for each indicator.
p_fcf_data = []
fcf_yield_data = []
pe_ratio_data = []
roic_data = []
debt_equity_data = []

for ticker, stock in stocks.items():
    p_fcf = calculate_p_fcf(stock)
    fcf_yield = calculate_fcf_yield(stock)
    pe_ratio = calculate_pe_ratio(stock)
    roic = calculate_roic(stock)
    debt_equity = calculate_debt_to_equity(stock)

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

# Create DataFrames for each indicator and sort in descending order.
df_p_fcf = pd.DataFrame(p_fcf_data).sort_values(by='P/FCF', ascending=False)
df_fcf_yield = pd.DataFrame(fcf_yield_data).sort_values(by='FCF Yield (%)', ascending=False)
df_pe_ratio = pd.DataFrame(pe_ratio_data).sort_values(by='P/E Ratio', ascending=False)
df_roic = pd.DataFrame(roic_data).sort_values(by='ROIC (%)', ascending=False)
df_debt_equity = pd.DataFrame(debt_equity_data).sort_values(by='Debt to Equity Ratio', ascending=False)

# Create bar charts for each indicator.
def create_bar_chart(df, title, x_col, y_col, filename):
    fig = go.Figure([go.Bar(x=df[x_col], y=df[y_col])])
    fig.update_layout(title=title, xaxis_title=x_col, yaxis_title=y_col)
    fig.write_html(filename)

create_bar_chart(df_p_fcf, 'P/FCF Comparison (Descending Order)', 'Ticker', 'P/FCF', 'p_fcf_chart.html')
create_bar_chart(df_fcf_yield, 'FCF Yield Comparison (Descending Order)', 'Ticker', 'FCF Yield (%)', 'fcf_yield_chart.html')
create_bar_chart(df_pe_ratio, 'P/E Ratio Comparison (Descending Order)', 'Ticker', 'P/E Ratio', 'pe_ratio_chart.html')
create_bar_chart(df_roic, 'ROIC Comparison (Descending Order)', 'Ticker', 'ROIC (%)', 'roic_chart.html')
create_bar_chart(df_debt_equity, 'Debt to Equity Ratio Comparison (Descending Order)', 'Ticker', 'Debt to Equity Ratio', 'debt_equity_chart.html')

print("Charts generated and saved to HTML files.")
