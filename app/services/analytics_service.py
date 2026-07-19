"""Aggregation logic for dashboard KPIs and chart data.

Kept separate from routes so the same numbers can be reused by the
dashboard page, the JSON API (for Chart.js), and PDF/Excel reports.
"""
from collections import defaultdict

from app.models import Campaign, CampaignMetric
from app.extensions import db


def get_campaign_rows(user_id: int, period: str | None = None):
    """Return (campaign, aggregated_metrics_dict) tuples for a user, optionally
    filtered to a single reporting period."""
    query = Campaign.query.filter_by(user_id=user_id)
    campaigns = query.all()

    rows = []
    for campaign in campaigns:
        metrics_query = campaign.metrics
        if period and period != "All":
            metrics_query = metrics_query.filter(CampaignMetric.period == period)
        metric_rows = metrics_query.all() if hasattr(metrics_query, "all") else list(metrics_query)

        cost = sum(m.cost for m in metric_rows)
        revenue = sum(m.revenue for m in metric_rows)
        impressions = sum(m.impressions for m in metric_rows)
        clicks = sum(m.clicks for m in metric_rows)
        conversions = sum(m.conversions for m in metric_rows)

        if not metric_rows:
            continue

        rows.append(
            {
                "campaign": campaign,
                "cost": cost,
                "revenue": revenue,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "roi": ((revenue - cost) / cost * 100) if cost else 0.0,
                "ctr": (clicks / impressions * 100) if impressions else 0.0,
                "cpc": (cost / clicks) if clicks else 0.0,
                "cpa": (cost / conversions) if conversions else 0.0,
                "conversion_rate": (conversions / clicks * 100) if clicks else 0.0,
            }
        )
    return rows


def get_available_periods(user_id: int) -> list[str]:
    periods = (
        db.session.query(CampaignMetric.period)
        .join(Campaign, Campaign.id == CampaignMetric.campaign_id)
        .filter(Campaign.user_id == user_id)
        .distinct()
        .all()
    )
    return sorted({p[0] for p in periods})


def compute_kpis(rows: list[dict]) -> dict:
    if not rows:
        return {
            "total_campaigns": 0,
            "total_budget": 0.0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "roi": 0.0,
            "conversion_rate": 0.0,
            "ctr": 0.0,
            "cpc": 0.0,
            "cpa": 0.0,
            "total_conversions": 0,
            "total_clicks": 0,
            "total_impressions": 0,
            "best_channel": None,
        }

    total_cost = sum(r["cost"] for r in rows)
    total_revenue = sum(r["revenue"] for r in rows)
    total_impressions = sum(r["impressions"] for r in rows)
    total_clicks = sum(r["clicks"] for r in rows)
    total_conversions = sum(r["conversions"] for r in rows)

    channel_profit = defaultdict(float)
    for r in rows:
        channel_profit[r["campaign"].channel.name] += r["revenue"] - r["cost"]
    best_channel = max(channel_profit, key=channel_profit.get) if channel_profit else None

    return {
        "total_campaigns": len(rows),
        "total_budget": total_cost,
        "total_revenue": total_revenue,
        "total_profit": total_revenue - total_cost,
        "roi": ((total_revenue - total_cost) / total_cost * 100) if total_cost else 0.0,
        "conversion_rate": (total_conversions / total_clicks * 100) if total_clicks else 0.0,
        "ctr": (total_clicks / total_impressions * 100) if total_impressions else 0.0,
        "cpc": (total_cost / total_clicks) if total_clicks else 0.0,
        "cpa": (total_cost / total_conversions) if total_conversions else 0.0,
        "total_conversions": total_conversions,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "best_channel": best_channel,
    }


def budget_allocation_by_channel(rows: list[dict]) -> list[dict]:
    agg = defaultdict(lambda: {"cost": 0.0, "revenue": 0.0, "color": "#64748B"})
    for r in rows:
        name = r["campaign"].channel.name
        agg[name]["cost"] += r["cost"]
        agg[name]["revenue"] += r["revenue"]
        agg[name]["color"] = r["campaign"].channel.color_hex
    total = sum(v["cost"] for v in agg.values()) or 1
    return [
        {
            "channel": name,
            "cost": v["cost"],
            "revenue": v["revenue"],
            "share_pct": v["cost"] / total * 100,
            "color": v["color"],
        }
        for name, v in sorted(agg.items(), key=lambda kv: kv[1]["cost"], reverse=True)
    ]


def performance_trend(user_id: int) -> list[dict]:
    """Cost vs revenue across all periods, ordered chronologically for a line chart."""
    metric_rows = (
        db.session.query(
            CampaignMetric.period,
            db.func.sum(CampaignMetric.cost),
            db.func.sum(CampaignMetric.revenue),
        )
        .join(Campaign, Campaign.id == CampaignMetric.campaign_id)
        .filter(Campaign.user_id == user_id)
        .group_by(CampaignMetric.period)
        .all()
    )
    return [
        {"period": period, "cost": float(cost or 0), "revenue": float(revenue or 0)}
        for period, cost, revenue in sorted(metric_rows, key=lambda r: r[0])
    ]


def top_campaigns(rows: list[dict], limit: int = 5) -> list[dict]:
    return sorted(rows, key=lambda r: r["roi"], reverse=True)[:limit]
