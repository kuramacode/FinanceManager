"""Prompts for question-answer tasks."""


QA_PROMPT = """
{base}

Question:
{question}

Rules:
- Answer only from the provided data.
- Do not invent facts, numbers, categories, accounts, budgets, or rates.
- If the data is insufficient, say so directly.
- Stay within the selected AI scenario.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "answer": "string"
}}
"""
