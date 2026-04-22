"""Schemas for generic AI action execution."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AIActionRunInputSchema(BaseModel):
    action_id: str
    page_key: str = "generic"
    message: str = ""
    language: Optional[str] = None


class AIActionRunOutputSchema(BaseModel):
    action_id: str
    page_key: str
    title: str
    prompt_type: str
    message: str
    raw: dict[str, Any] = Field(default_factory=dict)


class AIActionRunResultSchema(BaseModel):
    ok: bool = True
    data: Optional[AIActionRunOutputSchema] = None
    error: Optional[str] = None
