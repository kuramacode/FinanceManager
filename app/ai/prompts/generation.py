"""Prompts for generation tasks."""


BUDGET_GENERATION_PROMPT = """
{base}

Task:
Generate practical budget recommendations for the selected scenario.

What to do:
1. Suggest category limits when the data supports them.
2. Explain each recommendation briefly.
3. Do not add categories that are not present in the input unless the data clearly justifies a new category suggestion.

Rules:
- Do not invent numbers.
- Rely only on income, expenses, budgets, accounts, and categories from the input data.
- If the data is insufficient, return an empty budget list and explain why.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "budget": [
    {{
      "category": "string",
      "limit": 0,
      "reason": "string"
    }}
  ],
  "note": "string"
}}
"""


UI_INSIGHTS_PROMPT = """
{base}

Task:
Generate concise user-facing insights for the selected page or scenario.

Requirements:
- Produce 3-5 useful insights.
- Keep each insight short and specific.
- Avoid generic filler.
- Use only the provided data.

Rules:
- Do not invent data.
- If there is not enough data, return one clear insight about the data gap.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "insights": [
    "string"
  ]
}}
"""
