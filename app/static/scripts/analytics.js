const ANALYTICS_PERIODS = [7, 30, 90, 180];
const ANALYTICS_COLORS = [
  "#3a7a50",
  "#b84040",
  "#4a72b0",
  "#c28c2c",
  "#7a5ccf",
  "#2a8a8a",
  "#a06030",
  "#8a4d5f",
];

const DEFAULT_WIDGET_SLOTS = {
  "slot-1": null,
  "slot-2": null,
  "slot-3": null,
  "slot-4": null,
};

let analyticsTransactions = [];
let analyticsCategories = [];
let analyticsAccounts = [];
let analyticsBudgets = [];
let currentCurrency = "UAH";
let currentPeriod = 30;
let donutMode = "expense";
let widgetSlots = { ...DEFAULT_WIDGET_SLOTS };
let widgetModalSlotId = null;
let rangeAnchorDate = new Date();

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

function normalizeTransaction(transaction) {
  return {
    id: Number(transaction?.id),
    description: transaction?.description ?? "",
    amount: Number(transaction?.amount ?? 0),
    date: transaction?.date ? String(transaction.date) : "",
    type: String(transaction?.type ?? "expense").toLowerCase(),
    category_id: Number(transaction?.category_id),
    category_name: transaction?.category_name ?? "Unknown category",
    category_emoji: transaction?.category_emoji ?? "#",
    account_id: transaction?.account_id === null || transaction?.account_id === undefined || transaction?.account_id === ""
      ? null
      : Number(transaction.account_id),
    account_name: transaction?.account_name ?? "",
    account_emoji: transaction?.account_emoji ?? "",
    currency_code: String(transaction?.currency_code ?? "UAH").toUpperCase(),
  };
}

function normalizeCategory(category) {
  return {
    id: Number(category?.id),
    name: category?.name ?? "Unnamed category",
    emoji: category?.emoji ?? "#",
    type: String(category?.type ?? "expense").toLowerCase(),
  };
}

function normalizeAccount(account) {
  return {
    id: Number(account?.id),
    name: account?.name ?? "Unnamed account",
    balance: Number(account?.balance ?? 0),
    initial_balance: Number(account?.initial_balance ?? account?.balance ?? 0),
    transactions_delta: Number(account?.transactions_delta ?? 0),
    status: String(account?.status ?? "active").toLowerCase(),
    currency_code: String(account?.currency_code ?? "UAH").toUpperCase(),
    emoji: account?.emoji ?? "#",
    subtitle: account?.subtitle ?? "",
    note: account?.note ?? "",
    type: account?.type ?? "",
  };
}

function normalizeBudget(budget) {
  return {
    id: Number(budget?.id),
    name: budget?.name ?? "Untitled budget",
    desc: budget?.desc ?? "",
    amount_limit: Number(budget?.amount_limit ?? 0),
    currency_code: String(budget?.currency_code ?? "UAH").toUpperCase(),
    spent: Number(budget?.spent ?? 0),
    remaining: Number(budget?.remaining ?? 0),
    percent: Number(budget?.percent ?? 0),
    status: String(budget?.status ?? "inactive").toLowerCase(),
    is_active: budget?.is_active === true || budget?.is_active === 1 || String(budget?.is_active).toLowerCase() === "true",
    conversion_error: budget?.conversion_error ?? "",
    icon: budget?.icon ?? "#",
    categories: Array.isArray(budget?.categories) ? budget.categories : [],
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

function startOfDay(value) {
  const next = new Date(value);
  next.setHours(0, 0, 0, 0);
  return next;
}

function endOfDay(value) {
  const next = new Date(value);
  next.setHours(23, 59, 59, 999);
  return next;
}

function shiftDays(value, days) {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
}

function dateKey(value) {
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, "0"),
    String(value.getDate()).padStart(2, "0"),
  ].join("-");
}

function formatShortDate(value) {
  return value.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatRangeLabel(start, end) {
  const sameYear = start.getFullYear() === end.getFullYear();
  const sameDay = dateKey(start) === dateKey(end);

  if (sameDay) {
    return start.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  const startOptions = sameYear
    ? { month: "short", day: "numeric" }
    : { month: "short", day: "numeric", year: "numeric" };

  return `${start.toLocaleDateString("en-US", startOptions)} - ${end.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })}`;
}

function formatMoney(amount, currencyCode) {
  const code = String(currencyCode || "UAH").toUpperCase();

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: code,
      minimumFractionDigits: Math.abs(amount % 1) > 0 ? 2 : 0,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch (_) {
    const numeric = Number(amount || 0).toLocaleString("en-US", {
      minimumFractionDigits: Math.abs(amount % 1) > 0 ? 2 : 0,
      maximumFractionDigits: 2,
    });
    return `${numeric} ${code}`;
  }
}

function formatSignedMoney(amount, currencyCode) {
  const value = Number(amount || 0);
  const prefix = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${prefix}${formatMoney(Math.abs(value), currencyCode)}`;
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(0)}%`;
}

function storageKey() {
  const page = document.getElementById("analyticsPage");
  const userId = page?.dataset.userId || "guest";
  return `ledger.analytics.widgets.v1.${userId}`;
}

function loadWidgetSlots() {
  try {
    const raw = window.localStorage.getItem(storageKey());
    if (!raw) return { ...DEFAULT_WIDGET_SLOTS };

    const parsed = JSON.parse(raw);
    const nextState = { ...DEFAULT_WIDGET_SLOTS };
    Object.keys(nextState).forEach(slotId => {
      const value = parsed?.[slotId];
      nextState[slotId] = typeof value === "string" ? value : null;
    });
    return nextState;
  } catch (_) {
    return { ...DEFAULT_WIDGET_SLOTS };
  }
}

function saveWidgetSlots() {
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify(widgetSlots));
  } catch (_) {
    // Ignore localStorage failures and keep the current session state in memory.
  }
}

