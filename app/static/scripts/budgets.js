const BUDGETS_API = "/api/budgets";
const CATEGORIES_API = "/api/category";
const UI_LOCALE = window.ledgerI18n?.locale || "en-US";

function tr(key, replacements = {}, fallback = "") {
  return window.ledgerI18n?.t(key, replacements, fallback) || fallback || key;
}

let budgets = [];
let expenseCategories = [];
let activeFilter = "all";
let searchQuery = "";
let budgetsPageInitialized = false;
let feedbackTimer = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.error || `HTTP ${response.status}`);
  }

  return data;
}

function toInputDate(value = new Date()) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseDate(value) {
  if (!value) return null;
  const [year, month, day] = String(value).slice(0, 10).split("-").map(Number);
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
    return null;
  }
  return new Date(year, month - 1, day);
}

function formatDateShort(value) {
  const parsed = parseDate(value);
  if (!parsed) return "--";
  return parsed.toLocaleDateString(UI_LOCALE, { month: "short", day: "numeric" });
}

function formatDateRange(start, end) {
  if (!start || !end) return tr("budgets.dates_unavailable");
  return `${formatDateShort(start)} - ${formatDateShort(end)}`;
}

function formatMoney(amount, code) {
  const value = Number(amount || 0);
  const abs = Math.abs(value).toLocaleString(UI_LOCALE, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const prefix = value < 0 ? "-" : "";

  if (code === "USD") return `${prefix}$${abs}`;
  if (code === "EUR") return `${prefix}EUR ${abs}`;
  if (code === "GBP") return `${prefix}GBP ${abs}`;
  if (code === "UAH") return `${prefix}UAH ${abs}`;
  return `${prefix}${abs} ${code}`;
}

function statusMeta(status) {
  if (status === "exceeded") {
    return { label: tr("common.status.exceeded"), className: "over" };
  }
  if (status === "warning") {
    return { label: tr("common.status.warning"), className: "warn" };
  }
  if (status === "inactive") {
    return { label: tr("common.status.inactive"), className: "muted" };
  }
  if (status === "unavailable") {
    return { label: tr("common.status.unavailable"), className: "muted" };
  }
  return { label: tr("common.status.on_track"), className: "good" };
}

function normalizeCategory(category) {
  return {
    id: Number(category?.id),
    name: category?.name ?? tr("common.unnamed_category"),
    desc: category?.desc ?? "",
    emoji: category?.emoji ?? "#",
    type: category?.type ?? "expense",
    built_in: category?.built_in === true || category?.built_in === 1 || String(category?.built_in).toLowerCase() === "true",
  };
}

function normalizeBudget(budget) {
  const categories = Array.isArray(budget?.categories) ? budget.categories.map(normalizeCategory) : [];

  return {
    id: Number(budget?.id),
    name: budget?.name ?? tr("common.untitled_budget"),
    desc: budget?.desc ?? "",
    amount_limit: Number(budget?.amount_limit ?? 0),
    currency_code: (budget?.currency_code ?? "UAH").toUpperCase(),
    period_type: budget?.period_type ?? "monthly",
    start_date: budget?.start_date ? String(budget.start_date).slice(0, 10) : "",
    end_date: budget?.end_date ? String(budget.end_date).slice(0, 10) : "",
    period_start: budget?.period_start ? String(budget.period_start).slice(0, 10) : "",
    period_end: budget?.period_end ? String(budget.period_end).slice(0, 10) : "",
    category_ids: Array.isArray(budget?.category_ids) ? budget.category_ids.map(Number) : categories.map(category => category.id),
    categories,
    icon: budget?.icon ?? (budget?.name ? String(budget.name).charAt(0).toUpperCase() : "B"),
    spent: Number(budget?.spent ?? 0),
    remaining: Number(budget?.remaining ?? 0),
    percent: Number(budget?.percent ?? 0),
    status: budget?.status ?? "on_track",
    is_active: budget?.is_active ?? budget?.status !== "inactive",
    conversion_error: budget?.conversion_error ?? null,
  };
}

function buildBudgetNote(budget) {
  if (budget.conversion_error) {
    return budget.conversion_error;
  }

  if (budget.desc) {
    return budget.desc;
  }

  const today = toInputDate();
  if (budget.status === "inactive") {
    if (budget.start_date && budget.start_date > today) {
      return tr("budgets.starts_on", { date: formatDateShort(budget.start_date) });
    }
    if (budget.end_date && budget.end_date < today) {
      return tr("budgets.ended_on", { date: formatDateShort(budget.end_date) });
    }
    return tr("budgets.outside_window");
  }

  if (budget.status === "unavailable") {
    return tr("budgets.conversion_issue");
  }

  if (budget.categories.length) {
    const names = budget.categories.slice(0, 3).map(category => category.name).join(", ");
    return budget.categories.length > 3
      ? tr("budgets.tracking_more", { names })
      : tr("budgets.tracking_categories", { names });
  }

  return tr("common.no_description");
}

function buildCategoryTags(budget) {
  if (!budget.categories.length) return "";

  const visible = budget.categories.slice(0, 3).map(category => `
    <span class="budget-tag">${escapeHtml(category.emoji)} ${escapeHtml(category.name)}</span>
  `);

  if (budget.categories.length > 3) {
    visible.push(`<span class="budget-tag">+${budget.categories.length - 3} ${escapeHtml(tr("common.more"))}</span>`);
  }

  return visible.join("");
}

function formatPeriodLabel(budget) {
  const typeLabel = tr(`common.periods.${budget.period_type}`, {}, budget.period_type.charAt(0).toUpperCase() + budget.period_type.slice(1));
  if (budget.period_start && budget.period_end) {
    return `${typeLabel} - ${formatDateRange(budget.period_start, budget.period_end)}`;
  }
  if (budget.start_date && budget.end_date) {
    return `${typeLabel} - ${formatDateRange(budget.start_date, budget.end_date)}`;
  }
  return typeLabel;
}

function progressWidth(budget) {
  return Math.max(0, Math.min(Number(budget.percent || 0), 100));
}

function remainingMeta(budget) {
  if (budget.status === "inactive") {
    return {
      className: "muted",
      label: tr("budgets.status"),
      value: tr("common.status.inactive"),
    };
  }

  if (budget.status === "unavailable") {
    return {
      className: "muted",
      label: tr("budgets.status"),
      value: tr("common.status.awaiting_rates"),
    };
  }

  if (budget.remaining < 0) {
    return {
      className: "over",
      label: tr("common.status.exceeded"),
      value: tr("budgets.over", { amount: formatMoney(Math.abs(budget.remaining), budget.currency_code) }),
    };
  }

  return {
    className: "safe",
    label: tr("budgets.remaining"),
    value: tr("budgets.left", { amount: formatMoney(budget.remaining, budget.currency_code) }),
  };
}

function buildCurrencyBreakdown(list, key) {
  if (!list.length) return "--";

  const totals = new Map();
  list.forEach(item => {
    const code = item.currency_code || "UAH";
    totals.set(code, (totals.get(code) || 0) + Number(item[key] || 0));
  });

  return Array.from(totals.entries())
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([code, total]) => formatMoney(total, code))
    .join(" / ");
}

