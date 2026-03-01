# stock-charts

Interactive stock charts with Plotly & yfinance: P/E ratios, dividend yield, 25-year comparisons, DCF valuation, sector analysis.

## Scripts

| Script | Description |
|--------|-------------|
| `DCF.py` / `dcf2.py` | Discounted Cash Flow valuation calculator — input ticker, get intrinsic value estimate |
| `wk-chart-dividend-y-historical.py` | Historical dividend yield chart for a single stock |
| `wk-chart-dividendyieldcompare.py` | Compare dividend yield across multiple tickers |
| `wk-PEvshistownPE.py` | P/E ratio vs stock's own historical average P/E (Alpha Vantage) |
| `wk-chart-comparehist-own-PE-plotly.py` | Interactive Plotly chart: current vs historical P/E |
| `wk-chart-stockpe-vs-avg-sp500sectorpe.py` | Stock P/E vs its S&P 500 sector average |
| `wk-chart-pes-sectors-average.py` | Sector average P/E bar chart |
| `wk-crisischarts.py` / `covid-trump.py` | Market performance charts during crisis periods |
| `trump1st-term.py` / `trump1st-better-than-ftec.py` | Stock performance during Trump first term vs benchmarks |
| `WK-CHARTS-compare-25y-browser.py` / `wk-compare37years.py` | Long-term 25–37 year price comparisons, opens in browser |
| `chart-sp500-sector.py` | S&P 500 sector performance breakdown |
| `chart-peg-lynch.py` / `peg-ratio.py` | PEG ratio calculator (Peter Lynch valuation method) |
| `chart-onestock-maxtime-divyield-trendline.py` | Single stock max-timeframe chart with dividend yield trendline |
| `wk-charts-stocks-vs-spy-img.py` | Stock vs S&P 500 comparison — saves as image |
| `wk-charts-vs-spy-browser.py` | Stock vs S&P 500 comparison — opens in browser |
| `wk-indicators-ratelimit-yfinance.py` | Rate-limit-aware yfinance indicator fetcher |
| `wk-charts-by-indicator-plotly.py` | Multi-stock chart sorted by a chosen indicator |
| `wk-chartsindicatordescending-plotly.py` | Indicator ranking chart (descending order) |
| `3years.py` / `nonwk-growth-compare.py` | 3-year growth comparison across tickers |
| `non-wk-compare-perf-tickers-etfs.py` | Performance comparison: stocks vs ETFs |
| `wk-annual-PE-average-edgar-yfinance.py` | Annual P/E average using EDGAR + yfinance |
| `wk-stock-vs-pe-sector.py` | Single stock P/E vs full sector P/E distribution |
| `notatemporal.py` | Non-temporal (snapshot) fundamental chart |

## Prerequisites

- Python 3.9+
- Alpha Vantage API key (for P/E and earnings data)
- EDGAR identity string (for SEC data)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ALPHA_VANTAGE_API_KEY, EDGAR_IDENTITY
```

## Usage

```bash
# DCF valuation
python DCF.py

# P/E vs historical average (opens browser)
python wk-chart-comparehist-own-PE-plotly.py

# 25-year comparison chart
python WK-CHARTS-compare-25y-browser.py
```

Edit the ticker symbol variable at the top of each script before running.

## Notes

> **Yahoo Finance (yfinance):** Historical price data generally works. Fundamental data (P/E, dividends) from yfinance may be unreliable since Yahoo changed their API in 2023–2024. Scripts that use `ALPHA_VANTAGE_API_KEY` are more reliable for fundamental data and are the recommended approach.

## Built with

Python · Plotly · yfinance · Alpha Vantage API · EDGAR API  
AI-assisted development (Claude, GitHub Copilot) — architecture, requirements, QA validation and debugging by me.

