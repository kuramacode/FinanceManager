"""Use case for running any registered AI action."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.ai.actions import (
    AIActionDefinition,
    get_ai_action,
    is_action_available_for_page,
    normalize_page_key,
)
from app.ai.clients.openrouter import OpenRouterClient
from app.ai.context import build_ai_action_context
from app.ai.exceptions import AIError, AIResponseFormatError
from app.ai.history import record_ai_run
from app.ai.prompts import (
    ANOMALY_ANALYSIS_PROMPT,
    BASE_PROMPT,
    BUDGET_GENERATION_PROMPT,
    CATEGORY_ANALYSIS_PROMPT,
    EXPENSE_ANALYSIS_PROMPT,
    EXPENSE_FORECAST_PROMPT,
    FINANCIAL_SCORE_PROMPT,
    QA_PROMPT,
    UI_INSIGHTS_PROMPT,
)
from app.ai.schemas.action import (
    AIActionRunInputSchema,
    AIActionRunOutputSchema,
    AIActionRunResultSchema,
)
from app.i18n import translate_for_language


PROMPT_BY_TYPE = {
    "expense_analysis": EXPENSE_ANALYSIS_PROMPT,
    "category_analysis": CATEGORY_ANALYSIS_PROMPT,
    "anomaly_analysis": ANOMALY_ANALYSIS_PROMPT,
    "expense_forecast": EXPENSE_FORECAST_PROMPT,
    "budget_generation": BUDGET_GENERATION_PROMPT,
    "ui_insights": UI_INSIGHTS_PROMPT,
    "financial_score": FINANCIAL_SCORE_PROMPT,
}


def _safe_parse_json(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise AIResponseFormatError("AI response does not contain JSON object")

    json_part = raw_text[start : end + 1]

    try:
        parsed = json.loads(json_part)
    except json.JSONDecodeError as exc:
        raise AIResponseFormatError("AI returned invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise AIResponseFormatError("AI response JSON must be an object")
    return parsed


def _build_base_prompt(data: dict[str, Any]) -> str:
    response_language = data.get("response_language") or {}
    language_instruction = response_language.get(
        "ai_instruction",
        "Answer every user-facing string in English.",
    )
    return BASE_PROMPT.format(
        data=json.dumps(data, ensure_ascii=False, indent=2),
        language_instruction=language_instruction,
    )


def _build_action_prompt(
    *,
    action: AIActionDefinition,
    context_data: dict[str, Any],
    user_message: str,
) -> str:
    base = _build_base_prompt(context_data)

    if user_message.strip() or action.prompt_type == "qa":
        question = user_message.strip() or action.prompt
        return QA_PROMPT.format(base=base, question=question)

    template = PROMPT_BY_TYPE.get(action.prompt_type)
    if template is None:
        return QA_PROMPT.format(base=base, question=action.prompt)

    return template.format(base=base)


def _format_lines(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items if str(item or "").strip()]


def _format_object_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []

    lines = []
    for item in items:
        if isinstance(item, dict):
            parts = []
            for key, value in item.items():
                if value in (None, "", []):
                    continue
                parts.append(f"{key}: {value}")
            if parts:
                lines.append("; ".join(parts))
        elif str(item or "").strip():
            lines.append(str(item).strip())
    return lines


def _label(language: str | None, key: str, fallback: str) -> str:
    if not language:
        return fallback
    value = translate_for_language(language, key)
    return fallback if value == key else value


def _format_section(title: str, lines: list[str]) -> str:
    if not lines:
        return ""
    body = "\n".join(f"{index + 1}. {line}" for index, line in enumerate(lines))
    return f"{title}\n{body}"


def _format_ai_payload(payload: dict[str, Any], *, language: str | None = None) -> str:
    if isinstance(payload.get("answer"), str) and payload["answer"].strip():
        return payload["answer"].strip()

    sections = [
        _format_section(_label(language, "ai.sections.insights", "Insights"), _format_lines(payload.get("insights"))),
        _format_section(_label(language, "ai.sections.problems", "Problems"), _format_lines(payload.get("problems"))),
        _format_section(
            _label(language, "ai.sections.recommendations", "Recommendations"),
            _format_lines(payload.get("recommendations")),
        ),
        _format_section(
            _label(language, "ai.sections.problem_categories", "Problem categories"),
            _format_lines(payload.get("problem_categories")),
        ),
        _format_section(_label(language, "ai.sections.advice", "Advice"), _format_lines(payload.get("advice"))),
        _format_section(_label(language, "ai.sections.anomalies", "Anomalies"), _format_object_list(payload.get("anomalies"))),
        _format_section(_label(language, "ai.sections.budget", "Budget"), _format_object_list(payload.get("budget"))),
        _format_section(_label(language, "ai.sections.top_categories", "Top categories"), _format_lines(payload.get("top_categories"))),
    ]

    top_category = str(payload.get("top_category") or "").strip()
    if top_category:
        sections.insert(0, f"{_label(language, 'ai.sections.top_category', 'Top category')}\n{top_category}")

    forecast_parts = []
    if "expected_total" in payload:
        forecast_parts.append(f"{_label(language, 'ai.sections.expected_total', 'Expected total')}: {payload.get('expected_total')}")
    if payload.get("trend"):
        forecast_parts.append(f"{_label(language, 'ai.sections.trend', 'Trend')}: {payload.get('trend')}")
    if payload.get("note"):
        forecast_parts.append(str(payload["note"]))
    if forecast_parts:
        sections.append(f"{_label(language, 'ai.sections.forecast', 'Forecast')}\n" + "\n".join(forecast_parts))

    score_parts = []
    if "score" in payload:
        score_parts.append(f"{_label(language, 'ai.sections.score', 'Score')}: {payload.get('score')}")
    if payload.get("status"):
        score_parts.append(f"{_label(language, 'ai.sections.status', 'Status')}: {payload.get('status')}")
    if payload.get("explanation"):
        score_parts.append(str(payload["explanation"]))
    if score_parts:
        sections.append(f"{_label(language, 'ai.sections.financial_score', 'Financial score')}\n" + "\n".join(score_parts))

    message = "\n\n".join(section for section in sections if section)
    if message:
        return message

    return json.dumps(payload, ensure_ascii=False, indent=2)


class RunAIActionUseCase:
    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client

    def execute(
        self,
        *,
        user_id: int,
        action_id: str,
        page_key: str | None = None,
        message: str | None = None,
        language: str | None = None,
    ) -> AIActionRunResultSchema:
        try:
            validated_input = AIActionRunInputSchema(
                action_id=action_id,
                page_key=page_key or "generic",
                message=message or "",
                language=language,
            )

            action = get_ai_action(validated_input.action_id)
            if action is None:
                raise ValueError(f"Unknown AI action: {validated_input.action_id}")

            resolved_page = normalize_page_key(validated_input.page_key or action.page)
            if not is_action_available_for_page(action, resolved_page):
                raise ValueError(f"AI action '{action.id}' is not available for page '{resolved_page}'")

            context_data = build_ai_action_context(
                user_id=user_id,
                action=action,
                page_key=resolved_page,
                language=validated_input.language,
                user_message=validated_input.message,
            )
            prompt = _build_action_prompt(
                action=action,
                context_data=context_data,
                user_message=validated_input.message,
            )

            client = self.client or OpenRouterClient()
            raw_response = client.send_prompt(prompt, json_response=True)
            parsed_response = _safe_parse_json(raw_response)

            output = AIActionRunOutputSchema(
                action_id=action.id,
                page_key=resolved_page,
                title=action.title,
                prompt_type=action.prompt_type,
                message=_format_ai_payload(parsed_response, language=validated_input.language),
                raw=parsed_response,
            )

            record_ai_run(
                action_id=action.id,
                page_key=resolved_page,
                user_id=user_id,
                status="success",
                result=output.model_dump(),
            )
            return AIActionRunResultSchema(ok=True, data=output, error=None)

        except (ValidationError, AIError, ValueError, TypeError) as exc:
            action_for_history = action_id or "unknown"
            page_for_history = normalize_page_key(page_key)
            record_ai_run(
                action_id=action_for_history,
                page_key=page_for_history,
                user_id=user_id,
                status="error",
                error=str(exc),
            )
            return AIActionRunResultSchema(ok=False, data=None, error=str(exc))

        except Exception as exc:
            action_for_history = action_id or "unknown"
            page_for_history = normalize_page_key(page_key)
            message_text = f"Unexpected error: {exc}"
            record_ai_run(
                action_id=action_for_history,
                page_key=page_for_history,
                user_id=user_id,
                status="error",
                error=message_text,
            )
            return AIActionRunResultSchema(ok=False, data=None, error=message_text)