function findLatestTransactionDate() {
  const dates = analyticsTransactions
    .map(transaction => parseLocalDateTime(transaction.date))
    .filter(Boolean)
    .sort((left, right) => left - right);

  if (!dates.length) {
    return startOfDay(new Date());
  }

  return startOfDay(dates[dates.length - 1]);
}

function currentRange() {
  const end = endOfDay(rangeAnchorDate);
  const start = startOfDay(shiftDays(rangeAnchorDate, -(currentPeriod - 1)));
  return { start, end };
}

function transactionsInRange() {
  const { start, end } = currentRange();
  return analyticsTransactions.filter(transaction => {
    if (transaction.currency_code !== currentCurrency) return false;
    const parsed = parseLocalDateTime(transaction.date);
    if (!parsed) return false;
    return parsed >= start && parsed <= end;
  });
}

function budgetsForCurrency() {
  return analyticsBudgets.filter(budget => budget.currency_code === currentCurrency);
}

function accountsForCurrency() {
  return analyticsAccounts.filter(account => account.currency_code === currentCurrency);
}

function summaryForRange() {
  const list = transactionsInRange();
  const income = list
    .filter(transaction => transaction.type === "income")
    .reduce((sum, transaction) => sum + transaction.amount, 0);
  const expense = list
    .filter(transaction => transaction.type === "expense")
    .reduce((sum, transaction) => sum + transaction.amount, 0);

  return {
    count: list.length,
    income,
    expense,
    net: income - expense,
  };
}

function buildDailyBuckets(list) {
  const { start } = currentRange();
  const totalDays = currentPeriod;
  const bucketMap = new Map();
  const buckets = [];

  for (let index = 0; index < totalDays; index += 1) {
    const day = startOfDay(shiftDays(start, index));
    const key = dateKey(day);
    const bucket = {
      key,
      date: day,
      shortLabel: formatShortDate(day),
      income: 0,
      expense: 0,
      net: 0,
      count: 0,
    };
    bucketMap.set(key, bucket);
    buckets.push(bucket);
  }

  list.forEach(transaction => {
    const parsed = parseLocalDateTime(transaction.date);
    if (!parsed) return;

    const key = dateKey(parsed);
    const bucket = bucketMap.get(key);
    if (!bucket) return;

    bucket.count += 1;
    if (transaction.type === "income") {
      bucket.income += transaction.amount;
      bucket.net += transaction.amount;
    } else if (transaction.type === "expense") {
      bucket.expense += transaction.amount;
      bucket.net -= transaction.amount;
    }
  });

  return buckets;
}

function compressBuckets(buckets) {
  const groupSize = currentPeriod <= 14 ? 1 : currentPeriod <= 45 ? 5 : currentPeriod <= 120 ? 10 : 15;
  if (groupSize === 1) return buckets;

  const groups = [];
  for (let index = 0; index < buckets.length; index += groupSize) {
    const slice = buckets.slice(index, index + groupSize);
    const first = slice[0];
    const last = slice[slice.length - 1];
    groups.push({
      shortLabel: slice.length === 1 ? first.shortLabel : `${formatShortDate(first.date)} - ${formatShortDate(last.date)}`,
      income: slice.reduce((sum, bucket) => sum + bucket.income, 0),
      expense: slice.reduce((sum, bucket) => sum + bucket.expense, 0),
      net: slice.reduce((sum, bucket) => sum + bucket.net, 0),
      count: slice.reduce((sum, bucket) => sum + bucket.count, 0),
    });
  }

  return groups;
}

function aggregateCategories(list, type) {
  const totals = new Map();
  list
    .filter(transaction => transaction.type === type)
    .forEach(transaction => {
      const key = `${transaction.category_name}:::${transaction.category_emoji}`;
      const current = totals.get(key) || {
        name: transaction.category_name,
        emoji: transaction.category_emoji,
        amount: 0,
      };
      current.amount += transaction.amount;
      totals.set(key, current);
    });

  const items = Array.from(totals.values()).sort((left, right) => right.amount - left.amount);
  if (items.length <= 6) return items;

  const head = items.slice(0, 5);
  const other = items.slice(5).reduce((sum, item) => sum + item.amount, 0);
  head.push({ name: "Other", emoji: "#", amount: other });
  return head;
}

