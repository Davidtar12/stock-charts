import os
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime


class DCFAnalyzer:
    # Optional: Define threshold multipliers as class attributes for flexibility
    THRESHOLDS = {
        "extremely_undervalued": 0.65,
        "significantly_undervalued": 0.80,
        "moderately_undervalued": 0.95,
        "fair_value_upper": 1.05,
        "moderately_overvalued": 1.20,
        "significantly_overvalued": 1.35,
    }

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

        Expanded subranges:
          - Extremely Undervalued: stock_price < dcf_value * 0.65
          - Significantly Undervalued: stock_price < dcf_value * 0.80
          - Moderately Undervalued: stock_price < dcf_value * 0.95
          - Fair Value: stock_price is between dcf_value * 0.95 and dcf_value * 1.05
          - Moderately Overvalued: stock_price < dcf_value * 1.20
          - Significantly Overvalued: stock_price < dcf_value * 1.35
          - Extremely Overvalued: stock_price >= dcf_value * 1.35
        """
        margin_percentage = ((dcf_value - stock_price) / stock_price) * 100

        if stock_price < dcf_value * self.THRESHOLDS["extremely_undervalued"]:
            return ("Extremely Undervalued", margin_percentage,
                    "Very high margin of safety. The stock appears to be extremely undervalued, which might indicate a strong buying opportunity (subject to further due diligence).")
        elif stock_price < dcf_value * self.THRESHOLDS["significantly_undervalued"]:
            return ("Significantly Undervalued", margin_percentage,
                    "High margin of safety. The stock is significantly below its intrinsic value, making it a potential buy candidate.")
        elif stock_price < dcf_value * self.THRESHOLDS["moderately_undervalued"]:
            return ("Moderately Undervalued", margin_percentage,
                    "Decent margin of safety. The stock is undervalued but warrants a closer look.")
        elif stock_price <= dcf_value * self.THRESHOLDS["fair_value_upper"]:
            return ("Fair Value", margin_percentage,
                    "The current price is in line with the intrinsic value. It might be fairly priced.")
        elif stock_price < dcf_value * self.THRESHOLDS["moderately_overvalued"]:
            return ("Moderately Overvalued", margin_percentage,
                    "The stock is slightly overvalued with limited margin of safety. Exercise caution.")
        elif stock_price < dcf_value * self.THRESHOLDS["significantly_overvalued"]:
            return ("Significantly Overvalued", margin_percentage,
                    "The stock is significantly overvalued with little margin of safety. It may be risky to buy at this time.")
        else:
            return ("Extremely Overvalued", margin_percentage,
                    "No margin of safety. The stock appears extremely overvalued and might be considered a sell candidate or avoided entirely.")

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
    TICKERS = ['NVO', 'BABA', 'BRK-B','TMUS']

    try:
        analyzer = DCFAnalyzer()
        analyzer.analyze_stocks(TICKERS)
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
