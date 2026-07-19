from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.services.activity_service import get_recent as get_recent_activity
from app.services.analytics_service import (
    budget_allocation_by_channel,
    compute_kpis,
    get_available_periods,
    get_campaign_rows,
    performance_trend,
    top_campaigns,
)
from app.services.optimizer_service import CampaignInput, optimize_budget
from app.models.optimization import OptimizationGoal

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    selected_period = request.args.get("period", "All")

    rows = get_campaign_rows(current_user.id, period=selected_period)
    periods = get_available_periods(current_user.id)
    kpis = compute_kpis(rows)
    allocation = budget_allocation_by_channel(rows)
    trend = performance_trend(current_user.id)
    top = top_campaigns(rows, limit=5)
    recent_activity = get_recent_activity(current_user.id, limit=6)

    quick_optimization = None
    if current_user.can_manage_data and len(rows) >= 2:
        campaign_inputs = [
            CampaignInput(
                campaign_id=r["campaign"].id,
                name=r["campaign"].name,
                channel=r["campaign"].channel.name,
                cost=r["cost"],
                revenue=r["revenue"],
                conversions=r["conversions"],
                clicks=r["clicks"],
            )
            for r in rows
        ]
        total_budget = sum(c.cost for c in campaign_inputs) or 20000.0
        quick_optimization = optimize_budget(
            campaign_inputs, total_budget=total_budget, goal=OptimizationGoal.MAX_ROI
        ).to_dict()

    return render_template(
        "dashboard/index.html",
        kpis=kpis,
        allocation=allocation,
        trend=trend,
        top_campaigns=top,
        recent_activity=recent_activity,
        periods=periods,
        selected_period=selected_period,
        quick_optimization=quick_optimization,
        has_data=len(rows) > 0,
    )
