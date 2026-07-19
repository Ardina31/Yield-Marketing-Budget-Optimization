"""
Budget optimization engine.

Given a set of campaigns (aggregated cost/revenue/conversions) and a total
budget, this service recommends a new spend split per campaign using a
non-linear SciPy solver (SLSQP). Diminishing returns are modeled with
`log1p(budget)`, so the first dollars spent on a channel matter more than
the last -- mirroring real audience saturation.

Four selectable strategies (`OptimizationGoal`) share the same solver
machinery but differ in what they optimize for:

    MAX_ROI          maximize projected profit
    MAX_CONVERSIONS  maximize projected conversions
    MIN_COST         minimize total spend while holding current output
    BALANCED         weighted blend of the above
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

from app.models.optimization import OptimizationGoal


@dataclass
class CampaignInput:
    campaign_id: int
    name: str
    channel: str
    cost: float
    revenue: float
    conversions: float
    clicks: float = 0.0

    @property
    def roi_efficiency(self) -> float:
        """Profit generated per dollar spent (ROI expressed as a decimal)."""
        return (self.revenue - self.cost) / self.cost if self.cost > 0 else 0.0

    @property
    def conversion_efficiency(self) -> float:
        """Conversions generated per dollar spent."""
        return self.conversions / self.cost if self.cost > 0 else 0.0


@dataclass
class AllocationResult:
    campaign_id: int
    name: str
    channel: str
    original_cost: float
    optimized_cost: float
    change_pct: float
    projected_revenue: float
    projected_roi: float


@dataclass
class OptimizationResult:
    status: str  # "success" | "failed" | "insufficient_data"
    goal: str = ""
    message: str = ""
    allocations: list = field(default_factory=list)
    old_profit: float = 0.0
    new_profit: float = 0.0
    improvement_pct: float = 0.0
    total_budget: float = 0.0

    def to_dict(self):
        return {
            "status": self.status,
            "goal": self.goal,
            "message": self.message,
            "old_profit": round(self.old_profit, 2),
            "new_profit": round(self.new_profit, 2),
            "improvement_pct": round(self.improvement_pct, 2),
            "total_budget": round(self.total_budget, 2),
            "allocations": [
                {
                    "campaign_id": a.campaign_id,
                    "name": a.name,
                    "channel": a.channel,
                    "original_cost": round(a.original_cost, 2),
                    "optimized_cost": round(a.optimized_cost, 2),
                    "change_pct": round(a.change_pct, 1),
                    "projected_revenue": round(a.projected_revenue, 2),
                    "projected_roi": round(a.projected_roi, 1),
                }
                for a in self.allocations
            ],
        }


MIN_CAMPAIGNS_FOR_OPTIMIZATION = 2


def optimize_budget(
    campaigns: list[CampaignInput],
    total_budget: float,
    goal: str = OptimizationGoal.MAX_ROI,
    min_spend_factor: float = 0.20,
    max_spend_factor: float = 3.00,
) -> OptimizationResult:
    if len(campaigns) < MIN_CAMPAIGNS_FOR_OPTIMIZATION:
        return OptimizationResult(
            status="insufficient_data",
            goal=goal,
            message="At least two campaigns with spend data are needed to run an optimization.",
        )

    costs = np.array([max(c.cost, 1.0) for c in campaigns], dtype=float)
    roi_eff = np.array([c.roi_efficiency for c in campaigns], dtype=float)
    conv_eff = np.array([c.conversion_efficiency for c in campaigns], dtype=float)

    bounds = [(cost * min_spend_factor, cost * max_spend_factor) for cost in costs]
    lower = np.array([b[0] for b in bounds])
    upper = np.array([b[1] for b in bounds])
    initial_guess = np.clip(np.full(len(campaigns), total_budget / len(campaigns)), lower, upper)

    old_profit = float(np.sum(costs * roi_eff))  # == sum(revenue - cost)

    def projected_profit(x):
        return np.sum(roi_eff * np.log1p(x))

    def projected_conversions(x):
        return np.sum(conv_eff * np.log1p(x))

    result = None

    if goal == OptimizationGoal.MAX_ROI:
        result = _solve_fixed_budget(lambda x: -projected_profit(x), bounds, initial_guess, total_budget)

    elif goal == OptimizationGoal.MAX_CONVERSIONS:
        result = _solve_fixed_budget(lambda x: -projected_conversions(x), bounds, initial_guess, total_budget)

    elif goal == OptimizationGoal.BALANCED:
        # Normalize each term by its own scale so no single metric dominates.
        roi_scale = max(abs(old_profit), 1.0)
        conv_scale = max(float(np.sum(conv_eff * np.log1p(costs))), 1.0)

        def balanced_objective(x):
            roi_term = projected_profit(x) / roi_scale
            conv_term = projected_conversions(x) / conv_scale
            cost_term = -np.sum(x) / max(total_budget, 1.0)  # mild preference for lower spend
            return -(0.5 * roi_term + 0.35 * conv_term + 0.15 * cost_term)

        result = _solve_fixed_budget(balanced_objective, bounds, initial_guess, total_budget)

    elif goal == OptimizationGoal.MIN_COST:
        baseline_profit = projected_profit(costs)
        result = _solve_min_cost(
            objective=lambda x: np.sum(x),
            bounds=bounds,
            initial_guess=costs.copy(),
            performance_constraint=lambda x: projected_profit(x) - baseline_profit,
            spend_cap=total_budget * max_spend_factor,
        )
    else:
        return OptimizationResult(status="failed", goal=goal, message=f"Unknown optimization goal: {goal}")

    if result is None or not result.success:
        return OptimizationResult(
            status="failed",
            goal=goal,
            message="The solver could not find a feasible allocation. Try a different budget or goal.",
        )

    optimized = np.round(result.x, 2)

    # Conservative efficiency haircut: projected gains assume 85% execution
    # fidelity (creative/testing lag, market response uncertainty).
    EXECUTION_FACTOR = 0.85
    projected_revenue = optimized + (optimized * roi_eff * EXECUTION_FACTOR)
    projected_roi = np.where(optimized > 0, (projected_revenue - optimized) / optimized * 100, 0.0)

    new_profit = float(np.sum(optimized * roi_eff * EXECUTION_FACTOR))
    improvement_pct = ((new_profit - old_profit) / abs(old_profit) * 100) if old_profit != 0 else 0.0

    allocations = []
    for i, c in enumerate(campaigns):
        change_pct = ((optimized[i] - costs[i]) / costs[i] * 100) if costs[i] else 0.0
        allocations.append(
            AllocationResult(
                campaign_id=c.campaign_id,
                name=c.name,
                channel=c.channel,
                original_cost=float(costs[i]),
                optimized_cost=float(optimized[i]),
                change_pct=float(change_pct),
                projected_revenue=float(projected_revenue[i]),
                projected_roi=float(projected_roi[i]),
            )
        )
    allocations.sort(key=lambda a: a.optimized_cost, reverse=True)

    return OptimizationResult(
        status="success",
        goal=goal,
        message="Optimization completed successfully.",
        allocations=allocations,
        old_profit=old_profit,
        new_profit=new_profit,
        improvement_pct=improvement_pct,
        total_budget=total_budget,
    )


def _solve_fixed_budget(objective, bounds, initial_guess, total_budget):
    constraints = ({"type": "eq", "fun": lambda x: np.sum(x) - total_budget},)
    return minimize(
        objective, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints,
        options={"maxiter": 300, "ftol": 1e-9},
    )


def _solve_min_cost(objective, bounds, initial_guess, performance_constraint, spend_cap):
    constraints = (
        {"type": "ineq", "fun": performance_constraint},
        {"type": "ineq", "fun": lambda x: spend_cap - np.sum(x)},
    )
    return minimize(
        objective, initial_guess, method="SLSQP", bounds=bounds, constraints=constraints,
        options={"maxiter": 300, "ftol": 1e-9},
    )