function chooseTickIndexes(count, maxTicks = 6) {
  if (count <= maxTicks) {
    return Array.from({ length: count }, (_, index) => index);
  }

  const step = Math.ceil((count - 1) / (maxTicks - 1));
  const indexes = [];
  for (let index = 0; index < count; index += step) {
    indexes.push(index);
  }
  if (indexes[indexes.length - 1] !== count - 1) {
    indexes[indexes.length - 1] = count - 1;
  }
  return [...new Set(indexes)];
}

function createEmptyMarkup(message) {
  return `<div class="widget-empty">${escapeHtml(message)}</div>`;
}

function linePath(points) {
  if (!points.length) return "";
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
}

function areaPath(points, baselineY) {
  if (!points.length) return "";
  const lines = linePath(points);
  const last = points[points.length - 1];
  const first = points[0];
  return `${lines} L ${last.x.toFixed(2)} ${baselineY.toFixed(2)} L ${first.x.toFixed(2)} ${baselineY.toFixed(2)} Z`;
}

function renderLineChartSvg({ labels, series, positiveOnly = false, ySuffix = "" }) {
  if (!labels.length || !series.length) {
    return createEmptyMarkup("No values in the selected range yet.");
  }

  const width = 720;
  const height = 280;
  const margins = { top: 18, right: 12, bottom: 32, left: 48 };
  const plotWidth = width - margins.left - margins.right;
  const plotHeight = height - margins.top - margins.bottom;
  const values = series.flatMap(item => item.values);
  let minValue = positiveOnly ? 0 : Math.min(...values, 0);
  let maxValue = Math.max(...values, 0);

  if (minValue === maxValue) {
    if (maxValue === 0) {
      maxValue = 1;
    } else {
      minValue = positiveOnly ? 0 : minValue * 0.8;
      maxValue *= 1.2;
    }
  }

  const padding = (maxValue - minValue) * 0.08;
  if (!positiveOnly) {
    minValue -= padding;
  }
  maxValue += padding;

  const xAt = index => {
    if (labels.length === 1) return margins.left + plotWidth / 2;
    return margins.left + (plotWidth / (labels.length - 1)) * index;
  };
  const yAt = value => margins.top + plotHeight - ((value - minValue) / (maxValue - minValue)) * plotHeight;
  const baselineValue = positiveOnly || minValue > 0 ? minValue : 0;
  const baselineY = yAt(baselineValue);

  const gridLines = 5;
  const gridMarkup = Array.from({ length: gridLines }, (_, index) => {
    const ratio = index / (gridLines - 1);
    const value = maxValue - (maxValue - minValue) * ratio;
    const y = margins.top + plotHeight * ratio;
    const label = `${Number(value).toFixed(ySuffix ? 0 : 0)}${ySuffix}`;
    return `
      <line x1="${margins.left}" y1="${y.toFixed(2)}" x2="${width - margins.right}" y2="${y.toFixed(2)}" stroke="#e0d8c8" stroke-width="1" />
      <text x="${margins.left - 10}" y="${(y + 4).toFixed(2)}" text-anchor="end" fill="#9a9080" font-size="11" font-family="Epilogue">${escapeHtml(label)}</text>
    `;
  }).join("");

  const tickIndexes = chooseTickIndexes(labels.length);
  const tickMarkup = tickIndexes.map(index => {
    const x = xAt(index);
    return `
      <text x="${x.toFixed(2)}" y="${height - 8}" text-anchor="middle" fill="#9a9080" font-size="11" font-family="Epilogue">${escapeHtml(labels[index])}</text>
    `;
  }).join("");

  const seriesMarkup = series.map(item => {
    const points = item.values.map((value, index) => ({ x: xAt(index), y: yAt(value) }));
    const fillMarkup = item.fillColor
      ? `<path d="${areaPath(points, baselineY)}" fill="${item.fillColor}" opacity="1"></path>`
      : "";
    const pointMarkup = labels.length <= 30
      ? points.map(point => `<circle cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" r="3.5" fill="${item.color}" stroke="#fdfaf4" stroke-width="2"></circle>`).join("")
      : "";

    return `
      ${fillMarkup}
      <path d="${linePath(points)}" fill="none" stroke="${item.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></path>
      ${pointMarkup}
    `;
  }).join("");

  return `
    <div class="chart-shell">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Analytics chart">
        ${gridMarkup}
        <line x1="${margins.left}" y1="${baselineY.toFixed(2)}" x2="${width - margins.right}" y2="${baselineY.toFixed(2)}" stroke="#cabfab" stroke-width="1.2" />
        ${seriesMarkup}
        ${tickMarkup}
      </svg>
    </div>
  `;
}

