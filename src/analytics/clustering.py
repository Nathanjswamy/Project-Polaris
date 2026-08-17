"""
Clustering / Segmentation for Project Polaris
==============================================

K-Means segmentation on standardized business features.
Uses silhouette score for k selection.
Cluster labels derived from centroid characteristics, not arbitrary names.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# Features used for clustering — each has an analytical justification
CLUSTERING_FEATURES = [
    "rating",
    "monthly_reviews",
    "sentiment_score",
    "engagement_rate",
    "review_growth_rate",
    "service_score",
    "price_level",
]

FEATURE_LABELS = {
    "rating": "Rating",
    "monthly_reviews": "Review Volume",
    "sentiment_score": "Sentiment",
    "engagement_rate": "Engagement",
    "review_growth_rate": "Growth",
    "service_score": "Service",
    "price_level": "Price Level",
}


def _characterize_cluster(centroid: np.ndarray, feature_names: list,
                          global_means: np.ndarray) -> str:
    """
    Generate a descriptive label for a cluster based on which features
    are above or below the global mean.
    """
    above = []
    below = []
    for i, feat in enumerate(feature_names):
        label = FEATURE_LABELS.get(feat, feat)
        if centroid[i] > global_means[i] + 0.3:
            above.append(label)
        elif centroid[i] < global_means[i] - 0.3:
            below.append(label)

    if len(above) >= 3 and "Rating" in above and "Service" in above:
        return "Premium Leaders"
    elif "Review Volume" in above and "Growth" in above:
        return "High-Volume Growth"
    elif "Rating" in above and "Review Volume" not in above:
        return "Niche Quality"
    elif "Growth" in above and "Engagement" in above:
        return "Emerging Challengers"
    elif len(below) >= 3:
        return "Low-Engagement Businesses"
    elif "Review Volume" in above:
        return "High-Volume Mainstream"
    else:
        return "Moderate Performers"


def run_segmentation(df: pd.DataFrame, date: str = None,
                     k_range: tuple = (3, 7)) -> dict:
    """
    Run K-Means clustering on the latest month's data.
    Uses silhouette score to select optimal k.
    """
    if date:
        period = df[df["date"] == date].copy()
    else:
        period = df[df["date"] == df["date"].max()].copy()

    # Prepare features
    feature_data = period[CLUSTERING_FEATURES].copy()
    feature_data = feature_data.fillna(feature_data.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_data)

    # Select optimal k using silhouette score
    best_k = k_range[0]
    best_score = -1
    silhouette_scores = {}

    for k in range(k_range[0], k_range[1] + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        silhouette_scores[k] = round(score, 4)
        if score > best_score:
            best_score = score
            best_k = k

    # Run final clustering with optimal k
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    period["cluster_id"] = kmeans.fit_predict(X_scaled)

    # Compute global means for labeling (in scaled space)
    global_means = X_scaled.mean(axis=0)

    # Characterize clusters
    clusters = []
    for cluster_id in range(best_k):
        cluster_mask = period["cluster_id"] == cluster_id
        cluster_data = period[cluster_mask]
        centroid = kmeans.cluster_centers_[cluster_id]

        label = _characterize_cluster(centroid, CLUSTERING_FEATURES, global_means)

        # Cluster statistics
        stats = {}
        for feat in CLUSTERING_FEATURES:
            stats[feat] = {
                "mean": round(float(cluster_data[feat].mean()), 4),
                "std": round(float(cluster_data[feat].std()), 4),
                "min": round(float(cluster_data[feat].min()), 4),
                "max": round(float(cluster_data[feat].max()), 4),
            }

        clusters.append({
            "cluster_id": int(cluster_id),
            "label": label,
            "size": int(cluster_mask.sum()),
            "percentage": round(cluster_mask.sum() / len(period) * 100, 1),
            "statistics": stats,
        })

    # Business-level assignments for scatter plot
    assignments = []
    for _, row in period.iterrows():
        assignments.append({
            "business_id": row["business_id"],
            "business_name": row["business_name"],
            "cluster_id": int(row["cluster_id"]),
            "cluster_label": clusters[int(row["cluster_id"])]["label"],
            "rating": round(float(row["rating"]), 2),
            "monthly_reviews": int(row["monthly_reviews"]),
            "sentiment_score": round(float(row["sentiment_score"]), 3),
            "competitive_score": round(float(row["competitive_score"]), 1),
            "is_our_business": bool(row["is_our_business"]),
        })

    return {
        "methodology": {
            "algorithm": "K-Means Clustering",
            "features": CLUSTERING_FEATURES,
            "feature_labels": FEATURE_LABELS,
            "preprocessing": "StandardScaler (z-score normalization)",
            "k_selection": "Silhouette Score",
            "optimal_k": best_k,
            "silhouette_score": round(best_score, 4),
            "silhouette_scores_by_k": silhouette_scores,
            "note": "Cluster labels are derived from centroid characteristics relative to global means, not arbitrary names.",
        },
        "clusters": clusters,
        "assignments": assignments,
    }
