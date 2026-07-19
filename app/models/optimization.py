from datetime import datetime, timezone

from app.extensions import db


class OptimizationGoal:
    MAX_ROI = "max_roi"
    MAX_CONVERSIONS = "max_conversions"
    MIN_COST = "min_cost"
    BALANCED = "balanced"

    ALL = (MAX_ROI, MAX_CONVERSIONS, MIN_COST, BALANCED)

    LABELS = {
        MAX_ROI: "Maximize ROI",
        MAX_CONVERSIONS: "Maximize Conversions",
        MIN_COST: "Minimize Cost",
        BALANCED: "Balanced Strategy",
    }

    DESCRIPTIONS = {
        MAX_ROI: "Shift budget toward channels with the strongest return on ad spend.",
        MAX_CONVERSIONS: "Shift budget toward channels producing the most conversions per dollar.",
        MIN_COST: "Hold current performance while spending as little as possible.",
        BALANCED: "Blend ROI, conversions, and cost efficiency for a well-rounded plan.",
    }


class OptimizationRun(db.Model):
    __tablename__ = "optimization_runs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    goal = db.Column(db.String(30), nullable=False, default=OptimizationGoal.MAX_ROI)
    total_budget = db.Column(db.Float, nullable=False)
    period_filter = db.Column(db.String(20), nullable=True)  # which month(s) this run covered

    status = db.Column(db.String(20), nullable=False, default="success")
    message = db.Column(db.String(255), nullable=True)

    old_profit = db.Column(db.Float, nullable=True)
    new_profit = db.Column(db.Float, nullable=True)
    improvement_pct = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    allocations = db.relationship(
        "OptimizationAllocation",
        backref="run",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    @property
    def goal_label(self) -> str:
        return OptimizationGoal.LABELS.get(self.goal, self.goal)

    def __repr__(self):
        return f"<OptimizationRun {self.id} goal={self.goal!r}>"


class OptimizationAllocation(db.Model):
    """A single channel/campaign's recommended budget within an optimization run."""

    __tablename__ = "optimization_allocations"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(
        db.Integer, db.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)

    original_cost = db.Column(db.Float, nullable=False, default=0.0)
    optimized_cost = db.Column(db.Float, nullable=False, default=0.0)
    projected_revenue = db.Column(db.Float, nullable=False, default=0.0)
    projected_roi = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"<OptimizationAllocation run={self.run_id} campaign={self.campaign_id}>"
