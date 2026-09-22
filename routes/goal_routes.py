import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from extensions import limiter
from schemas import goal_plan_schema
from services.goal_service import calculate_goal_plan
from routes.user_routes import get_user_by_id
import config as app_config

logger  = logging.getLogger(__name__)
goal_bp = Blueprint("goal", __name__)


@goal_bp.route("/goal-plan", methods=["POST"])
@limiter.limit(lambda: app_config.Config.RATELIMIT_GOAL)
def goal_plan():
    """
    Goal Feasibility Simulator API
    ---
    tags:
      - Goal
    summary: >
      Simulate goal feasibility across Conservative / Balanced / Aggressive
      scenarios using SIP compounding (PMT annuity-due formula).
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - target_amount
            - time_years
          properties:
            user_id:
              type: integer
              example: 1
            goal_name:
              type: string
              example: "Car Purchase"
              description: "Optional label for this simulation scenario"
            target_amount:
              type: number
              example: 500000
              description: "Goal amount in ₹"
            time_years:
              type: number
              example: 3
              description: "Target horizon in years (minimum 0.5)"
    responses:
      200:
        description: >
          Full simulation result including feasibility score, gap analysis,
          three scenario projections, and investment strategy.
        schema:
          type: object
          properties:
            goal_name:
              type: string
            required_monthly_saving:
              type: number
            current_monthly_saving:
              type: number
            monthly_gap:
              type: number
            feasible:
              type: boolean
            feasibility_score:
              type: integer
              description: "0–100 rule-based feasibility score"
            feasibility_label:
              type: string
              description: "High / Moderate / Low Feasibility"
            recommended_timeline:
              type: string
              description: "How long it takes at current savings rate"
            investment_strategy:
              type: string
            scenario_message:
              type: string
            scenarios:
              type: array
              description: "Conservative / Balanced / Aggressive scenario objects"
            gap_analysis:
              type: object
      400:
        description: Validation error or user not found
      500:
        description: Simulation error
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    try:
        data = goal_plan_schema.load(raw)
    except ValidationError as exc:
        logger.warning("goal_plan: validation failed — %s", exc.messages)
        return jsonify({"error": "Validation failed", "details": exc.messages}), 400

    user_id = data["user_id"]
    profile = get_user_by_id(user_id)
    if not profile:
        return jsonify({"error": f"User profile #{user_id} not found"}), 404

    status, result = calculate_goal_plan(profile, data)
    if not status:
        logger.error(
            "goal_plan: simulation failed for user #%d — %s", user_id, result
        )
        return jsonify({"error": result}), 500

    logger.info(
        "goal_plan: simulation complete for user #%d — goal='%s' target=₹%.0f "
        "in %.1f yr(s) feasibility_score=%d feasible=%s",
        user_id,
        result.get("goal_name"),
        data["target_amount"],
        data["time_years"],
        result.get("feasibility_score", 0),
        result.get("feasible"),
    )
    return jsonify(result)