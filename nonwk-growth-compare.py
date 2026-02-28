import yfinance as yf
import pandas as pd
from pandas.tseries.offsets import DateOffset
import plotly.graph_objects as go
import os
import pickle  # For caching data

# Define the list of tickers
tickers_list = [ 'FTEC', 'NVDA', 'NVO', 'AMZN', 'AVGO', 'MELI', 'MCD', 'XOM', 'WMT', 'GOOGL', 'WM', 'LULU', 'BN', 'ULTA', 'BRK-A', 'META', 'AMAT', 'V', 'LRCX', 'ROST', 'MAR', 'TJX', 'ORLY', 'CPRT', 'HLT', 'AAPL', 'ASML', 'MU', 'OXY', 'TPL', 'VST', 'AXON', 'BYDDY', 'KO', 'AXP', 'TM', 'BYDDY', 'TSLA', 'HIMS', 'PYPL', 'SOFI', 'ARM', 'TSM', 'HON', 'DE', 'ONON', 'UNH', 'JNJ', 'PG', 'FUBO', 'LVMUY','FTEC']
# Define periods for performance comparison
periods = {
    '1M': DateOffset(months=1),
    '2M': DateOffset(months=2),
    '3M': DateOffset(months=3),
    '4M': DateOffset(months=4),
    '5M': DateOffset(months=5),
    'YTD': 'YTD',  # Year-To-Date
    '6M': DateOffset(months=6),
    '1Y': DateOffset(years=1),
    '2Y': DateOffset(years=2),
    '3Y': DateOffset(years=3),
    '4Y': DateOffset(years=4),
    '10Y': DateOffset(years=10)
}

# Set date ranges
end_date = pd.Timestamp.today()
start_date_max = end_date - DateOffset(years=10)  # Cover the longest period

# Check if cached data exists
cache_file = "adj_close_data.pkl"
if os.path.exists(cache_file):
    print("Loading cached data...")
    with open(cache_file, "rb") as f:
        adj_close_data = pickle.load(f)
else:
    adj_close_data = {}  # Initialize an empty dictionary if no cache file exists

# Identify missing tickers
available_tickers = list(adj_close_data.keys())
missing_tickers = set(tickers_list) - set(available_tickers)

# Download missing tickers' data
if missing_tickers:
    print(f"Downloading data for missing tickers: {missing_tickers}")
    for ticker in missing_tickers:
        try:
            print(f"Downloading data for {ticker}...")
            ticker_data = yf.download(ticker, start=start_date_max, end=end_date)
            if 'Adj Close' in ticker_data.columns and not ticker_data['Adj Close'].isnull().all():
                adj_close_data[ticker] = ticker_data['Adj Close']
            else:
                print(f"'Adj Close' not found or empty for {ticker}")
        except Exception as e:
            print(f"Error downloading data for {ticker}: {e}")

    # Save the updated data to the cache file
    with open(cache_file, "wb") as f:
        pickle.dump(adj_close_data, f)
    print(f"Updated data cached to {cache_file}")

# Convert the dictionary to a DataFrame
adj_close_df = pd.DataFrame(adj_close_data)
adj_close_df = adj_close_df.ffill()  # Forward-fill missing data

# Filter the DataFrame to include only the tickers in tickers_list
available_tickers = [ticker for ticker in tickers_list if ticker in adj_close_df.columns]
missing_tickers = set(tickers_list) - set(available_tickers)

if missing_tickers:
    print(f"Warning: The following tickers are still missing from the data and will be excluded: {missing_tickers}")

adj_close_df = adj_close_df[available_tickers]

# Function to create individual charts for the specified time periods
def create_individual_charts(adj_close_df, periods, output_folder):
    for label, offset in periods.items():
        if label == 'YTD':
            start_date = pd.Timestamp(year=pd.Timestamp.today().year, month=1, day=1)
        else:
            start_date = end_date - offset
        period_data = adj_close_df.loc[start_date:end_date]
        period_data = period_data.dropna(axis=1, how='any')  # Drop tickers with missing data

        # Normalize data to start at 100
        normalized_data = period_data / period_data.iloc[0] * 100

        # Calculate percentage change
        pct_change = (period_data.iloc[-1] / period_data.iloc[0] - 1) * 100

        # Sort tickers by performance
        sorted_tickers = sorted(period_data.columns, key=lambda x: pct_change[x], reverse=True)

        # Create a chart for the specified group of tickers
        fig = go.Figure()

        for ticker in sorted_tickers:
            fig.add_trace(go.Scatter(
                x=normalized_data.index,
                y=normalized_data[ticker],
                mode='lines',
                name=f"{ticker} ({pct_change[ticker]:.2f}%)"
            ))

        # Update layout
        fig.update_layout(
            title=f'{label} Performance for All Tickers',
            xaxis_title='Date',
            yaxis_title='Normalized Adj Close Price (Start=100)',
            legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
            xaxis=dict(tickformat='%Y-%m', dtick='M12', tickmode='auto'),
            width=1600,
            height=1000
        )

        # Save the chart to an HTML file
        output_file = os.path.join(output_folder, f"all_tickers_{label}_performance.html")
        fig.write_html(output_file)
        print(f"Chart saved to {output_file}")

# Main script execution
if __name__ == "__main__":
    # Define the output folder for charts
    output_folder = r"C:\path\to\your_data"
    os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists

    # Create individual charts for the specified time periods
    create_individual_charts(adj_close_df, periods, output_folder)