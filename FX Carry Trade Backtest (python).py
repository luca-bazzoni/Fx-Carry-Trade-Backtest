#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 11:48:28 2026

@author: lucabazzoni
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from pandas_datareader import data as web


#SETTINGS

start_date = "2015-01-01"
end_date = "2025-01-01"

# FX pairs imported from Yahoo Finance
fx_tickers = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "USDJPY": "JPY=X"
}

# Short-term interest rate proxies from FRED
fred_rates = {
    "USD": "FEDFUNDS",          # US Fed Funds Rate
    "EUR": "ECBDFR",            # ECB Deposit Facility Rate
    "GBP": "IR3TIB01GBM156N",   # UK 3-month interbank rate proxy
    "AUD": "IR3TIB01AUM156N",   # Australia 3-month interbank rate proxy
    "JPY": "IR3TIB01JPM156N"    # Japan 3-month interbank rate proxy
}


# FX DATA DOWNLOAD

fx_prices = pd.DataFrame()

for pair, ticker in fx_tickers.items():
    price = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)["Close"]
    fx_prices[pair] = price

# Convert USDJPY into JPYUSD
fx_prices["JPYUSD"] = 1 / fx_prices["USDJPY"]
fx_prices = fx_prices.drop(columns=["USDJPY"])

# FX returns
fx_returns = fx_prices.pct_change()


# INTEREST RATE DOWNLOAD

rates = pd.DataFrame()

for ccy, code in fred_rates.items():
    rates[ccy] = web.DataReader(code, "fred", start_date, end_date)


rates = rates.ffill() / 100.0

rates = rates.reindex(fx_returns.index).ffill()


# BUILD CARRY SIGNALS

# If foreign interest rate > USD rate => long foreign currency vs USD
# Else => short foreign currency vs USD

signals = pd.DataFrame(index=fx_returns.index)

signals["EURUSD"] = np.where(rates["EUR"] > rates["USD"], 1, -1)
signals["GBPUSD"] = np.where(rates["GBP"] > rates["USD"], 1, -1)
signals["AUDUSD"] = np.where(rates["AUD"] > rates["USD"], 1, -1)
signals["JPYUSD"] = np.where(rates["JPY"] > rates["USD"], 1, -1)

# Lag by 1 day to avoid look-ahead bias
signals = signals.shift(1)


# STRATEGY RETURNS

strategy_returns = signals * fx_returns

# Equal-weight basket
strategy_returns["Carry_Basket"] = strategy_returns.mean(axis=1)

strategy_returns = strategy_returns.dropna()


# PERFORMANCE METRICS

def performance_metrics(returns):
    returns = returns.dropna()
    cumulative = (1 + returns).cumprod()

    annual_return = cumulative.iloc[-1] ** (252 / len(returns)) - 1
    annual_vol = returns.std() * np.sqrt(252)
    sharpe = annual_return / annual_vol if annual_vol != 0 else np.nan

    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min()

    return pd.Series({
        "Annual Return": annual_return,
        "Annual Volatility": annual_vol,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown
    })


# OVERALL RESULTS

overall_results = performance_metrics(strategy_returns["Carry_Basket"])

print("\n=== OVERALL FX CARRY STRATEGY RESULTS ===")
print(overall_results)


# CUMULATIVE PERFORMANCE PLOT

strategy_returns["Cumulative"] = (1 + strategy_returns["Carry_Basket"]).cumprod()

plt.figure(figsize=(10, 5))
plt.plot(strategy_returns.index, strategy_returns["Cumulative"], label="FX Carry Basket")
plt.title("FX Carry Trade Strategy Backtest")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.grid(True)
plt.show()


# VOLATILITY / MARKET REGIMES USING VIX

vix = yf.download("^VIX", start=start_date, end=end_date, auto_adjust=True, progress=False)["Close"]


if isinstance(vix, pd.DataFrame):
    vix = vix.squeeze()

vix = vix.reindex(strategy_returns.index).ffill()


high_vol_mask = vix > 20
low_vol_mask = vix <= 20

high_vol_returns = strategy_returns.loc[high_vol_mask, "Carry_Basket"]
low_vol_returns = strategy_returns.loc[low_vol_mask, "Carry_Basket"]

high_vol_results = performance_metrics(high_vol_returns)
low_vol_results = performance_metrics(low_vol_returns)

print("\n=== HIGH VOLATILITY REGIME (VIX > 20) ===")
print(high_vol_results)

print("\n=== LOW VOLATILITY REGIME (VIX <= 20) ===")
print(low_vol_results)


# CARRY STRATEGY VS VIX REGIME PLOT


plt.figure(figsize=(10,5))

plt.plot(strategy_returns.index,
         strategy_returns["Cumulative"],
         label="FX Carry Basket")

plt.fill_between(
    strategy_returns.index,
    strategy_returns["Cumulative"].min(),
    strategy_returns["Cumulative"].max(),
    where=high_vol_mask,
    alpha=0.3,
    label="High VIX Regime"
)

plt.title("FX Carry Strategy with Market Regimes")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.grid(True)

plt.show()