function filteredBudgets() {
  return budgets.filter(budget => {
    const matchesFilter = activeFilter === "all" ? true : budget.status === activeFilter;
    const haystack = [
      budget.name,
      budget.desc,
      budget.status,
      budget.currency_code,
      ...budget.categories.map(category => category.name),
    ].join(" ").toLowerCase();
    const matchesSearch = haystack.includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });
}

function updateSummary() {
  const activeBudgets = budgets.filter(budget => budget.is_active);
  const attentionCount = budgets.filter(budget => ["warning", "exceeded", "unavailable"].includes(budget.status)).length;
  const currencies = [...new Set(activeBudgets.map(budget => budget.currency_code))];

  const setText = (id, value) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  };

  setText("summaryPlanned", buildCurrencyBreakdown(activeBudgets, "amount_limit"));
  setText("summarySpent", buildCurrencyBreakdown(activeBudgets, "spent"));
  setText("summaryActive", String(activeBudgets.length));
  const currencyUnit = currencies.length === 1 ? tr("budgets.currency_unit_one") : tr("budgets.currency_unit_many");
  setText("summaryActiveSub", activeBudgets.length ? tr("budgets.currencies_in_use", { count: currencies.length, unit: currencyUnit }) : tr("budgets.no_active_budgets"));
  setText("summaryAttention", String(attentionCount));
  setText("summaryAttentionSub", attentionCount ? tr("budgets.attention_sub") : tr("budgets.everything_healthy"));
}

