import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StockAnalyzer:
    def __init__(self, tickers, start_date, end_date):
        """Initialize the StockAnalyzer with tickers and date range."""
        self.tickers = tickers
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.data = None
        self.validate_inputs()

    def validate_inputs(self):
        """Validate input parameters."""
        if not self.tickers:
            raise ValueError("Tickers list cannot be empty")
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        if self.end_date > datetime.now():
            raise ValueError("End date cannot be in the future")

    def download_stock_data(self, ticker):
        """Download data for a single ticker with improved error handling."""
        try:
            # Create a Ticker object
            stock = yf.Ticker(ticker)

            # Get the historical data
            df = stock.history(start=self.start_date, end=self.end_date)

            # Check if the dataframe is empty or has no data
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return None

            # Add the ticker column
            df['Ticker'] = ticker
            return df

        except Exception as e:
            logger.error(f"Error downloading {ticker}: {str(e)}")
            return None

    def fetch_all_data(self):
        """Fetch data for all tickers using parallel processing."""
        logger.info("Starting data download...")

        # Download data sequentially first to test the connection
        test_ticker = self.tickers[0]
        test_data = self.download_stock_data(test_ticker)
        if test_data is None:
            raise ValueError(
                f"Failed to download test ticker {test_ticker}. Please check your internet connection and API access.")

        # If test successful, proceed with parallel downloads
        with ThreadPoolExecutor(max_workers=min(len(self.tickers), 5)) as executor:
            data_list = list(executor.map(self.download_stock_data, self.tickers))

        # Filter out None values (failed downloads)
        valid_data = [df for df in data_list if df is not None and not df.empty]

        if not valid_data:
            raise ValueError("No valid data downloaded for any ticker")

        self.data = pd.concat(valid_data)
        self.data.reset_index(inplace=True)
        logger.info(f"Successfully downloaded data for {len(valid_data)} out of {len(self.tickers)} tickers")

    def calculate_metrics(self):
        """Calculate performance metrics for each stock."""
        if self.data is None or self.data.empty:
            raise ValueError("No data available for analysis")

        # Get starting prices for each ticker
        start_prices = self.data.groupby('Ticker').first()[['Close']].reset_index()
        start_prices.columns = ['Ticker', 'Close_start']

        # Merge and calculate metrics
        self.data = pd.merge(self.data, start_prices, on='Ticker', how='left')
        self.data['Performance'] = ((self.data['Close'] - self.data['Close_start']) /
                                    self.data['Close_start']) * 100
        self.data['Daily_Return'] = self.data.groupby('Ticker')['Close'].pct_change() * 100
        self.data['Volatility'] = self.data.groupby('Ticker')['Daily_Return'].transform(
            lambda x: x.rolling(window=20).std()
        )

    def create_visualization(self):
        """Create an enhanced interactive visualization."""
        if self.data is None or self.data.empty:
            raise ValueError("No data available for visualization")

        # Create the main performance chart
        fig = go.Figure()

        for ticker in self.data['Ticker'].unique():
            ticker_data = self.data[self.data['Ticker'] == ticker]
            fig.add_trace(go.Scatter(
                x=ticker_data['Date'],
                y=ticker_data['Performance'],
                name=ticker,
                mode='lines',
                hovertemplate=(
                        '<b>%{text}</b><br>' +
                        'Date: %{x}<br>' +
                        'Performance: %{y:.2f}%<br>' +
                        'Close: $%{customdata[0]:.2f}<br>' +
                        'Volatility: %{customdata[1]:.2f}%<br>' +
                        '<extra></extra>'
                ),
                text=ticker_data['Ticker'],
                customdata=np.column_stack((
                    ticker_data['Close'],
                    ticker_data['Volatility']
                ))
            ))

        # Update layout with better formatting
        fig.update_layout(
            title={
                'text': f'Stock Performance Comparison ({self.start_date.strftime("%B %Y")} to {self.end_date.strftime("%B %Y")})',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='Date',
            yaxis_title='Performance (%)',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            ),
            template='plotly_white'
        )

        return fig


def main():
    """Main function to run the analysis."""
    # Define the list of tickers
    tickers = ['AVGO', 'TSLA', 'TPL', 'NVDA', 'ANET', 'ISRG',
               'PGR', 'OXY', 'DVN', 'VST', 'MPC', 'PLTR']

    # Set the date range
    start_date = '2020-02-01'
    end_date = '2020-08-31'

    try:
        # Initialize and run analysis
        analyzer = StockAnalyzer(tickers, start_date, end_date)
        analyzer.fetch_all_data()

        if analyzer.data is not None and not analyzer.data.empty:
            analyzer.calculate_metrics()

            # Create and display visualization
            fig = analyzer.create_visualization()
            fig.show()

            # Print summary statistics
            summary = analyzer.data.groupby('Ticker').agg({
                'Performance': ['last', 'min', 'max'],
                'Volatility': 'mean'
            }).round(2)
            print("\nSummary Statistics:")
            print(summary)
        else:
            logger.error("No data available for analysis")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()