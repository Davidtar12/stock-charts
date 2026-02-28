import yfinance as yf
import pandas as pd
from pandas.tseries.offsets import DateOffset
import plotly.graph_objects as go

# List of tickers
tickers = ['FXAIX', 'VOO', 'VFIAX', 'SPY', 'VIGAX', 'VITAX', 'FTEC', 'QQQ','VGT', 'VUG','VTI','LRCX', 'YUM', 'MCD', 'CNI', 'V', 'NDSN', 'ROST', 'MAR', 'MAS', 'TJX', 'ADP', 'TER', 'ORLY', 'CPRT', 'HLT', 'NKE', 'NVDA', 'AMD','ADBE','AXP','NU','BKNG','DPZ','PZZA']

# Define periods in years
periods = [5, 10, 15, 20, 21, 22, 23, 24, 25, 29, 31, 37]

# Set date ranges
end_date = pd.Timestamp.today()
start_date_max = end_date - DateOffset(years=37)

# Create an empty dictionary to hold 'Adj Close' data
adj_close_data = {}

# Download data for tickers
valid_tickers = []

for ticker in tickers:
    try:
        print(f"Downloading data for {ticker}...")
        ticker_data = yf.download(ticker, start=start_date_max, end=end_date)
        if 'Adj Close' in ticker_data.columns and not ticker_data['Adj Close'].isnull().all():
            adj_close_data[ticker] = ticker_data['Adj Close']
            valid_tickers.append(ticker)
        else:
            print(f"'Adj Close' not found or empty for {ticker}")
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")

# Convert the dictionary to a DataFrame
adj_close_df = pd.DataFrame(adj_close_data)

# Handle missing data by forward-filling
adj_close_df = adj_close_df.ffill()

# Create performance charts for specified periods
for years in periods:
    start_date = end_date - DateOffset(years=years)
    period_data = adj_close_df.loc[start_date:end_date]
    valid_period_data = period_data.dropna(axis=1, how='any')
    if 'SPY' not in valid_period_data.columns and 'SPY' in adj_close_df.columns:
        spy_period_data = adj_close_df.loc[start_date:end_date, 'SPY']
        if not spy_period_data.isnull().all():
            valid_period_data['SPY'] = spy_period_data
    if valid_period_data.empty:
        print(f"No valid data found for {years}-year period.")
        continue
    try:
        normalized_data = valid_period_data / valid_period_data.iloc[0] * 100
    except IndexError:
        print(f"Could not normalize data for {years}-year period.")
        continue
    pct_change = (valid_period_data.iloc[-1] / valid_period_data.iloc[0] - 1) * 100
    sorted_tickers = sorted(valid_period_data.columns, key=lambda x: pct_change[x], reverse=True)
    fig = go.Figure()
    for ticker in sorted_tickers:
        fig.add_trace(go.Scatter(
            x=normalized_data.index,
            y=normalized_data[ticker],
            mode='lines',
            name=f"{ticker} ({pct_change[ticker]:.2f}%)"
        ))
    fig.update_layout(
        title=f'{years}-Year Performance Comparison with SPY',
        xaxis_title='Date',
        yaxis_title='Normalized Adj Close Price (Start=100)',
        legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
        xaxis=dict(tickformat='%Y-%m', dtick='M12', tickmode='auto'),
        width=1600,
        height=1000
    )
    with open(f"{years}_year_performance.html", "w") as f:
        f.write(f"<html><head><title>{years}-Year Performance Comparison with SPY</title></head><body>\n")
        f.write(f"<h1>{years}-Year Performance Comparison with SPY</h1>\n")
        f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write("</body></html>")
    print(f"Saved chart for {years}-year period.")

print("Completed generating performance comparison charts. Open the individual HTML files in a web browser.")