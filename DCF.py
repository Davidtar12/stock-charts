import os
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime


class DCFAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FMPAPI')
        if not self.api_key:
            raise ValueError("API key not found. Please set the FMPAPI environment variable.")

    def fetch_dcf(self, ticker: str) -> Optional[Dict]:
        """
        Fetch DCF data for a given ticker from FMP API with error handling.
        """
        url = f'https://financialmodelingprep.com/api/v3/discounted-cash-flow/{ticker}?apikey={self.api_key}'
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data[0] if data else None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing data for {ticker}: {str(e)}")
            return None

    def analyze_valuation(self, dcf_value: float, stock_price: float) -> Tuple[str, float, str]:
        """
        Provide detailed valuation analysis with margin of safety calculations.

        Returns:
        Tuple containing (valuation_status, margin_percentage, detailed_analysis)
        """
        margin_percentage = ((dcf_value - stock_price) / stock_price) * 100

        if stock_price < dcf_value * 0.7:
            return ("Significantly Undervalued", margin_percentage,
                    "High margin of safety, potentially strong buy signal")
        elif stock_price < dcf_value * 0.9:
            return ("Moderately Undervalued", margin_percentage,
                    "Decent margin of safety, consider buying")
        elif stock_price < dcf_value * 1.1:
            return ("Fair Value", margin_percentage,
                    "Price is within reasonable range of intrinsic value")
        elif stock_price < dcf_value * 1.3:
            return ("Moderately Overvalued", margin_percentage,
                    "Limited margin of safety, exercise caution")
        else:
            return ("Significantly Overvalued", margin_percentage,
                    "No margin of safety, high risk")

    def analyze_stocks(self, tickers: list) -> None:
        """
        Analyze multiple stocks and print detailed results.
        """
        print("\nDCF Analysis Report")
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

        for ticker in tickers:
            data = self.fetch_dcf(ticker)
            if not data:
                print(f"\n{ticker}: Unable to retrieve data")
                continue

            dcf_value = data.get('dcf')
            stock_price = data.get('Stock Price')

            if not (dcf_value and stock_price):
                print(f"\n{ticker}: Incomplete data")
                continue

            status, margin, analysis = self.analyze_valuation(dcf_value, stock_price)

            print(f"\n{ticker} Analysis:")
            print(f"DCF Value: ${dcf_value:.2f}")
            print(f"Current Price: ${stock_price:.2f}")
            print(f"Margin: {margin:.1f}%")
            print(f"Status: {status}")
            print(f"Analysis: {analysis}")


def main():
    TICKERS = ['MSFT','ASML','LOGI','LRCX','GWW','ABBV']

    try:
        analyzer = DCFAnalyzer()
        analyzer.analyze_stocks(TICKERS)
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()