const PAGE_SIZE = 7;
const TRANSACTION_TYPES = ["all", "income", "expense", "transfer"];
const UI_LOCALE = window.ledgerI18n?.locale || "en-US";

function tr(key, replacements = {}, fallback = "") {
  return window.ledgerI18n?.t(key, replacements, fallback) || fallback || key;
}

let transactions = [];
let categories = [];
let accounts = [];
let activeFilter = "all";
let searchQuery = "";
let currentPage = 1;
let feedbackTimer = null;

function readJsonScript(id, fallback = []) {
  const element = document.getElementById(id);
  if (!element) return fallback;

  try {
    const parsed = JSON.parse(element.textContent || "null");
    return parsed ?? fallback;
  } catch (_) {
    return fallback;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalizeCategory(category) {
  return {
    id: Number(category?.id),
    name: category?.name ?? tr("common.unnamed_category"),
    desc: category?.desc ?? "",
    emoji: category?.emoji ?? "#",
    type: String(category?.type ?? "expense").toLowerCase(),
    built_in: category?.built_in === true || category?.built_in === 1 || String(category?.built_in).toLowerCase() === "true",
  };
}

function normalizeAccount(account) {
  return {
    id: Number(account?.id),
    name: account?.name ?? tr("common.unnamed_account"),
    emoji: account?.emoji ?? "#",
    status: String(account?.status ?? "active").toLowerCase(),
    currency_code: String(account?.currency_code ?? "UAH").toUpperCase(),
    type: account?.type ?? "",
    subtitle: account?.subtitle ?? "",
    note: account?.note ?? "",
  };
}

function normalizeTransaction(transaction) {
  return {
    id: Number(transaction?.id),
    description: transaction?.description ?? "",
    amount: Number(transaction?.amount ?? 0),
    date: transaction?.date ? String(transaction.date) : "",
    type: String(transaction?.type ?? "expense").toLowerCase(),
    category_id: Number(transaction?.category_id),
    category_name: transaction?.category_name ?? tr("common.unknown_category"),
    category_emoji: transaction?.category_emoji ?? "#",
    account_id: transaction?.account_id === null || transaction?.account_id === undefined || transaction?.account_id === ""
      ? null
      : Number(transaction.account_id),
    account_name: transaction?.account_name ?? "",
    account_emoji: transaction?.account_emoji ?? "",
    currency_code: String(transaction?.currency_code ?? "UAH").toUpperCase(),
  };
}

function parseLocalDateTime(value) {
  if (!value) return null;

  const normalized = String(value).replace(" ", "T");
  const [datePart, timePart = "00:00"] = normalized.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.slice(0, 5).split(":").map(Number);

  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
    return null;
  }

  return new Date(
    year,
    month - 1,
    day,
    Number.isFinite(hour) ? hour : 0,
    Number.isFinite(minute) ? minute : 0,
    0,
    0,
  );
}

function toInputDate(value = new Date()) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function toInputTime(value = new Date()) {
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function formatDateTime(value) {
  const parsed = parseLocalDateTime(value);
  if (!parsed) return tr("common.unknown_date");

  const options = {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };

  if (parsed.getFullYear() !== new Date().getFullYear()) {
    options.year = "numeric";
  }

  return parsed.toLocaleString(UI_LOCALE, options);
}

function formatMoney(amount, currencyCode) {
  const value = Number(amount || 0);
  const abs = Math.abs(value).toLocaleString(UI_LOCALE, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const code = String(currencyCode || "UAH").toUpperCase();

  if (code === "USD") return `$${abs}`;
  if (code === "EUR") return `EUR ${abs}`;
  if (code === "GBP") return `GBP ${abs}`;
  if (code === "UAH") return `UAH ${abs}`;
  return `${abs} ${code}`;
}

function amountDisplay(transaction) {
  const formatted = formatMoney(transaction.amount, transaction.currency_code);
  if (transaction.type === "income") return `+${formatted}`;
  if (transaction.type === "expense") return `-${formatted}`;
  return formatted;
}

function typeMeta(type) {
  if (type === "income") {
    return {
      label: tr("common.types.income"),
      className: "income",
      helper: tr("transactions.type_income_helper"),
    };
  }

  if (type === "transfer") {
    return {
      label: tr("common.types.transfer"),
      className: "transfer",
      helper: tr("transactions.type_transfer_helper"),
    };
  }

  return {
    label: tr("common.types.expense"),
    className: "expense",
    helper: tr("transactions.type_expense_helper"),
  };
}

function buildCurrencyBreakdown(list) {
  if (!list.length) return "--";

  const totals = new Map();
  list.forEach(transaction => {
    const code = transaction.currency_code || "UAH";
    totals.set(code, (totals.get(code) || 0) + Math.abs(Number(transaction.amount || 0)));
  });

  return Array.from(totals.entries())
    .sort((left, right) => left[0].localeCompare(right[0]))
    .map(([code, total]) => formatMoney(total, code))
    .join(" / ");
}

function transactionTitle(transaction) {
  if (transaction.description) return transaction.description;
  return `${typeMeta(transaction.type).label} ${tr("common.in")} ${transaction.category_name}`;
}

function filteredTransactions() {
  const query = searchQuery.toLowerCase();

  return transactions.filter(transaction => {
    const matchesFilter = activeFilter === "all" ? true : transaction.type === activeFilter;
    const haystack = [
      transaction.description,
      transaction.category_name,
      transaction.account_name,
      transaction.currency_code,
      transaction.type,
      formatDateTime(transaction.date),
    ].join(" ").toLowerCase();
    const matchesSearch = haystack.includes(query);
    return matchesFilter && matchesSearch;
  });
}

function syncBodyLock() {
  document.body.style.overflow = document.querySelector(".modal-overlay.open") ? "hidden" : "";
}

function openOverlay(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.add("open");
  syncBodyLock();
}

function closeOverlay(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.remove("open");
  syncBodyLock();
}

function showFeedback(message, type = "error") {
  const feedback = document.getElementById("transactionsFeedback");
  if (!feedback || !message) return;

  feedback.hidden = false;
  feedback.className = `tx-feedback ${type === "success" ? "is-success" : "is-error"}`;
  feedback.textContent = message;

  if (feedbackTimer) {
    clearTimeout(feedbackTimer);
  }

  feedbackTimer = window.setTimeout(() => {
    feedback.hidden = true;
    feedback.textContent = "";
  }, 5000);
}

function updateFilterButtons() {
  document.querySelectorAll("#transactionFilterTabs .filter-tab").forEach(button => {
    button.classList.toggle("active", button.dataset.filter === activeFilter);
  });
}

function updateFilterUrl() {
  const url = new URL(window.location.href);
  if (activeFilter === "all") {
    url.searchParams.delete("filter");
  } else {
    url.searchParams.set("filter", activeFilter);
  }
  history.replaceState(null, "", url);
}

function updateReturnFilterInputs() {
  const current = activeFilter || "all";
  const formInput = document.getElementById("transactionReturnFilter");
  const deleteInput = document.getElementById("deleteTransactionReturnFilter");
  const periodFilterInput = document.getElementById("transactionsPeriodFilter");

  if (formInput) formInput.value = current;
  if (deleteInput) deleteInput.value = current;
  if (periodFilterInput) periodFilterInput.value = current;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function renderSummary() {
  return;
}

function buildTransactionCard(transaction) {
  const meta = typeMeta(transaction.type);
  const accountMarkup = transaction.account_name
    ? `<span class="tx-account">${escapeHtml(transaction.account_name)}</span>`
    : `<span class="tx-account">${escapeHtml(tr("transactions.no_account"))}</span>`;
  const title = transactionTitle(transaction);
  const amountClass = transaction.type === "income"
    ? "pos"
    : transaction.type === "expense"
      ? "neg"
      : "neutral";

  return `
    <article class="tx-row" data-id="${transaction.id}">
      <div class="tx-main">
        <div class="tx-main-icon">${escapeHtml(transaction.category_emoji)}</div>
        <div class="tx-main-body">
          <div class="tx-main-title">${escapeHtml(title)}</div>
          <div class="tx-main-sub">
            <span class="tx-date-mini">${escapeHtml(formatDateTime(transaction.date))}</span>
          </div>
        </div>
      </div>
      <div><span class="tx-status ${meta.className}">${escapeHtml(meta.label)}</span></div>
      <div><span class="tx-category">${escapeHtml(transaction.category_name)}</span></div>
      <div>${accountMarkup}</div>
      <div><span class="tx-currency-badge">${escapeHtml(transaction.currency_code)}</span></div>
      <div class="tx-amount-cell ${amountClass}">
        ${escapeHtml(amountDisplay(transaction))}
      </div>
      <div class="tx-actions">
        <button type="button" class="tx-action-btn" data-action="edit" data-id="${transaction.id}" title="${escapeHtml(tr("transactions.edit_title"))}">
          <svg viewBox="0 0 15 15" fill="none">
            <path d="M10.9 2.2a1.5 1.5 0 112.1 2.1l-7.8 7.8-3 .7.7-3 8-7.6z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round" />
          </svg>
        </button>
        <button type="button" class="tx-action-btn danger" data-action="delete" data-id="${transaction.id}" title="${escapeHtml(tr("transactions.delete_action_title"))}">
          <svg viewBox="0 0 15 15" fill="none">
            <path d="M2.5 4h10M6 2.2h3M5 5.2v6M7.5 5.2v6M10 5.2v6M3.8 4l.6 8c.04.6.54 1 1 1h3.84c.6 0 1.1-.4 1.14-1l.6-8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </article>
  `;
}

function renderPagination(totalItems) {
  const container = document.getElementById("pageBtns");
  const pageInfo = document.getElementById("pageInfo");
  if (!container || !pageInfo) return;

  container.innerHTML = "";

  if (!totalItems) {
    pageInfo.textContent = tr("transactions.no_results");
    return;
  }

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);
  const start = (currentPage - 1) * PAGE_SIZE + 1;
  const end = Math.min(currentPage * PAGE_SIZE, totalItems);
  pageInfo.textContent = tr("transactions.page_range", { start, end, total: totalItems }, `${start}-${end} of ${totalItems}`);

  if (totalPages <= 1) return;

  const addPageButton = (label, page, disabled = false, active = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `page-btn${active ? " active" : ""}`;
    button.textContent = label;
    button.disabled = disabled;
    button.addEventListener("click", () => {
      currentPage = page;
      renderTransactions();
    });
    container.appendChild(button);
  };

  addPageButton("<", currentPage - 1, currentPage === 1, false);

  for (let page = 1; page <= totalPages; page += 1) {
    addPageButton(String(page), page, false, page === currentPage);
  }

  addPageButton(">", currentPage + 1, currentPage === totalPages, false);
}

function renderEmptyState(list) {
  const empty = document.getElementById("transactionEmpty");
  const title = document.getElementById("transactionEmptyTitle");
  const copy = document.getElementById("transactionEmptyCopy");
  const pagination = document.getElementById("transactionPagination");
  if (!empty || !title || !copy) return;

  if (list.length) {
    empty.hidden = true;
    if (pagination) pagination.hidden = false;
    return;
  }

  empty.hidden = false;
  if (pagination) pagination.hidden = true;
  if (!transactions.length) {
    title.textContent = tr("transactions.no_transactions_title");
    copy.textContent = tr("transactions.no_transactions_copy");
    return;
  }

  title.textContent = tr("transactions.no_matching_title");
  copy.textContent = tr("transactions.no_matching_copy");
}

function renderTransactions() {
  const list = filteredTransactions();
  const container = document.getElementById("transactionList");
  const resultsCopy = document.getElementById("resultsCopy");

  if (!container || !resultsCopy) return;

  const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
  if (currentPage > totalPages) {
    currentPage = totalPages;
  }

  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = list.slice(start, start + PAGE_SIZE);

  const filterLabel = activeFilter === "all"
    ? tr("transactions.all_transactions")
    : tr("transactions.type_transactions", { type: typeMeta(activeFilter).label }, `${typeMeta(activeFilter).label} transactions`);
  resultsCopy.textContent = `${filterLabel} (${list.length})`;
  container.innerHTML = pageItems.map(buildTransactionCard).join("");

  renderEmptyState(list);
  renderPagination(list.length);
}

function sortedAccounts() {
  const statusOrder = { active: 0, frozen: 1, closed: 2 };
  return [...accounts].sort((left, right) => {
    const statusDelta = (statusOrder[left.status] ?? 99) - (statusOrder[right.status] ?? 99);
    if (statusDelta !== 0) return statusDelta;
    return left.name.localeCompare(right.name);
  });
}

function categoriesForType(type) {
  return categories
    .filter(category => category.type === type)
    .sort((left, right) => left.name.localeCompare(right.name));
}

function resolveFormType(preferred = "expense") {
  const available = TRANSACTION_TYPES
    .filter(type => type !== "all")
    .filter(type => categoriesForType(type).length > 0);

  if (available.includes(preferred)) return preferred;
  return available[0] || "expense";
}

function renderAccountOptions(selectedId = "") {
  const select = document.getElementById("transactionAccount");
  if (!select) return;

  const normalizedSelectedId = selectedId === null || selectedId === undefined || selectedId === ""
    ? ""
    : String(selectedId);
  const options = [
    `<option value="">${escapeHtml(tr("transactions.no_account_selected"))}</option>`,
    ...sortedAccounts().map(account => {
      const statusLabel = account.status !== "active" ? ` - ${tr(`common.status.${account.status}`, {}, account.status)}` : "";
      return `<option value="${account.id}">${escapeHtml(account.emoji)} ${escapeHtml(account.name)} - ${escapeHtml(account.currency_code)}${escapeHtml(statusLabel)}</option>`;
    }),
  ];

  select.innerHTML = options.join("");
  select.value = normalizedSelectedId;
}

function renderCategoryOptions(type, selectedId = "") {
  const select = document.getElementById("transactionCategory");
  const hint = document.getElementById("transactionCategoryHint");
  const submit = document.getElementById("transactionSubmitBtn");
  if (!select || !hint || !submit) return;

  const available = categoriesForType(type);
  const normalizedSelectedId = selectedId === null || selectedId === undefined || selectedId === ""
    ? ""
    : String(selectedId);

  if (!available.length) {
    const typeLabel = typeMeta(type).label.toLowerCase();
    select.innerHTML = `<option value="">${escapeHtml(tr("transactions.no_categories_for_type", { type: typeLabel }, `No categories available for ${typeLabel}`))}</option>`;
    select.disabled = true;
    submit.disabled = true;
    hint.classList.add("is-error");
    hint.textContent = tr("transactions.create_category_before_save", { type: typeLabel }, `Create at least one ${typeLabel} category before saving this transaction.`);
    return;
  }

  select.disabled = false;
  submit.disabled = false;
  hint.classList.remove("is-error");
  hint.textContent = tr("transactions.category_hint");
  select.innerHTML = available
    .map(category => `<option value="${category.id}">${escapeHtml(category.emoji)} ${escapeHtml(category.name)}</option>`)
    .join("");

  if (normalizedSelectedId && available.some(category => String(category.id) === normalizedSelectedId)) {
    select.value = normalizedSelectedId;
  } else {
    select.value = String(available[0].id);
  }
}

function syncTypeOptions(preferredType) {
  const typeSelect = document.getElementById("transactionType");
  if (!typeSelect) return;

  [...typeSelect.options].forEach(option => {
    option.disabled = categoriesForType(option.value).length === 0;
  });

  const nextType = resolveFormType(preferredType || typeSelect.value);
  typeSelect.value = nextType;

  const hint = document.getElementById("transactionTypeHint");
  if (hint) {
    hint.textContent = typeMeta(nextType).helper;
  }

  renderCategoryOptions(nextType);
}

function syncCurrencyFromAccount() {
  const accountSelect = document.getElementById("transactionAccount");
  const currencyInput = document.getElementById("transactionCurrency");
  if (!accountSelect || !currencyInput) return;

  const account = accounts.find(item => String(item.id) === accountSelect.value);
  if (account) {
    currencyInput.value = account.currency_code;
  } else if (!currencyInput.value.trim()) {
    currencyInput.value = "UAH";
  }
}

function resetTransactionForm() {
  const form = document.getElementById("transactionForm");
  if (form) form.reset();

  setText("transactionModalTitle", tr("transactions.modal_new_title_text"));
  setText("transactionModalSubtitle", tr("transactions.modal_new_subtitle"));
  setText("transactionSubmitBtn", tr("transactions.create_submit"));

  const now = new Date();
  document.getElementById("transactionFormAction").value = "create";
  document.getElementById("transactionId").value = "";
  document.getElementById("transactionDescription").value = "";
  document.getElementById("transactionAmount").value = "";
  document.getElementById("transactionDate").value = toInputDate(now);
  document.getElementById("transactionTime").value = toInputTime(now);

  renderAccountOptions("");
  const defaultAccount = sortedAccounts().find(account => account.status !== "closed");
  if (defaultAccount) {
    document.getElementById("transactionAccount").value = String(defaultAccount.id);
  }

  syncTypeOptions("expense");
  syncCurrencyFromAccount();
}

function openCreateTransactionModal() {
  resetTransactionForm();
  openOverlay("transactionModal");
}

function openEditTransactionModal(id) {
  const transaction = transactions.find(item => item.id === id);
  if (!transaction) return;

  const parsedDate = parseLocalDateTime(transaction.date) || new Date();
  const type = resolveFormType(transaction.type);

  setText("transactionModalTitle", tr("transactions.modal_edit_title"));
  setText("transactionModalSubtitle", tr("transactions.modal_edit_subtitle"));
  setText("transactionSubmitBtn", tr("common.buttons.save_changes"));

  document.getElementById("transactionFormAction").value = "update";
  document.getElementById("transactionId").value = String(transaction.id);
  document.getElementById("transactionDescription").value = transaction.description;
  document.getElementById("transactionAmount").value = String(transaction.amount);
  document.getElementById("transactionDate").value = toInputDate(parsedDate);
  document.getElementById("transactionTime").value = toInputTime(parsedDate);

  renderAccountOptions(transaction.account_id ?? "");
  syncTypeOptions(type);
  document.getElementById("transactionType").value = type;
  renderCategoryOptions(type, transaction.category_id);
  document.getElementById("transactionCurrency").value = transaction.currency_code;

  openOverlay("transactionModal");
}

function openDeleteTransactionModal(id) {
  const transaction = transactions.find(item => item.id === id);
  if (!transaction) return;

  document.getElementById("deleteTransactionId").value = String(id);
  document.getElementById("deleteTransactionName").textContent = transactionTitle(transaction);
  openOverlay("transactionDeleteModal");
}

function setActiveFilter(filter, updateUrl = true) {
  activeFilter = TRANSACTION_TYPES.includes(filter) ? filter : "all";
  currentPage = 1;
  updateFilterButtons();
  updateReturnFilterInputs();
  if (updateUrl) {
    updateFilterUrl();
  }
  renderTransactions();
}

function consumeFeedbackFromPage() {
  const page = document.getElementById("transactionsPage");
  if (!page) return;

  const status = page.dataset.feedbackStatus;
  const message = page.dataset.feedbackMessage;
  if (!status || !message) return;

  showFeedback(message, status === "success" ? "success" : "error");

  const url = new URL(window.location.href);
  url.searchParams.delete("status");
  url.searchParams.delete("message");
  history.replaceState(null, "", url);
}

function initPageDate() {
  const pageDate = document.getElementById("pageDate");
  if (!pageDate) return;

  pageDate.textContent = new Date().toLocaleDateString(UI_LOCALE, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function initTransactionsPage() {
  const page = document.getElementById("transactionsPage");
  if (!page) return;

  categories = readJsonScript("transaction-categories-data").map(normalizeCategory);
  accounts = readJsonScript("transaction-accounts-data").map(normalizeAccount);
  transactions = readJsonScript("transactions-data").map(normalizeTransaction);

  initPageDate();
  updateReturnFilterInputs();

  const initialFilter = TRANSACTION_TYPES.includes(page.dataset.initialFilter) ? page.dataset.initialFilter : "all";

  document.getElementById("openTransactionModal")?.addEventListener("click", openCreateTransactionModal);

  document.getElementById("transactionSearch")?.addEventListener("input", event => {
    searchQuery = event.target.value.trim();
    currentPage = 1;
    renderTransactions();
  });

  document.querySelectorAll("#transactionFilterTabs .filter-tab").forEach(button => {
    button.addEventListener("click", () => setActiveFilter(button.dataset.filter || "all"));
  });

  document.getElementById("transactionList")?.addEventListener("click", event => {
    const editButton = event.target.closest('[data-action="edit"]');
    const deleteButton = event.target.closest('[data-action="delete"]');

    if (editButton) {
      openEditTransactionModal(Number(editButton.dataset.id));
      return;
    }

    if (deleteButton) {
      openDeleteTransactionModal(Number(deleteButton.dataset.id));
    }
  });

  document.getElementById("transactionType")?.addEventListener("change", event => {
    syncTypeOptions(event.target.value);
  });

  document.getElementById("transactionAccount")?.addEventListener("change", () => {
    syncCurrencyFromAccount();
  });

  document.getElementById("transactionCurrency")?.addEventListener("input", event => {
    event.target.value = event.target.value.toUpperCase().slice(0, 3);
  });

  document.getElementById("transactionForm")?.addEventListener("submit", event => {
    const categorySelect = document.getElementById("transactionCategory");
    const currencyInput = document.getElementById("transactionCurrency");

    updateReturnFilterInputs();

    if (!categorySelect || categorySelect.disabled || !categorySelect.value) {
      event.preventDefault();
      showFeedback(tr("transactions.category_hint"));
      return;
    }

    currencyInput.value = currencyInput.value.trim().toUpperCase();
    if (!/^[A-Z]{3}$/.test(currencyInput.value)) {
      event.preventDefault();
      showFeedback(tr("errors.currency_code"));
      currencyInput.focus();
    }
  });

  document.getElementById("transactionDeleteForm")?.addEventListener("submit", () => {
    updateReturnFilterInputs();
  });

  document.querySelectorAll("[data-close]").forEach(button => {
    button.addEventListener("click", () => closeOverlay(button.dataset.close));
  });

  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", event => {
      if (event.target === overlay) {
        closeOverlay(overlay.id);
      }
    });
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      closeOverlay("transactionModal");
      closeOverlay("transactionDeleteModal");
    }
  });

  consumeFeedbackFromPage();
  setActiveFilter(initialFilter, false);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTransactionsPage);
} else {
  initTransactionsPage();
}
