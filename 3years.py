import yfinance as yf
import pandas as pd
from pandas.tseries.offsets import DateOffset
import plotly.graph_objects as go

# List of tickers
tickers = ['TDY','FTEC','VITAX','VIGAX','QQQ','TMO','NVO','BLD','JNJ','PEP','KO'
]
# Define periods with labels and offsets - now including shorter timeframes
periods = [
    ('5D', DateOffset(days=5)),
    ('1M', DateOffset(months=1)),
    ('2M', DateOffset(months=2)),
    ('3M', DateOffset(months=3)),
    ('4M', DateOffset(months=4)),
    ('6M', DateOffset(months=6)),
    ('YTD', 'YTD'),
    ('1Y', DateOffset(years=1)),
    ('2Y', DateOffset(years=2)),
    ('3Y', DateOffset(years=3)),
    ('5Y', DateOffset(years=5)),
    ('10Y', DateOffset(years=10)),
    ('15Y', DateOffset(years=15)),
    ('16Y', DateOffset(years=16)),
    ('17Y', DateOffset(years=17)),
    ('18Y', DateOffset(years=18)),
    ('19Y', DateOffset(years=19)),
    ('20Y', DateOffset(years=20)),
    ('21Y', DateOffset(years=21)),
    ('22Y', DateOffset(years=22)),
    ('23Y', DateOffset(years=23)),
    ('24Y', DateOffset(years=24)),
    ('25Y', DateOffset(years=25)),
    ('29Y', DateOffset(years=29)),
    ('31Y', DateOffset(years=31)),
    ('32Y', DateOffset(years=32)),
    ('33Y', DateOffset(years=33)),
    ('34Y', DateOffset(years=34)),
    ('36Y', DateOffset(years=36)),
    ('37Y', DateOffset(years=37)),
]

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


# Function to get start date based on period label and offset
def get_start_date(label, offset):
    if label == 'YTD':
        current_year = end_date.year
        start_date = pd.Timestamp(f"{current_year}-01-01")
    elif isinstance(offset, DateOffset):
        start_date = end_date - offset
    else:
        start_date = end_date - offset
    return start_date


# Create performance charts for specified periods
for label, offset in periods:
    start_date = get_start_date(label, offset)

    period_data = adj_close_df.loc[start_date:end_date]
    valid_period_data = period_data.dropna(axis=1, how='any').copy()

    if 'SPY' not in valid_period_data.columns and 'SPY' in adj_close_df.columns:
        spy_period_data = adj_close_df.loc[start_date:end_date, 'SPY']
        if not spy_period_data.isnull().all():
            valid_period_data.loc[:, 'SPY'] = spy_period_data

    if valid_period_data.empty:
        print(f"No valid data found for {label} period.")
        continue

    try:
        normalized_data = valid_period_data / valid_period_data.iloc[0] * 100
    except IndexError:
        print(f"Could not normalize data for {label} period.")
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

    # Adjust x-axis tick format based on period
    if label in ['5D', '1M', '2M', '3M']:
        dtick = 'D1'  # Daily ticks for shorter periods
        tickformat = '%Y-%m-%d'
    else:
        dtick = 'M1'  # Monthly ticks for longer periods
        tickformat = '%Y-%m'

    fig.update_layout(
        title=f'{label} Performance Comparison with SPY',
        xaxis_title='Date',
        yaxis_title='Normalized Adj Close Price (Start=100)',
        legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
        xaxis=dict(tickformat=tickformat, dtick=dtick, tickmode='auto'),
        width=1600,
        height=1000
    )

    with open(f"{label}_performance.html", "w") as f:
        f.write(f"<html><head><title>{label} Performance Comparison with SPY</title></head><body>\n")
        f.write(f"<h1>{label} Performance Comparison with SPY</h1>\n")
        f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write("</body></html>")

    print(f"Saved chart for {label} period.")

print("Completed generating performance comparison charts. Open the individual HTML files in a web browser.")