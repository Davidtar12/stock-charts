import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import plotly.graph_objects as go
import statistics
import requests
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import os
load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TEMPLATE = 'plotly_dark'
SYMBOLS = ['AAPL','ABT','ADBE','ALGN','ANSS','BLD','EPAM','GRMN',
           'MEDP','TDY','TER','TMO','ZTS','MAS','EXEL','CNI','ROST'
]   # Replace with your desired stock symbols
YEARS = 10
QUARTERS = 40  # 10 years * 4 quarters per year
RECT_MARGIN = 0.02
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Initialize a session with a larger connection pool
session = requests.Session()
adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Load JSON file containing quarterly EPS
def load_json(symbol):
    try:
        with open(f'{symbol}_eps_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.info(f"No existing EPS data found for {symbol}. Will fetch from API.")
        return None

# Save JSON file containing quarterly EPS
def save_json(symbol, data):
    with open(f'{symbol}_eps_data.json', 'w') as file:
        json.dump(data, file)

# Fetch quarterly EPS from Alpha Vantage
def fetch_eps_from_alpha_vantage(symbol):
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = session.get(url)
    if response.status_code != 200:
        logging.error(f"Failed to fetch EPS data for {symbol}. Status code: {response.status_code}")
        return None
    data = response.json()
    save_json(symbol, data)
    time.sleep(12)  # To avoid hitting API rate limits
    return data

# Check if a value can be converted to float
def is_convertible_to_float(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

# Create DataFrame for EPS
def create_eps_df(symbol):
    json_data = load_json(symbol)
    if json_data is None:
        json_data = fetch_eps_from_alpha_vantage(symbol)
        if json_data is None:
            return None

    data = {
        'fiscalDateEnding': [],
        'reportedEPS': []
    }

    quarterly_earnings = json_data.get('quarterlyEarnings', [])
    for idx, x in enumerate(quarterly_earnings):
        if idx == QUARTERS:
            break
        reported_eps = x.get('reportedEPS')
        if is_convertible_to_float(reported_eps):
            data['fiscalDateEnding'].append(datetime.strptime(x['fiscalDateEnding'], '%Y-%m-%d'))
            data['reportedEPS'].append(float(reported_eps))
        else:
            logging.warning(f"Non-numeric reportedEPS value '{reported_eps}' for {symbol} on {x['fiscalDateEnding']}")
    return pd.DataFrame(data)

# Get EPS for a Date
def get_eps(search_date, eps_df):
    start_date = search_date - timedelta(365)
    eps_quarters = list(filter(lambda x: x <= search_date and x > start_date, eps_df['fiscalDateEnding']))
    if len(eps_quarters) == 4:
        return eps_df[eps_df['fiscalDateEnding'].isin(eps_quarters)]['reportedEPS'].sum()
    logging.warning(f"Not enough EPS quarters for date {search_date}")
    return np.NaN

# Get the price history for the symbol from Yahoo Finance
def get_price_history(symbols, years):
    end_date = datetime.now()
    start_date = end_date - timedelta(365 * years)
    data = yf.download(symbols, start=start_date, end=end_date)['Close']
    return data, start_date, end_date

# Create PE DataFrame
def create_pe_df(symbol, eps_df, price_history):
    ticker_history = price_history[symbol]
    pe_dict = {
        'Date': [],
        'PE': []
    }
    for index, row in ticker_history.items():
        close_date = index.replace(tzinfo=None)
        eps = get_eps(close_date, eps_df)
        pe_dict['Date'].append(close_date)
        if np.isnan(eps) or eps <= 0:
            logging.warning(f'Unable to calculate PE for {symbol} on {close_date}')
            pe_dict['PE'].append(np.NaN)
        else:
            pe_dict['PE'].append(row / eps)
    return pd.DataFrame(pe_dict)

# Plot PE and save as HTML
def plot_pe(symbol, pe_df, start_date, end_date):
    fig = go.Figure()

    # Plot the PE ratio
    fig.add_trace(go.Scatter(x=pe_df.Date, y=pe_df.PE, line_color='lightgreen', line_width=1, name='P/E Ratio'))

    # Update y & x axis labels
    fig.update_yaxes(title_text='P/E Ratio')
    fig.update_xaxes(title_text='Date')

    layout = go.Layout(template=TEMPLATE, title=f'P/E Ratio for {symbol} from {start_date.date()} to {end_date.date()}', height=700)

    # Update options and layout
    fig.update_layout(layout)

    # Calculate standard deviation and mean
    pe_values = pe_df['PE'].dropna()
    if len(pe_values) > 0:
        std = statistics.stdev(pe_values)
        mean = statistics.mean(pe_values)

        # Plot the low threshold
        low = mean - (1 * std)
        fig.add_hline(y=low, line_color='limegreen', line_width=1, annotation_text='Low Threshold', annotation_position='bottom right')
        fig.add_hrect(y0=pe_values.min() * (1 - RECT_MARGIN), y1=low, line_width=0, fillcolor='green', opacity=0.2)

        # Plot the high threshold
        high = mean + (1 * std)
        fig.add_hline(y=high, line_color='red', line_width=1, annotation_text='High Threshold', annotation_position='top right')
        fig.add_hrect(y0=high, y1=pe_values.max() * (1 + RECT_MARGIN), line_width=0, fillcolor='red', opacity=0.2)

    fig.write_html(f'{symbol}_pe_chart.html')
    logging.info(f"P/E chart for {symbol} saved as HTML.")

# Main function
def main():
    price_history, start_date, end_date = get_price_history(SYMBOLS, YEARS)
    for symbol in SYMBOLS:
        eps_df = create_eps_df(symbol)
        if eps_df is not None and not eps_df.empty:
            pe_df = create_pe_df(symbol, eps_df, price_history)
            plot_pe(symbol, pe_df, start_date, end_date)
        else:
            logging.warning(f"Skipping {symbol} due to insufficient data.")

if __name__ == '__main__':
    main()
