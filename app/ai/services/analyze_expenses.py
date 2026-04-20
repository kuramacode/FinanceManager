"""Use case for expense analysis."""

import json
from typing import Any, Dict

from pydantic import ValidationError

from app.ai.clients import OpenRouterClient
from app.ai.context import build_expense_analysis_context
from app.ai.exceptions import AIResponseFormatError
from app.ai.prompts import BASE_PROMPT, EXPENSE_ANALYSIS_PROMPT
from app.ai.schemas.analysis import (
    ExpenseAnalysisInputSchema,
    ExpenseAnalysisOutputSchema,
    ExpenseAnalysisResultSchema,
)

def _build_base_prompt(data: Dict[str, Any]) -> str:
    return BASE_PROMPT.format(
        data=json.dumps(data, ensure_ascii=False, indent=2)
    )
    
def _build_expense_analysis_prompt(data: Dict[str, Any]) -> str:
    return EXPENSE_ANALYSIS_PROMPT.format(
        base=_build_base_prompt(data)
    )
    
def _safe_parse_json(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()

    # Попытка вытащить JSON даже если модель прислала мусор вокруг
    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise AIResponseFormatError("AI response does not contain JSON object")

    json_part = raw_text[start:end + 1]

    try:
        return json.loads(json_part)
    except json.JSONDecodeError as exc:
        raise AIResponseFormatError("AI returned invalid JSON") from exc
    
class AnalyzeExpensesUseCase:
    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()
        
    def execute(
        self,
        user_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> ExpenseAnalysisResultSchema:
        try:
            context_data = build_expense_analysis_context(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
            )
            
            validated_input = ExpenseAnalysisInputSchema(**context_data)
            prompt = _build_expense_analysis_prompt(validated_input.model_dump())
            
            raw_response = self.client.send_prompt(prompt)
            parsed_response = _safe_parse_json(raw_response)
            
            validated_output = ExpenseAnalysisOutputSchema(**parsed_response)
            
            return ExpenseAnalysisResultSchema(
                ok=True,
                data=validated_output,
                error=None,
            )
            
        except (ValidationError, AIResponseFormatError, ValueError, TypeError) as exc:
            return ExpenseAnalysisResultSchema(
                ok=False,
                data=None,
                error=str(exc)
            )
        
        except Exception as exc:
            return ExpenseAnalysisResultSchema(
                ok=False,
                data=None,
                error=f"Unexpected error: {exc}"
            )