function buildBudgetCard(budget) {
  const status = statusMeta(budget.status);
  const remaining = remainingMeta(budget);

  return `
    <article class="budget-card" data-id="${budget.id}">
      <div class="budget-head">
        <div class="budget-meta">
          <div class="budget-icon">${escapeHtml(budget.icon)}</div>
          <div class="budget-title-wrap">
            <div class="budget-name">${escapeHtml(budget.name)}</div>
            <div class="budget-period">${escapeHtml(formatPeriodLabel(budget))}</div>
          </div>
        </div>
        <span class="budget-status ${status.className}">${status.label}</span>
      </div>

      <div class="budget-amounts">
        <div>
          <div class="budget-current">${formatMoney(budget.spent, budget.currency_code)}</div>
          <div class="budget-limit">${escapeHtml(tr("budgets.spent_of_limit", { limit: formatMoney(budget.amount_limit, budget.currency_code) }))}</div>
        </div>
        <div class="budget-left">
          <div class="budget-left-value ${remaining.className}">${escapeHtml(remaining.value)}</div>
          <div class="budget-left-label">${escapeHtml(remaining.label)}</div>
        </div>
      </div>

      <div class="budget-progress-wrap">
        <div class="budget-progress-top">
          <span class="budget-progress-label">${escapeHtml(tr("budgets.usage"))}</span>
          <span class="budget-progress-value">${Number(budget.percent || 0).toFixed(1)}%</span>
        </div>
        <div class="budget-progress">
          <div class="budget-progress-bar ${status.className}" style="width:${progressWidth(budget)}%"></div>
        </div>
      </div>

      <div class="budget-footer">
        <div class="budget-copy">
          <div class="budget-note${budget.conversion_error ? " error" : ""}">${escapeHtml(buildBudgetNote(budget))}</div>
          <div class="budget-tags">${buildCategoryTags(budget)}</div>
        </div>
        <div class="budget-actions">
          <button type="button" class="icon-btn" data-action="edit" data-id="${budget.id}" title="${escapeHtml(tr("common.buttons.edit"))}">
            <svg viewBox="0 0 15 15" fill="none">
              <path d="M10.9 2.2a1.5 1.5 0 112.1 2.1l-7.8 7.8-3 .7.7-3 8-7.6z"
                stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
            </svg>
          </button>
          <button type="button" class="icon-btn" data-action="delete" data-id="${budget.id}" title="${escapeHtml(tr("common.buttons.delete"))}">
            <svg viewBox="0 0 15 15" fill="none">
              <path d="M2.5 4h10M6 2.2h3M5 5.2v6M7.5 5.2v6M10 5.2v6 M3.8 4l.6 8c.04.6.54 1 1 1h3.84c.6 0 1.1-.4 1.14-1l.6-8"
                stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </article>
  `;
}

function renderBudgets() {
  const grid = document.getElementById("budgetGrid");
  const empty = document.getElementById("budgetEmpty");
  if (!grid || !empty) return;

  updateSummary();

  const list = filteredBudgets();
  if (!list.length) {
    grid.innerHTML = "";
    grid.style.display = "none";
    empty.style.display = "block";
    return;
  }

  grid.style.display = "grid";
  empty.style.display = "none";
  grid.innerHTML = list.map(buildBudgetCard).join("");
}

