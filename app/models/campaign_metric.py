from datetime import datetime, timezone

from app.extensions import db


class CampaignMetric(db.Model):
    """
    One row = one campaign's performance during one reporting period
    (e.g. "2026-01"). Normalizing metrics this way lets a single campaign
    accumulate history across many months instead of being overwritten.
    """

    __tablename__ = "campaign_metrics"
    __table_args__ = (
        db.UniqueConstraint("campaign_id", "period", name="uq_campaign_period"),
        db.Index("ix_metrics_period", "period"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )

    period = db.Column(db.String(20), nullable=False)  # e.g. "2026-01" or "January"

    cost = db.Column(db.Float, nullable=False, default=0.0)
    impressions = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    conversions = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Float, nullable=False, default=0.0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def roi(self) -> float:
        return ((self.revenue - self.cost) / self.cost * 100) if self.cost else 0.0

    @property
    def ctr(self) -> float:
        return (self.clicks / self.impressions * 100) if self.impressions else 0.0

    @property
    def cpc(self) -> float:
        return (self.cost / self.clicks) if self.clicks else 0.0

    @property
    def cpa(self) -> float:
        return (self.cost / self.conversions) if self.conversions else 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks else 0.0

    def __repr__(self):
        return f"<CampaignMetric campaign_id={self.campaign_id} period={self.period!r}>"
