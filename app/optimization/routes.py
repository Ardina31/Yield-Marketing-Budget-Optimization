from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models.optimization import OptimizationAllocation, OptimizationGoal, OptimizationRun
from app.models.user import Role
from app.services.activity_service import log_activity
from app.services.analytics_service import get_available_periods, get_campaign_rows
from app.services.notification_service import notify
from app.services.optimizer_service import CampaignInput, optimize_budget
from app.utils.decorators import roles_required

optimization_bp = Blueprint("optimization", __name__, url_prefix="/optimization")


@optimization_bp.route("/", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.AGENT)
def index():
    periods = get_available_periods(current_user.id)
    goals = [(g, OptimizationGoal.LABELS[g], OptimizationGoal.DESCRIPTIONS[g]) for g in OptimizationGoal.ALL]

    selected_period = request.values.get("period", "All")
    selected_goal = request.values.get("goal", OptimizationGoal.MAX_ROI)
    result = None

    rows = get_campaign_rows(current_user.id, period=selected_period)
    default_budget = round(sum(r["cost"] for r in rows), 2) or 20000.0
    total_budget = request.values.get("total_budget", type=float) or default_budget

    if request.method == "POST":
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

        optimization = optimize_budget(campaign_inputs, total_budget=total_budget, goal=selected_goal)
        result = optimization.to_dict()
        result["goal_label"] = OptimizationGoal.LABELS.get(selected_goal, selected_goal)

        if optimization.status == "success":
            run = OptimizationRun(
                user_id=current_user.id,
                goal=selected_goal,
                total_budget=total_budget,
                period_filter=selected_period,
                status="success",
                old_profit=optimization.old_profit,
                new_profit=optimization.new_profit,
                improvement_pct=optimization.improvement_pct,
            )
            db.session.add(run)
            db.session.flush()

            for alloc in optimization.allocations:
                db.session.add(OptimizationAllocation(
                    run_id=run.id,
                    campaign_id=alloc.campaign_id,
                    original_cost=alloc.original_cost,
                    optimized_cost=alloc.optimized_cost,
                    projected_revenue=alloc.projected_revenue,
                    projected_roi=alloc.projected_roi,
                ))
            db.session.commit()

            log_activity(
                current_user.id, "optimization_run",
                f"Ran '{OptimizationGoal.LABELS[selected_goal]}' optimization on ${total_budget:,.0f}.",
            )
            notify(
                current_user.id, "Optimization complete",
                f"Projected profit change: {optimization.improvement_pct:+.1f}%.",
                "success" if optimization.improvement_pct >= 0 else "warning",
            )
        else:
            flash(optimization.message, "warning")

    return render_template(
        "optimization/index.html",
        goals=goals,
        selected_goal=selected_goal,
        periods=periods,
        selected_period=selected_period,
        total_budget=total_budget,
        result=result,
        has_enough_data=len(rows) >= 2,
    )


@optimization_bp.route("/history")
@login_required
def history():
    runs = (
        OptimizationRun.query.filter_by(user_id=current_user.id)
        .order_by(OptimizationRun.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template("optimization/history.html", runs=runs)
