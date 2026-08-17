"""
Sentiment Analysis for Project Polaris
=======================================

Aggregation of STRUCTURED sentiment scores.
This dataset does NOT contain raw review text, so no NLP is performed.
All sentiment analysis is based on pre-existing sentiment scores.
This is clearly stated throughout the UI.
"""

import numpy as np
import pandas as pd
from typing import Optional


# Simulated topic assignments for sentiment breakdown
# In a real system, these would come from NLP topic modeling on review text.
# Here, we simulate topic distribution based on structured scores.
TOPICS = ["Service", "Quality", "Ambiance", "Price", "Speed", "Staff", "Location"]


def compute_sentiment_distribution(df: pd.DataFrame,
                                    date: Optional[str] = None) -> dict:
    """
    Compute sentiment distribution (positive / neutral / negative)
    for a given period.
    """
    if date:
        data = df[df["date"] == date]
    else:
        data = df[df["date"] == df["date"].max()]

    sentiments = data["sentiment_score"].dropna()

    positive = int((sentiments > 0.2).sum())
    neutral = int(((sentiments >= -0.2) & (sentiments <= 0.2)).sum())
    negative = int((sentiments < -0.2).sum())
    total = positive + neutral + negative

    return {
        "period": str(data["date"].iloc[0])[:10] if len(data) > 0 else None,
        "total": total,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "positive_pct": round(positive / max(total, 1) * 100, 1),
        "neutral_pct": round(neutral / max(total, 1) * 100, 1),
        "negative_pct": round(negative / max(total, 1) * 100, 1),
        "mean_sentiment": round(float(sentiments.mean()), 3) if len(sentiments) > 0 else 0,
        "note": "Sentiment classification is based on pre-existing structured sentiment scores, not NLP analysis of review text.",
    }


def compute_sentiment_trends(df: pd.DataFrame,
                              business_id: Optional[str] = None) -> list:
    """
    Compute sentiment trends over time.
    Returns monthly sentiment breakdown.
    """
    if business_id:
        data = df[df["business_id"] == business_id].copy()
    else:
        data = df.copy()

    grouped = data.groupby("date").agg(
        mean_sentiment=("sentiment_score", "mean"),
        positive_count=("sentiment_score", lambda x: (x > 0.2).sum()),
        neutral_count=("sentiment_score", lambda x: ((x >= -0.2) & (x <= 0.2)).sum()),
        negative_count=("sentiment_score", lambda x: (x < -0.2).sum()),
        total=("sentiment_score", "count"),
    ).reset_index().sort_values("date")

    trends = []
    for _, row in grouped.iterrows():
        total = int(row["total"])
        trends.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "mean_sentiment": round(float(row["mean_sentiment"]), 3),
            "positive_pct": round(int(row["positive_count"]) / max(total, 1) * 100, 1),
            "neutral_pct": round(int(row["neutral_count"]) / max(total, 1) * 100, 1),
            "negative_pct": round(int(row["negative_count"]) / max(total, 1) * 100, 1),
        })

    return trends


def compute_topic_analysis(df: pd.DataFrame,
                           date: Optional[str] = None) -> dict:
    """
    Simulate topic-level sentiment analysis.

    Since we don't have raw review text, topics are SIMULATED
    by distributing the overall sentiment score across predefined
    topic categories with realistic variation.

    This is clearly labeled as simulated in the response.
    """
    np.random.seed(42)

    if date:
        data = df[df["date"] == date]
    else:
        data = df[df["date"] == df["date"].max()]

    base_sentiment = float(data["sentiment_score"].mean())
    n_businesses = len(data)

    topics = []
    for topic in TOPICS:
        # Add realistic variation per topic
        topic_offset = np.random.uniform(-0.15, 0.15)
        topic_sentiment = np.clip(base_sentiment + topic_offset, -1, 1)

        # Simulate mention count (some topics mentioned more than others)
        mention_rate = np.random.uniform(0.3, 0.8)
        mention_count = int(n_businesses * mention_rate)

        # Trend (slight variation)
        trend = np.random.choice(["improving", "stable", "declining"],
                                  p=[0.35, 0.40, 0.25])

        topics.append({
            "topic": topic,
            "mention_count": mention_count,
            "avg_sentiment": round(topic_sentiment, 3),
            "trend": trend,
        })

    # Sort by mention count descending
    topics.sort(key=lambda x: x["mention_count"], reverse=True)

    return {
        "topics": topics,
        "note": "Topic analysis is SIMULATED based on structured sentiment scores. No NLP or text analysis was performed. In a production system, topics would be extracted from review text using topic modeling.",
    }