function renderBarChartSvg({ labels, series, ySuffix = "" }) {
  if (!labels.length || !series.length) {
    return createEmptyMarkup("No values in the selected range yet.");
  }

  const width = 720;
  const height = 280;
  const margins = { top: 18, right: 12, bottom: 32, left: 48 };
  const plotWidth = width - margins.left - margins.right;
  const plotHeight = height - margins.top - margins.bottom;
  const maxValue = Math.max(...series.flatMap(item => item.values), 0);

  if (maxValue <= 0) {
    return createEmptyMarkup("No values in the selected range yet.");
  }

  const yAt = value => margins.top + plotHeight - (value / maxValue) * plotHeight;
  const gridLines = 5;
  const gridMarkup = Array.from({ length: gridLines }, (_, index) => {
    const ratio = index / (gridLines - 1);
    const value = maxValue - maxValue * ratio;
    const y = margins.top + plotHeight * ratio;
    return `
      <line x1="${margins.left}" y1="${y.toFixed(2)}" x2="${width - margins.right}" y2="${y.toFixed(2)}" stroke="#e0d8c8" stroke-width="1" />
      <text x="${margins.left - 10}" y="${(y + 4).toFixed(2)}" text-anchor="end" fill="#9a9080" font-size="11" font-family="Epilogue">${escapeHtml(`${Number(value).toFixed(0)}${ySuffix}`)}</text>
    `;
  }).join("");

  const groupWidth = plotWidth / Math.max(labels.length, 1);
  const barGap = 6;
  const barWidth = Math.max(6, Math.min(22, (groupWidth * 0.72 - barGap * (series.length - 1)) / series.length));
  const tickIndexes = chooseTickIndexes(labels.length);

  const barsMarkup = labels.map((label, labelIndex) => {
    const totalBarWidth = barWidth * series.length + barGap * Math.max(series.length - 1, 0);
    const groupLeft = margins.left + labelIndex * groupWidth + (groupWidth - totalBarWidth) / 2;

    const rects = series.map((item, seriesIndex) => {
      const value = item.values[labelIndex] || 0;
      const x = groupLeft + seriesIndex * (barWidth + barGap);
      const y = yAt(value);
      const heightValue = Math.max(0, margins.top + plotHeight - y);
      return `
        <rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${barWidth.toFixed(2)}" height="${heightValue.toFixed(2)}" rx="6" fill="${item.color}"></rect>
      `;
    }).join("");

    return rects;
  }).join("");

  const tickMarkup = tickIndexes.map(index => {
    const x = margins.left + index * groupWidth + groupWidth / 2;
    return `
      <text x="${x.toFixed(2)}" y="${height - 8}" text-anchor="middle" fill="#9a9080" font-size="11" font-family="Epilogue">${escapeHtml(labels[index])}</text>
    `;
  }).join("");

  return `
    <div class="chart-shell">
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Analytics bar chart">
        ${gridMarkup}
        ${barsMarkup}
        ${tickMarkup}
      </svg>
    </div>
  `;
}

function createWidgetShell({ title, subtitle, chips = [], content, removable = false }) {
  const chipsMarkup = chips
    .map(chip => `<span class="widget-chip">${escapeHtml(chip)}</span>`)
    .join("");
  const removeMarkup = removable
    ? `
      <div class="widget-actions">
        <button class="widget-action-btn danger" type="button" data-action="remove-widget" aria-label="Remove widget">
          <svg viewBox="0 0 15 15" fill="none">
            <path d="M2.5 4h10M6 2.2h3M5 5.2v6M7.5 5.2v6M10 5.2v6M3.8 4l.6 8c.04.6.54 1 1 1h3.84c.6 0 1.1-.4 1.14-1l.6-8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    `
    : "";

  return `
    <section class="widget-panel">
      <div class="widget-head">
        <div class="widget-head-main">
          <div class="widget-title">${escapeHtml(title)}</div>
          <div class="widget-subtitle">${escapeHtml(subtitle)}</div>
        </div>
        <div class="widget-meta">
          ${chipsMarkup}
          ${removeMarkup}
        </div>
      </div>
      <div class="widget-body">
        ${content}
      </div>
    </section>
  `;
}

function renderStats() {
  const container = document.getElementById("analyticsStats");
  if (!container) return;

  const summary = summaryForRange();
  const budgetsCount = budgetsForCurrency().filter(budget => budget.is_active).length;
  const accountsCount = accountsForCurrency().length;

  container.innerHTML = `
    <div class="card neutral">
      <div class="card-label">Records</div>
      <div class="card-value">${summary.count}</div>
      <div class="card-sub">${currentPeriod} day range in ${escapeHtml(currentCurrency)}</div>
    </div>
    <div class="card green">
      <div class="card-label">Income</div>
      <div class="card-value">${escapeHtml(formatMoney(summary.income, currentCurrency))}</div>
      <div class="card-sub">Posted inflows in the selected period</div>
    </div>
    <div class="card red">
      <div class="card-label">Expenses</div>
      <div class="card-value">${escapeHtml(formatMoney(summary.expense, currentCurrency))}</div>
      <div class="card-sub">Tracked outflows in the selected period</div>
    </div>
    <div class="card ${summary.net >= 0 ? "neutral" : "red"}">
      <div class="card-label">Net Result</div>
      <div class="card-value">${escapeHtml(formatSignedMoney(summary.net, currentCurrency))}</div>
      <div class="card-sub">${accountsCount} accounts, ${budgetsCount} active budgets</div>
    </div>
  `;
}

