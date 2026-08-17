"""
Forecasting Module for Project Polaris
=======================================

Exponential Smoothing on monthly time-series data.
Produces forecast + confidence intervals + evaluation metrics.

Uses statsmodels if available, falls back to simple moving average.
"""

import numpy as np
import pandas as pd
from typing import Optional

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def _moving_average_forecast(series: pd.Series, periods: int = 3,
                              forecast_horizon: int = 6) -> dict:
    """
    Simple moving average baseline forecast.
    Used when statsmodels is not available or when data is insufficient.
    """
    ma = series.rolling(window=periods).mean()
    last_ma = float(ma.iloc[-1]) if not np.isnan(ma.iloc[-1]) else float(series.mean())
    std = float(series.std())

    forecast_values = [last_ma] * forecast_horizon
    lower = [round(last_ma - 1.96 * std, 4)] * forecast_horizon
    upper = [round(last_ma + 1.96 * std, 4)] * forecast_horizon

    # Evaluation on last 3 points
    actual = series.iloc[-3:].values
    predicted = [last_ma] * min(3, len(actual))
    mae = round(float(np.mean(np.abs(actual[:len(predicted)] - predicted[:len(actual)]))), 4)
    rmse = round(float(np.sqrt(np.mean((actual[:len(predicted)] - predicted[:len(actual)]) ** 2))), 4)
    mape_vals = np.abs((actual[:len(predicted)] - predicted[:len(actual)]) / np.where(actual[:len(predicted)] == 0, 1, actual[:len(predicted)]))
    mape = round(float(np.mean(mape_vals) * 100), 2)

    return {
        "forecast": forecast_values,
        "lower": lower,
        "upper": upper,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "model_name": f"Simple Moving Average (window={periods})",
    }


def _exponential_smoothing_forecast(series: pd.Series,
                                     forecast_horizon: int = 6) -> dict:
    """
    Holt-Winters Exponential Smoothing forecast.
    """
    # Fit model
    try:
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,  # Monthly data may not have enough for seasonal
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)

        # Forecast
        forecast = fitted.forecast(forecast_horizon)
        forecast_values = [round(float(v), 4) for v in forecast.values]

        # Confidence intervals (approximate using residual std)
        residuals = fitted.resid
        std_resid = float(residuals.std())

        lower = [round(v - 1.96 * std_resid, 4) for v in forecast_values]
        upper = [round(v + 1.96 * std_resid, 4) for v in forecast_values]

        # Evaluation metrics (in-sample)
        fitted_values = fitted.fittedvalues
        actual = series.values
        predicted = fitted_values.values

        valid_mask = ~np.isnan(predicted) & ~np.isnan(actual)
        actual_clean = actual[valid_mask]
        predicted_clean = predicted[valid_mask]

        mae = round(float(np.mean(np.abs(actual_clean - predicted_clean))), 4)
        rmse = round(float(np.sqrt(np.mean((actual_clean - predicted_clean) ** 2))), 4)
        nonzero_mask = actual_clean != 0
        if nonzero_mask.sum() > 0:
            mape = round(float(np.mean(
                np.abs((actual_clean[nonzero_mask] - predicted_clean[nonzero_mask]) /
                       actual_clean[nonzero_mask])
            ) * 100), 2)
        else:
            mape = 0.0

        return {
            "forecast": forecast_values,
            "lower": lower,
            "upper": upper,
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "model_name": "Holt-Winters Exponential Smoothing (additive trend)",
        }
    except Exception:
        # Fall back to moving average if exponential smoothing fails
        return _moving_average_forecast(series, forecast_horizon=forecast_horizon)


def generate_forecast(df: pd.DataFrame,
                      metric: str = "rating",
                      business_id: Optional[str] = None,
                      forecast_horizon: int = 6) -> dict:
    """
    Generate a forecast for a given metric.

    Args:
        df: The processed dataset
        metric: The metric to forecast (rating, sentiment_score, monthly_reviews)
        business_id: Optional business filter. If None, uses market average.
        forecast_horizon: Number of months to forecast

    Returns:
        Dict with historical data, forecast, confidence intervals, and metrics.
    """
    if business_id:
        data = df[df["business_id"] == business_id].copy()
        scope = f"Business: {data['business_name'].iloc[0]}" if len(data) > 0 else "Unknown"
    else:
        data = df.groupby("date").agg({metric: "mean"}).reset_index()
        data["date"] = pd.to_datetime(data["date"])
        scope = "Market Average"

    data = data.sort_values("date")
    series = data.set_index("date")[metric].dropna()

    if len(series) < 6:
        return {
            "error": "Insufficient data for forecasting (need at least 6 data points).",
            "data_points": len(series),
        }

    # Run forecast
    if HAS_STATSMODELS and len(series) >= 12:
        result = _exponential_smoothing_forecast(series, forecast_horizon)
    else:
        result = _moving_average_forecast(series, forecast_horizon=forecast_horizon)

    # Historical data
    historical = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)}
        for d, v in series.items()
    ]

    # Forecast dates
    last_date = series.index[-1]
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1),
                                    periods=forecast_horizon, freq="MS")
    forecast_points = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "value": result["forecast"][i],
            "lower": result["lower"][i],
            "upper": result["upper"][i],
        }
        for i, d in enumerate(forecast_dates)
    ]

    return {
        "metric": metric,
        "scope": scope,
        "historical": historical,
        "forecast": forecast_points,
        "evaluation": {
            "mae": result["mae"],
            "rmse": result["rmse"],
            "mape": result["mape"],
            "mae_description": "Mean Absolute Error: average magnitude of forecast errors.",
            "rmse_description": "Root Mean Squared Error: penalizes larger errors more heavily.",
            "mape_description": "Mean Absolute Percentage Error: error as a percentage of actual values.",
        },
        "model": {
            "name": result["model_name"],
            "library": "statsmodels" if HAS_STATSMODELS else "numpy (fallback)",
            "note": "The simplest model that adequately fits the data is used. This is a statistical forecast, not a prediction — it represents expected values given historical patterns continue.",
        },
    }
