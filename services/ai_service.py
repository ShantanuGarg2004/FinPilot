import logging

from groq import Groq
from config import Config

logger = logging.getLogger(__name__)

# Initialize Groq client (OpenAI-compatible chat completions interface).
client = Groq(
    api_key=Config.GROQ_API_KEY
)


# -------------------------------
# SYSTEM PERSONA
# -------------------------------
SYSTEM_PROMPT = """
You are FinPilot AI, a professional personal financial advisor.

You specialize in:
- Budgeting
- Savings strategy
- Investing
- Risk management
- Goal planning
- Indian personal finance

Behavior Rules:
- Always give personalized advice.
- Be practical, not generic.
- Use real examples when useful (SIP, index funds, FD, emergency fund etc.)
- Avoid motivational fluff.
- Keep advice concise but meaningful.
- Sound like a real financial advisor.
- If user says simple things like 'hello', greet warmly and offer help.
"""


# -------------------------------
# GROQ CALL WRAPPER
# -------------------------------
def ask_gpt(prompt, model=None, max_tokens=None):
    """
    Send a single-turn prompt to the Groq chat completions API.

    Parameters
    ----------
    prompt : str
        The user prompt to send alongside the system persona.
    model : str, optional
        Groq model id to use. Falls back to ``Config.GROQ_CHAT_MODEL``.
    max_tokens : int, optional
        Completion budget. Falls back to ``Config.GROQ_CHAT_MAX_TOKENS``.

    Returns
    -------
    tuple[bool, str]
        ``(True, content)`` on success, ``(False, error_message)`` on failure.
    """
    selected_model = model or Config.GROQ_CHAT_MODEL
    token_budget = max_tokens if max_tokens is not None else Config.GROQ_CHAT_MAX_TOKENS

    try:
        response = client.chat.completions.create(
            model=selected_model,
            temperature=0.7,
            max_tokens=token_budget,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        choice = response.choices[0]
        finish_reason = getattr(choice, "finish_reason", None)
        content = (choice.message.content or "").strip()

        if finish_reason == "length":
            logger.warning(
                "ask_gpt: response truncated (finish_reason=length, model=%s, max_tokens=%s, chars=%d)",
                selected_model,
                token_budget,
                len(content),
            )

        return True, content

    except Exception as exc:
        logger.exception("ask_gpt: Groq completion failed (model=%s)", selected_model)
        return False, str(exc)


# -------------------------------
# FINANCIAL REPORT GENERATION
# -------------------------------
def generate_financial_report(profile, health_data):

    prompt = f"""
Analyze this user profile and generate a professional advisory report.

USER PROFILE
Age: {profile['age']}
Monthly Income: ₹{profile['income']}
Monthly Expenses: ₹{profile['expenses']}
Current Savings: ₹{profile['savings']}
Risk Appetite: {profile['risk_appetite']}
Financial Goal: {profile['financial_goals']}

FINANCIAL HEALTH SCORE:
{health_data['score']}/100

Insights:
{', '.join(health_data['insights'])}

Warnings:
{', '.join(health_data['warnings'])}


Return response in this exact structure:

## Financial Summary
Brief assessment of current financial condition.

## Budget Optimization
Specific spending/saving improvements.

## Investment Recommendations
Suggest practical allocation strategy.
Mention percentages if possible.

## Risk Warnings
Mention financial risks or gaps.

## Goal Strategy
How user should achieve stated goal.

## 30-Day Action Plan
Give 5 actionable next steps.

Rules:
- Keep it practical.
- Use Indian finance examples.
- Personalized advice only.
- No generic textbook content.
"""

    return ask_gpt(
        prompt,
        model=Config.GROQ_REPORT_MODEL,
        max_tokens=Config.GROQ_REPORT_MAX_TOKENS,
    )


# -------------------------------
# CHAT ADVISOR
# -------------------------------
def chat_with_advisor(profile, user_query, history=None):

    conversation_context = ""

    if history and isinstance(history, list):
        for msg in history[-5:]:
            role = msg.get("role", "user")
            # DB stores "message"; tolerate "content" for forward compatibility.
            content = msg.get("message") or msg.get("content") or ""
            conversation_context += f"{role}: {content}\n"

    prompt = f"""
You are the user's personal financial advisor.

User Financial Profile:
Age: {profile['age']}
Income: ₹{profile['income']}
Expenses: ₹{profile['expenses']}
Savings: ₹{profile['savings']}
Risk Appetite: {profile['risk_appetite']}
Goals: {profile['financial_goals']}

Recent Conversation:
{conversation_context}

Current User Message:
{user_query}

Instructions:
- Use user profile for personalized advice
- Use conversation context if relevant
- If user says hello, greet warmly
- Be concise and practical
"""

    return ask_gpt(
        prompt,
        model=Config.GROQ_CHAT_MODEL,
        max_tokens=Config.GROQ_CHAT_MAX_TOKENS,
    )
