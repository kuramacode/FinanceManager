"""Prompts for prediction tasks."""


EXPENSE_FORECAST_PROMPT = """
{base}

Task:
Forecast near-term expenses or overspending risk from the available data.

What to produce:
1. Expected total expenses for the next comparable period, if the data supports it.
2. The overall trend: up, down, stable, or unknown.
3. Categories or budgets that are most likely to remain important.
4. A short note explaining uncertainty.

Rules:
- Do not invent data.
- Make only a simple conservative forecast.
- If the data is insufficient, say so directly and use trend "unknown".
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "expected_total": 0,
  "trend": "up|down|stable|unknown",
  "top_categories": [
    "string"
  ],
  "note": "string"
}}
"""
