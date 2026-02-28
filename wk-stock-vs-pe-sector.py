import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np
import time


# Function to adjust color brightness
def adjust_color_brightness(color, factor):
    color = color.lstrip('#')
    r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    r = min(max(r, 0), 255)
    g = min(max(g, 0), 255)
    b = min(max(b, 0), 255)
    return f'#{r:02x}{g:02x}{b:02x}'


# Load cached sector data
try:
    with open('sector_cache.json', 'r') as f:
        sectors_cached = json.load(f)
except FileNotFoundError:
    sectors_cached = {}

# First, get S&P 500 components and their sector averages
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
tables = pd.read_html(url)
sp500_df = tables[0]
sp500_symbols = sp500_df['Symbol'].tolist()

# Get P/E ratios and sectors for S&P 500 stocks
sp500_data = []
for symbol in sp500_symbols:
    modified_symbol = symbol.replace('.', '-')

    try:
        if modified_symbol in sectors_cached:
            sector = sectors_cached[modified_symbol]
        else:
            stock = yf.Ticker(modified_symbol)
            sector = stock.info.get('sector', 'Unknown')
            sectors_cached[modified_symbol] = sector
            time.sleep(0.1)  # Rate limiting

        # Get P/E ratio
        stock = yf.Ticker(modified_symbol)
        pe_ratio = stock.info.get('trailingPE', None)

        sp500_data.append({
            'Stock': modified_symbol,
            'P/E Ratio': pe_ratio,
            'Sector': sector
        })

    except Exception as e:
        print(f"Error fetching data for {modified_symbol}: {e}")

# Create DataFrame for S&P 500 stocks
sp500_pe_df = pd.DataFrame(sp500_data)
sp500_pe_df['P/E Ratio'] = pd.to_numeric(sp500_pe_df['P/E Ratio'], errors='coerce')
sp500_pe_df['P/E Ratio'].replace([np.inf, -np.inf], np.nan, inplace=True)

# Calculate sector averages from S&P 500 stocks
sector_averages = sp500_pe_df.groupby('Sector')['P/E Ratio'].mean().reset_index()
sector_averages.rename(columns={'P/E Ratio': 'Sector Avg P/E'}, inplace=True)

# Now get data for your specific stocks
target_symbols = tickers = ['UTHR'] # Your target stocks
target_stock_data = []

for symbol in target_symbols:
    modified_symbol = symbol.replace('.', '-')

    try:
        stock = yf.Ticker(modified_symbol)
        info = stock.info

        # Get sector (from cache or fresh)
        if modified_symbol in sectors_cached:
            sector = sectors_cached[modified_symbol]
        else:
            sector = info.get('sector', 'Unknown')
            sectors_cached[modified_symbol] = sector

        # Get P/E ratio
        pe_ratio = info.get('trailingPE', None)

        target_stock_data.append({
            'Stock': modified_symbol,
            'P/E Ratio': pe_ratio,
            'Sector': sector,
            'Is_Target': True
        })

        time.sleep(0.1)  # Rate limiting

    except Exception as e:
        print(f"Error fetching data for {modified_symbol}: {e}")

# Save the updated sector cache
with open('sector_cache.json', 'w') as f:
    json.dump(sectors_cached, f)

# Create DataFrame for target stocks
target_df = pd.DataFrame(target_stock_data)
target_df['P/E Ratio'] = pd.to_numeric(target_df['P/E Ratio'], errors='coerce')

# Merge with sector averages
combined_df = pd.merge(target_df, sector_averages, on='Sector', how='left')

# Generate color scheme
unique_sectors = combined_df['Sector'].unique()
base_colors = px.colors.qualitative.Plotly
sector_color_map = {
    sector: {
        'base': base_colors[i % len(base_colors)],
        'light': adjust_color_brightness(base_colors[i % len(base_colors)], 1.1)
    }
    for i, sector in enumerate(unique_sectors)
}

# Create traces
traces = []

# Create x-axis categories
x_categories = []
for idx, row in combined_df.iterrows():
    x_categories.extend([row['Stock'], f"S&P 500 {row['Sector']} Avg"])

# Add bars for individual stocks and their sector averages
for idx, row in combined_df.iterrows():
    # Stock bar
    stock_x_pos = x_categories.index(row['Stock'])
    traces.append(go.Bar(
        x=[stock_x_pos],
        y=[row['P/E Ratio']],
        name=row['Sector'],
        marker_color=sector_color_map[row['Sector']]['base'],
        opacity=0.8,
        width=0.8,
        customdata=[row['Stock']],
        hovertemplate='Stock: %{customdata}<br>P/E Ratio: %{y:.2f}'
    ))

    # Sector average bar
    avg_x_pos = x_categories.index(f"S&P 500 {row['Sector']} Avg")
    traces.append(go.Bar(
        x=[avg_x_pos],
        y=[row['Sector Avg P/E']],
        name=f"{row['Sector']} S&P 500 Avg",
        marker_color=sector_color_map[row['Sector']]['light'],
        opacity=0.8,
        width=0.8,
        customdata=[f"S&P 500 {row['Sector']} Average"],
        hovertemplate='%{customdata}<br>P/E Ratio: %{y:.2f}'
    ))

    # Add marker for sector average
    traces.append(go.Scatter(
        x=[avg_x_pos],
        y=[row['Sector Avg P/E']],
        mode='markers',
        marker=dict(
            color=sector_color_map[row['Sector']]['base'],
            size=10,
            symbol='circle'
        ),
        showlegend=False,
        hovertemplate='S&P 500 Sector Average: %{y:.2f}'
    ))

# Create layout
layout = go.Layout(
    title='Stock P/E Ratios vs S&P 500 Sector Averages',
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(x_categories))),
        ticktext=x_categories,
        tickangle=45,
        tickfont_size=10,
        automargin=True,
        ticklabeloverflow='allow'
    ),
    yaxis=dict(title='P/E Ratio'),
    legend=dict(title='Sector', x=1.05, y=1),
    bargap=0.1,
    bargroupgap=0.1,
    margin=dict(l=50, r=50, t=50, b=50)
)

# Create and show figure
fig = go.Figure(data=traces, layout=layout)
fig.show()