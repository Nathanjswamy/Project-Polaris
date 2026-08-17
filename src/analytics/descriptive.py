"""
Descriptive Analytics for Project Polaris
=========================================

Summary statistics, distributions, and aggregations.
Provides the data backing the Executive Overview.
"""

import numpy as np
import pandas as pd
from typing import Optional


def compute_overview_kpis(df: pd.DataFrame, latest_date: Optional[str] = None) -> dict:
    """
    Compute the 6 executive KPIs for the Overview page.
    Each KPI includes: current value, previous period value, % change.

    Uses the most recent month vs. the month before.
    """
    dates = sorted(df["date"].unique())
    if latest_date:
        current_date = pd.Timestamp(latest_date)
    else:
        current_date = dates[-1]

    # Find previous period
    date_idx = list(dates).index(current_date)
    prev_date = dates[max(0, date_idx - 1)]

    current = df[df["date"] == current_date]
    previous = df[df["date"] == prev_date]

    def pct_change(curr_val, prev_val):
        if prev_val == 0:
            return 0.0
        return round((curr_val - prev_val) / abs(prev_val) * 100, 2)

    kpis = {}

    # 1. Average Rating
    curr_rating = round(current["rating"].mean(), 2)
    prev_rating = round(previous["rating"].mean(), 2)
    kpis["avg_rating"] = {
        "label": "Average Rating",
        "value": curr_rating,
        "previous": prev_rating,
        "change_pct": pct_change(curr_rating, prev_rating),
        "format": "decimal",
        "definition": "Mean rating across all monitored businesses for the current period.",
    }

    # 2. Review Volume (total monthly reviews)
    curr_reviews = int(current["monthly_reviews"].sum())
    prev_reviews = int(previous["monthly_reviews"].sum())
    kpis["review_volume"] = {
        "label": "Review Volume",
        "value": curr_reviews,
        "previous": prev_reviews,
        "change_pct": pct_change(curr_reviews, prev_reviews),
        "format": "integer",
        "definition": "Total new reviews received across all businesses this month.",
    }

    # 3. Sentiment Score
    curr_sent = round(current["sentiment_score"].mean(), 3)
    prev_sent = round(previous["sentiment_score"].mean(), 3)
    kpis["sentiment_score"] = {
        "label": "Avg Sentiment",
        "value": curr_sent,
        "previous": prev_sent,
        "change_pct": pct_change(curr_sent, prev_sent),
        "format": "decimal",
        "definition": "Mean sentiment score (-1 to 1) across all businesses. Based on pre-existing structured sentiment scores.",
    }

    # 4. Competitive Position (our business's competitive_score rank)
    our_biz = current[current["is_our_business"] == True]
    if len(our_biz) > 0:
        our_score = float(our_biz["competitive_score"].iloc[0])
        our_rank = int((current["competitive_score"] >= our_score).sum())
        total = len(current)
        position_pct = round(our_rank / total * 100, 1)
    else:
        our_rank = 0
        total = len(current)
        position_pct = 0.0

    prev_our = previous[previous["is_our_business"] == True]
    if len(prev_our) > 0:
        prev_score = float(prev_our["competitive_score"].iloc[0])
        prev_rank = int((previous["competitive_score"] >= prev_score).sum())
        prev_total = len(previous)
        prev_position_pct = round(prev_rank / prev_total * 100, 1)
    else:
        prev_position_pct = 0.0

    kpis["competitive_position"] = {
        "label": "Competitive Position",
        "value": f"#{our_rank} of {total}",
        "value_numeric": our_rank,
        "total": total,
        "percentile": position_pct,
        "previous_percentile": prev_position_pct,
        "change_pct": pct_change(position_pct, prev_position_pct) if prev_position_pct else 0,
        "format": "rank",
        "definition": "Our business's rank by competitive score among all monitored businesses.",
    }

    # 5. Market Growth (month-over-month change in total reviews)
    market_growth = pct_change(curr_reviews, prev_reviews)
    kpis["market_growth"] = {
        "label": "Market Growth",
        "value": market_growth,
        "previous": 0,
        "change_pct": market_growth,
        "format": "percentage",
        "definition": "Month-over-month change in total market review volume.",
    }

    # 6. Avg Engagement Rate
    curr_eng = round(current["engagement_rate"].mean(), 4)
    prev_eng = round(previous["engagement_rate"].mean(), 4)
    kpis["engagement_rate"] = {
        "label": "Avg Engagement Rate",
        "value": curr_eng,
        "previous": prev_eng,
        "change_pct": pct_change(curr_eng, prev_eng),
        "format": "percentage",
        "definition": "Mean social engagement rate across all businesses.",
    }

    return {
        "current_period": str(current_date)[:10],
        "previous_period": str(prev_date)[:10],
        "kpis": kpis,
    }


def compute_time_series(df: pd.DataFrame, metric: str = "rating",
                        business_id: Optional[str] = None) -> list:
    """
    Compute monthly time series for a given metric.
    If business_id is provided, returns data for that business.
    Otherwise, returns market-wide averages.
    """
    if business_id:
        data = df[df["business_id"] == business_id].copy()
    else:
        data = df.copy()

    grouped = data.groupby("date").agg(
        value=(metric, "mean"),
    ).reset_index()

    grouped = grouped.sort_values("date")

    return [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "value": round(row["value"], 4),
        }
        for _, row in grouped.iterrows()
    ]


def compute_sparkline(df: pd.DataFrame, metric: str,
                      business_id: Optional[str] = None,
                      periods: int = 6) -> list:
    """Generate a compact sparkline (last N periods) for a KPI."""
    ts = compute_time_series(df, metric, business_id)
    return [point["value"] for point in ts[-periods:]]


def compute_distributions(df: pd.DataFrame, metric: str,
                          date: Optional[str] = None) -> dict:
    """
    Compute distribution statistics for a metric at a point in time.
    Returns histogram data + summary stats.
    """
    if date:
        data = df[df["date"] == date][metric].dropna()
    else:
        # Latest date
        latest = df["date"].max()
        data = df[df["date"] == latest][metric].dropna()

    hist, bin_edges = np.histogram(data, bins=20)

    return {
        "metric": metric,
        "count": int(len(data)),
        "mean": round(float(data.mean()), 4),
        "median": round(float(data.median()), 4),
        "std": round(float(data.std()), 4),
        "min": round(float(data.min()), 4),
        "max": round(float(data.max()), 4),
        "q25": round(float(data.quantile(0.25)), 4),
        "q75": round(float(data.quantile(0.75)), 4),
        "histogram": {
            "counts": hist.tolist(),
            "bin_edges": [round(float(b), 4) for b in bin_edges],
        },
    }