function renderRangeChip() {
  const chip = document.getElementById("analyticsRangeLabel");
  if (!chip) return;

  const { start, end } = currentRange();
  chip.textContent = formatRangeLabel(start, end);
}

function renderCashflowWidget() {
  const host = document.getElementById("cashflowWidget");
  if (!host) return;

  const buckets = buildDailyBuckets(transactionsInRange());
  const summary = summaryForRange();
  const chartMarkup = renderLineChartSvg({
    labels: buckets.map(bucket => bucket.shortLabel),
    series: [
      {
        color: "#3a7a50",
        values: buckets.map(bucket => bucket.income),
      },
      {
        color: "#b84040",
        values: buckets.map(bucket => bucket.expense),
      },
    ],
    positiveOnly: true,
  });

  const content = `
    <div class="widget-summary">
      <div class="summary-pill">
        <span class="summary-pill-label">Income</span>
        <span class="summary-pill-value pos">${escapeHtml(formatMoney(summary.income, currentCurrency))}</span>
      </div>
      <div class="summary-pill">
        <span class="summary-pill-label">Expenses</span>
        <span class="summary-pill-value neg">${escapeHtml(formatMoney(summary.expense, currentCurrency))}</span>
      </div>
      <div class="summary-pill">
        <span class="summary-pill-label">Net</span>
        <span class="summary-pill-value ${summary.net >= 0 ? "pos" : "neg"}">${escapeHtml(formatSignedMoney(summary.net, currentCurrency))}</span>
      </div>
    </div>
    ${chartMarkup}
    <div class="chart-legend">
      <span class="chart-legend-item"><span class="legend-swatch" style="background:#3a7a50"></span>Income</span>
      <span class="chart-legend-item"><span class="legend-swatch" style="background:#b84040"></span>Expenses</span>
    </div>
  `;

  host.innerHTML = createWidgetShell({
    title: "Cash Flow Trend",
    subtitle: `Daily income and expense movement for ${currentCurrency}.`,
    chips: ["Line", currentCurrency],
    content,
  });
}

function renderCategoryWidget() {
  const host = document.getElementById("categoryWidget");
  if (!host) return;

  const items = aggregateCategories(transactionsInRange(), donutMode);
  const total = items.reduce((sum, item) => sum + item.amount, 0);

  const donutMarkup = !items.length
    ? createEmptyMarkup(`No ${donutMode} data in ${currentCurrency} for the selected period.`)
    : (() => {
      let progress = 0;
      const segments = items.map((item, index) => {
        const portion = total > 0 ? (item.amount / total) * 100 : 0;
        const start = progress;
        progress += portion;
        return `${ANALYTICS_COLORS[index % ANALYTICS_COLORS.length]} ${start.toFixed(2)}% ${progress.toFixed(2)}%`;
      }).join(", ");

      const legendItems = items.map((item, index) => {
        const pct = total > 0 ? (item.amount / total) * 100 : 0;
        return `
          <li class="donut-legend-item">
            <span class="donut-legend-dot" style="background:${ANALYTICS_COLORS[index % ANALYTICS_COLORS.length]}"></span>
            <div class="donut-legend-meta">
              <div class="donut-legend-name">${escapeHtml(`${item.emoji} ${item.name}`)}</div>
              <div class="donut-legend-sub">${escapeHtml(formatPercent(pct))} of ${escapeHtml(currentCurrency)}</div>
            </div>
            <div class="donut-legend-value">${escapeHtml(formatMoney(item.amount, currentCurrency))}</div>
          </li>
        `;
      }).join("");

      return `
        <div class="donut-layout">
          <div class="donut-ring-wrap">
            <div class="donut-ring" style="background: conic-gradient(${segments});">
              <div class="donut-center">
                <div class="donut-center-value">${escapeHtml(formatMoney(total, currentCurrency))}</div>
                <div class="donut-center-label">${escapeHtml(donutMode === "income" ? "Income total" : "Expense total")}</div>
              </div>
            </div>
          </div>
          <ul class="donut-legend">${legendItems}</ul>
        </div>
      `;
    })();

  const content = `
    <div class="donut-tabs">
      <button class="donut-tab ${donutMode === "expense" ? "active" : ""}" type="button" data-action="set-donut-mode" data-mode="expense">Expenses</button>
      <button class="donut-tab ${donutMode === "income" ? "active" : ""}" type="button" data-action="set-donut-mode" data-mode="income">Income</button>
    </div>
    ${donutMarkup}
  `;

  host.innerHTML = createWidgetShell({
    title: "Category Breakdown",
    subtitle: `Largest ${donutMode} groups built from recorded transactions only.`,
    chips: ["Donut", currentCurrency],
    content,
  });
}

