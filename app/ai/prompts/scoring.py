"""Prompts for scoring tasks."""


FINANCIAL_SCORE_PROMPT = """
{base}

Task:
Estimate the user's financial health score for the selected scenario.

Criteria:
- income versus expenses;
- expense stability;
- overspending or budget pressure;
- balance and account distribution;
- availability and quality of the provided data.

Rules:
- Do not invent data.
- If there is not enough data, explain that clearly.
- score must be a number from 0 to 100.
- status must be one of: good, medium, bad, unknown.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "score": 0,
  "status": "good|medium|bad|unknown",
  "explanation": "string"
}}
"""
