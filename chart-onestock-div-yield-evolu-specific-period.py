import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Download historical data for MCD
symbol = 'MCD'
df = yf.download(symbol, start='2022-01-01', end='2024-12-14')

# Assuming annual dividend per share (you can get this from financial reports or websites like Koyfin)
annual_dividend = 7.08

# Calculate dividend yield
df['Dividend_Yield'] = annual_dividend / df['Close']

# Create the figure
fig = go.Figure(data=[go.Scatter(x=df.index, y=df['Dividend_Yield'], mode='lines')])

# Customize the plot
fig.update_layout(
    title='McDonald\'s Corporation (MCD) Dividend Yield Over Last 2 Years',
    xaxis_title='Date',
    yaxis_title='Dividend Yield (%)'
)

# Display the plot
fig.show()