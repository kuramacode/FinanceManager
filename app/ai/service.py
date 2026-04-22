from app.ai.services import AnalyzeExpensesUseCase, RunAIActionUseCase

class AIService:
    def __init__(self) -> None:
        self._analyze_expenses_use_case = AnalyzeExpensesUseCase()
        self._run_action_use_case = RunAIActionUseCase()
        
    def analyze_expenses(
        self,
        user_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
        language: str | None = None,
    ):
        return self._analyze_expenses_use_case.execute(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            language=language,
        )

    def run_action(
        self,
        *,
        user_id: int,
        action_id: str,
        page_key: str | None = None,
        message: str | None = None,
        language: str | None = None,
    ):
        return self._run_action_use_case.execute(
            user_id=user_id,
            action_id=action_id,
            page_key=page_key,
            message=message,
            language=language,
        )
