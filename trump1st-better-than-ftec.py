import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import os
import pickle
import requests
from dotenv import load_dotenv
load_dotenv()


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
    nasdaq100_df = tables[4]
    if 'Symbol' in nasdaq100_df.columns:
        return nasdaq100_df['Symbol'].tolist()
    else:
        raise ValueError("No 'Symbol' column found in the NASDAQ-100 table.")

# Function to fetch tickers from Excel and CSV files in the specified folder
def get_tickers_from_excel_csv_files(folder_path):
    tickers = set()
    for file_name in os.listdir(folder_path):
        if file_name.endswith((".xlsx", ".xls", ".csv")):
            file_path = os.path.join(folder_path, file_name)
            try:
                if file_name.endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                if 'ticker' in df.columns:
                    tickers.update(df['ticker'].dropna().astype(str))
                else:
                    print(f"'ticker' column not found in file: {file_name}")
            except Exception as e:
                print(f"Failed to read {file_name}: {e}")
    return sorted(tickers)

# Function to combine all tickers
def get_all_tickers(folder_path):
    sp500_tickers = get_sp500_tickers()
    nasdaq100_tickers = get_nasdaq100_tickers()
    excel_csv_tickers = get_tickers_from_excel_csv_files(folder_path)
    all_tickers = set(sp500_tickers + nasdaq100_tickers + excel_csv_tickers)
    all_tickers.add('SPY')
    return list(all_tickers)

# Fetch data for a ticker from Yahoo Finance or Alpha Vantage
def fetch_data(ticker, start_date, end_date, alpha_vantage_api_key=None):
    try:
        # Attempt to fetch from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            print(f"Warning: No data found for {ticker} on Yahoo Finance.")
            return None
        return data['Adj Close']
    except Exception as e:
        print(f"Error fetching {ticker} data from Yahoo Finance: {e}")
        if alpha_vantage_api_key:
            return fetch_data_from_alpha_vantage(ticker, start_date, end_date, alpha_vantage_api_key)
        return None

# Fetch data from Alpha Vantage if available
def fetch_data_from_alpha_vantage(ticker, start_date, end_date, alpha_vantage_api_key):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY_ADJUSTED',
        'symbol': ticker,
        'apikey': alpha_vantage_api_key,
        'outputsize': 'full',
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'Time Series (Daily)' in data:
            dates = data['Time Series (Daily)']
            adjusted_close = {
                pd.to_datetime(date): float(info['5. adjusted close'])
                for date, info in dates.items()
                if start_date <= pd.to_datetime(date) <= end_date
            }
            adjusted_close = pd.Series(adjusted_close)
            return adjusted_close.sort_index()
    else:
        print(f"Error fetching data from Alpha Vantage for {ticker}: {response.status_code}")
    return None

# Function to create individual charts for each ETF/index
def create_individual_charts(adj_close_df, start_date, end_date, output_folder):
    normalized_data = adj_close_df.loc[start_date:end_date] / adj_close_df.loc[start_date] * 100
    normalized_data = normalized_data.dropna(axis=1, how='any')

    pct_change = (normalized_data.iloc[-1] / normalized_data.iloc[0] - 1) * 100
    sorted_tickers = sorted(normalized_data.columns, key=lambda x: pct_change[x], reverse=True)

    etf_labels = {
        'S&P 500': get_sp500_tickers(),
        'NASDAQ-100': get_nasdaq100_tickers(),
        'ExcelCSV ETFs': get_tickers_from_excel_csv_files(folder_path)
    }

    for etf_label, tickers in etf_labels.items():
        fig = go.Figure()
        for ticker in sorted_tickers:
            if ticker in tickers:
                fig.add_trace(go.Scatter(
                    x=normalized_data.index,
                    y=normalized_data[ticker],
                    mode='lines',
                    name=f"{ticker} ({pct_change[ticker]:.2f}%)"
                ))
        fig.update_layout(
            title=f'Trump Presidency Performance for {etf_label}',
            xaxis_title='Date',
            yaxis_title='Normalized Adj Close Price (Start=100)',
            legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
            xaxis=dict(tickformat='%Y-%m', dtick='M12', tickmode='auto'),
            width=1600,
            height=1000
        )
        output_file = os.path.join(output_folder, f"{etf_label}_Trump_Presidency_performance.html")
        fig.write_html(output_file)
        print(f"Chart saved to {output_file}")

# Function to find and store tickers better than FTEC
def find_tickers_better_than_ftec(adj_close_df, start_date, end_date, output_file, alpha_vantage_api_key=None):
    # Fetch FTEC data
    ftec_data = fetch_data('FTEC', start_date, end_date, alpha_vantage_api_key)
    if ftec_data is None:
        print("FTEC data is missing. Proceeding with other tickers.")
        return

    normalized_data = adj_close_df.loc[start_date:end_date] / adj_close_df.loc[start_date] * 100
    normalized_data = normalized_data.dropna(axis=1, how='any')

    pct_change = (normalized_data.iloc[-1] / normalized_data.iloc[0] - 1) * 100
    ftec_performance = (ftec_data.iloc[-1] / ftec_data.iloc[0] - 1) * 100

    better_tickers = []
    for ticker, performance in pct_change.items():
        if performance > ftec_performance:
            better_tickers.append(ticker)

    if better_tickers:
        formatted_output = ",".join([f"'{ticker}'" for ticker in better_tickers])
        try:
            with open(output_file, "w") as f:
                f.write(formatted_output)
            print(f"Tickers that outperformed FTEC: {formatted_output}")
            print(f"Tickers saved to {output_file}")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}")
    else:
        print("No tickers outperformed FTEC.")

# Main script execution
if __name__ == "__main__":
    folder_path = r"C:\path\to\your_data"
    start_date = pd.Timestamp('2017-01-20')
    end_date = pd.Timestamp('2021-01-20')

    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

    cache_file = "adj_close_data.pkl"
    if os.path.exists(cache_file):
        print("Loading cached data...")
        with open(cache_file, "rb") as f:
            adj_close_data = pickle.load(f)
    else:
        tickers_list = get_all_tickers(folder_path)
        adj_close_data = {}
        for ticker in tickers_list:
            try:
                print(f"Downloading data for {ticker}...")
                ticker_data = fetch_data(ticker, start_date, end_date, ALPHA_VANTAGE_API_KEY)
                if ticker_data is not None:
                    adj_close_data[ticker] = ticker_data
                else:
                    print(f"No adjusted close data found for {ticker}")
            except Exception as e:
                print(f"Error downloading data for {ticker}: {e}")
        with open(cache_file, "wb") as f:
            pickle.dump(adj_close_data, f)
        print(f"Data cached to {cache_file}")

    adj_close_df = pd.DataFrame(adj_close_data)
    adj_close_df = adj_close_df.ffill()

    output_file = r"C:\path\to\your_data"
    find_tickers_better_than_ftec(adj_close_df, start_date, end_date, output_file, ALPHA_VANTAGE_API_KEY)

    output_folder = r"C:\path\to\your_data"
    os.makedirs(output_folder, exist_ok=True)
    create_individual_charts(adj_close_df, start_date, end_date, output_folder)
