EXPENSE_ANALYSIS_PROMPT = """
{base}

Task:
Analyze the user's financial data.

What to produce:
1. Provide 5-7 key expense insights.
2. Name 3-5 potential problems.
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

Задача:
Проаналізуй категорії витрат користувача.

Що потрібно визначити:
1. Найбільш витратну категорію
2. 2 категорії, де можливі неефективні витрати
3. Короткі поради по оптимізації

Правила:
- не вигадуй дані
- використовуй тільки передані дані
- якщо даних недостатньо, вкажи це явно
- формат відповіді строго JSON

Формат відповіді:
{{
  "top_category": "string",
  "problem_categories": [
    "string",
    "string"
  ],
  "advice": [
    "string",
    "string"
  ]
}}
"""


ANOMALY_ANALYSIS_PROMPT = """
{base}

Задача:
Знайди аномальні витрати.

Аномалією вважай:
- різкий стрибок суми
- нетипово велику транзакцію
- витрату, яка сильно вибивається із загального патерну

Правила:
- не вигадуй дані
- аналізуй тільки те, що є у вхідних даних
- якщо аномалій немає, поверни порожній список
- формат відповіді строго JSON

Формат відповіді:
{{
  "anomalies": [
    {{
      "date": "YYYY-MM-DD",
      "category": "string",
      "amount": 0,
      "reason": "string"
    }}
  ]
}}
"""
