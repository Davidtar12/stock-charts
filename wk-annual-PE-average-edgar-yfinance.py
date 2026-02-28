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
from edgar import Company, set_identity

# Set your identity for accessing EDGAR (set EDGAR_IDENTITY in .env)
set_identity(os.getenv("EDGAR_IDENTITY", "your.email@example.com"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TEMPLATE = 'plotly_dark'
SYMBOLS = ['GE']  # Replace with your desired stock symbols
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
        logging.info(f"No existing EPS data found for {symbol}. Will fetch from Edgar.")
        return None


def save_json(symbol, data):
    """Save JSON file containing quarterly EPS."""
    cache_path = os.path.join(CACHE_DIR, f'{symbol}_eps_data.json')
    with open(cache_path, 'w') as file:
        json.dump(data, file)


def fetch_eps_from_edgar(symbol):
    """Fetch EPS from Edgar for each year."""
    try:
        company = Company(symbol)

        # Fetch the income statement
        income_statement = company.financials.get_income_statement()

        # Filter for Earnings Per Share (Basic and Diluted)
        basic_eps_row = income_statement.data[income_statement.data['concept'] == 'us-gaap_EarningsPerShareBasic']

        eps_data = {}

        if not basic_eps_row.empty:
            # Extract the basic EPS for each year and store it in a dictionary
            for year in basic_eps_row.columns:
                eps_value = basic_eps_row[year].values[0]

                if eps_value is None:
                    logging.warning(f"EPS value for {symbol} in year {year} is missing.")
                    continue

                try:
                    # Attempt to convert the value to a float
                    eps_data[int(year)] = float(eps_value)
                except ValueError as e:
                    logging.warning(f"Skipping invalid EPS value for {symbol} in year {year}: {eps_value}")
                    continue

        return eps_data
    except Exception as e:
        logging.error(f"Error fetching EPS from Edgar for {symbol}: {str(e)}")
        return None


def fetch_price_data(symbols, start_date, end_date):
    """Fetch price history from yfinance."""
    price_data = {}
    for symbol in symbols:
        logging.info(f"Downloading price data for {symbol} from yfinance")
        try:
            # Use yfinance to get historical price data
            import yfinance as yf
            stock_data = yf.download(symbol, start=start_date, end=end_date)

            if stock_data.empty:
                logging.error(f"No price data found for {symbol} in the specified date range")
                continue

            price_data[symbol] = stock_data['Close']

        except Exception as e:
            logging.error(f"Error downloading price data for {symbol}: {str(e)}")
            continue

    if not price_data:
        return None

    # Combine all price data into a single DataFrame
    price_history = pd.concat(price_data.values(), axis=1)
    price_history.columns = price_data.keys()
    logging.info(f"Fetched price data for {', '.join(symbols)}")
    return price_history


def get_eps(date, eps_data):
    """Get the most recent EPS value for a given date."""
    year = date.year
    if year in eps_data:
        return eps_data[year]
    return np.nan


def create_pe_df(symbol, eps_data, price_history):
    """Create annual PE DataFrame."""

    # Check if eps_data is a dictionary of scalar values
    if isinstance(eps_data, dict):
        # If eps_data contains scalar values, we need to add an index to create a DataFrame
        if not eps_data:
            logging.error(f"No valid EPS data for {symbol}")
            return None

        # Assuming the data contains a 'fiscalDateEnding' (year) and 'reportedEPS' (EPS value)
        # You should update the structure of eps_data if needed
        eps_data_cleaned = []
        for year, eps in eps_data.items():
            eps_data_cleaned.append({'Year': year, 'reportedEPS': eps})

        # Now create a DataFrame
        eps_df = pd.DataFrame(eps_data_cleaned)

    else:
        eps_df = eps_data

    # Ensure 'Year' column exists
    if 'Year' not in eps_df.columns:
        logging.error(f"Missing 'Year' in EPS data for {symbol}")
        logging.error(f"EPS DataFrame columns: {eps_df.columns}")
        return None

    pe_data = []

    # Group price data by year and calculate the average for each year
    price_history['Year'] = price_history.index.year
    annual_price = price_history.groupby('Year').mean()

    # Merge the annual price data with EPS data
    eps_df['Year'] = eps_df['Year']  # Ensure Year column is set
    annual_eps = eps_df.groupby('Year').agg({'reportedEPS': 'mean'})

    # Calculate P/E for each year (Price / EPS)
    for year in annual_price.index:
        price = annual_price.loc[year, symbol] if year in annual_price.index else None
        eps = annual_eps.loc[year, 'reportedEPS'] if year in annual_eps.index else None
        if price is not None and eps is not None and eps > 0:
            pe_data.append({'Year': year, 'PE': price / eps})

    if not pe_data:
        return None

    df = pd.DataFrame(pe_data)
    logging.info(f"Created annual PE DataFrame with {len(df)} valid entries")
    return df


def plot_pe(symbol, pe_df, start_date, end_date):
    """Plot P/E ratio for the given symbol."""

    if pe_df is None or pe_df.empty:
        logging.warning(f"No data available to plot for {symbol}")
        return

    # Make sure the 'Year' column exists in pe_df
    if 'Year' not in pe_df.columns:
        logging.error(f"Missing 'Year' column in PE DataFrame for {symbol}")
        return

    fig = go.Figure()

    # Plotting the PE data by year
    fig.add_trace(go.Scatter(x=pe_df['Year'], y=pe_df['PE'],
                             mode='lines+markers', name=f'{symbol} P/E Ratio'))

    # Set axis labels and title
    fig.update_layout(
        title=f'{symbol} P/E Ratio Over Time',
        xaxis_title='Year',
        yaxis_title='P/E Ratio',
        showlegend=True
    )

    # Show the plot
    fig.show()

    # Save and open
    output_file = os.path.abspath(f'{symbol}_pe_chart.html')
    fig.write_html(output_file)
    webbrowser.open('file://' + output_file)


def main():
    """Main function to run the PE ratio analysis."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * YEARS)

    for symbol in SYMBOLS:
        logging.info(f"Processing {symbol}")

        # Get EPS data from Edgar
        eps_data = fetch_eps_from_edgar(symbol)
        if eps_data is None or not eps_data:
            continue

        # Get price data
        price_history = fetch_price_data([symbol], start_date, end_date)
        if price_history is None:
            continue

        # Calculate PE ratios
        pe_df = create_pe_df(symbol, eps_data, price_history)
        if pe_df is None or pe_df.empty:
            continue

        # Generate plot
        plot_pe(symbol, pe_df, start_date, end_date)

        # Display statistics
        current_pe = pe_df.iloc[-1].PE
        avg_pe = pe_df['PE'].mean()
        logging.info(f"Current P/E: {current_pe:.2f}")
        logging.info(f"{YEARS}-Year Average P/E: {avg_pe:.2f}")
        logging.info(f"Valuation: {'Undervalued' if current_pe < avg_pe else 'Overvalued'}")

    logging.info("Analysis complete")


if __name__ == "__main__":
    main()
