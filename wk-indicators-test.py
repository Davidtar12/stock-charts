import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# List of tickers
tickers = ['NVO','BLD','PNW']

def get_capital_expenditure(cf):
    """Flexibly retrieve capital expenditure from cashflow statement"""
    possible_keys = [
        'Capital Expenditure',
        'Capital Expenditures',
        'Purchase of Property, Plant and Equipment',
        'Purchases of Property, Plant and Equipment',
        'Purchase of PPE',
        'Capital Expenditure Reported'
    ]
    for key in possible_keys:
        if key in cf.index:
            return cf.loc[key].iloc[0]
    return 0  # Default to 0 if no valid keys found


def get_financial_data(stock, statement_type, possible_keys):
    """Helper function to retrieve financial data with multiple key options"""
    try:
        if statement_type == 'balance_sheet':
            statement = stock.balance_sheet
        elif statement_type == 'financials':
            statement = stock.financials
        elif statement_type == 'cashflow':
            statement = stock.cashflow
        else:
            return None

        for key in possible_keys:
            if key in statement.index:
                return statement.loc[key].iloc[0]
        return None
    except Exception as e:
        print(f"Error retrieving {statement_type} data: {e}")
        return None


# Metric calculation functions
def calculate_p_fcf(ticker):
    try:
        stock = yf.Ticker(ticker)

        # Get required data points
        market_price = stock.info.get('currentPrice')
        if not market_price:
            print(f"No current price available for {ticker}")
            return None

        shares_outstanding = stock.info.get('sharesOutstanding')
        if not shares_outstanding:
            print(f"No shares outstanding data for {ticker}")
            return None

        cf = stock.cashflow
        if cf.empty:
            print(f"No cashflow data available for {ticker}")
            return None

        operating_cash_flow = get_financial_data(stock, 'cashflow',
                                                 ['Operating Cash Flow',
                                                  'Cash Flow From Continuing Operating Activities'])
        if not operating_cash_flow:
            print(f"No operating cash flow data for {ticker}")
            return None

        capital_expenditure = get_capital_expenditure(cf)

        # Calculate free cash flow per share
        free_cash_flow = operating_cash_flow - capital_expenditure
        fcf_per_share = free_cash_flow / shares_outstanding

        if fcf_per_share <= 0:
            print(f"Negative or zero FCF per share for {ticker}")
            return None

        return market_price / fcf_per_share

    except Exception as e:
        print(f"Error calculating P/FCF for {ticker}: {e}")
        return None


def calculate_fcf_yield(ticker):
    try:
        stock = yf.Ticker(ticker)

        market_cap = stock.info.get('marketCap')
        if not market_cap or market_cap <= 0:
            print(f"Invalid market cap for {ticker}")
            return None

        cf = stock.cashflow
        if cf.empty:
            print(f"No cashflow data available for {ticker}")
            return None

        operating_cash_flow = get_financial_data(stock, 'cashflow',
                                                 ['Operating Cash Flow',
                                                  'Cash Flow From Continuing Operating Activities'])
        if not operating_cash_flow:
            print(f"No operating cash flow data for {ticker}")
            return None

        capital_expenditure = get_capital_expenditure(cf)
        free_cash_flow = operating_cash_flow - capital_expenditure

        return (free_cash_flow / market_cap) * 100

    except Exception as e:
        print(f"Error calculating FCF Yield for {ticker}: {e}")
        return None


def calculate_pe_ratio(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info.get('trailingPE') or stock.info.get('forwardPE')
    except Exception as e:
        print(f"Error calculating P/E Ratio for {ticker}: {e}")
        return None


def calculate_roic(ticker):
    try:
        stock = yf.Ticker(ticker)

        net_income = get_financial_data(stock, 'financials',
                                        ['Net Income', 'Net Income Common Stockholders'])
        total_debt = get_financial_data(stock, 'balance_sheet',
                                        ['Total Debt', 'Long Term Debt'])
        total_equity = get_financial_data(stock, 'balance_sheet',
                                          ['Stockholders Equity', 'Total Equity'])

        if None in (net_income, total_debt, total_equity):
            print(f"Missing data for ROIC calculation in {ticker}")
            return None

        invested_capital = total_debt + total_equity
        if invested_capital <= 0:
            print(f"Invalid invested capital for {ticker}")
            return None

        return (net_income / invested_capital) * 100

    except Exception as e:
        print(f"Error calculating ROIC for {ticker}: {e}")
        return None


def calculate_debt_to_equity(ticker):
    try:
        stock = yf.Ticker(ticker)

        total_debt = get_financial_data(stock, 'balance_sheet',
                                        ['Total Debt', 'Long Term Debt'])
        total_equity = get_financial_data(stock, 'balance_sheet',
                                          ['Stockholders Equity', 'Total Equity'])

        if None in (total_debt, total_equity):
            print(f"Missing data for D/E ratio in {ticker}")
            return None

        if total_equity == 0:
            print(f"Infinite D/E ratio for {ticker} (zero equity)")
            return None

        return total_debt / total_equity

    except Exception as e:
        print(f"Error calculating Debt to Equity Ratio for {ticker}: {e}")
        return None


# Data collection and processing
def collect_data(tickers):
    metrics = {
        'P/FCF': [],
        'FCF Yield (%)': [],
        'P/E Ratio': [],
        'ROIC (%)': [],
        'Debt to Equity Ratio': []
    }

    for ticker in tickers:
        print(f"Processing {ticker}...")

        p_fcf = calculate_p_fcf(ticker)
        fcf_yield = calculate_fcf_yield(ticker)
        pe_ratio = calculate_pe_ratio(ticker)
        roic = calculate_roic(ticker)
        debt_equity = calculate_debt_to_equity(ticker)

        if p_fcf is not None:
            metrics['P/FCF'].append({'Ticker': ticker, 'Value': p_fcf})
        if fcf_yield is not None:
            metrics['FCF Yield (%)'].append({'Ticker': ticker, 'Value': fcf_yield})
        if pe_ratio is not None:
            metrics['P/E Ratio'].append({'Ticker': ticker, 'Value': pe_ratio})
        if roic is not None:
            metrics['ROIC (%)'].append({'Ticker': ticker, 'Value': roic})
        if debt_equity is not None:
            metrics['Debt to Equity Ratio'].append({'Ticker': ticker, 'Value': debt_equity})

    return metrics


def create_charts(metrics):
    for metric_name, data in metrics.items():
        if not data:
            print(f"No data available for {metric_name}")
            continue

        df = pd.DataFrame(data).sort_values(by='Value', ascending=False)
        fig = go.Figure([go.Bar(x=df['Ticker'], y=df['Value'])])

        fig.update_layout(
            title=f'{metric_name} Comparison',
            xaxis_title='Ticker',
            yaxis_title=metric_name,
            template='plotly_white'
        )

        filename = f'../../{metric_name.replace(" ", "_").replace("/", "_")}_chart.html'
        fig.write_html(filename)
        print(f"Saved {filename}")


# Main execution
if __name__ == "__main__":
    metrics_data = collect_data(tickers)
    create_charts(metrics_data)
    print("Analysis complete. Charts saved to HTML files.")