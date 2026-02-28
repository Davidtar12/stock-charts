import yfinance as yf
import pandas as pd
import numpy as np


# Function to calculate PEG ratio
def calculate_peg(pe_ratio, eps_growth):
    try:
        return pe_ratio / eps_growth
    except ZeroDivisionError:
        return np.nan


# Function to get fundamental data
def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    pe_ratio = stock.info.get('trailingPE', np.nan)  # Handle missing trailingPE
    eps_growth = stock.info.get('earningsGrowth', np.nan)  # Handle missing earningsGrowth
    peg_ratio = calculate_peg(pe_ratio, eps_growth)
    return pe_ratio, eps_growth, peg_ratio


# Function to calculate RSI (Relative Strength Index)
def calculate_rsi(prices, period):
    delta = prices.diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Function to get technical indicators (SMA and RSI)
def get_technical_indicators(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="6mo")
    sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
    sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
    rsi = calculate_rsi(df['Close'], 14).iloc[-1]
    return sma_50, sma_200, rsi


# Define screening criteria
def screening_criteria(pe_ratio, eps_growth, peg_ratio):
    if pe_ratio and eps_growth and peg_ratio:
        if peg_ratio < 1:
            return 'Buy'
        elif peg_ratio < 2:
            return 'Hold'
        else:
            return 'Sell'
    return 'Insufficient Data'


# Create DataFrame for results
results = pd.DataFrame(
    columns=['Ticker', 'P/E Ratio', 'EPS Growth', 'PEG Ratio', 'SMA 50', 'SMA 200', 'RSI', 'Recommendation'])

# List of tickers
tickers = [
    "MMM", "AOS", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AES", "AFL", "A", "APD", "ABNB", "AKAM", "ALB", "ARE",
    "ALGN", "ALLE", "LNT", "ALL", "GOOGL", "GOOG", "MO", "AMZN", "AMCR", "AEE", "AAL", "AEP", "AXP", "AIG", "AMT",
    "AWK", "AMP", "AME", "AMGN"
]

# Loop through each ticker and fetch data
for ticker in tickers:
    try:
        # Get fundamentals
        pe_ratio, eps_growth, peg_ratio = get_fundamentals(ticker)

        # Get technical indicators
        sma_50, sma_200, rsi = get_technical_indicators(ticker)

        # Apply screening criteria
        recommendation = screening_criteria(pe_ratio, eps_growth, peg_ratio)

        # Create a new row with the data
        new_row = pd.DataFrame([{
            'Ticker': ticker,
            'P/E Ratio': pe_ratio,
            'EPS Growth': eps_growth,
            'PEG Ratio': peg_ratio,
            'SMA 50': sma_50,
            'SMA 200': sma_200,
            'RSI': rsi,
            'Recommendation': recommendation
        }], dtype=object)  # Explicitly set dtype

        # Only append the row if it's not empty (i.e., it contains valid data)
        if not all(pd.isna([pe_ratio, eps_growth, peg_ratio, sma_50, sma_200, rsi])):
            results = pd.concat([results, new_row], ignore_index=True)
        else:
            print(f"Skipping {ticker} due to insufficient data.")
    except Exception as e:
        print(f"Error retrieving data for {ticker}: {e}")

# Print the final DataFrame with all tickers' data
print(results)
