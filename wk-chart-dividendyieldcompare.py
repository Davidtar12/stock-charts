import yfinance as yf
import plotly.graph_objs as go
import pandas as pd

# List of tickers to compare
tickers = ['LRCX','NVDA','EXEL','SMCI','FIX','CNI','INTC','KLAC']

# Lists to store ticker symbols and their dividend yields
symbols = []
yields_list = []

for ticker_symbol in tickers:
    try:
        # Fetch ticker information
        ticker = yf.Ticker(ticker_symbol)

        # Try multiple ways to get dividend yield
        yield_value = 0
        if 'dividendYield' in ticker.info:
            yield_value = ticker.info['dividendYield']
        elif 'forwardDividendYield' in ticker.info:
            yield_value = ticker.info['forwardDividendYield']
        elif 'yield' in ticker.info:
            yield_value = ticker.info['yield']

        # Convert to percentage and handle potential None values
        yield_value = float(yield_value * 100) if yield_value is not None else 0

        symbols.append(ticker_symbol)
        yields_list.append(yield_value)

    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")

# Create a DataFrame to enable sorting
df = pd.DataFrame({
    'Ticker': symbols,
    'Dividend Yield': yields_list
})

# Sort in descending order of dividend yield
df_sorted = df.sort_values('Dividend Yield', ascending=False)

# Create bar chart using Plotly graph_objs
fig = go.Figure(data=[
    go.Bar(x=df_sorted['Ticker'], y=df_sorted['Dividend Yield'])
])

# Customize the layout
fig.update_layout(
    title='Dividend Yield Comparison (Descending Order)',
    xaxis_title='Ticker',
    yaxis_title='Dividend Yield (%)',
    yaxis_tickformat='.2f'
)

# Show the chart
fig.show()