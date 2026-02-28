import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta


def get_dividend_yield(ticker):
    # Download historical price data
    price_data = yf.download(ticker, period="max")

    # Download historical dividend data
    dividends = yf.Ticker(ticker).dividends

    # Make dividends.index timezone-naive
    dividends.index = dividends.index.tz_localize(None)

    # Calculate TTM dividends
    if not dividends.empty:
        last_date = price_data.index[-1]
        one_year_ago = last_date - timedelta(days=365)
        dividends_last_year = dividends[dividends.index > one_year_ago]
        ttm_dividend = dividends_last_year.sum()
    else:
        ttm_dividend = 0

    # Calculate Dividend Yield
    price_data['Dividend_Yield'] = (ttm_dividend / price_data['Close']) * 100
    return price_data['Dividend_Yield']


# Define the tickers
tickers = ['MCD', 'AAPL', 'MSFT', 'GOOG']

# Fetch dividend yield data for all tickers
dividend_yield_data = {}
for ticker in tickers:
    dividend_yield_data[ticker] = get_dividend_yield(ticker)

# Create the main figure with all data
fig = go.Figure()

for ticker, dividend_yield in dividend_yield_data.items():
    fig.add_trace(go.Scatter(x=dividend_yield.index, y=dividend_yield, name=ticker))

fig.update_layout(
    title='Dividend Yield Over Maximum Available Period',
    xaxis_title='Date',
    yaxis_title='Dividend Yield (%)',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    ),
    yaxis=dict(autorange=True, fixedrange=False)  # Enable Y-axis autoscaling
)

# Define date ranges for simulation using one of the tickers
reference_ticker = tickers[0]  # Use the first ticker as a reference
date_ranges = {
    '1m': (dividend_yield_data[reference_ticker].index.max() - pd.Timedelta(days=30),
           dividend_yield_data[reference_ticker].index.max()),
    '6m': (dividend_yield_data[reference_ticker].index.max() - pd.Timedelta(days=180),
           dividend_yield_data[reference_ticker].index.max()),
    'YTD': (dividend_yield_data[reference_ticker].index.max().replace(month=1, day=1),
            dividend_yield_data[reference_ticker].index.max()),
    '1y': (dividend_yield_data[reference_ticker].index.max() - pd.Timedelta(days=365),
           dividend_yield_data[reference_ticker].index.max()),
    'all': (dividend_yield_data[reference_ticker].index.min(), dividend_yield_data[reference_ticker].index.max())
}

# Generate separate figures for each date range
for label, (min_date, max_date) in date_ranges.items():
    filtered_data = {ticker: dividend_yield[(dividend_yield.index >= min_date) & (dividend_yield.index <= max_date)] for
                     ticker, dividend_yield in dividend_yield_data.items()}
    y_min = min([filtered_data[ticker].min() for ticker in tickers])
    y_max = max([filtered_data[ticker].max() for ticker in tickers])

    # Create a new figure for each date range
    fig_range = go.Figure()
    for ticker, dividend_yield in filtered_data.items():
        fig_range.add_trace(go.Scatter(x=dividend_yield.index, y=dividend_yield, name=ticker))

    fig_range.update_layout(
        title=f'Dividend Yield Over {label} Period',
        xaxis_title='Date',
        yaxis_title='Dividend Yield (%)',
        xaxis=dict(
            type="date"
        ),
        yaxis=dict(range=[y_min, y_max])
    )

    fig_range.show()

# Show the original figure with all data
fig.show()