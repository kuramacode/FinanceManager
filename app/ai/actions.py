"""Central registry for page-aware AI actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


AI_ACTION_ENDPOINT_PREFIX = "/api/ai/actions"


@dataclass(frozen=True)
class AIActionDefinition:
    id: str
    page: str
    title: str
    description: str
    prompt: str
    prompt_type: str
    method: str = "POST"

    @property
    def endpoint(self) -> str:
        return f"{AI_ACTION_ENDPOINT_PREFIX}/{self.id}"

    def model_dump(self) -> dict[str, str]:
        return {
            "id": self.id,
            "page": self.page,
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "prompt_type": self.prompt_type,
            "endpoint": self.endpoint,
            "method": self.method,
        }


@dataclass(frozen=True)
class AIPageDefinition:
    key: str
    label: str
    caption: str


PROMPT_TYPES = {
    "expense_analysis",
    "category_analysis",
    "anomaly_analysis",
    "expense_forecast",
    "budget_generation",
    "ui_insights",
    "qa",
    "financial_score",
}


PAGE_DEFINITIONS: dict[str, AIPageDefinition] = {
    "dashboard": AIPageDefinition(
        key="dashboard",
        label="Dashboard",
        caption="Run AI analysis for the current dashboard period.",
    ),
    "transactions": AIPageDefinition(
        key="transactions",
        label="Transactions",
        caption="Use AI shortcuts to inspect transaction flow, anomalies, repeating payments, and spending structure.",
    ),
    "budgets": AIPageDefinition(
        key="budgets",
        label="Budgets",
        caption="Ask AI to compare plan versus actuals, detect unstable categories, and flag overspending risk.",
    ),
    "accounts": AIPageDefinition(
        key="accounts",
        label="Accounts",
        caption="Use AI to review liquidity, balance distribution, and whether money is spread across accounts effectively.",
    ),
    "analytics": AIPageDefinition(
        key="analytics",
        label="Analytics",
        caption="Open AI shortcuts for trend explanations, anomaly detection, and quick summaries of the current analytics setup.",
    ),
    "history": AIPageDefinition(
        key="history",
        label="History",
        caption="Summarize past financial changes, key milestones, and unusual periods from the history view.",
    ),
    "profile": AIPageDefinition(
        key="profile",
        label="Profile",
        caption="Use AI to understand product capabilities and discover personalized analysis scenarios.",
    ),
    "categories": AIPageDefinition(
        key="categories",
        label="Categories",
        caption="Use AI to review category structure, naming consistency, and whether the taxonomy is easy to analyze.",
    ),
    "currency": AIPageDefinition(
        key="currency",
        label="Exchange",
        caption="Open AI shortcuts to explain exchange-rate moves and compare the currencies currently visible on the page.",
    ),
    "generic": AIPageDefinition(
        key="generic",
        label="Workspace",
        caption="Use AI shortcuts that adapt to the current page and real finance workflows.",
    ),
}


ACTION_DEFINITIONS: tuple[AIActionDefinition, ...] = (
    AIActionDefinition(
        id="expense-analysis",
        page="dashboard",
        title="Expense analysis",
        description="Analyze expenses, potential problems, and practical recommendations for this month.",
        prompt="Analyze dashboard expenses using the current user data.",
        prompt_type="expense_analysis",
    ),
    AIActionDefinition(
        id="ui-insights",
        page="dashboard",
        title="Quick dashboard insights",
        description="Generate short insights for the dashboard cards and recent activity.",
        prompt="Generate concise dashboard insights from the current user data.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="expense-forecast",
        page="dashboard",
        title="Expense forecast",
        description="Forecast near-term expenses from the available history.",
        prompt="Forecast the user's next-period expenses from the current transaction history.",
        prompt_type="expense_forecast",
    ),
    AIActionDefinition(
        id="financial-score",
        page="dashboard",
        title="Financial score",
        description="Estimate the overall financial health score from income, expenses, budgets, and balances.",
        prompt="Score the user's current financial state and explain the result.",
        prompt_type="financial_score",
    ),
    AIActionDefinition(
        id="analyze-transactions",
        page="transactions",
        title="Analyze transactions",
        description="Summarize the main patterns across the visible transaction list.",
        prompt="Analyze the visible transactions and summarize the strongest patterns.",
        prompt_type="expense_analysis",
    ),
    AIActionDefinition(
        id="find-anomalies",
        page="transactions",
        title="Find unusual expenses",
        description="Look for expense entries that stand out from the usual behavior.",
        prompt="Look for expense transactions that appear unusual or out of pattern.",
        prompt_type="anomaly_analysis",
    ),
    AIActionDefinition(
        id="largest-spend",
        page="transactions",
        title="Show biggest spending",
        description="Surface the largest outgoing transactions and the categories behind them.",
        prompt="Show the largest spending items and explain where they come from.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="recurring-payments",
        page="transactions",
        title="Recurring payments",
        description="Identify payments that may repeat on a schedule.",
        prompt="Identify transactions that look like recurring or subscription-style payments.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="spending-structure",
        page="transactions",
        title="Explain spending mix",
        description="Describe how spending is distributed across categories and accounts.",
        prompt="Explain the current spending structure across categories and accounts.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="suspicious-operations",
        page="transactions",
        title="Suspicious operations",
        description="Highlight transactions that deserve a second look.",
        prompt="Highlight transactions that might be suspicious or worth reviewing manually.",
        prompt_type="anomaly_analysis",
    ),
    AIActionDefinition(
        id="optimize-expenses",
        page="transactions",
        title="Expense optimization tips",
        description="Suggest areas where spending could be reduced or simplified.",
        prompt="Suggest ways to optimize spending based on the visible transactions.",
        prompt_type="expense_analysis",
    ),
    AIActionDefinition(
        id="analyze-budgets",
        page="budgets",
        title="Analyze budgets",
        description="Summarize how healthy the current budget setup looks.",
        prompt="Analyze the visible budgets and summarize the overall health of the setup.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="overspend-risk",
        page="budgets",
        title="Overspending risk",
        description="Find budgets that are most likely to exceed their limit soon.",
        prompt="Identify budgets that are at the highest risk of being exceeded soon.",
        prompt_type="expense_forecast",
    ),
    AIActionDefinition(
        id="problem-categories",
        page="budgets",
        title="Problem categories",
        description="Highlight categories that are driving the most budget pressure.",
        prompt="Highlight the categories that create the biggest budget pressure.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="budget-allocation",
        page="budgets",
        title="Budget allocation advice",
        description="Suggest how limits could be redistributed more effectively.",
        prompt="Suggest how the current budget allocation could be improved.",
        prompt_type="budget_generation",
    ),
    AIActionDefinition(
        id="plan-vs-actual",
        page="budgets",
        title="Compare plan vs actual",
        description="Review the difference between configured limits and current spend.",
        prompt="Compare budget limits with actual spending and explain the main gaps.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="unstable-categories",
        page="budgets",
        title="Most unstable categories",
        description="Spot categories whose behavior looks the least predictable.",
        prompt="Identify the least stable or most volatile budget categories.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="limit-improvements",
        page="budgets",
        title="Suggest better limits",
        description="Recommend more realistic limits based on the current budget picture.",
        prompt="Suggest better budget limits based on current usage patterns.",
        prompt_type="budget_generation",
    ),
    AIActionDefinition(
        id="budget-generation",
        page="budgets",
        title="Generate budget proposal",
        description="Create recommended category limits from the available income and expense history.",
        prompt="Generate a recommended budget by category using the available financial history.",
        prompt_type="budget_generation",
    ),
    AIActionDefinition(
        id="analyze-accounts",
        page="accounts",
        title="Analyze accounts",
        description="Summarize balances, account mix, and notable account-level signals.",
        prompt="Analyze the visible accounts and summarize the most important balance signals.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="balance-imbalance",
        page="accounts",
        title="Balance imbalance",
        description="Look for accounts that are too heavy or too underused compared with the rest.",
        prompt="Identify imbalances between accounts and explain where funds are concentrated.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="inefficient-distribution",
        page="accounts",
        title="Inefficient fund distribution",
        description="Highlight where the current spread of funds may be inefficient.",
        prompt="Identify accounts that suggest inefficient money distribution.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="storage-optimization",
        page="accounts",
        title="Storage optimization",
        description="Suggest better placement of funds across account types.",
        prompt="Suggest how balances could be distributed across accounts more efficiently.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="account-state",
        page="accounts",
        title="Describe account state",
        description="Generate a short plain-language summary of the current account setup.",
        prompt="Describe the current state of accounts in plain language.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="history-summary",
        page="history",
        title="History summary",
        description="Produce a concise summary of the financial timeline.",
        prompt="Create a concise summary of the visible financial history.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="key-history-shifts",
        page="history",
        title="Key changes",
        description="Highlight the most important turning points in the visible history.",
        prompt="Highlight the key financial changes visible in the history view.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="history-dynamics",
        page="history",
        title="Explain the dynamics",
        description="Describe the main direction and pace of change over time.",
        prompt="Explain the financial dynamics visible across the history timeline.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="unusual-periods",
        page="history",
        title="Unusual periods",
        description="Spot stretches of time that behave very differently from the rest.",
        prompt="Identify unusual periods or outlier moments in the financial history.",
        prompt_type="anomaly_analysis",
    ),
    AIActionDefinition(
        id="history-events",
        page="history",
        title="Major events",
        description="Call out the moments that mattered the most.",
        prompt="Highlight the main financial events visible in the history timeline.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="explain-charts",
        page="analytics",
        title="Explain charts",
        description="Translate the current widgets and graphs into plain-language insights.",
        prompt="Explain the main charts and widgets on this analytics page in plain language.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="main-trends",
        page="analytics",
        title="Main trends",
        description="Highlight the strongest ongoing trends in the selected range.",
        prompt="Summarize the main financial trends visible in the current analytics view.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="analytics-anomalies",
        page="analytics",
        title="Detect anomalies",
        description="Call out patterns or values that look unusual.",
        prompt="Identify anomalies or outliers in the current analytics view.",
        prompt_type="anomaly_analysis",
    ),
    AIActionDefinition(
        id="analytics-summary",
        page="analytics",
        title="Analytics summary",
        description="Create a short executive-style summary of the visible analytics.",
        prompt="Create a concise summary of the current analytics page.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="problem-zones",
        page="analytics",
        title="Problem zones",
        description="Point out the areas that may need attention first.",
        prompt="Highlight the problem areas or weak spots visible in the analytics.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="strengths-weaknesses",
        page="analytics",
        title="Strengths and weaknesses",
        description="Balance the strongest signals against the weakest ones.",
        prompt="Describe the strongest and weakest parts of the current financial picture.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="ai-capabilities",
        page="profile",
        title="Explain AI capabilities",
        description="Describe what the AI assistant can help with inside the product.",
        prompt="Explain the AI capabilities available in this finance product.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="personalization-ideas",
        page="profile",
        title="Personalization ideas",
        description="Suggest ways the assistant could adapt to this account.",
        prompt="Suggest useful personalization ideas for this account.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="analysis-scenarios",
        page="profile",
        title="Useful analysis scenarios",
        description="List the most helpful AI workflows for this user.",
        prompt="List the most helpful AI scenarios this user could run.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="analysis-scope",
        page="profile",
        title="What can be analyzed",
        description="Show which parts of the account are good candidates for AI review.",
        prompt="Explain what can be analyzed with AI in this account.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="category-structure",
        page="categories",
        title="Review category structure",
        description="Check whether the category system looks clear and balanced.",
        prompt="Review the visible category structure and explain whether it looks clear and balanced.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="category-overlap",
        page="categories",
        title="Find overlapping categories",
        description="Look for categories that may be redundant or too similar.",
        prompt="Identify categories that may overlap or duplicate each other.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="category-cleanup",
        page="categories",
        title="Suggest cleanup",
        description="Recommend naming or grouping improvements.",
        prompt="Suggest cleanup ideas for category names, descriptions, and grouping.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="category-analysis-readiness",
        page="categories",
        title="Check analysis readiness",
        description="Estimate how useful the current categories are for future analytics.",
        prompt="Evaluate whether the current category setup is ready for clear analytics and reporting.",
        prompt_type="category_analysis",
    ),
    AIActionDefinition(
        id="rate-summary",
        page="currency",
        title="Rate summary",
        description="Summarize the currently visible exchange-rate picture.",
        prompt="Summarize the current exchange-rate picture shown on this page.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="rate-comparison",
        page="currency",
        title="Compare currencies",
        description="Compare the strongest and weakest movements in the visible list.",
        prompt="Compare the visible currencies and highlight the main differences between them.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="rate-outliers",
        page="currency",
        title="Find unusual moves",
        description="Highlight currencies that look more volatile than the rest.",
        prompt="Identify unusual or standout currency moves in the current exchange view.",
        prompt_type="anomaly_analysis",
    ),
    AIActionDefinition(
        id="converter-guide",
        page="currency",
        title="Guide the conversion view",
        description="Explain how the converter and rates could be interpreted together.",
        prompt="Explain how to interpret the converter and current rates together.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="page-summary",
        page="generic",
        title="Summarize this page",
        description="Generate a short summary of what is currently visible.",
        prompt="Summarize the current page in plain language.",
        prompt_type="ui_insights",
    ),
    AIActionDefinition(
        id="surface-risks",
        page="generic",
        title="Surface risks",
        description="Highlight the parts of the page that may need attention.",
        prompt="Highlight the parts of this page that may need attention first.",
        prompt_type="qa",
    ),
    AIActionDefinition(
        id="suggest-next-steps",
        page="generic",
        title="Suggest next steps",
        description="Recommend useful follow-up actions based on the current page.",
        prompt="Suggest useful next steps based on the current page.",
        prompt_type="qa",
    ),
)


_ACTIONS_BY_ID = {action.id: action for action in ACTION_DEFINITIONS}
_ACTIONS_BY_PAGE: dict[str, tuple[AIActionDefinition, ...]] = {
    page: tuple(action for action in ACTION_DEFINITIONS if action.page == page)
    for page in PAGE_DEFINITIONS
}


def normalize_page_key(page_key: str | None) -> str:
    page = (page_key or "generic").strip().lower()
    return page if page in PAGE_DEFINITIONS else "generic"


def get_ai_action(action_id: str | None) -> AIActionDefinition | None:
    return _ACTIONS_BY_ID.get((action_id or "").strip())


def get_ai_actions_for_page(page_key: str | None) -> tuple[AIActionDefinition, ...]:
    page = normalize_page_key(page_key)
    actions = _ACTIONS_BY_PAGE.get(page, ())
    return actions or _ACTIONS_BY_PAGE["generic"]


def get_ai_page_definition(page_key: str | None) -> AIPageDefinition:
    return PAGE_DEFINITIONS[normalize_page_key(page_key)]


def is_action_available_for_page(action: AIActionDefinition, page_key: str | None) -> bool:
    page = normalize_page_key(page_key)
    return action.page == page or action.page == "generic" or page == "generic"


def iter_ai_actions() -> Iterable[AIActionDefinition]:
    return iter(ACTION_DEFINITIONS)