function renderBudgetWidget() {
  const host = document.getElementById("budgetWidget");
  if (!host) return;

  const budgets = budgetsForCurrency()
    .sort((left, right) => right.percent - left.percent)
    .slice(0, 6);

  const content = !budgets.length
    ? createEmptyMarkup(`No budgets found in ${currentCurrency}.`)
    : `
      <div class="budget-list">
        ${budgets.map(budget => {
          const fillClass = budget.percent >= 100 ? "exceeded" : budget.percent >= 80 ? "warning" : "good";
          const categoryNames = budget.categories.map(category => category.name).join(", ") || "No categories";
          const errorNote = budget.conversion_error ? ` • ${budget.conversion_error}` : "";
          return `
            <div class="budget-row">
              <div class="budget-row-top">
                <div class="budget-row-label">
                  <span class="budget-icon">${escapeHtml(budget.icon)}</span>
                  <div>
                    <div class="budget-name">${escapeHtml(budget.name)}</div>
                    <div class="budget-sub">${escapeHtml(categoryNames)}${escapeHtml(errorNote)}</div>
                  </div>
                </div>
                <div class="budget-value">${escapeHtml(formatPercent(budget.percent))}</div>
              </div>
              <div class="budget-track">
                <div class="budget-fill ${fillClass}" style="width:${Math.min(Math.max(budget.percent, 0), 100)}%"></div>
              </div>
              <div class="budget-sub">
                ${escapeHtml(formatMoney(budget.spent, budget.currency_code))} of ${escapeHtml(formatMoney(budget.amount_limit, budget.currency_code))}
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

  host.innerHTML = createWidgetShell({
    title: "Budget Utilization",
    subtitle: "Current usage and thresholds for budgets in the selected currency.",
    chips: ["Budget", currentCurrency],
    content,
  });
}

function renderAccountsBalanceWidget() {
  const accounts = accountsForCurrency()
    .slice()
    .sort((left, right) => Math.abs(right.balance) - Math.abs(left.balance))
    .slice(0, 6);
  const maxValue = Math.max(...accounts.map(account => Math.abs(account.balance)), 0);

  if (!accounts.length) {
    return createWidgetShell({
      title: "Account Balances",
      subtitle: `Balances across ${currentCurrency} accounts.`,
      chips: ["Accounts", currentCurrency],
      content: createEmptyMarkup(`No accounts found in ${currentCurrency}.`),
      removable: true,
    });
  }

  const content = `
    <div class="bar-list">
      ${accounts.map(account => {
        const width = maxValue > 0 ? (Math.abs(account.balance) / maxValue) * 100 : 0;
        const fillClass = account.balance >= 0 ? "positive" : "negative";
        const subtitle = account.subtitle || account.status;
        return `
          <div class="bar-row">
            <div class="bar-row-top">
              <div class="bar-row-label">
                <span class="bar-icon">${escapeHtml(account.emoji)}</span>
                <div>
                  <div class="bar-name">${escapeHtml(account.name)}</div>
                  <div class="bar-sub">${escapeHtml(subtitle)}</div>
                </div>
              </div>
              <div class="bar-value">${escapeHtml(formatSignedMoney(account.balance, currentCurrency))}</div>
            </div>
            <div class="bar-track">
              <div class="bar-fill ${fillClass}" style="width:${width.toFixed(2)}%"></div>
            </div>
          </div>
        `;
      }).join("")}
    </div>
  `;

  return createWidgetShell({
    title: "Account Balances",
    subtitle: `Balances across ${currentCurrency} accounts.`,
    chips: ["Bars", "Accounts"],
    content,
    removable: true,
  });
}

function renderIncomeExpenseBarsWidget() {
  const buckets = compressBuckets(buildDailyBuckets(transactionsInRange()));
  const content = renderBarChartSvg({
    labels: buckets.map(bucket => bucket.shortLabel),
    series: [
      { color: "#3a7a50", values: buckets.map(bucket => bucket.income) },
      { color: "#b84040", values: buckets.map(bucket => bucket.expense) },
    ],
  });

  return createWidgetShell({
    title: "Income vs Expenses",
    subtitle: "Compressed comparison across the selected period.",
    chips: ["Bars", currentCurrency],
    content: `
      ${content}
      <div class="chart-legend">
        <span class="chart-legend-item"><span class="legend-swatch" style="background:#3a7a50"></span>Income</span>
        <span class="chart-legend-item"><span class="legend-swatch" style="background:#b84040"></span>Expenses</span>
      </div>
    `,
    removable: true,
  });
}

function renderSavingsRateWidget() {
  const buckets = buildDailyBuckets(transactionsInRange());
  const values = buckets.map(bucket => {
    if (bucket.income <= 0) {
      return bucket.expense > 0 ? -100 : 0;
    }
    return ((bucket.income - bucket.expense) / bucket.income) * 100;
  });

  const content = renderLineChartSvg({
    labels: buckets.map(bucket => bucket.shortLabel),
    series: [
      {
        color: "#4a72b0",
        fillColor: "rgba(74, 114, 176, 0.12)",
        values,
      },
    ],
    ySuffix: "%",
  });

  return createWidgetShell({
    title: "Savings Rate",
    subtitle: "Daily savings efficiency based on posted income and expenses.",
    chips: ["Line", "%"],
    content,
    removable: true,
  });
}

