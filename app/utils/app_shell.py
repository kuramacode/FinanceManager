from __future__ import annotations

from copy import deepcopy

from flask import request
from flask_login import current_user

_BLUEPRINT_TO_PAGE = {
    "dashboard": "dashboard",
    "transactions": "transactions",
    "budgets": "budgets",
    "accounts": "accounts",
    "analytics": "analytics",
    "category": "categories",
    "currency": "currency",
    "history": "history",
    "profile": "profile",
}

_AI_ENTRYPOINTS = {
    "dashboard": {
        "key": "dashboard",
        "label": "Dashboard",
        "caption": "Launch AI shortcuts for a quick overview of balances, budgets, and recent financial movement.",
        "actions": [
            {
                "id": "financial-summary",
                "title": "Financial summary",
                "description": "Review the page at a glance and surface the most important balance and cash-flow signals.",
                "prompt": "Create a concise financial summary of the dashboard and focus on the biggest balance and cash-flow signals.",
            },
            {
                "id": "period-change",
                "title": "What changed in this period",
                "description": "Highlight the biggest shifts since the last comparable period.",
                "prompt": "Explain what changed during the current period compared with the previous one.",
            },
            {
                "id": "key-risks",
                "title": "Key risks",
                "description": "Spot the areas that may need attention first.",
                "prompt": "Point out the most important risks visible on the dashboard right now.",
            },
            {
                "id": "achievements",
                "title": "Recent wins",
                "description": "Summarize the healthiest improvements or positive signals on the page.",
                "prompt": "Summarize the strongest positive signals and recent wins visible on the dashboard.",
            },
            {
                "id": "quick-recommendations",
                "title": "Quick recommendations",
                "description": "Suggest practical next steps based on the current overview.",
                "prompt": "Give a short list of practical recommendations based on the current dashboard state.",
            },
            {
                "id": "page-brief",
                "title": "AI page brief",
                "description": "Generate a short dashboard walkthrough in plain language.",
                "prompt": "Give a short AI overview of the dashboard in plain language.",
            },
        ],
    },
    "transactions": {
        "key": "transactions",
        "label": "Transactions",
        "caption": "Use AI shortcuts to inspect transaction flow, anomalies, repeating payments, and spending structure.",
        "actions": [
            {
                "id": "analyze-transactions",
                "title": "Analyze transactions",
                "description": "Summarize the main patterns across the visible transaction list.",
                "prompt": "Analyze the visible transactions and summarize the strongest patterns.",
            },
            {
                "id": "find-anomalies",
                "title": "Find unusual expenses",
                "description": "Look for expense entries that stand out from the usual behavior.",
                "prompt": "Look for expense transactions that appear unusual or out of pattern.",
            },
            {
                "id": "largest-spend",
                "title": "Show biggest spending",
                "description": "Surface the largest outgoing transactions and the categories behind them.",
                "prompt": "Show the largest spending items and explain where they come from.",
            },
            {
                "id": "recurring-payments",
                "title": "Recurring payments",
                "description": "Identify payments that may repeat on a schedule.",
                "prompt": "Identify transactions that look like recurring or subscription-style payments.",
            },
            {
                "id": "spending-structure",
                "title": "Explain spending mix",
                "description": "Describe how spending is distributed across categories and accounts.",
                "prompt": "Explain the current spending structure across categories and accounts.",
            },
            {
                "id": "suspicious-operations",
                "title": "Suspicious operations",
                "description": "Highlight transactions that deserve a second look.",
                "prompt": "Highlight transactions that might be suspicious or worth reviewing manually.",
            },
            {
                "id": "optimize-expenses",
                "title": "Expense optimization tips",
                "description": "Suggest areas where spending could be reduced or simplified.",
                "prompt": "Suggest ways to optimize spending based on the visible transactions.",
            },
        ],
    },
    "budgets": {
        "key": "budgets",
        "label": "Budgets",
        "caption": "Ask AI to compare plan versus actuals, detect unstable categories, and flag overspending risk.",
        "actions": [
            {
                "id": "analyze-budgets",
                "title": "Analyze budgets",
                "description": "Summarize how healthy the current budget setup looks.",
                "prompt": "Analyze the visible budgets and summarize the overall health of the setup.",
            },
            {
                "id": "overspend-risk",
                "title": "Overspending risk",
                "description": "Find budgets that are most likely to exceed their limit soon.",
                "prompt": "Identify budgets that are at the highest risk of being exceeded soon.",
            },
            {
                "id": "problem-categories",
                "title": "Problem categories",
                "description": "Highlight categories that are driving the most budget pressure.",
                "prompt": "Highlight the categories that create the biggest budget pressure.",
            },
            {
                "id": "budget-allocation",
                "title": "Budget allocation advice",
                "description": "Suggest how limits could be redistributed more effectively.",
                "prompt": "Suggest how the current budget allocation could be improved.",
            },
            {
                "id": "plan-vs-actual",
                "title": "Compare plan vs actual",
                "description": "Review the difference between configured limits and current spend.",
                "prompt": "Compare budget limits with actual spending and explain the main gaps.",
            },
            {
                "id": "unstable-categories",
                "title": "Most unstable categories",
                "description": "Spot categories whose behavior looks the least predictable.",
                "prompt": "Identify the least stable or most volatile budget categories.",
            },
            {
                "id": "limit-improvements",
                "title": "Suggest better limits",
                "description": "Recommend more realistic limits based on the current budget picture.",
                "prompt": "Suggest better budget limits based on current usage patterns.",
            },
        ],
    },
    "accounts": {
        "key": "accounts",
        "label": "Accounts",
        "caption": "Use AI to review liquidity, balance distribution, and whether money is spread across accounts effectively.",
        "actions": [
            {
                "id": "analyze-accounts",
                "title": "Analyze accounts",
                "description": "Summarize balances, account mix, and notable account-level signals.",
                "prompt": "Analyze the visible accounts and summarize the most important balance signals.",
            },
            {
                "id": "balance-imbalance",
                "title": "Balance imbalance",
                "description": "Look for accounts that are too heavy or too underused compared with the rest.",
                "prompt": "Identify imbalances between accounts and explain where funds are concentrated.",
            },
            {
                "id": "inefficient-distribution",
                "title": "Inefficient fund distribution",
                "description": "Highlight where the current spread of funds may be inefficient.",
                "prompt": "Identify accounts that suggest inefficient money distribution.",
            },
            {
                "id": "storage-optimization",
                "title": "Storage optimization",
                "description": "Suggest better placement of funds across account types.",
                "prompt": "Suggest how balances could be distributed across accounts more efficiently.",
            },
            {
                "id": "account-state",
                "title": "Describe account state",
                "description": "Generate a short plain-language summary of the current account setup.",
                "prompt": "Describe the current state of accounts in plain language.",
            },
        ],
    },
    "history": {
        "key": "history",
        "label": "History",
        "caption": "Summarize past financial changes, key milestones, and unusual periods from the history view.",
        "actions": [
            {
                "id": "history-summary",
                "title": "History summary",
                "description": "Produce a concise summary of the financial timeline.",
                "prompt": "Create a concise summary of the visible financial history.",
            },
            {
                "id": "key-history-shifts",
                "title": "Key changes",
                "description": "Highlight the most important turning points in the visible history.",
                "prompt": "Highlight the key financial changes visible in the history view.",
            },
            {
                "id": "history-dynamics",
                "title": "Explain the dynamics",
                "description": "Describe the main direction and pace of change over time.",
                "prompt": "Explain the financial dynamics visible across the history timeline.",
            },
            {
                "id": "unusual-periods",
                "title": "Unusual periods",
                "description": "Spot stretches of time that behave very differently from the rest.",
                "prompt": "Identify unusual periods or outlier moments in the financial history.",
            },
            {
                "id": "history-events",
                "title": "Major events",
                "description": "Call out the moments that mattered the most.",
                "prompt": "Highlight the main financial events visible in the history timeline.",
            },
        ],
    },
    "analytics": {
        "key": "analytics",
        "label": "Analytics",
        "caption": "Open AI shortcuts for trend explanations, anomaly detection, and quick summaries of the current analytics setup.",
        "actions": [
            {
                "id": "explain-charts",
                "title": "Explain charts",
                "description": "Translate the current widgets and graphs into plain-language insights.",
                "prompt": "Explain the main charts and widgets on this analytics page in plain language.",
            },
            {
                "id": "main-trends",
                "title": "Main trends",
                "description": "Highlight the strongest ongoing trends in the selected range.",
                "prompt": "Summarize the main financial trends visible in the current analytics view.",
            },
            {
                "id": "analytics-anomalies",
                "title": "Detect anomalies",
                "description": "Call out patterns or values that look unusual.",
                "prompt": "Identify anomalies or outliers in the current analytics view.",
            },
            {
                "id": "analytics-summary",
                "title": "Analytics summary",
                "description": "Create a short executive-style summary of the visible analytics.",
                "prompt": "Create a concise summary of the current analytics page.",
            },
            {
                "id": "problem-zones",
                "title": "Problem zones",
                "description": "Point out the areas that may need attention first.",
                "prompt": "Highlight the problem areas or weak spots visible in the analytics.",
            },
            {
                "id": "strengths-weaknesses",
                "title": "Strengths and weaknesses",
                "description": "Balance the strongest signals against the weakest ones.",
                "prompt": "Describe the strongest and weakest parts of the current financial picture.",
            },
        ],
    },
    "profile": {
        "key": "profile",
        "label": "Profile",
        "caption": "Use AI to understand product capabilities and discover personalized analysis scenarios.",
        "actions": [
            {
                "id": "ai-capabilities",
                "title": "Explain AI capabilities",
                "description": "Describe what the AI assistant can help with inside the product.",
                "prompt": "Explain the AI capabilities available in this finance product.",
            },
            {
                "id": "personalization-ideas",
                "title": "Personalization ideas",
                "description": "Suggest ways the assistant could adapt to this account.",
                "prompt": "Suggest useful personalization ideas for this account.",
            },
            {
                "id": "analysis-scenarios",
                "title": "Useful analysis scenarios",
                "description": "List the most helpful AI workflows for this user.",
                "prompt": "List the most helpful AI scenarios this user could run.",
            },
            {
                "id": "analysis-scope",
                "title": "What can be analyzed",
                "description": "Show which parts of the account are good candidates for AI review.",
                "prompt": "Explain what can be analyzed with AI in this account.",
            },
        ],
    },
    "categories": {
        "key": "categories",
        "label": "Categories",
        "caption": "Use AI to review category structure, naming consistency, and whether the taxonomy is easy to analyze.",
        "actions": [
            {
                "id": "category-structure",
                "title": "Review category structure",
                "description": "Check whether the category system looks clear and balanced.",
                "prompt": "Review the visible category structure and explain whether it looks clear and balanced.",
            },
            {
                "id": "category-overlap",
                "title": "Find overlapping categories",
                "description": "Look for categories that may be redundant or too similar.",
                "prompt": "Identify categories that may overlap or duplicate each other.",
            },
            {
                "id": "category-cleanup",
                "title": "Suggest cleanup",
                "description": "Recommend naming or grouping improvements.",
                "prompt": "Suggest cleanup ideas for category names, descriptions, and grouping.",
            },
            {
                "id": "category-analysis-readiness",
                "title": "Check analysis readiness",
                "description": "Estimate how useful the current categories are for future analytics.",
                "prompt": "Evaluate whether the current category setup is ready for clear analytics and reporting.",
            },
        ],
    },
    "currency": {
        "key": "currency",
        "label": "Exchange",
        "caption": "Open AI shortcuts to explain exchange-rate moves and compare the currencies currently visible on the page.",
        "actions": [
            {
                "id": "rate-summary",
                "title": "Rate summary",
                "description": "Summarize the currently visible exchange-rate picture.",
                "prompt": "Summarize the current exchange-rate picture shown on this page.",
            },
            {
                "id": "rate-comparison",
                "title": "Compare currencies",
                "description": "Compare the strongest and weakest movements in the visible list.",
                "prompt": "Compare the visible currencies and highlight the main differences between them.",
            },
            {
                "id": "rate-outliers",
                "title": "Find unusual moves",
                "description": "Highlight currencies that look more volatile than the rest.",
                "prompt": "Identify unusual or standout currency moves in the current exchange view.",
            },
            {
                "id": "converter-guide",
                "title": "Guide the conversion view",
                "description": "Explain how the converter and rates could be interpreted together.",
                "prompt": "Explain how to interpret the converter and current rates together.",
            },
        ],
    },
    "generic": {
        "key": "generic",
        "label": "Workspace",
        "caption": "Use AI shortcuts that adapt to the current page and can later connect to real page-level finance workflows.",
        "actions": [
            {
                "id": "page-summary",
                "title": "Summarize this page",
                "description": "Generate a short summary of what is currently visible.",
                "prompt": "Summarize the current page in plain language.",
            },
            {
                "id": "surface-risks",
                "title": "Surface risks",
                "description": "Highlight the parts of the page that may need attention.",
                "prompt": "Highlight the parts of this page that may need attention first.",
            },
            {
                "id": "suggest-next-steps",
                "title": "Suggest next steps",
                "description": "Recommend useful follow-up actions based on the current page.",
                "prompt": "Suggest useful next steps based on the current page.",
            },
        ],
    },
}


def _resolve_username() -> str:
    if getattr(current_user, "is_authenticated", False):
        return getattr(current_user, "username", "") or "Personal"
    return "Guest"


def resolve_active_page(endpoint: str | None = None) -> str:
    current_endpoint = endpoint or getattr(request, "endpoint", None) or ""
    blueprint = current_endpoint.split(".", 1)[0]
    return _BLUEPRINT_TO_PAGE.get(blueprint, "generic")


def get_ai_entrypoint(page_key: str | None = None) -> dict:
    resolved_key = page_key or resolve_active_page()
    config = deepcopy(_AI_ENTRYPOINTS.get(resolved_key, _AI_ENTRYPOINTS["generic"]))
    config["key"] = config.get("key") or resolved_key
    return config


def get_app_shell_context() -> dict:
    active_page = resolve_active_page()
    return {
        "app_shell": {
            "active_page": active_page,
            "username": _resolve_username(),
        },
        "ai_entrypoint": get_ai_entrypoint(active_page),
    }
