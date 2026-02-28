import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Define tickers
tickers = ['LRCX', 'NVDA','EXEL','SMCI','FIX','CNI','INTC']

# Function to find the first available date for a ticker in 2000
def get_first_available_date(ticker, year=2000):
    try:
        ticker_obj = yf.Ticker(ticker)
        historical_data = ticker_obj.history(start=f'{year}-01-01', end=f'{year}-12-31', auto_adjust=True)
        if not historical_data.empty:
            return historical_data.index[0].strftime('%Y-%m-%d')
        return None
    except Exception as e:
        print(f"Error finding first date for {ticker} in {year}: {e}")
        return None

# Function to download and validate ticker data
def get_validated_ticker_data(ticker, start_date, end_date):
    try:
        ticker_obj = yf.Ticker(ticker)
        historical_data = ticker_obj.history(start=start_date, end=end_date, auto_adjust=True)
        if not historical_data.empty and len(historical_data) > 0:
            return historical_data['Close']
        return None
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return None

# Function to create and save the chart
def create_chart(df, start_date, end_date, description):
    if df.empty:
        print(f"No data available for the period {description}")
        return

    normalized = df / df.iloc[0] * 100
    pct_change = (normalized.iloc[-1] / normalized.iloc[0] - 1) * 100

    valid_tickers = [ticker for ticker in normalized.columns
                     if not pd.isna(pct_change[ticker]) and abs(pct_change[ticker]) > 0.01]

    if not valid_tickers:
        print(f"No valid tickers for the period {description}")
        return

    normalized = normalized[valid_tickers]
    pct_change = pct_change[valid_tickers]

    sorted_tickers = sorted(valid_tickers, key=lambda x: pct_change[x], reverse=True)

    fig = go.Figure()
    for ticker in sorted_tickers:
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized[ticker],
            mode='lines',
            name=f"{ticker} ({pct_change[ticker]:.2f}%)"
        ))

    fig.update_layout(
        title=f'Stock Performance: {description}',
        xaxis_title='Date',
        yaxis_title='Normalized Price (Start=100)',
        legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
        width=1600,
        height=1000
    )

    safe_description = description.replace(' ', '_').replace('-', '_').lower()
    filename = f'stock_performance_{safe_description}.html'
    fig.write_html(filename)
    print(f'Chart saved as {filename} with tickers: {", ".join(sorted_tickers)}')

# Find first available dates for 2000
first_dates_2000 = {ticker: get_first_available_date(ticker) for ticker in tickers}
print("First available dates in 2000:")
for ticker, date in first_dates_2000.items():
    print(f"{ticker}: {date}")

# Define periods
periods = {
    '2001-bottom_2007-2010_crash': {
        'start': '2001-01-02',
        'end': '2009-03-09',
        'description': '2001 Bottom to 2007-2010 Crash Bottom'
    },
    '2000-bottom_2007-2010_crash': {
        'start': min(date for date in first_dates_2000.values() if date is not None),
        'end': '2009-03-09',
        'description': '2000 Bottom to 2007-2010 Crash Bottom'
    },
    '2004-bottom_2007-2010_crash': {
        'start': '2004-03-01',
        'end': '2009-03-09',
        'description': '2004 Bottom to 2007-2010 Crash Bottom'
    },
    '2001-bottom_2020_crash': {
        'start': '2001-01-02',
        'end': '2020-03-23',
        'description': '2001 Bottom to COVID Crash Bottom'
    },
    '2000-bottom_2020_crash': {
        'start': min(date for date in first_dates_2000.values() if date is not None),
        'end': '2020-03-23',
        'description': '2000 Bottom to COVID Crash Bottom'
    },
    '2004-bottom_2020_crash': {
        'start': '2004-03-01',
        'end': '2020-03-23',
        'description': '2004 Bottom to COVID Crash Bottom'
    },
    '2007-2010_crash_bottom_to_latest': {
        'start': '2009-03-09',
        'end': datetime.today().strftime('%Y-%m-%d'),
        'description': '2007-2010 Crash Bottom to Latest'
    },
    'recovery_to_latest': {
        'start': '2010-10-11',
        'end': datetime.today().strftime('%Y-%m-%d'),
        'description': 'Recovery Point to Latest'
    }
}

# Generate charts for each period
for label, dates in periods.items():
    validated_data = {}
    for ticker in tickers:
        ticker_data = get_validated_ticker_data(ticker, dates['start'], dates['end'])
        if ticker_data is not None:
            validated_data[ticker] = ticker_data

    if validated_data:
        adj_close_df = pd.DataFrame(validated_data)
        try:
            create_chart(adj_close_df, dates['start'], dates['end'], dates['description'])
        except Exception as e:
            print(f"Error creating chart for {label}: {e}")
    else:
        print(f"No valid data found for any ticker in {label} period.")

print("Completed generating performance comparison charts. Open the HTML files in a web browser.")