function renderTopCategoriesWidget() {
  const items = aggregateCategories(transactionsInRange(), "expense");
  const maxValue = Math.max(...items.map(item => item.amount), 0);

  const content = !items.length
    ? createEmptyMarkup(`No expense categories in ${currentCurrency} for the selected range.`)
    : `
      <div class="breakdown-list">
        ${items.map((item, index) => {
          const width = maxValue > 0 ? (item.amount / maxValue) * 100 : 0;
          return `
            <div class="breakdown-row">
              <div class="breakdown-row-top">
                <div class="breakdown-row-label">
                  <span class="breakdown-icon">${escapeHtml(item.emoji)}</span>
                  <div>
                    <div class="breakdown-name">${escapeHtml(item.name)}</div>
                    <div class="breakdown-sub">Expense category</div>
                  </div>
                </div>
                <div class="breakdown-value">${escapeHtml(formatMoney(item.amount, currentCurrency))}</div>
              </div>
              <div class="breakdown-track">
                <div class="breakdown-fill" style="width:${width.toFixed(2)}%; background:${ANALYTICS_COLORS[index % ANALYTICS_COLORS.length]}"></div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

  return createWidgetShell({
    title: "Top Categories",
    subtitle: "Highest expense categories in the active range.",
    chips: ["Ranking", currentCurrency],
    content,
    removable: true,
  });
}

function renderNetFlowWidget() {
  const buckets = buildDailyBuckets(transactionsInRange());
  let runningTotal = 0;
  const values = buckets.map(bucket => {
    runningTotal += bucket.net;
    return runningTotal;
  });

  const content = renderLineChartSvg({
    labels: buckets.map(bucket => bucket.shortLabel),
    series: [
      {
        color: "#2a2520",
        fillColor: "rgba(42, 37, 32, 0.08)",
        values,
      },
    ],
  });

  return createWidgetShell({
    title: "Net Flow",
    subtitle: "Cumulative income minus expenses through the selected period.",
    chips: ["Area", currentCurrency],
    content,
    removable: true,
  });
}

function renderActivityWidget() {
  const buckets = compressBuckets(buildDailyBuckets(transactionsInRange()));
  const content = renderBarChartSvg({
    labels: buckets.map(bucket => bucket.shortLabel),
    series: [
      {
        color: "#476e87",
        values: buckets.map(bucket => bucket.count),
      },
    ],
  });

  return createWidgetShell({
    title: "Transaction Activity",
    subtitle: "Record counts grouped across the selected range.",
    chips: ["Activity", "Count"],
    content,
    removable: true,
  });
}

const WIDGET_CATALOG = {
  "income-expense-bars": {
    title: "Income vs expenses",
    description: "Grouped bars for inflows and outflows across the active period.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M2 13V8M8 13V3M14 13V6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
    `,
    render: renderIncomeExpenseBarsWidget,
  },
  "accounts-balance": {
    title: "Account balances",
    description: "Compare balances for accounts that use the selected currency.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <rect x="2" y="4" width="12" height="8" rx="1.6" stroke="currentColor" stroke-width="1.4" />
        <path d="M2 7h12" stroke="currentColor" stroke-width="1.4" />
      </svg>
    `,
    render: renderAccountsBalanceWidget,
  },
  "savings-rate": {
    title: "Savings rate",
    description: "Track how efficiently income turns into retained value day by day.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M2 12l3.5-4 2.5 2 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    `,
    render: renderSavingsRateWidget,
  },
  "top-categories": {
    title: "Top categories",
    description: "Highlight the expense categories carrying the most weight right now.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M3 4.5h10M3 8h7M3 11.5h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
    `,
    render: renderTopCategoriesWidget,
  },
  "net-flow": {
    title: "Net flow",
    description: "See how cumulative income minus expenses moved through the range.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M2 11.5c2-4.3 4.2-6.4 6.6-6.4 1.8 0 3 1 5.4 3.9V13H2v-1.5z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" />
      </svg>
    `,
    render: renderNetFlowWidget,
  },
  "activity-count": {
    title: "Transaction activity",
    description: "Monitor posting frequency across the active range.",
    icon: `
      <svg viewBox="0 0 16 16" fill="none">
        <circle cx="4" cy="8" r="1.4" fill="currentColor" />
        <circle cx="8" cy="5" r="1.4" fill="currentColor" />
        <circle cx="12" cy="10.5" r="1.4" fill="currentColor" />
        <path d="M4 8l4-3M8 5l4 5.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
      </svg>
    `,
    render: renderActivityWidget,
  },
};

function renderWidgetOptions() {
  const container = document.getElementById("widgetOptions");
  if (!container) return;

  container.innerHTML = Object.entries(WIDGET_CATALOG).map(([type, config]) => `
    <button class="widget-option" type="button" data-action="choose-widget" data-widget-type="${escapeHtml(type)}">
      <div class="widget-option-top">
        <span class="widget-option-icon">${config.icon}</span>
        <span class="widget-option-title">${escapeHtml(config.title)}</span>
      </div>
      <div class="widget-option-sub">${escapeHtml(config.description)}</div>
    </button>
  `).join("");
}

