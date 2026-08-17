"""
Correlation & Drivers Analysis for Project Polaris
===================================================

Pearson correlation matrix and feature importance / drivers analysis.
All results are clearly labeled as ASSOCIATIONS, not causation.
"""

import numpy as np
import pandas as pd
from typing import Optional


# Metrics included in correlation analysis
CORRELATION_METRICS = [
    "rating", "sentiment_score", "monthly_reviews", "response_rate",
    "response_time_hours", "service_score", "value_score",
    "engagement_rate", "website_visits", "social_engagement",
    "repeat_customer_rate", "review_growth_rate",
]

METRIC_LABELS = {
    "rating": "Rating",
    "sentiment_score": "Sentiment",
    "monthly_reviews": "Review Volume",
    "response_rate": "Response Rate",
    "response_time_hours": "Response Time",
    "service_score": "Service Score",
    "value_score": "Value Score",
    "engagement_rate": "Engagement Rate",
    "website_visits": "Website Visits",
    "social_engagement": "Social Engagement",
    "repeat_customer_rate": "Repeat Customers",
    "review_growth_rate": "Review Growth",
}


def compute_correlation_matrix(df: pd.DataFrame,
                                date: Optional[str] = None) -> dict:
    """
    Compute Pearson correlation matrix across key metrics.

    IMPORTANT: Correlation measures linear association, not causation.
    This is clearly stated in the response and displayed in the UI.
    """
    if date:
        data = df[df["date"] == date]
    else:
        data = df[df["date"] == df["date"].max()]

    available_metrics = [m for m in CORRELATION_METRICS if m in data.columns]
    corr_data = data[available_metrics].dropna()
    corr_matrix = corr_data.corr(method="pearson")

    # Convert to serializable format
    matrix = []
    for row_metric in available_metrics:
        row_data = []
        for col_metric in available_metrics:
            val = corr_matrix.loc[row_metric, col_metric]
            row_data.append(round(float(val), 4))
        matrix.append(row_data)

    return {
        "metrics": available_metrics,
        "labels": [METRIC_LABELS.get(m, m) for m in available_metrics],
        "matrix": matrix,
        "method": "Pearson Correlation",
        "sample_size": len(corr_data),
        "note": "Correlation measures the strength and direction of a linear association between two variables. It does NOT imply causation.",
    }


def compute_drivers_analysis(df: pd.DataFrame,
                              target: str = "rating",
                              date: Optional[str] = None) -> dict:
    """
    Identify variables most strongly associated with the target metric.
    Uses correlation coefficients as a simple, transparent method.

    This is NOT a causal analysis. The methodology is:
    1. Compute Pearson correlation between each feature and the target.
    2. Sort by absolute correlation strength.
    3. Present as "factors most strongly associated with [target]".
    """
    if date:
        data = df[df["date"] == date]
    else:
        data = df[df["date"] == df["date"].max()]

    features = [m for m in CORRELATION_METRICS if m != target and m in data.columns]

    drivers = []
    for feature in features:
        clean_data = data[[feature, target]].dropna()
        if len(clean_data) < 10:
            continue
        corr = clean_data[feature].corr(clean_data[target])
        drivers.append({
            "feature": feature,
            "label": METRIC_LABELS.get(feature, feature),
            "correlation": round(float(corr), 4),
            "abs_correlation": round(abs(float(corr)), 4),
            "direction": "positive" if corr > 0 else "negative",
            "strength": _classify_strength(abs(corr)),
        })

    # Sort by absolute correlation
    drivers.sort(key=lambda x: x["abs_correlation"], reverse=True)

    return {
        "target": target,
        "target_label": METRIC_LABELS.get(target, target),
        "drivers": drivers,
        "methodology": {
            "method": "Pearson Correlation Coefficients",
            "description": "Each feature's linear association with the target metric is measured. Stronger absolute correlation indicates a stronger linear relationship.",
            "limitations": [
                "Correlation measures association, not causation.",
                "Only captures linear relationships.",
                "May be influenced by confounding variables.",
                "Small sample sizes may produce unreliable estimates.",
            ],
        },
    }


def _classify_strength(abs_corr: float) -> str:
    """Classify correlation strength following standard conventions."""
    if abs_corr >= 0.7:
        return "strong"
    elif abs_corr >= 0.4:
        return "moderate"
    elif abs_corr >= 0.2:
        return "weak"
    else:
        return "negligible"
