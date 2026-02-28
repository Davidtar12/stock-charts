import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Function to adjust color brightness
def adjust_color_brightness(color, factor):
    # Convert hex to RGB
    color = color.lstrip('#')
    r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    # Adjust RGB values
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    # Ensure values are within 0-255
    r = min(max(r, 0), 255)
    g = min(max(g, 0), 255)
    b = min(max(b, 0), 255)
    # Convert back to hex
    return f'#{r:02x}{g:02x}{b:02x}'

# List of stock tickers
tickers = ['LRCX', 'NVDA','EXEL','SMCI','FIX','CNI']


# Function to fetch P/E ratio and sector for each ticker
def fetch_stock_data(tickers):
    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe_ratio = info.get('trailingPE', None)
        sector = info.get('sector', 'Unknown')
        data.append({'Stock': ticker, 'P/E Ratio': pe_ratio, 'Sector': sector})
    return pd.DataFrame(data)

# Fetch stock data
df = fetch_stock_data(tickers)

# Calculate sector averages
sector_avg = df.groupby('Sector')['P/E Ratio'].mean().reset_index()
sector_avg['Stock'] = 'Avg ' + sector_avg['Sector']
sector_avg['Is_Avg'] = True

# Add a flag to original stocks
df['Is_Avg'] = False

# Combine stock data with sector averages
combined_df = pd.concat([df, sector_avg]).reset_index(drop=True)

# Create a 'Group' column
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
    text=combined_df['P/E Ratio'].astype(str),
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