function renderDynamicSlots() {
  document.querySelectorAll(".analytics-slot").forEach(slot => {
    const slotId = slot.dataset.slotId || "";
    const widgetType = widgetSlots[slotId];
    const config = WIDGET_CATALOG[widgetType];

    if (!config) {
      slot.innerHTML = `
        <button class="empty-tile" type="button" data-action="open-widget-picker" data-slot-id="${escapeHtml(slotId)}">
          <div class="empty-tile-inner">
            <div class="empty-plus">
              <svg viewBox="0 0 12 12" fill="none">
                <path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
            </div>
            <div class="empty-title">Add widget</div>
            <div class="empty-sub">Choose another chart or graph for this analytics slot.</div>
          </div>
        </button>
      `;
      return;
    }

    const markup = config.render();
    slot.innerHTML = markup.replace(
      '<button class="widget-action-btn danger" type="button"',
      `<button class="widget-action-btn danger" type="button" data-slot-id="${escapeHtml(slotId)}"`,
    );
  });
}

function renderAnalyticsPage() {
  renderRangeChip();
  renderStats();
  renderCashflowWidget();
  renderCategoryWidget();
  renderBudgetWidget();
  renderDynamicSlots();
}

function syncPeriodButtons() {
  document.querySelectorAll("#analyticsPeriodTabs .filter-tab").forEach(button => {
    button.classList.toggle("active", Number(button.dataset.period) === currentPeriod);
  });
}

function openWidgetModal(slotId) {
  widgetModalSlotId = slotId;
  const overlay = document.getElementById("widgetModalOverlay");
  if (!overlay) return;

  overlay.classList.add("open");
  overlay.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeWidgetModal() {
  widgetModalSlotId = null;
  const overlay = document.getElementById("widgetModalOverlay");
  if (!overlay) return;

  overlay.classList.remove("open");
  overlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function selectWidget(type) {
  if (!widgetModalSlotId || !WIDGET_CATALOG[type]) return;

  widgetSlots[widgetModalSlotId] = type;
  saveWidgetSlots();
  closeWidgetModal();
  renderDynamicSlots();
}

function removeWidget(slotId) {
  if (!slotId || !(slotId in widgetSlots)) return;

  widgetSlots[slotId] = null;
  saveWidgetSlots();
  renderDynamicSlots();
}

function initAnalyticsPage() {
  const page = document.getElementById("analyticsPage");
  if (!page) return;

  analyticsTransactions = readJsonScript("analytics-transactions-data").map(normalizeTransaction);
  analyticsCategories = readJsonScript("analytics-categories-data").map(normalizeCategory);
  analyticsAccounts = readJsonScript("analytics-accounts-data").map(normalizeAccount);
  analyticsBudgets = readJsonScript("analytics-budgets-data").map(normalizeBudget);
  widgetSlots = loadWidgetSlots();
  rangeAnchorDate = findLatestTransactionDate();

  currentCurrency = String(page.dataset.primaryCurrency || "UAH").toUpperCase();
  currentPeriod = 30;
  donutMode = "expense";

  const currencySelect = document.getElementById("analyticsCurrency");
  if (currencySelect) {
    currencySelect.value = currentCurrency;
    currencySelect.addEventListener("change", event => {
      currentCurrency = String(event.target.value || "UAH").toUpperCase();
      renderAnalyticsPage();
    });
  }

  document.getElementById("analyticsPeriodTabs")?.addEventListener("click", event => {
    const button = event.target.closest("[data-period]");
    if (!button) return;

    const nextPeriod = Number(button.dataset.period);
    if (!ANALYTICS_PERIODS.includes(nextPeriod)) return;

    currentPeriod = nextPeriod;
    syncPeriodButtons();
    renderAnalyticsPage();
  });

  document.getElementById("analyticsGrid")?.addEventListener("click", event => {
    const addButton = event.target.closest('[data-action="open-widget-picker"]');
    if (addButton) {
      openWidgetModal(addButton.dataset.slotId || "");
      return;
    }

    const removeButton = event.target.closest('[data-action="remove-widget"]');
    if (removeButton) {
      removeWidget(removeButton.dataset.slotId || "");
      return;
    }

    const donutButton = event.target.closest('[data-action="set-donut-mode"]');
    if (donutButton) {
      donutMode = donutButton.dataset.mode === "income" ? "income" : "expense";
      renderCategoryWidget();
    }
  });

  document.getElementById("widgetOptions")?.addEventListener("click", event => {
    const option = event.target.closest('[data-action="choose-widget"]');
    if (!option) return;
    selectWidget(option.dataset.widgetType || "");
  });

  document.getElementById("widgetModalClose")?.addEventListener("click", closeWidgetModal);

  document.getElementById("widgetModalOverlay")?.addEventListener("click", event => {
    if (event.target.id === "widgetModalOverlay") {
      closeWidgetModal();
    }
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      closeWidgetModal();
    }
  });

  renderWidgetOptions();
  syncPeriodButtons();
  renderAnalyticsPage();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAnalyticsPage);
} else {
  initAnalyticsPage();
}
