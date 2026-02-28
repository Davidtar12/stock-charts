import yfinance as yf
import pandas as pd
from pandas.tseries.offsets import DateOffset
import plotly.graph_objects as go
import os
import pickle  # For caching data


# Function to fetch S&P 500 components from Wikipedia
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    sp500_df = tables[0]
    return sp500_df['Symbol'].tolist()


# Function to fetch NASDAQ-100 components from Wikipedia
def get_nasdaq100_tickers():
    url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
    tables = pd.read_html(url)

    # The NASDAQ-100 table is the fifth table on the page
    nasdaq100_df = tables[4]  # Index 4 corresponds to the fifth table

    # Check if the table has the required columns
    if 'Symbol' in nasdaq100_df.columns:
        return nasdaq100_df['Symbol'].tolist()
    else:
        raise ValueError("No 'Symbol' column found in the NASDAQ-100 table.")


# Function to fetch tickers from Excel and CSV files in the specified folder
def get_tickers_from_excel_csv_files(folder_path):
    tickers = set()  # Using a set to ensure uniqueness

    # Iterate through all files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".xlsx") or file_name.endswith(".xls") or file_name.endswith(".csv"):  # Include CSV files
            file_path = os.path.join(folder_path, file_name)
            try:
                # Read the file (auto-detect Excel or CSV format)
                if file_name.endswith(".csv"):
                    df = pd.read_csv(file_path)  # Read CSV file
                else:
                    df = pd.read_excel(file_path)  # Read Excel file

                # Check for 'ticker' column and process
                if 'ticker' in df.columns:  # Ensure the 'ticker' column exists
                    tickers.update(df['ticker'].dropna().astype(str))  # Drop NaN values and convert to string
                else:
                    print(f"'ticker' column not found in file: {file_name}")
            except Exception as e:
                print(f"Failed to read {file_name}: {e}")

    # Convert the set to a sorted list
    return sorted(tickers)


# Function to combine all tickers
def get_all_tickers(folder_path):
    sp500_tickers = get_sp500_tickers()
    nasdaq100_tickers = get_nasdaq100_tickers()
    excel_csv_tickers = get_tickers_from_excel_csv_files(folder_path)

    # Combine all tickers into a single set to avoid duplicates
    all_tickers = set(sp500_tickers + nasdaq100_tickers + excel_csv_tickers)
    all_tickers.add('SPY')  # Add SPY for comparison
    return list(all_tickers)


# Function to create individual charts for each ETF/index and time period
def create_individual_charts(adj_close_df, periods, output_folder):
    for label, offset in periods.items():
        if label == 'YTD':
            start_date = pd.Timestamp(year=pd.Timestamp.today().year, month=1, day=1)
        else:
            start_date = end_date - offset
        period_data = adj_close_df.loc[start_date:end_date]
        period_data = period_data.dropna(axis=1, how='any')

        # Normalize data to start at 100
        normalized_data = period_data / period_data.iloc[0] * 100

        # Calculate percentage change
        pct_change = (period_data.iloc[-1] / period_data.iloc[0] - 1) * 100

        # Sort tickers by performance
        sorted_tickers = sorted(period_data.columns, key=lambda x: pct_change[x], reverse=True)

        # Create a chart for each ETF/index
        for etf in ['S&P 500', 'NASDAQ-100', 'ExcelCSV ETFs']:
            fig = go.Figure()

            # Add traces for the specific ETF/index
            if etf == 'S&P 500':
                tickers = get_sp500_tickers()
            elif etf == 'NASDAQ-100':
                tickers = get_nasdaq100_tickers()
            elif etf == 'ExcelCSV ETFs':
                tickers = get_tickers_from_excel_csv_files(folder_path)

            for ticker in sorted_tickers:
                if ticker in tickers:
                    fig.add_trace(go.Scatter(
                        x=normalized_data.index,
                        y=normalized_data[ticker],
                        mode='lines',
                        name=f"{ticker} ({pct_change[ticker]:.2f}%)"
                    ))

            # Update layout
            fig.update_layout(
                title=f'{label} Performance for {etf}',
                xaxis_title='Date',
                yaxis_title='Normalized Adj Close Price (Start=100)',
                legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
                xaxis=dict(tickformat='%Y-%m', dtick='M12', tickmode='auto'),
                width=1600,
                height=1000
            )

            # Save the chart to an HTML file
            output_file = os.path.join(output_folder, f"{etf}_{label}_performance.html")
            fig.write_html(output_file)
            print(f"Chart saved to {output_file}")


# Main script execution
if __name__ == "__main__":
    # Define the folder path where the Excel and CSV files are located
    folder_path = r"C:\path\to\your_data"

    # Define periods for performance comparison
    periods = {
        '1M': DateOffset(months=1),
        '2M': DateOffset(months=2),
        '3M': DateOffset(months=3),
        '4M': DateOffset(months=4),
        '5M': DateOffset(months=5),
        'YTD': 'YTD',  # Special case for Year-To-Date
        '6M': DateOffset(months=6),
        '1Y': DateOffset(years=1),
        '2Y': DateOffset(years=2),
        '3Y': DateOffset(years=3),
        '4Y': DateOffset(years=4),
        '10Y': DateOffset(years=10)
    }

    # Set date ranges
    end_date = pd.Timestamp.today()
    start_date_max = end_date - DateOffset(years=10)  # Cover the longest period

    # Check if cached data exists
    cache_file = "adj_close_data.pkl"
    if os.path.exists(cache_file):
        print("Loading cached data...")
        with open(cache_file, "rb") as f:
            adj_close_data = pickle.load(f)
    else:
        # Fetch all tickers
        tickers_list = get_all_tickers(folder_path)

        # Download historical data
        adj_close_data = {}
        for ticker in tickers_list:
            try:
                print(f"Downloading data for {ticker}...")
                ticker_data = yf.download(ticker, start=start_date_max, end=end_date)
                if 'Adj Close' in ticker_data.columns and not ticker_data['Adj Close'].isnull().all():
                    adj_close_data[ticker] = ticker_data['Adj Close']
                else:
                    print(f"'Adj Close' not found or empty for {ticker}")
            except Exception as e:
                print(f"Error downloading data for {ticker}: {e}")

        # Save the downloaded data to a cache file
        with open(cache_file, "wb") as f:
            pickle.dump(adj_close_data, f)
        print(f"Data cached to {cache_file}")

    # Convert the dictionary to a DataFrame
    adj_close_df = pd.DataFrame(adj_close_data)
    adj_close_df = adj_close_df.ffill()  # Forward-fill missing data

    # Create individual charts for each ETF/index and time period
    output_folder = r"C:\path\to\your_data"
    os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
    create_individual_charts(adj_close_df, periods, output_folder)