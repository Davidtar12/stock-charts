import yfinance as yf
from datetime import datetime, timedelta

# List of tickers
tickers = ['NVDA','VRT','TSM'
]

# Define the periods
periods = {
    "2y": 2 * 365,
    "1mo": 30,
    "4mo": 4 * 30,
    "6mo": 6 * 30
}

# Get the current date
current_date = datetime.now()

# Function to get the performance of a ticker over a given period
def get_performance(ticker, period_days):
    end_date = current_date
    start_date = end_date - timedelta(days=period_days)
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        return None
    start_price = data.iloc[0]['Adj Close']
    end_price = data.iloc[-1]['Adj Close']
    return (end_price - start_price) / start_price * 100

# Get the performance of FTEC over the periods
ftec_performance = {period: get_performance("FTEC", days) for period, days in periods.items()}

# Filter tickers that outperform FTEC in the specified periods
outperforming_tickers = []

for ticker in tickers:
    performance = {period: get_performance(ticker, days) for period, days in periods.items()}
    if (performance["2y"] > ftec_performance["2y"] and
        performance["1mo"] > ftec_performance["1mo"] and
        (performance["4mo"] > ftec_performance["4mo"] or performance["6mo"] > ftec_performance["6mo"])):
        outperforming_tickers.append(ticker)

# Print the outperforming tickers
for ticker in outperforming_tickers:
    print(ticker)