function showFeedback(message, type = "error") {
  const feedback = document.getElementById("budgetFeedback");
  if (!feedback) return;

  feedback.hidden = false;
  feedback.className = `budget-feedback ${type === "success" ? "is-success" : "is-error"}`;
  feedback.textContent = message;

  if (feedbackTimer) {
    clearTimeout(feedbackTimer);
  }
  feedbackTimer = window.setTimeout(() => {
    feedback.hidden = true;
    feedback.textContent = "";
  }, 5000);
}

function openOverlay(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeOverlay(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.remove("open");
  document.body.style.overflow = "";
}

function closeOnBackdrop(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.addEventListener("click", event => {
    if (event.target === event.currentTarget) {
      closeOverlay(id);
    }
  });
}

function updateCategorySummary() {
  const summary = document.getElementById("budgetCategorySummary");
  if (!summary) return;

  const selectedCount = document.querySelectorAll(".budget-category-checkbox:checked").length;
  if (!expenseCategories.length) {
    summary.textContent = tr("budgets.no_expense_categories");
    return;
  }

  summary.textContent = selectedCount
    ? tr("budgets.selected_categories", {
      count: selectedCount,
      unit: selectedCount === 1 ? tr("budgets.category_unit_one") : tr("budgets.category_unit_many"),
    })
    : tr("budgets.select_categories");
}

function renderCategoryPicker(selectedIds = []) {
  const container = document.getElementById("budgetCategoryList");
  const empty = document.getElementById("budgetCategoryEmpty");
  if (!container || !empty) return;

  const selectedSet = new Set(selectedIds.map(Number));
  if (!expenseCategories.length) {
    container.innerHTML = "";
    empty.hidden = false;
    updateCategorySummary();
    return;
  }

  empty.hidden = true;
  container.innerHTML = expenseCategories.map(category => `
    <label class="budget-category-option">
      <input class="budget-category-checkbox" type="checkbox" value="${category.id}" ${selectedSet.has(category.id) ? "checked" : ""} />
      <span class="budget-category-card">
        <span class="budget-category-emoji">${escapeHtml(category.emoji)}</span>
        <span class="budget-category-copy">
          <span class="budget-category-name">${escapeHtml(category.name)}</span>
          <span class="budget-category-desc">${escapeHtml(category.desc || (category.built_in ? tr("common.built_in_category") : tr("common.expense_category")))}</span>
        </span>
      </span>
    </label>
  `).join("");

  updateCategorySummary();
}

function getSelectedCategoryIds() {
  return [...document.querySelectorAll(".budget-category-checkbox:checked")].map(input => Number(input.value));
}

function syncPeriodFields() {
  const periodType = document.getElementById("budgetPeriodType")?.value || "monthly";
  const endDateGroup = document.getElementById("budgetEndDateGroup");
  const endDateInput = document.getElementById("budgetEndDate");
  const startDateInput = document.getElementById("budgetStartDate");
  const hint = document.getElementById("budgetPeriodHint");

  if (!endDateGroup || !endDateInput || !startDateInput || !hint) return;

  if (periodType === "custom") {
    endDateGroup.classList.remove("is-hidden");
    endDateInput.required = true;
    hint.textContent = tr("budgets.custom_hint");
    return;
  }

  endDateGroup.classList.add("is-hidden");
  endDateInput.required = false;
  endDateInput.value = startDateInput.value;

  hint.textContent = periodType === "weekly"
    ? tr("budgets.weekly_hint")
    : tr("budgets.monthly_hint");
}

function resetBudgetForm() {
  const form = document.getElementById("budgetForm");
  if (form) form.reset();

  document.getElementById("budgetId").value = "";
  document.getElementById("budgetName").value = "";
  document.getElementById("budgetDesc").value = "";
  document.getElementById("budgetLimit").value = "";
  document.getElementById("budgetCurrency").value = "UAH";
  document.getElementById("budgetPeriodType").value = "monthly";
  document.getElementById("budgetStartDate").value = toInputDate();
  document.getElementById("budgetEndDate").value = toInputDate();
  document.getElementById("budgetSubmitBtn").textContent = tr("budgets.add_budget");
  document.getElementById("budget-modal-title").textContent = tr("budgets.modal_new_title");
  document.getElementById("budget-modal-subtitle").textContent = tr("budgets.modal_new_subtitle");
  renderCategoryPicker([]);
  syncPeriodFields();
}

function openCreateBudgetModal() {
  resetBudgetForm();
  openOverlay("modal-budget");
}

function openEditBudgetModal(id) {
  const budget = budgets.find(item => item.id === id);
  if (!budget) return;

  document.getElementById("budgetId").value = String(budget.id);
  document.getElementById("budgetName").value = budget.name;
  document.getElementById("budgetDesc").value = budget.desc;
  document.getElementById("budgetLimit").value = String(budget.amount_limit);
  document.getElementById("budgetCurrency").value = budget.currency_code;
  document.getElementById("budgetPeriodType").value = budget.period_type;
  document.getElementById("budgetStartDate").value = budget.start_date;
  document.getElementById("budgetEndDate").value = budget.end_date || budget.start_date;
  document.getElementById("budgetSubmitBtn").textContent = tr("common.buttons.save_changes");
  document.getElementById("budget-modal-title").textContent = tr("budgets.modal_edit_title");
  document.getElementById("budget-modal-subtitle").textContent = tr("budgets.modal_edit_subtitle");

  renderCategoryPicker(budget.category_ids);
  syncPeriodFields();
  openOverlay("modal-budget");
}

function openDeleteBudgetModal(id) {
  const budget = budgets.find(item => item.id === id);
  if (!budget) return;

  document.getElementById("deleteBudgetId").value = String(id);
  document.getElementById("deleteBudgetName").textContent = budget.name;
  openOverlay("modal-budget-delete");
}

async function loadBudgetsPageData() {
  const [budgetData, categoryData] = await Promise.all([
    apiRequest(BUDGETS_API),
    apiRequest(CATEGORIES_API),
  ]);

  budgets = Array.isArray(budgetData) ? budgetData.map(normalizeBudget) : [];
  expenseCategories = Array.isArray(categoryData)
    ? categoryData
        .map(normalizeCategory)
        .filter(category => category.type === "expense")
        .sort((left, right) => left.name.localeCompare(right.name))
    : [];

  renderBudgets();
}

async function submitBudgetForm(event) {
  event.preventDefault();

  const submitButton = document.getElementById("budgetSubmitBtn");
  const budgetId = document.getElementById("budgetId").value.trim();
  const name = document.getElementById("budgetName").value.trim();
  const desc = document.getElementById("budgetDesc").value.trim();
  const amount_limit = Number(document.getElementById("budgetLimit").value);
  const currency_code = document.getElementById("budgetCurrency").value;
  const period_type = document.getElementById("budgetPeriodType").value;
  const start_date = document.getElementById("budgetStartDate").value;
  const end_date = period_type === "custom"
    ? document.getElementById("budgetEndDate").value
    : start_date;
  const category_ids = getSelectedCategoryIds();

  if (!name) {
    showFeedback(tr("budgets.name_required"));
    document.getElementById("budgetName").focus();
    return;
  }

  if (!Number.isFinite(amount_limit) || amount_limit <= 0) {
    showFeedback(tr("errors.amount_positive"));
    document.getElementById("budgetLimit").focus();
    return;
  }

  if (!start_date) {
    showFeedback(tr("errors.date_required"));
    document.getElementById("budgetStartDate").focus();
    return;
  }

  if (period_type === "custom" && !end_date) {
    showFeedback(tr("budgets.end_date") + " " + tr("common.required"));
    document.getElementById("budgetEndDate").focus();
    return;
  }

  if (!category_ids.length) {
    showFeedback(tr("budgets.select_categories"));
    return;
  }

  const payload = {
    name,
    desc,
    amount_limit,
    currency_code,
    period_type,
    start_date,
    end_date,
    category_ids,
  };

  try {
    if (submitButton) submitButton.disabled = true;

    const saved = budgetId
      ? await apiRequest(`${BUDGETS_API}/${budgetId}`, { method: "PUT", body: JSON.stringify(payload) })
      : await apiRequest(BUDGETS_API, { method: "POST", body: JSON.stringify(payload) });

    const normalized = normalizeBudget(saved);
    const existingIndex = budgets.findIndex(item => item.id === normalized.id);
    if (existingIndex === -1) {
      budgets.unshift(normalized);
    } else {
      budgets[existingIndex] = normalized;
    }

    renderBudgets();
    closeOverlay("modal-budget");
    showFeedback(budgetId ? tr("budgets.updated") : tr("budgets.created"), "success");
  } catch (error) {
    showFeedback(error.message);
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

async function submitBudgetDelete() {
  const button = document.getElementById("budgetDeleteConfirmBtn");
  const budgetId = Number(document.getElementById("deleteBudgetId").value);

  try {
    if (button) button.disabled = true;
    await apiRequest(`${BUDGETS_API}/${budgetId}`, { method: "DELETE" });
    budgets = budgets.filter(item => item.id !== budgetId);
    renderBudgets();
    closeOverlay("modal-budget-delete");
    showFeedback(tr("budgets.deleted"), "success");
  } catch (error) {
    showFeedback(error.message);
  } finally {
    if (button) button.disabled = false;
  }
}

function initFilterTabs() {
  document.querySelectorAll(".filter-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".filter-tab").forEach(button => button.classList.remove("active"));
      tab.classList.add("active");
      activeFilter = tab.dataset.filter || "all";
      renderBudgets();
    });
  });
}

