import yfinance as yf
import pandas as pd
from pandas.tseries.offsets import DateOffset
import plotly.graph_objects as go
import os
import pickle
from datetime import datetime, timedelta


def get_sp500_tickers():
    tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    return tables[0]['Symbol'].tolist()


def get_nasdaq100_tickers():
    tables = pd.read_html('https://en.wikipedia.org/wiki/NASDAQ-100')
    return tables[4]['Symbol'].tolist()


def get_tickers_from_excel_csv_files(folder_path):
    tickers = set()
    for file_name in os.listdir(folder_path):
        if file_name.endswith((".xlsx", ".xls", ".csv")):
            try:
                df = pd.read_csv(file_name) if file_name.endswith(".csv") else pd.read_excel(file_name)
                if 'ticker' in df.columns:
                    tickers.update(df['ticker'].dropna().astype(str))
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    return sorted(tickers)


def get_all_tickers(folder_path):
    all_tickers = set(get_sp500_tickers() + get_nasdaq100_tickers() +
                      get_tickers_from_excel_csv_files(folder_path))
    all_tickers.add('SPY')
    return list(all_tickers)


def load_or_update_cache(cache_file, start_date_max, end_date, tickers_list):
    cache_needs_update = True
    adj_close_data = {}

    if os.path.exists(cache_file):
        cache_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_modified_time < timedelta(days=1):
            with open(cache_file, "rb") as f:
                adj_close_data = pickle.load(f)
                cache_needs_update = False
                print("Using recent cached data...")

    if cache_needs_update:
        print("Fetching fresh data...")
        new_data = {}
        for ticker in tickers_list:
            try:
                ticker_data = yf.download(ticker, start=start_date_max, end=end_date)
                if not ticker_data['Adj Close'].empty:
                    new_data[ticker] = ticker_data['Adj Close']
            except Exception as e:
                print(f"Error downloading {ticker}: {e}")

        adj_close_data = new_data if not adj_close_data else {**adj_close_data, **new_data}

        with open(cache_file, "wb") as f:
            pickle.dump(adj_close_data, f)

    return pd.DataFrame(adj_close_data)


def create_individual_charts(adj_close_df, periods, output_folder, folder_path):
    for label, offset in periods.items():
        start_date = adj_close_df.index[-1] - offset
        period_data = adj_close_df.loc[start_date:]

        if period_data.empty or len(period_data) < 2:
            print(f"Insufficient data for {label}. Skipping...")
            continue

        normalized_data = period_data / period_data.iloc[0] * 100
        pct_change = (period_data.iloc[-1] / period_data.iloc[0] - 1) * 100
        sorted_tickers = sorted(period_data.columns, key=lambda x: pct_change[x], reverse=True)

        for etf in ['S&P 500', 'NASDAQ-100', 'ExcelCSV ETFs']:
            fig = go.Figure()
            tickers = {
                'S&P 500': get_sp500_tickers(),
                'NASDAQ-100': get_nasdaq100_tickers(),
                'ExcelCSV ETFs': get_tickers_from_excel_csv_files(folder_path)
            }[etf]

            relevant_tickers = [t for t in sorted_tickers if t in tickers]
            for ticker in relevant_tickers:
                fig.add_trace(go.Scatter(
                    x=normalized_data.index,
                    y=normalized_data[ticker],
                    mode='lines',
                    name=f"{ticker} ({pct_change[ticker]:.2f}%)"
                ))

            fig.update_layout(
                title=f'{label} Performance for {etf}',
                xaxis_title='Date',
                yaxis_title='Normalized Price (Start=100)',
                legend=dict(x=1, y=1, xanchor='right', yanchor='top'),
                xaxis=dict(tickformat='%Y-%m', dtick='M1'),
                width=1600,
                height=1000,
                showlegend=True
            )

            output_file = os.path.join(output_folder, f"{etf}_{label}_performance.html")
            fig.write_html(output_file)
            print(f"Saved chart: {output_file}")


def main():
    folder_path = r"C:\path\to\your_data"
    output_folder = r"C:\path\to\your_data"
    cache_file = "adj_close_data.pkl"

    periods = {
        '1D': DateOffset(days=1),
        '3D': DateOffset(days=3),
        '5D': DateOffset(days=5),
        '10D': DateOffset(days=10),
        '15D': DateOffset(days=15),
        '20D': DateOffset(days=20),
        '25D': DateOffset(days=25),
        '1M': DateOffset(months=1),
        '2M': DateOffset(months=2),
        '3M': DateOffset(months=3),
        '6M': DateOffset(months=6),
        '1Y': DateOffset(years=1)
    }

    os.makedirs(output_folder, exist_ok=True)

    end_date = pd.Timestamp.today()
    start_date_max = end_date - DateOffset(years=1)

    tickers_list = get_all_tickers(folder_path)
    adj_close_df = load_or_update_cache(cache_file, start_date_max, end_date, tickers_list)
    adj_close_df = adj_close_df.ffill()

    create_individual_charts(adj_close_df, periods, output_folder, folder_path)


if __name__ == "__main__":
    main()