from app.ai.services import AnalyzeExpensesUseCase

class AIService:
    def __init__(self) -> None:
        self._analyze_expenses_use_case = AnalyzeExpensesUseCase()
        
    def analyze_expenses(
        self,
        user_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        return self._analyze_expenses_use_case.execute(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )