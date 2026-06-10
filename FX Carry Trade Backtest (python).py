#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: lucabazzoni
"""

import os
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


start_date = "2015-01-01"
end_date = "2025-01-01"

RATES_DIR = "/Users/lucabazzoni/Desktop/JOB/fred_csv"

# FX pairs (Yahoo Finance) 
fx_tickers = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "USDJPY": "JPY=X",
}


fred_rates = {
    "USD": "FEDFUNDS",          # US Fed Funds Rate
    "EUR": "IR3TIB01EZM156N",   # Euro Area 3-month interbank rate (OECD)
    "GBP": "IR3TIB01GBM156N",   # UK 3-month interbank rate proxy
    "AUD": "IR3TIB01AUM156N",   # Australia 3-month interbank rate proxy
    "JPY": "IR3TIB01JPM156N",   # Japan 3-month interbank rate proxy
}

PAIRS = ["EURUSD", "GBPUSD", "AUDUSD", "JPYUSD"]

FOREIGN_CCY = {
    "EURUSD": "EUR",
    "GBPUSD": "GBP",
    "AUDUSD": "AUD",
    "JPYUSD": "JPY",
}

TRADING_DAYS = 252


fx_prices = pd.DataFrame()
for pair, ticker in fx_tickers.items():
    price = yf.download(ticker, start=start_date, end=end_date,
                        auto_adjust=True, progress=False)["Close"]
    fx_prices[pair] = price

# JPY=X -> invert to JPYUSD = USD per JPY (FOREIGN/USD convention)
fx_prices["JPYUSD"] = 1.0 / fx_prices["USDJPY"]
fx_prices = fx_prices.drop(columns=["USDJPY"])

fx_returns = fx_prices[PAIRS].pct_change()


# INTEREST RATES FROM LOCAL CSV

def load_fred_csv(code: str) -> pd.Series:
    """
    Read one FRED series from a local CSV (downloaded from
    fredgraph.csv?id=<code>). The file has two columns: a date column
    and the value column ('.' marks missing values).
    """
    path = os.path.join(RATES_DIR, f"{code}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing CSV: {path}\n"
            f"Download it from "
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code} "
            f"and save it as {code}.csv in RATES_DIR."
        )
    df = pd.read_csv(path, na_values=".")
    df = df.iloc[:, :2]
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["value"].astype(float)
    return s


rates = pd.DataFrame()
for ccy, code in fred_rates.items():
    rates[ccy] = load_fred_csv(code)


rates = rates.sort_index().ffill() / 100.0
rates = rates.reindex(fx_returns.index).ffill()



# CARRY SIGNALS lagged 1 day to avoid look-ahead

signals = pd.DataFrame(index=fx_returns.index)
for pair in PAIRS:
    fccy = FOREIGN_CCY[pair]
    signals[pair] = np.where(rates[fccy] > rates["USD"], 1, -1)

signals = signals.shift(1)



# RETURN COMPONENTS

rate_diff = pd.DataFrame(index=fx_returns.index)
for pair in PAIRS:
    fccy = FOREIGN_CCY[pair]
    rate_diff[pair] = rates[fccy] - rates["USD"]

daily_carry = rate_diff / TRADING_DAYS

spot_pnl = signals * fx_returns
carry_pnl = signals * daily_carry
total_pnl = spot_pnl + carry_pnl

spot_basket = spot_pnl[PAIRS].mean(axis=1).rename("Spot")
carry_basket = carry_pnl[PAIRS].mean(axis=1).rename("Carry")
total_basket = total_pnl[PAIRS].mean(axis=1).rename("Carry_Basket")

components = pd.concat([spot_basket, carry_basket, total_basket], axis=1).dropna()
spot_basket = components["Spot"]
carry_basket = components["Carry"]
total_basket = components["Carry_Basket"]


# PERFORMANCE METRICS

def performance_metrics(returns: pd.Series) -> pd.Series:
    returns = returns.dropna()
    cumulative = (1 + returns).cumprod()

    annual_return = cumulative.iloc[-1] ** (TRADING_DAYS / len(returns)) - 1
    annual_vol = returns.std() * np.sqrt(TRADING_DAYS)
    sharpe = annual_return / annual_vol if annual_vol != 0 else np.nan

    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min()

    return pd.Series({
        "Annual Return": annual_return,
        "Annual Volatility": annual_vol,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown,
    })


print("\n=== FULL CARRY STRATEGY (spot + carry) ===")
print(performance_metrics(total_basket))

print("\n--- Spot-only component ---")
print(performance_metrics(spot_basket))

print("\n--- Carry-only component ---")
print(performance_metrics(carry_basket))



# CUMULATIVE PERFORMANCE: total vs spot vs carry

cum_total = (1 + total_basket).cumprod()
cum_spot = (1 + spot_basket).cumprod()
cum_carry = (1 + carry_basket).cumprod()

plt.figure(figsize=(10, 5))
plt.plot(cum_total.index, cum_total, label="Total (spot + carry)", linewidth=2)
plt.plot(cum_spot.index, cum_spot, label="Spot component", alpha=0.7)
plt.plot(cum_carry.index, cum_carry, label="Carry component", alpha=0.7)
plt.title("FX Carry Trade Backtest - return decomposition")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.grid(True)
plt.show()


# VIX REGIME ANALYSIS

vix = yf.download("^VIX", start=start_date, end=end_date,
                  auto_adjust=True, progress=False)["Close"]
if isinstance(vix, pd.DataFrame):
    vix = vix.squeeze()
vix = vix.reindex(total_basket.index).ffill()

high_vol_mask = vix > 20
low_vol_mask = vix <= 20

print("\n=== HIGH VOLATILITY REGIME (VIX > 20) ===")
print(performance_metrics(total_basket.loc[high_vol_mask]))

print("\n=== LOW VOLATILITY REGIME (VIX <= 20) ===")
print(performance_metrics(total_basket.loc[low_vol_mask]))

plt.figure(figsize=(10, 5))
plt.plot(cum_total.index, cum_total, label="FX Carry Basket (total)")
plt.fill_between(cum_total.index, cum_total.min(), cum_total.max(),
                 where=high_vol_mask.values, alpha=0.3, label="High VIX Regime")
plt.title("FX Carry Strategy with Market Regimes")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.grid(True)
plt.show()
