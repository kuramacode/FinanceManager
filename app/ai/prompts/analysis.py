"""Prompts for analytical AI tasks."""


EXPENSE_ANALYSIS_PROMPT = """
{base}

Task:
Analyze the user's financial data for the selected scenario.

What to produce:
1. Provide 5-7 key insights.
2. Name 3-5 potential problems or risks.
3. Give 3-4 practical recommendations.

Rules:
- Do not invent data.
- Rely only on the input data.
- Write briefly and to the point.
- If there is not enough data, say so clearly.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "insights": [
    "string"
  ],
  "problems": [
    "string"
  ],
  "recommendations": [
    "string"
  ]
}}
"""


CATEGORY_ANALYSIS_PROMPT = """
{base}

Task:
Analyze categories, category-level spending, or category readiness for the selected scenario.

What to produce:
1. Identify the strongest or most important category signal.
2. Name 1-3 categories that may create problems, overlap, or inefficient spending.
3. Give short practical advice for improving the category setup or spending mix.

Rules:
- Do not invent data.
- Use only the input data.
- If there is not enough data, say so clearly in the JSON values.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "top_category": "string",
  "problem_categories": [
    "string"
  ],
  "advice": [
    "string"
  ]
}}
"""


ANOMALY_ANALYSIS_PROMPT = """
{base}

Task:
Find unusual financial movements, suspicious operations, or outlier periods for the selected scenario.

Treat as unusual:
- a sharp amount jump;
- an unusually large transaction;
- a period, category, account, or rate movement that differs strongly from the rest;
- an operation that deserves manual review based on the provided data.

Rules:
- Do not invent data.
- Analyze only what exists in the input data.
- If there are no clear anomalies, return an empty list.
- Every user-facing string value must follow the response language instruction from the base prompt.
- The response format must be strict JSON.

Response format:
{{
  "anomalies": [
    {{
      "date": "string",
      "label": "string",
      "amount": 0,
      "reason": "string"
    }}
  ]
}}
"""
