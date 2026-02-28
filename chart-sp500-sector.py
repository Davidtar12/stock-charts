import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import json

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
            sectors_cached[modified_symbol] = sector
            time.sleep(1)  # Delay to respect rate limits
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
            time.sleep(1)  # Delay to respect rate limits
        except Exception as e:
            print(f"Error fetching P/E ratio for {modified_symbol}: {e}")
            pe_ratio = None
    all_stock_data.append({
        'Stock': modified_symbol,
        'P/E Ratio': pe_ratio,
        'Sector': sectors_cached.get(modified_symbol, 'Unknown')
    })

# Save the updated P/E ratio cache
with open('pe_ratio_cache.json', 'w') as f:
    json.dump(pe_cached, f)

# Create DataFrame
df = pd.DataFrame(all_stock_data)

# Ensure 'P/E Ratio' is numeric
df['P/E Ratio'] = pd.to_numeric(df['P/E Ratio'], errors='coerce')

# Calculate sector averages
sector_avg = df.groupby('Sector')['P/E Ratio'].mean().reset_index()
sector_avg.rename(columns={'P/E Ratio': 'Avg P/E Ratio'}, inplace=True)
sector_avg['Stock'] = 'Avg ' + sector_avg['Sector']
sector_avg['Is_Avg'] = True

# Add a flag to original stocks
df['Is_Avg'] = False

# Combine stock data with sector averages
combined_df = pd.concat([df, sector_avg], ignore_index=True)

# Create a 'Group' column for sorting
combined_df['Group'] = combined_df['Sector'] + '_' + combined_df['Is_Avg'].map({False: 'stock', True: 'avg'})

# Sort the data by 'Group'
combined_df.sort_values(by='Group', inplace=True)

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

# Create the figure
fig = go.Figure()

# Plot stocks and averages
fig.add_trace(go.Bar(
    x=combined_df['Stock'],
    y=combined_df['P/E Ratio'],
    marker_color=combined_df['Color'],
    text=combined_df['P/E Ratio'].round(2).astype(str),
    textposition='auto',
    hovertemplate='%{x}: %{y:.2f}<br>Sector: %{customdata}<extra></extra>',
    customdata=combined_df['Sector'],
    showlegend=False  # Hide individual traces from the legend
))

# Add sector names to the legend
for sector in unique_sectors:
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker_color=sector_color_map[sector]['base'],
        name=sector
    ))

fig.update_layout(
    title='P/E Ratio Comparison by Sector',
    xaxis_title='Stock',
    yaxis_title='P/E Ratio',
    barmode='group',
    xaxis_tickangle=-45,
    legend_title='Sector'
)

fig.show()