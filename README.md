# FX Carry Trade Strategy Backtest

This project implements a Python backtest of a Foreign Exchange (FX) carry trade strategy and evaluates its performance across different volatility regimes.

# Strategy Overview
The FX carry trade involves:

- Borrowing in currencies with low interest rates
- Investing in currencies with higher interest rates

The strategy goes **long high-yield currencies** and **short low-yield currencies** based on interest rate differentials.
Currency pairs used:
- EUR/USD
- GBP/USD
- AUD/USD
- JPY/USD

# Data Sources
The model uses the following data sources:

- FX spot rates: Yahoo Finance
- Interest rates: FRED (Federal Reserve Economic Data)
- Market volatility proxy: VIX Index

# Methodology
1. Download FX price data
2. Download central bank interest rate data
3. Construct carry signals using interest rate differentials
4. Backtest the strategy across currency pairs
5. Build an equal-weighted carry portfolio
6. Compute risk and performance metrics
7. Analyse performance across volatility regimes using the VIX

# Performance Metrics
The strategy evaluates:

- Annual Return
- Volatility
- Sharpe Ratio
- Maximum Drawdown

# Key Result
The results confirm a well-known empirical feature of FX markets: carry strategies tend to perform better during **low-volatility environments** and deteriorate during **high-volatility regimes**, when investors unwind risk-seeking positions.

# Tools Used
- Python
- pandas
- numpy
- yfinance
- pandas-datareader
- matplotlib
