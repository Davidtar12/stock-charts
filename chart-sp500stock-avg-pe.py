import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np

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

# Load cached P/E ratio data
try:
    with open('pe_ratio_cache.json', 'r') as f:
        pe_cached = json.load(f)
except FileNotFoundError:
    pe_cached = {}

# Fetch S&P 500 components from Wikipedia
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
tables = pd.read_html(url)
sp500_df = tables[0]
symbols = sp500_df['Symbol'].tolist()

# Fetch sector data
sectors = {}
for symbol in symbols:
    modified_symbol = symbol.replace('.', '-')
    if modified_symbol in sectors_cached:
        sector = sectors_cached[modified_symbol]
    else:
        try:
            stock = yf.Ticker(modified_symbol)
            sector = stock.info.get('sector', 'Unknown')
            # Manual adjustment for Financial Services
            if sector in ['Financials', 'Finance']:
                sector = 'Financial Services'
            sectors_cached[modified_symbol] = sector
        except Exception as e:
            print(f"Error fetching sector for {modified_symbol}: {e}")
            sector = 'Unknown'
    sectors.setdefault(sector, []).append(modified_symbol)

# Save the updated sector cache
with open('sector_cache.json', 'w') as f:
    json.dump(sectors_cached, f)

# Fetch P/E ratios for all S&P 500 stocks
all_stock_data = []
for symbol in symbols:
    modified_symbol = symbol.replace('.', '-')
    if modified_symbol in pe_cached:
        pe_ratio = pe_cached[modified_symbol]
    else:
        try:
            stock = yf.Ticker(modified_symbol)
            pe_ratio = stock.info.get('trailingPE', None)
            pe_cached[modified_symbol] = pe_ratio
        except Exception as e:
            print(f"Error fetching P/E ratio for {modified_symbol}: {e}")
            pe_ratio = None
    all_stock_data.append({
        'Stock': modified_symbol,
        'P/E Ratio': pe_ratio,
        'Sector': sectors_cached.get(modified_symbol, 'Unknown'),
        'Is_Avg': False
    })

# Save the updated P/E ratio cache
with open('pe_ratio_cache.json', 'w') as f:
    json.dump(pe_cached, f)

# Create DataFrame
combined_df = pd.DataFrame(all_stock_data)

# Ensure 'P/E Ratio' is numeric and handle missing values
combined_df['P/E Ratio'] = pd.to_numeric(combined_df['P/E Ratio'], errors='coerce')

# Replace inf with NaN
combined_df['P/E Ratio'].replace([np.inf, -np.inf], np.nan, inplace=True)

# Calculate sector averages, excluding NaN values
sector_avg = combined_df.groupby('Sector')['P/E Ratio'].mean().reset_index()
sector_avg.rename(columns={'P/E Ratio': 'Avg P/E Ratio'}, inplace=True)
sector_avg['Stock'] = 'Avg ' + sector_avg['Sector']
sector_avg['Is_Avg'] = True

# Combine stock data with sector averages
combined_df = pd.concat([combined_df, sector_avg], ignore_index=True)

# Debugging: Verify sector averages
print("Sector Averages:", sector_avg)

# Generate color schemes for sectors
unique_sectors = combined_df['Sector'].unique()
base_colors = px.colors.qualitative.Plotly
sector_color_map = {}
for i, sector in enumerate(unique_sectors):
    base_color = base_colors[i % len(base_colors)]
    sector_color_map[sector] = {
        'base': base_color,
        'light': adjust_color_brightness(base_color, 1.1)
    }

# Assign colors to stocks and averages
combined_df['Color'] = combined_df.apply(
    lambda row: sector_color_map[row['Sector']]['base'] if not row['Is_Avg'] else sector_color_map[row['Sector']]['light'],
    axis=1
)

# Assign group numbers to sectors for ordering
sectors_ordered = sorted(combined_df['Sector'].unique().tolist())
sector_groups = {sector: idx for idx, sector in enumerate(sectors_ordered)}
combined_df['Group'] = combined_df['Sector'].map(sector_groups)

# Sort the DataFrame by 'Group' and 'Is_Avg'
combined_df.sort_values(by=['Group', 'Is_Avg'], inplace=True)

# Assign x_position
combined_df['x_position'] = combined_df.apply(
    lambda row: row['Stock'] if not row['Is_Avg'] else f"Avg {row['Sector']}",
    axis=1
)

# Create x_categories list
x_categories = []
for sector in sectors_ordered:
    sector_stocks = combined_df[(combined_df['Sector'] == sector) & (combined_df['Is_Avg'] == False)]['x_position'].tolist()
    x_categories.extend(sector_stocks)
    x_categories.append(f"Avg {sector}")

# Assign 'x_num' based on x_categories order
combined_df['x_num'] = combined_df['x_position'].apply(lambda x: x_categories.index(x))

# Create empty list for traces
traces = []

# Create bar traces for individual stocks
for sector in sectors_ordered:
    sector_stocks = combined_df[(combined_df['Sector'] == sector) & (combined_df['Is_Avg'] == False)]
    traces.append(go.Bar(
        x=sector_stocks['x_num'],
        y=sector_stocks['P/E Ratio'],
        name=sector,
        marker_color=sector_color_map[sector]['base'],
        opacity=0.8,
        width=0.8
    ))

# Create bar traces for sector averages
for sector in sectors_ordered:
    avg_row = combined_df[(combined_df['Sector'] == sector) & (combined_df['Is_Avg'] == True)]
    if not avg_row.empty:
        traces.append(go.Bar(
            x=[x_categories.index(f"Avg {sector}")],
            y=[avg_row['Avg P/E Ratio'].values[0]],
            name=sector,
            marker_color=sector_color_map[sector]['light'],
            opacity=0.8,
            width=0.8
        ))

# Add scatter traces for average points
for sector in sectors_ordered:
    avg_row = combined_df[(combined_df['Sector'] == sector) & (combined_df['Is_Avg'] == True)]
    if not avg_row.empty:
        traces.append(go.Scatter(
            x=[x_categories.index(f"Avg {sector}")],
            y=[avg_row['Avg P/E Ratio'].values[0]],
            mode='markers',
            marker=dict(color=sector_color_map[sector]['base'], size=10, symbol='circle'),
            showlegend=False
        ))

# Create layout with adjusted settings
layout = go.Layout(
    title='P/E Ratio by Stock and Sector Average',
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(x_categories))),
        ticktext=x_categories,
        tickangle=90,
        tickfont_size=10
    ),
    yaxis=dict(title='P/E Ratio'),
    legend=dict(title='Sector', x=1.05, y=1),
    bargap=0.1,
    bargroupgap=0.1,
    margin=dict(l=0, r=0, t=30, b=0)
)

# Create the figure
fig = go.Figure(data=traces, layout=layout)

# Update hover templates
fig.update_traces(hovertemplate='Stock: %{customdata}<br>P/E Ratio: %{y}', selector=dict(type='bar'))

# Set customdata for hover
for trace in fig.data:
    if trace.name in sectors_ordered:
        trace.customdata = combined_df.loc[combined_df['Sector'] == trace.name, 'x_position'].tolist()

# Show the plot
fig.show()