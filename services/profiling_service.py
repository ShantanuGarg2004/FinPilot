import logging

logger = logging.getLogger(__name__)

VALID_RISK = {"low", "medium", "high"}


def validate_user_input(data: dict):
    """Check presence and value constraints on all profile fields."""
    required_fields = ["age", "income", "expenses", "savings",
                       "risk_appetite", "financial_goals"]

    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return False, f"Missing required field: {field}"

    # ── Numeric range checks ───────────────────────────────────────────────
    try:
        age      = int(data["age"])
        income   = float(data["income"])
        expenses = float(data["expenses"])
        savings  = float(data["savings"])
    except (ValueError, TypeError):
        return False, "age, income, expenses, and savings must be valid numbers"

    if not (1 <= age <= 120):
        return False, "age must be between 1 and 120"
    if income < 0:
        return False, "income cannot be negative"
    if expenses < 0:
        return False, "expenses cannot be negative"
    if savings < 0:
        return False, "savings cannot be negative"
    if income > 0 and expenses > income:
        # Valid but worth a soft warning — we don't block it
        logger.warning("Profile: expenses (%.0f) exceed income (%.0f)", expenses, income)

    # ── Risk appetite ──────────────────────────────────────────────────────
    risk = str(data["risk_appetite"]).lower().strip()
    if risk not in VALID_RISK:
        return False, f"risk_appetite must be one of: {', '.join(sorted(VALID_RISK))}"

    # ── Goals ──────────────────────────────────────────────────────────────
    goals = str(data["financial_goals"]).strip()
    if len(goals) < 3:
        return False, "financial_goals must be at least 3 characters"
    if len(goals) > 500:
        return False, "financial_goals must be under 500 characters"

    return True, "Valid input"


def normalize_data(data: dict):
    """Coerce types and clean strings."""
    try:
        normalized = {
            "age":             int(data["age"]),
            "income":          round(float(data["income"]), 2),
            "expenses":        round(float(data["expenses"]), 2),
            "savings":         round(float(data["savings"]), 2),
            "risk_appetite":   str(data["risk_appetite"]).lower().strip(),
            "financial_goals": str(data["financial_goals"]).strip(),
        }
        return True, normalized
    except Exception as e:
        logger.exception("normalize_data failed")
        return False, str(e)


def create_user_profile(data: dict):
    is_valid, message = validate_user_input(data)
    if not is_valid:
        return False, message

    is_normalized, normalized_data = normalize_data(data)
    if not is_normalized:
        return False, normalized_data

    return True, normalized_data