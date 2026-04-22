"""Schemas for expense analysis use case."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

class PeriodSchema(BaseModel):
    date_from: str
    date_to: str
    
class TotalStatsSchema(BaseModel):
    income: float = 0
    expense: float = 0
    balance: float = 0
    
class CategoryStatSchema(BaseModel):
    name: str
    amount: float
    transaction_count: int = 0

class ResponseLanguageSchema(BaseModel):
    language: str = "en"
    locale: str = "en-US"
    label: str = "English"
    native: str = "English"
    ai_instruction: str = "Answer every user-facing string in English."
    
class ExpenseAnalysisInputSchema(BaseModel):
    response_language: ResponseLanguageSchema = Field(default_factory=ResponseLanguageSchema)
    period: PeriodSchema
    totals: TotalStatsSchema
    top_expense_categories: List[CategoryStatSchema] = Field(default_factory=list)
    top_income_categories: List[CategoryStatSchema] = Field(default_factory=list)
    transactions_count: int = 0
    currency: str = "UAH"
    
class ExpenseAnalysisOutputSchema(BaseModel):
    insights: List[str] = Field(default_factory=list)
    problems: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
class ExpenseAnalysisResultSchema(BaseModel):
    ok: bool = True
    data: Optional[ExpenseAnalysisOutputSchema] = None
    error: Optional[str] = None
