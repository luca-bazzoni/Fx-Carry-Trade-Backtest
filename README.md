# FX Carry Trade Backtest

A Python backtest of a multi-currency FX carry strategy, with a clean
decomposition of returns into **spot** and **carry** components and an
analysis of performance conditional on **market volatility regimes** (VIX).

The goal of the project is not to find an optimal trading strategy, but to
implement a carry strategy correctly, measure it honestly, and understand
*where* its return and risk come from.

---

## What it does

- Builds long/short positions on four major pairs (EUR, GBP, AUD, JPY vs USD)
  from the sign of the interest-rate differential against the USD.
- Computes the **full carry P&L**, i.e. spot move **plus** the interest-rate
  carry actually earned by the position — not just the spot return.
- **Decomposes** the total P&L into a spot component and a carry component to
  show how much of the return comes from each.
- Reports risk-adjusted metrics (annualised return, volatility, Sharpe,
  max drawdown).
- Splits realised performance by **VIX regime** (calm vs stressed markets) to
  study the strategy's behaviour across the cycle.

---

## Methodology

**Data**
- FX spot: Yahoo Finance (`yfinance`), daily, 2015–2025.
- Short-term rates: FRED 3-month interbank proxies (OECD) for EUR, GBP, AUD,
  JPY, and the Fed Funds rate for USD. Provided as CSV files in `data/`.
- VIX: Yahoo Finance, used only for the (descriptive) regime split.

**Signal**
- For each pair: long the foreign currency vs USD if its rate is higher than
  the USD rate, short otherwise. Signals are **lagged one day** to avoid
  look-ahead bias.

**Return model**

For each position:

```
position_return = direction * ( spot_return + daily_carry )
daily_carry     = (r_foreign - r_usd) / 252
```

The basket is equal-weighted across the four pairs. The same logic is computed
separately for the spot-only and carry-only legs to produce the decomposition.

---

## Key results (2015–2025, equal-weight, unlevered)

| Strategy            | Ann. return | Ann. vol | Sharpe | Max drawdown |
|---------------------|------------:|---------:|-------:|-------------:|
| **Full (spot+carry)** | 1.48%     | 5.47%    | 0.27   | −12.1%       |
| Spot component       | 0.40%      | 5.47%    | 0.07   | −14.1%       |
| Carry component      | 1.08%      | ~0%      | n/a*   | ~0%          |

\* The carry leg is a near-deterministic accrual, so its standalone volatility
is ≈ 0 and a standalone Sharpe is **not meaningful** — carry cannot be earned
without bearing the spot risk. The decomposition is used to attribute *return*,
not to compute a risk-adjusted ratio on the carry in isolation.

**Performance by VIX regime**

| Regime              | Ann. return | Sharpe | Max drawdown |
|---------------------|------------:|-------:|-------------:|
| Low VIX (≤ 20)      | 2.50%       | 0.52   | −8.7%        |
| High VIX (> 20)     | −0.81%      | −0.12  | −11.6%       |

**Takeaways**
- The carry leg drives most of the return and almost all of the *stability*;
  the spot leg adds little return and most of the volatility and drawdown.
- The strategy earns steadily in calm markets and loses in stress — the classic
  carry signature of selling implicit tail-risk insurance.
- Real tail events (e.g. the June 2016 Brexit move in GBP, −7.6% in a day) are
  **kept in** the sample, not cleaned out, to keep the risk picture honest.

---

## How to run

```bash
pip install numpy pandas yfinance matplotlib
python FX_Carry_Trade_Backtest_fixed.py
```

Interest-rate CSVs are read from the `data/` folder (downloaded from FRED), so
the rate series are reproducible without hitting the FRED API. FX and VIX are
pulled live from Yahoo Finance at runtime. Set `RATES_DIR` at the top of the
script to point at `data/`.

Required CSV files in `data/`:
`FEDFUNDS.csv`, `IR3TIB01EZM156N.csv`, `IR3TIB01GBM156N.csv`,
`IR3TIB01AUM156N.csv`, `IR3TIB01JPM156N.csv`.

---

## Known limitations

- Rates are short-term proxies at **monthly** frequency, forward-filled to
  daily — so the carry signal effectively updates monthly.
- No transaction costs or bid/ask spreads; equal-weight basket.
- Binary long/short per pair on the sign of the differential, rather than a
  cross-sectional ranking.
- The VIX > 20 split is a fixed, **descriptive** threshold applied ex-post, not
  an input to the strategy.

## Possible extensions

- Cross-sectional carry: long the top-yielding currencies, short the lowest.
- Volatility targeting / risk-parity weighting instead of equal weight.
- Higher-frequency money-market rates (€STR, SOFR, SONIA) for a daily signal.
- Transaction-cost modelling.

---

*Author: Luca Bazzoni — personal quantitative project.*
