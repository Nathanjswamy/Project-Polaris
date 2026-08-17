"""
Opportunity Detection for Project Polaris
==========================================

Evidence-based opportunity analysis.
Every opportunity includes: Observation, Evidence, Implication, Action.
No causal claims unless statistically justified.
"""

import numpy as np
import pandas as pd
from typing import Optional


def detect_opportunities(df: pd.DataFrame,
                          our_business_id: str = "BIZ_001") -> list:
    """
    Detect competitive opportunities by comparing our business
    to the market and competitors.

    Each opportunity is structured as:
    - observation: What was observed
    - evidence: Measurable data supporting it
    - implication: What it may mean
    - action: Recommended next step
    - priority: high / medium / low
    """
    latest_date = df["date"].max()
    current = df[df["date"] == latest_date]
    our_biz = current[current["business_id"] == our_business_id]

    if len(our_biz) == 0:
        return []

    our = our_biz.iloc[0]
    competitors = current[current["business_id"] != our_business_id]
    opportunities = []

    # 1. Response Rate Advantage
    our_rr = float(our["response_rate"])
    comp_median_rr = float(competitors["response_rate"].median())
    if our_rr > comp_median_rr * 1.15:
        opportunities.append({
            "id": "response_rate_advantage",
            "observation": "Our response rate significantly exceeds competitor median.",
            "evidence": {
                "our_value": f"{our_rr:.1%}",
                "competitor_median": f"{comp_median_rr:.1%}",
                "difference": f"+{(our_rr - comp_median_rr):.1%}",
            },
            "implication": "Higher responsiveness is associated with stronger customer trust and may represent a competitive positioning opportunity.",
            "action": "Promote rapid-response service in marketing materials. Monitor whether response rate correlates with review sentiment improvement over the next 60 days.",
            "priority": "medium",
            "category": "Competitive Advantage",
        })

    # 2. Sentiment Gap
    our_sent = float(our["sentiment_score"])
    top_competitors = competitors.nlargest(10, "competitive_score")
    top_sent = float(top_competitors["sentiment_score"].mean())
    if our_sent < top_sent - 0.05:
        opportunities.append({
            "id": "sentiment_gap",
            "observation": "Our sentiment score trails top-10 competitors.",
            "evidence": {
                "our_value": f"{our_sent:.3f}",
                "top_10_avg": f"{top_sent:.3f}",
                "gap": f"{(top_sent - our_sent):.3f}",
            },
            "implication": "Lower sentiment relative to top competitors may indicate areas for customer experience improvement.",
            "action": "Investigate which service dimensions (response time, service score, value score) most strongly correlate with sentiment and prioritize improvements.",
            "priority": "high",
            "category": "Customer Experience",
        })

    # 3. Review Volume Opportunity
    our_reviews = int(our["monthly_reviews"])
    market_p75 = float(competitors["monthly_reviews"].quantile(0.75))
    if our_reviews < market_p75:
        opportunities.append({
            "id": "review_volume_gap",
            "observation": "Our monthly review volume is below the 75th percentile.",
            "evidence": {
                "our_value": str(our_reviews),
                "market_p75": str(int(market_p75)),
                "gap": str(int(market_p75 - our_reviews)),
            },
            "implication": "Lower review volume may reduce social proof effectiveness. Review volume is associated with competitive score.",
            "action": "Implement a review solicitation program (e.g., post-visit email or SMS prompts). Track review velocity weekly.",
            "priority": "medium",
            "category": "Growth",
        })

    # 4. Engagement Rate Opportunity
    our_eng = float(our["engagement_rate"])
    market_median_eng = float(competitors["engagement_rate"].median())
    if our_eng < market_median_eng:
        opportunities.append({
            "id": "engagement_opportunity",
            "observation": "Our engagement rate is below the market median.",
            "evidence": {
                "our_value": f"{our_eng:.2%}",
                "market_median": f"{market_median_eng:.2%}",
            },
            "implication": "Lower engagement may indicate content or platform strategy could be improved.",
            "action": "Audit social media content strategy. Consider A/B testing post types (visual, video, promotional, educational) to identify what drives engagement.",
            "priority": "medium",
            "category": "Digital Presence",
        })

    # 5. Service Score Leadership
    our_service = float(our["service_score"])
    service_p90 = float(competitors["service_score"].quantile(0.90))
    if our_service >= service_p90:
        opportunities.append({
            "id": "service_leadership",
            "observation": "Our service score is in the top 10% of the market.",
            "evidence": {
                "our_value": f"{our_service:.2f}",
                "market_p90": f"{service_p90:.2f}",
            },
            "implication": "Strong service quality is a differentiator that can be leveraged in positioning.",
            "action": "Feature service quality prominently in marketing. Consider premium service tiers.",
            "priority": "low",
            "category": "Competitive Advantage",
        })

    # 6. Price-Value Misalignment
    our_value = float(our["value_score"])
    our_price = int(our["price_level"])
    same_price = competitors[competitors["price_level"] == our_price]
    if len(same_price) > 3:
        same_price_value = float(same_price["value_score"].mean())
        if our_value < same_price_value - 0.2:
            opportunities.append({
                "id": "price_value_gap",
                "observation": "Our value score is below average for businesses at the same price level.",
                "evidence": {
                    "our_value_score": f"{our_value:.2f}",
                    "same_price_avg": f"{same_price_value:.2f}",
                    "price_level": str(our_price),
                },
                "implication": "Customers at this price point may perceive better value elsewhere.",
                "action": "Review pricing strategy or enhance perceived value through portion sizes, quality improvements, or loyalty programs.",
                "priority": "high",
                "category": "Pricing",
            })

    # 7. Geographic Opportunity
    our_cluster = our["cluster"]
    cluster_biz = current[current["cluster"] == our_cluster]
    other_clusters = current[current["cluster"] != our_cluster]
    underserved_clusters = []
    for cluster_name in other_clusters["cluster"].unique():
        cluster_data = other_clusters[other_clusters["cluster"] == cluster_name]
        avg_comp_score = float(cluster_data["competitive_score"].mean())
        n_businesses = len(cluster_data)
        if avg_comp_score < float(current["competitive_score"].median()) and n_businesses < len(cluster_biz):
            underserved_clusters.append({
                "cluster": cluster_name,
                "businesses": n_businesses,
                "avg_score": round(avg_comp_score, 1),
            })

    if underserved_clusters:
        best = min(underserved_clusters, key=lambda x: x["avg_score"])
        opportunities.append({
            "id": "geographic_expansion",
            "observation": f"The {best['cluster']} area has fewer businesses and lower average competitive scores.",
            "evidence": {
                "target_area": best["cluster"],
                "businesses_in_area": str(best["businesses"]),
                "avg_competitive_score": str(best["avg_score"]),
                "our_area_businesses": str(len(cluster_biz)),
            },
            "implication": "This area may represent an expansion opportunity with less competitive pressure.",
            "action": f"Conduct a location-specific feasibility study for the {best['cluster']} area. Assess foot traffic, demographics, and lease costs.",
            "priority": "low",
            "category": "Expansion",
        })

    return opportunities
