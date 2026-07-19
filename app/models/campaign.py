from datetime import datetime, timezone

from app.extensions import db


class CampaignStatus:
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ALL = (ACTIVE, PAUSED, COMPLETED)


class CampaignObjective:
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    RETENTION = "retention"
    ALL = (AWARENESS, TRAFFIC, CONVERSIONS, RETENTION)


class Campaign(db.Model):
    __tablename__ = "campaigns"
    __table_args__ = (
        db.Index("ix_campaigns_user_channel", "user_id", "channel_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    objective = db.Column(db.String(20), nullable=False, default=CampaignObjective.CONVERSIONS)
    status = db.Column(db.String(20), nullable=False, default=CampaignStatus.ACTIVE)

    budget_allocated = db.Column(db.Float, nullable=False, default=0.0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False)

    metrics = db.relationship(
        "CampaignMetric",
        backref="campaign",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="CampaignMetric.period",
    )
    optimization_allocations = db.relationship(
        "OptimizationAllocation", backref="campaign", lazy="dynamic"
    )

    # ---- Aggregate helpers (computed from CampaignMetric rows) ----

    def totals(self):
        """Aggregate cost/revenue/etc. across every metric period."""
        rows = self.metrics.all()
        cost = sum(r.cost for r in rows)
        revenue = sum(r.revenue for r in rows)
        impressions = sum(r.impressions for r in rows)
        clicks = sum(r.clicks for r in rows)
        conversions = sum(r.conversions for r in rows)
        return {
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

    def __repr__(self):
        return f"<Campaign {self.name!r}>"