function initSearch() {
  const input = document.getElementById("budgetSearch");
  if (!input) return;
  input.addEventListener("input", event => {
    searchQuery = event.target.value.trim();
    renderBudgets();
  });
}

async function initBudgetsPage() {
  if (budgetsPageInitialized) return;
  budgetsPageInitialized = true;

  initFilterTabs();
  initSearch();

  document.getElementById("btn-open-budget-modal")?.addEventListener("click", openCreateBudgetModal);
  document.getElementById("budgetForm")?.addEventListener("submit", submitBudgetForm);
  document.getElementById("budgetDeleteConfirmBtn")?.addEventListener("click", submitBudgetDelete);
  document.getElementById("budgetPeriodType")?.addEventListener("change", syncPeriodFields);
  document.getElementById("budgetStartDate")?.addEventListener("change", () => {
    const endDateInput = document.getElementById("budgetEndDate");
    const periodType = document.getElementById("budgetPeriodType")?.value;
    if (periodType !== "custom" && endDateInput) {
      endDateInput.value = document.getElementById("budgetStartDate").value;
    }
    syncPeriodFields();
  });

  document.getElementById("budgetCategoryList")?.addEventListener("change", updateCategorySummary);
  document.getElementById("budgetGrid")?.addEventListener("click", event => {
    const editButton = event.target.closest('[data-action="edit"]');
    const deleteButton = event.target.closest('[data-action="delete"]');

    if (editButton) {
      openEditBudgetModal(Number(editButton.dataset.id));
      return;
    }

    if (deleteButton) {
      openDeleteBudgetModal(Number(deleteButton.dataset.id));
    }
  });

  document.querySelectorAll("[data-close]").forEach(button => {
    button.addEventListener("click", () => closeOverlay(button.dataset.close));
  });

  ["modal-budget", "modal-budget-delete"].forEach(closeOnBackdrop);

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      closeOverlay("modal-budget");
      closeOverlay("modal-budget-delete");
    }
  });

  try {
    await loadBudgetsPageData();
  } catch (error) {
    showFeedback(tr("budgets.load_failed", { message: error.message }, `Failed to load budgets: ${error.message}`));
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initBudgetsPage);
} else {
  initBudgetsPage();
}
