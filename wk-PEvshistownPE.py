import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import logging
import plotly.graph_objects as go
import statistics
import os
import numpy as np
import webbrowser
from dotenv import load_dotenv
load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
TEMPLATE = 'plotly_dark'
SYMBOLS = ['NVO','BRK-B','BABA']  # Replace with your desired stock symbols
YEARS = 10
QUARTERS = 40  # 10 years * 4 quarters per year
RECT_MARGIN = 0.02
CACHE_DIR = 'cache_data'

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def load_json(symbol):
    """Load JSON file containing quarterly EPS."""
    cache_path = os.path.join(CACHE_DIR, f'{symbol}_eps_data.json')
    try:
        with open(cache_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.info(f"No existing EPS data found for {symbol}. Will fetch from API.")
        return None


def save_json(symbol, data):
    """Save JSON file containing quarterly EPS."""
    cache_path = os.path.join(CACHE_DIR, f'{symbol}_eps_data.json')
    with open(cache_path, 'w') as file:
        json.dump(data, file)


def fetch_eps_from_alpha_vantage(symbol):
    """Fetch quarterly EPS from Alpha Vantage."""
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    if response.status_code != 200:
        logging.error(f"Failed to fetch EPS data for {symbol}. Status code: {response.status_code}")
        return None
    data = response.json()
    save_json(symbol, data)
    time.sleep(12)  # To avoid hitting API rate limits
    return data


def create_eps_df(symbol):
    """Create DataFrame for EPS."""
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
    if not quarterly_earnings:
        logging.error(f"No quarterly earnings data found for {symbol}")
        return None

    logging.info(f"Found {len(quarterly_earnings)} quarters of earnings data for {symbol}")

    for idx, x in enumerate(quarterly_earnings):
        if idx == QUARTERS:
            break
        reported_eps = x.get('reportedEPS')
        if reported_eps is not None and reported_eps != 'None':
            try:
                data['fiscalDateEnding'].append(datetime.strptime(x['fiscalDateEnding'], '%Y-%m-%d'))
                data['reportedEPS'].append(float(reported_eps))
            except ValueError:
                logging.warning(
                    f"Invalid EPS value '{reported_eps}' for {symbol} on {x['fiscalDateEnding']}. Skipping this entry.")
        else:
            logging.warning(f"Missing EPS value for {symbol} on {x['fiscalDateEnding']}. Skipping this entry.")

    df = pd.DataFrame(data)
    if not df.empty:
        logging.info(f"Created EPS DataFrame with {len(df)} rows")
        logging.info(f"EPS date range: {df['fiscalDateEnding'].min()} to {df['fiscalDateEnding'].max()}")
        logging.info(f"EPS values range: {df['reportedEPS'].min():.2f} to {df['reportedEPS'].max():.2f}")
    return df


def fetch_price_from_alpha_vantage(symbols, start_date, end_date):
    """Fetch price history from Alpha Vantage with caching mechanism."""
    cache_path = os.path.join(CACHE_DIR, f'{symbols[0]}_price_data.csv')
    if os.path.exists(cache_path):
        logging.info(f"Using cached price data for {symbols[0]}.")
        price_history = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        price_history.columns = [symbols[0]]
        logging.info(f"Loaded {len(price_history)} days of price data")
        logging.info(f"Price date range: {price_history.index.min()} to {price_history.index.max()}")
        logging.info(
            f"Price values range: {price_history[symbols[0]].min():.2f} to {price_history[symbols[0]].max():.2f}")
        return price_history

    price_data = {}
    for symbol in symbols:
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=full'
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Failed to fetch price data for {symbol}. Status code: {response.status_code}")
            continue

        data = response.json()
        if 'Time Series (Daily)' not in data:
            logging.error(f"Failed to retrieve time series data for {symbol}")
            continue

        symbol_price_data = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index', dtype=float)
        symbol_price_data.index = pd.to_datetime(symbol_price_data.index)
        symbol_price_data = symbol_price_data[['4. close']]
        symbol_price_data.columns = [symbol]

        price_data[symbol] = symbol_price_data
        time.sleep(12)

    price_history = pd.concat(price_data.values(), axis=1)
    price_history.to_csv(cache_path)
    logging.info(f"Cached price data for {', '.join(symbols)}.")

    return price_history.sort_index()


def get_eps(date, eps_df):
    """Get the most recent EPS value for a given date."""
    mask = eps_df['fiscalDateEnding'] <= date
    if mask.any():
        recent_eps = eps_df.loc[mask].iloc[-1]['reportedEPS']
        return recent_eps
    return np.nan


def create_pe_df(symbol, eps_df, price_history):
    """Create PE DataFrame."""
    ticker_history = price_history[symbol]
    pe_dict = {
        'Date': [],
        'PE': []
    }

    valid_pe_count = 0
    nan_pe_count = 0

    for index, row in ticker_history.items():
        close_date = index.replace(tzinfo=None)
        eps = get_eps(close_date, eps_df)
        pe_dict['Date'].append(close_date)
        if np.isnan(eps) or eps <= 0:
            pe_dict['PE'].append(np.NaN)
            nan_pe_count += 1
        else:
            pe_dict['PE'].append(row / eps)
            valid_pe_count += 1

    logging.info(f"Created {valid_pe_count} valid PE ratios and {nan_pe_count} NaN values")
    df = pd.DataFrame(pe_dict)
    if not df.empty and df['PE'].notna().any():
        logging.info(f"PE ratios range: {df['PE'].min():.2f} to {df['PE'].max():.2f}")
    return df


def plot_pe(symbol, pe_df, start_date, end_date):
    """Plot PE and save as HTML."""
    fig = go.Figure()

    # Plot the PE ratio
    fig.add_trace(go.Scatter(x=pe_df.Date, y=pe_df.PE, line_color='lightgreen', line_width=1, name='P/E Ratio'))

    # Update y & x axis labels
    fig.update_yaxes(title_text='P/E Ratio')
    fig.update_xaxes(title_text='Date')

    layout = go.Layout(template=TEMPLATE, title=f'P/E Ratio for {symbol} from {start_date.date()} to {end_date.date()}',
                       height=700)

    fig.update_layout(layout)

    pe_values = pe_df['PE'].dropna()
    if len(pe_values) > 0:
        std = statistics.stdev(pe_values)
        mean = statistics.mean(pe_values)

        # Plot the low threshold
        low = mean - (1 * std)
        fig.add_hline(y=low, line_color='limegreen', line_width=1, annotation_text='Low Threshold',
                      annotation_position='bottom right')
        fig.add_hrect(y0=pe_values.min() * (1 - RECT_MARGIN), y1=low, line_width=0, fillcolor='green', opacity=0.2)

        # Plot the high threshold
        high = mean + (1 * std)
        fig.add_hline(y=high, line_color='red', line_width=1, annotation_text='High Threshold',
                      annotation_position='top right')
        fig.add_hrect(y0=high, y1=pe_values.max() * (1 + RECT_MARGIN), line_width=0, fillcolor='indianred', opacity=0.2)

        # Plot the mean line
        fig.add_hrect(y0=low, y1=high, line_width=0, fillcolor='orange', opacity=0.2)
        fig.add_hline(y=mean, line_color='darkorange', line_width=1, annotation_text='Mean',
                      annotation_position='top right')

        # Maximum PE
        max_row = pe_df.loc[pe_df.PE.idxmax()]
        fig.add_trace(go.Scatter(x=[max_row.Date], y=[max_row.PE], mode='markers+text', name='Max',
                                 marker_line_color='red', marker_color='white', marker_line_width=2,
                                 marker_size=10, text='Maximum', textposition='top center',
                                 textfont=dict(color='white')))

        # Minimum PE
        min_row = pe_df.loc[pe_df.PE.idxmin()]
        fig.add_trace(go.Scatter(x=[min_row.Date], y=[min_row.PE], mode='markers+text', name='Min',
                                 marker_line_color='green', marker_color='white', marker_line_width=2,
                                 marker_size=10, text='Minimum', textposition='bottom center',
                                 textfont=dict(color='white')))

    # Save and open the chart
    output_file = os.path.abspath(f'{symbol}_pe_chart.html')
    fig.write_html(output_file)
    logging.info(f"Chart saved to: {output_file}")
    webbrowser.open('file://' + output_file)


def calculate_average_pe_ratio(pe_df):
    """Calculate average PE ratio."""
    return pe_df['PE'].dropna().mean()


def main():
    """Main function to run the PE ratio analysis."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        logging.info(f"Created cache directory: {CACHE_DIR}")

    end_date = datetime.now()
    start_date = end_date - timedelta(365 * YEARS)
    price_history = fetch_price_from_alpha_vantage(SYMBOLS, start_date, end_date)

    if price_history is None:
        logging.error("Price history data retrieval failed. Exiting.")
        return

    for symbol in SYMBOLS:
        logging.info(f"Processing {symbol}...")
        eps_df = create_eps_df(symbol)
        if eps_df is not None and not eps_df.empty:
            pe_df = create_pe_df(symbol, eps_df, price_history)
            if pe_df is not None and not pe_df.empty:
                plot_pe(symbol, pe_df, start_date, end_date)
                average_pe_ratio = calculate_average_pe_ratio(pe_df)
                current_pe = pe_df.iloc[-1].PE
                comparison = "cheaper" if current_pe < average_pe_ratio else "more expensive"
                logging.info(f'{YEARS}-Year Average P/E Ratio for {symbol}: {average_pe_ratio:.2f}')
                logging.info(
                    f'Current P/E Ratio for {symbol}: {current_pe:.2f} ({comparison} than the {YEARS}-year average)')
            else:
                logging.error(f"Unable to create PE DataFrame for {symbol}")
        else:
            logging.error(f"Unable to create EPS DataFrame for {symbol}")

    logging.info("Processing complete. Chart should open in your default web browser.")


if __name__ == "__main__":
    main()
