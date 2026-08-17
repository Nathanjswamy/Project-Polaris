"""
Analytical Alerts for Project Polaris
======================================

Rule-based alerts computed from data thresholds.
Each alert includes severity, metric, threshold, current/previous values, and explanation.
"""

import numpy as np
import pandas as pd
from typing import Optional


# Alert rules: metric, comparison, threshold, severity
ALERT_RULES = [
    {
        "id": "rating_drop",
        "metric": "rating",
        "label": "Rating Decline",
        "comparison": "decrease_pct",
        "threshold": 3.0,  # >3% drop
        "severity_thresholds": {"high": 5.0, "medium": 3.0},
    },
    {
        "id": "sentiment_decline",
        "metric": "sentiment_score",
        "label": "Sentiment Decline",
        "comparison": "decrease_pct",
        "threshold": 8.0,
        "severity_thresholds": {"high": 15.0, "medium": 8.0},
    },
    {
        "id": "review_volume_drop",
        "metric": "monthly_reviews",
        "label": "Review Volume Drop",
        "comparison": "decrease_pct",
        "threshold": 15.0,
        "severity_thresholds": {"high": 25.0, "medium": 15.0},
    },
    {
        "id": "response_time_increase",
        "metric": "response_time_hours",
        "label": "Response Time Increase",
        "comparison": "increase_pct",
        "threshold": 20.0,
        "severity_thresholds": {"high": 40.0, "medium": 20.0},
    },
    {
        "id": "engagement_drop",
        "metric": "engagement_rate",
        "label": "Engagement Rate Drop",
        "comparison": "decrease_pct",
        "threshold": 10.0,
        "severity_thresholds": {"high": 20.0, "medium": 10.0},
    },
    {
        "id": "competitive_position_decline",
        "metric": "competitive_score",
        "label": "Competitive Position Decline",
        "comparison": "decrease_pct",
        "threshold": 5.0,
        "severity_thresholds": {"high": 10.0, "medium": 5.0},
    },
]


def compute_alerts(df: pd.DataFrame,
                   business_id: Optional[str] = None) -> list:
    """
    Compute analytical alerts based on period-over-period changes.
    If business_id is provided, checks alerts for that business.
    Otherwise, checks market-wide alerts.
    """
    dates = sorted(df["date"].unique())
    if len(dates) < 2:
        return []

    current_date = dates[-1]
    previous_date = dates[-2]

    if business_id:
        current = df[(df["date"] == current_date) & (df["business_id"] == business_id)]
        previous = df[(df["date"] == previous_date) & (df["business_id"] == business_id)]
        scope = "business"
    else:
        current = df[df["date"] == current_date]
        previous = df[df["date"] == previous_date]
        scope = "market"

    if len(current) == 0 or len(previous) == 0:
        return []

    alerts = []

    for rule in ALERT_RULES:
        metric = rule["metric"]
        if metric not in current.columns:
            continue

        curr_val = float(current[metric].mean())
        prev_val = float(previous[metric].mean())

        if prev_val == 0:
            continue

        pct_change = (curr_val - prev_val) / abs(prev_val) * 100

        # Check if alert should fire
        triggered = False
        if rule["comparison"] == "decrease_pct" and pct_change < -rule["threshold"]:
            triggered = True
            change_magnitude = abs(pct_change)
        elif rule["comparison"] == "increase_pct" and pct_change > rule["threshold"]:
            triggered = True
            change_magnitude = pct_change

        if triggered:
            # Determine severity
            high_thresh = rule["severity_thresholds"]["high"]
            if change_magnitude >= high_thresh:
                severity = "high"
            else:
                severity = "medium"

            explanation = _generate_explanation(rule, curr_val, prev_val, pct_change, scope)

            alerts.append({
                "id": rule["id"],
                "severity": severity,
                "label": rule["label"],
                "metric": metric,
                "current_value": round(curr_val, 4),
                "previous_value": round(prev_val, 4),
                "change_pct": round(pct_change, 2),
                "threshold": rule["threshold"],
                "current_period": str(current_date)[:10],
                "previous_period": str(previous_date)[:10],
                "explanation": explanation,
                "scope": scope,
            })

    # Sort by severity (high first)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return alerts


def _generate_explanation(rule: dict, curr: float, prev: float,
                          pct_change: float, scope: str) -> str:
    """Generate a human-readable explanation for an alert."""
    direction = "decreased" if pct_change < 0 else "increased"
    scope_text = "Our business's" if scope == "business" else "The market's"

    explanations = {
        "rating_drop": f"{scope_text} average rating {direction} from {prev:.2f} to {curr:.2f} ({pct_change:+.1f}%). This exceeds the {rule['threshold']}% monitoring threshold.",
        "sentiment_decline": f"{scope_text} average sentiment {direction} from {prev:.3f} to {curr:.3f} ({pct_change:+.1f}%). Consider investigating recent customer feedback patterns.",
        "review_volume_drop": f"{scope_text} monthly review volume {direction} by {abs(pct_change):.1f}%. This may indicate reduced customer engagement or foot traffic.",
        "response_time_increase": f"{scope_text} average response time {direction} from {prev:.1f}h to {curr:.1f}h ({pct_change:+.1f}%). Slower responses are associated with lower customer satisfaction.",
        "engagement_drop": f"{scope_text} engagement rate {direction} by {abs(pct_change):.1f}%. Review recent content strategy and posting frequency.",
        "competitive_position_decline": f"{scope_text} competitive score {direction} by {abs(pct_change):.1f}%. Competitors may be gaining ground.",
    }

    return explanations.get(rule["id"], f"{scope_text} {rule['label']} has changed by {pct_change:+.1f}%.")
