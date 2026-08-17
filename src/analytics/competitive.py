"""
Competitive Analysis for Project Polaris
=========================================

Competitor scoring, ranking, comparison, and positioning.
All methodologies are transparent and documented.
"""

import numpy as np
import pandas as pd
from typing import Optional, List


# Competitive score weights — displayed in the UI and Methodology page
SCORE_WEIGHTS = {
    "rating": 0.25,
    "monthly_reviews": 0.20,
    "sentiment_score": 0.20,
    "engagement_rate": 0.15,
    "review_growth_rate": 0.10,
    "service_score": 0.10,
}

WEIGHT_LABELS = {
    "rating": "Rating",
    "monthly_reviews": "Review Volume",
    "sentiment_score": "Sentiment",
    "engagement_rate": "Engagement",
    "review_growth_rate": "Growth",
    "service_score": "Service Quality",
}


def get_competitor_ranking(df: pd.DataFrame, date: Optional[str] = None,
                           limit: int = 20) -> dict:
    """
    Rank businesses by competitive score for a given month.
    Returns the ranking table with score breakdown.
    """
    if date:
        period = df[df["date"] == date]
    else:
        period = df[df["date"] == df["date"].max()]

    ranked = period.sort_values("competitive_score", ascending=False).head(limit)

    rankings = []
    for rank, (_, row) in enumerate(ranked.iterrows(), 1):
        rankings.append({
            "rank": rank,
            "business_id": row["business_id"],
            "business_name": row["business_name"],
            "category": row["category"],
            "location": row["location"],
            "rating": round(row["rating"], 2),
            "monthly_reviews": int(row["monthly_reviews"]),
            "sentiment_score": round(row["sentiment_score"], 3),
            "engagement_rate": round(row["engagement_rate"], 4),
            "review_growth_rate": round(row["review_growth_rate"], 4),
            "service_score": round(row["service_score"], 2),
            "competitive_score": round(row["competitive_score"], 1),
            "is_our_business": bool(row["is_our_business"]),
        })

    return {
        "period": str(period["date"].iloc[0])[:10] if len(period) > 0 else None,
        "total_businesses": int(len(period)),
        "methodology": {
            "name": "Weighted Composite Score",
            "description": "Businesses are ranked by a composite score computed from min-max normalized metrics within each month.",
            "weights": SCORE_WEIGHTS,
            "weight_labels": WEIGHT_LABELS,
        },
        "rankings": rankings,
    }


def compare_businesses(df: pd.DataFrame, business_ids: List[str],
                       date: Optional[str] = None) -> dict:
    """
    Compare selected businesses across key metrics.
    Returns comparison data suitable for bar charts / radar charts.
    """
    if date:
        period = df[df["date"] == date]
    else:
        period = df[df["date"] == df["date"].max()]

    comparison_metrics = [
        "rating", "monthly_reviews", "sentiment_score", "service_score",
        "value_score", "engagement_rate", "response_rate",
        "competitive_score", "review_growth_rate"
    ]

    businesses = []
    for biz_id in business_ids:
        biz_data = period[period["business_id"] == biz_id]
        if len(biz_data) == 0:
            continue
        row = biz_data.iloc[0]
        entry = {
            "business_id": biz_id,
            "business_name": row["business_name"],
            "is_our_business": bool(row["is_our_business"]),
        }
        for metric in comparison_metrics:
            entry[metric] = round(float(row[metric]), 4)
        businesses.append(entry)

    # Also compute market averages for reference
    market_avg = {}
    for metric in comparison_metrics:
        market_avg[metric] = round(float(period[metric].mean()), 4)

    return {
        "period": str(period["date"].iloc[0])[:10] if len(period) > 0 else None,
        "businesses": businesses,
        "market_average": market_avg,
        "metrics": comparison_metrics,
    }


def get_positioning_data(df: pd.DataFrame, date: Optional[str] = None,
                         x_metric: str = "monthly_reviews",
                         y_metric: str = "rating") -> dict:
    """
    Generate scatter plot data for competitive positioning.
    Each business is a point; axes are configurable.
    Includes quadrant definitions based on median splits.
    """
    if date:
        period = df[df["date"] == date]
    else:
        period = df[df["date"] == df["date"].max()]

    x_median = float(period[x_metric].median())
    y_median = float(period[y_metric].median())

    points = []
    for _, row in period.iterrows():
        x_val = float(row[x_metric])
        y_val = float(row[y_metric])

        # Determine quadrant
        if x_val >= x_median and y_val >= y_median:
            quadrant = "Market Leaders"
        elif x_val < x_median and y_val >= y_median:
            quadrant = "Niche Quality"
        elif x_val >= x_median and y_val < y_median:
            quadrant = "High Volume, Lower Quality"
        else:
            quadrant = "Emerging / Struggling"

        points.append({
            "business_id": row["business_id"],
            "business_name": row["business_name"],
            "x": round(x_val, 4),
            "y": round(y_val, 4),
            "size": int(row["review_count"]),
            "category": row["category"],
            "quadrant": quadrant,
            "is_our_business": bool(row["is_our_business"]),
            "competitive_score": round(float(row["competitive_score"]), 1),
        })

    return {
        "x_metric": x_metric,
        "y_metric": y_metric,
        "x_median": round(x_median, 4),
        "y_median": round(y_median, 4),
        "quadrants": {
            "top_right": {"label": "Market Leaders", "description": f"High {x_metric} and high {y_metric}"},
            "top_left": {"label": "Niche Quality", "description": f"Low {x_metric} but high {y_metric}"},
            "bottom_right": {"label": "High Volume, Lower Quality", "description": f"High {x_metric} but low {y_metric}"},
            "bottom_left": {"label": "Emerging / Struggling", "description": f"Low {x_metric} and low {y_metric}"},
        },
        "points": points,
    }
