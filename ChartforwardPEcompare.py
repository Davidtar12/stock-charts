import yfinance as yf
import plotly.graph_objects as go

# List of tickers to compare
tickers = ['FXAIX', 'VOO', 'VFIAX', 'SPY', 'VIGAX', 'VITAX', 'FTEC', 'QQQ','VGT', 'VUG','VTI','LRCX', 'YUM', 'MCD', 'CNI', 'V', 'NDSN', 'ROST', 'MAR', 'MAS', 'TJX', 'ADP', 'TER', 'ORLY', 'CPRT', 'HLT', 'NKE', 'NVDA', 'AMD','ADBE','AXP','NU','BKNG','DPZ','PZZA','RDDT','INTC']

# Fetch data from yfinance
data = {ticker: yf.Ticker(ticker).info for ticker in tickers}

# Extract PEG ratio, Forward PE, and TTM PE
peg_ratios = [data[ticker].get('pegRatio', None) for ticker in tickers]
forward_pe = [data[ticker].get('forwardPE', None) for ticker in tickers]
ttm_pe = [data[ticker].get('trailingPE', None) for ticker in tickers]

# Create a Plotly bar chart
fig = go.Figure()

# Add bars for PEG ratio
fig.add_trace(go.Bar(
    x=tickers,
    y=peg_ratios,
    name='PEG Ratio',
    text=peg_ratios,
    textposition='auto',
    marker_color='blue'
))

# Add bars for Forward PE
fig.add_trace(go.Bar(
    x=tickers,
    y=forward_pe,
    name='Forward PE',
    text=forward_pe,
    textposition='auto',
    marker_color='green'
))

# Add bars for TTM PE
fig.add_trace(go.Bar(
    x=tickers,
    y=ttm_pe,
    name='TTM PE',
    text=ttm_pe,
    textposition='auto',
    marker_color='orange'
))

# Update layout for better visualization
fig.update_layout(
    title='PEG Ratio, Forward PE, and TTM PE Comparison',
    xaxis_title='Tickers',
    yaxis_title='Values',
    barmode='group',
    legend_title='Metrics',
    annotations=[
        dict(
            x=0.5,
            y=-0.2,
            showarrow=False,
            text="PEG Ratio: <1 is considered undervalued (Peter Lynch's ideal range).<br>"
                 "Forward PE: Lower is better, but should be compared with growth rate.<br>"
                 "TTM PE: Lower is better, but should be compared with industry average.",
            xref="paper",
            yref="paper"
        )
    ]
)

# Show the plot
fig.show()