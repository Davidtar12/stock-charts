import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset

# List of tickers
tickers = [
'LRCX', 'YUM', 'MCD', 'CNI', 'VISA', 'NDSN', 'ROST', 'MAR', 'MAS', 'TJX', 'ADP', 'TER', 'ORLY', 'CPRT', 'HLT'
]

# Add SPY for comparison
tickers.append('SPY')

# Define periods in years
periods = [5, 10, 15, 20]

# Set date ranges
end_date = pd.Timestamp.today()
start_date_20 = end_date - DateOffset(years=20)

# Create an empty dictionary to hold 'Adj Close' data
adj_close_data = {}

# Download data for tickers
valid_tickers = []  # Track tickers with valid data

for ticker in tickers:
    try:
        print(f"Downloading data for {ticker}...")
        ticker_data = yf.download(ticker, start=start_date_20, end=end_date)

        # Check if 'Adj Close' is in columns and not empty
        if 'Adj Close' in ticker_data.columns and not ticker_data['Adj Close'].isnull().all():
            adj_close_data[ticker] = ticker_data['Adj Close']
            valid_tickers.append(ticker)
        else:
            print(f"'Adj Close' not found or empty for {ticker}")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")

# Convert the dictionary to a DataFrame
adj_close_df = pd.DataFrame(adj_close_data)

# Handle missing data
adj_close_df = adj_close_df.ffill()

# Create performance charts for specified periods
for years in periods:
    # Calculate start date for the period
    start_date = end_date - DateOffset(years=years)

    # Slice data to the period
    period_data = adj_close_df.loc[start_date:end_date]

    # Filter out tickers with no valid data in the period
    valid_period_data = period_data.dropna(axis=1, how='any')

    # Ensure SPY is included if it has data
    if 'SPY' not in valid_period_data.columns and 'SPY' in adj_close_df.columns:
        # Find SPY data within the period
        spy_period_data = adj_close_df.loc[start_date:end_date, 'SPY']
        if not spy_period_data.isnull().all():
            valid_period_data['SPY'] = spy_period_data

    # Skip if no valid data
    if valid_period_data.empty:
        print(f"No valid data found for {years}-year period.")
        continue

    valid_period_tickers = valid_period_data.columns.tolist()

    # Normalize data to start at 100
    try:
        normalized_data = valid_period_data / valid_period_data.iloc[0] * 100
    except IndexError:
        print(f"Could not normalize data for {years}-year period.")
        continue

    # Calculate percentage change
    pct_change = (valid_period_data.iloc[-1] / valid_period_data.iloc[0] - 1) * 100

    # Create a sorted list of tickers based on performance (descending)
    sorted_tickers = sorted(valid_period_tickers, key=lambda x: pct_change[x], reverse=True)

    # Create legend labels with percentage change
    legend_labels = [f"{ticker} ({pct_change[ticker]:.2f}%)" for ticker in sorted_tickers]

    # Plot normalized performance with sorted tickers
    plt.figure(figsize=(16, 10))

    # Plot lines in the sorted order
    for ticker in sorted_tickers:
        plt.plot(normalized_data.index, normalized_data[ticker], label=f"{ticker} ({pct_change[ticker]:.2f}%)")

    # Customize the plot
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.title(f'{years}-Year Performance Comparison with SPY')
    plt.xlabel('Date')
    plt.ylabel('Normalized Adj Close Price (Start=100)')

    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())

    # Adjust layout to prevent cutting off labels
    plt.tight_layout()

    # Save the plot
    plt.savefig(f'{years}_year_performance.png', bbox_inches='tight')
    plt.close()
    print(f"Saved chart for {years}-year period.")

print("Completed generating performance comparison charts.")