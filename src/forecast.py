"""
FinSight AI - forecast.py

Forecasts Fielmann Group's quarterly total consolidated sales using
Holt-Winters additive exponential smoothing: a level, a trend, and a
quarterly seasonal component, each with its own smoothing weight, fit by
minimizing one-step-ahead squared forecast error.

Why this method: a first pass with trend-only (Holt's linear) smoothing
degenerated to a straight line and missed a real, consistent pattern in the
data - Q4 total consolidated sales dips versus Q3 in every single year in
the series (2023, 2024, 2025). That's a genuine seasonal effect specific to
this business (an eyewear/hearing-care retailer doesn't get the Q4 gift-retail
bump a typical retailer would), not noise, so it's worth modeling explicitly
rather than smoothing it away. Holt-Winters keeps the same "level + trend"
core, with a seasonal index added on top - still one simple, explainable
method, no black-box library.

Run directly for a quick check:
    python src/forecast.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.optimize import minimize

DATA_PATH = "data/processed/fielmann_quarterly_2023_2026.csv"
SEASON_LENGTH = 4  # quarterly


def load_quarterly_series(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.sort_values(["year", "quarter"]).reset_index(drop=True)
    return df


def holt_winters_additive(
    values: np.ndarray, alpha: float, beta: float, gamma: float, steps: int, m: int = SEASON_LENGTH
) -> tuple[np.ndarray, np.ndarray]:
    """
    Holt-Winters additive method.

    level[t]    = alpha * (y[t] - season[t-m]) + (1-alpha) * (level[t-1] + trend[t-1])
    trend[t]    = beta  * (level[t] - level[t-1]) + (1-beta) * trend[t-1]
    season[t]   = gamma * (y[t] - level[t]) + (1-gamma) * season[t-m]

    Requires at least 2*m data points to initialize. Returns (fitted, forecast).
    """
    n = len(values)
    level = np.zeros(n)
    trend = np.zeros(n)
    season = np.zeros(n)
    fitted = np.zeros(n)

    # Initialize: level/trend from the first two full seasons' averages,
    # seasonal indices from the average deviation in the first two seasons.
    first_cycle_avg = values[:m].mean()
    second_cycle_avg = values[m : 2 * m].mean()
    level[m - 1] = first_cycle_avg
    trend[m - 1] = (second_cycle_avg - first_cycle_avg) / m
    for i in range(m):
        season[i] = values[i] - first_cycle_avg

    for t in range(m, n):
        fitted[t] = level[t - 1] + trend[t - 1] + season[t - m]
        level[t] = alpha * (values[t] - season[t - m]) + (1 - alpha) * (level[t - 1] + trend[t - 1])
        trend[t] = beta * (level[t] - level[t - 1]) + (1 - beta) * trend[t - 1]
        season[t] = gamma * (values[t] - level[t]) + (1 - gamma) * season[t - m]

    forecast = np.zeros(steps)
    for h in range(steps):
        season_idx = n - m + (h % m)
        forecast[h] = level[n - 1] + (h + 1) * trend[n - 1] + season[season_idx]

    return fitted, forecast


def _sse(params: np.ndarray, values: np.ndarray) -> float:
    alpha, beta, gamma = params
    if not all(0 < p < 1 for p in params):
        return np.inf
    fitted, _ = holt_winters_additive(values, alpha, beta, gamma, steps=1)
    residuals = values[SEASON_LENGTH:] - fitted[SEASON_LENGTH:]
    return float(np.sum(residuals**2))


def fit_holt_winters(values: np.ndarray) -> dict:
    result = minimize(
        _sse,
        x0=np.array([0.4, 0.1, 0.3]),
        args=(values,),
        method="Nelder-Mead",
        bounds=[(0.01, 0.99)] * 3,
    )
    alpha, beta, gamma = result.x
    fitted, _ = holt_winters_additive(values, alpha, beta, gamma, steps=1)
    residuals = values[SEASON_LENGTH:] - fitted[SEASON_LENGTH:]
    mape = float(np.mean(np.abs(residuals / values[SEASON_LENGTH:]))) * 100
    return {"alpha": alpha, "beta": beta, "gamma": gamma, "in_sample_mape_pct": mape}


def forecast_next_quarters(df: pd.DataFrame, steps: int = 2) -> dict:
    values = df["total_consolidated_sales_eur_m"].to_numpy(dtype=float)
    fit = fit_holt_winters(values)
    _, forecast = holt_winters_additive(values, fit["alpha"], fit["beta"], fit["gamma"], steps=steps)

    last_year = int(df["year"].iloc[-1])
    last_q = int(df["quarter"].iloc[-1][1])
    future_periods = []
    y, q = last_year, last_q
    for _ in range(steps):
        q += 1
        if q > 4:
            q = 1
            y += 1
        future_periods.append((y, q))

    yoy = []
    for (year, qtr), value in zip(future_periods, forecast):
        prior = df[(df["year"] == year - 1) & (df["quarter"] == f"Q{qtr}")]
        if not prior.empty:
            prior_val = float(prior["total_consolidated_sales_eur_m"].iloc[0])
            yoy_growth_pct = (value - prior_val) / prior_val * 100
        else:
            prior_val, yoy_growth_pct = None, None
        yoy.append(
            {
                "period": f"{year}Q{qtr}",
                "forecast_eur_m": round(float(value), 1),
                "prior_year_same_quarter_eur_m": prior_val,
                "yoy_growth_pct": round(yoy_growth_pct, 1) if yoy_growth_pct is not None else None,
            }
        )

    return {
        "model": "Holt-Winters additive (level + trend + quarterly seasonality)",
        "fitted_params": {k: round(v, 4) for k, v in fit.items()},
        "history_last_actual": {
            "period": f"{last_year}Q{last_q}",
            "value_eur_m": round(float(values[-1]), 1),
        },
        "forecast": yoy,
    }


if __name__ == "__main__":
    df = load_quarterly_series()
    result = forecast_next_quarters(df, steps=2)
    print(json.dumps(result, indent=2))
