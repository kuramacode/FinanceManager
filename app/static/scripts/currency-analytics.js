const CURRENCY_UI_LOCALE = window.ledgerI18n?.locale || "uk-UA";
const CURRENCY_PALETTE = [
  "#3a7a50",
  "#b84040",
  "#4a72b0",
  "#c47a2a",
  "#7a4ab0",
  "#2a8a8a",
];

let currencyAnalyticsInitialized = false;
let currencyCurrentDays = 30;
let currencyRateChart = null;
let currencyCompareChart = null;
let currencyActiveCodes = [];

function currencyTr(key, replacements = {}, fallback = "") {
  return window.ledgerI18n?.t(key, replacements, fallback) || fallback || key;
}

function readCurrencyJson(id, fallback = {}) {
  const element = document.getElementById(id);
  if (!element) return fallback;

  try {
    return JSON.parse(element.textContent || "null") ?? fallback;
  } catch (_) {
    return fallback;
  }
}

const currencyAnalyticsData = readCurrencyJson("currency-analytics-data", {
  base_code: "UAH",
  currencies: [],
  rates: [],
});

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function formatChartDate(value) {
  return new Intl.DateTimeFormat(CURRENCY_UI_LOCALE, {
    day: "2-digit",
    month: "short",
  }).format(new Date(`${value}T00:00:00`));
}

function groupCurrencyRates() {
  const grouped = new Map();

  (currencyAnalyticsData.rates || []).forEach(point => {
    const code = String(point.code || "").toUpperCase();
    if (!code) return;

    if (!grouped.has(code)) grouped.set(code, []);
    grouped.get(code).push({
      date: point.date,
      label: point.label || formatChartDate(point.date),
      rate: Number(point.rate || 0),
    });
  });

  grouped.forEach(history => {
    history.sort((a, b) => a.date.localeCompare(b.date));
  });

  return grouped;
}

const currencyRateGroups = groupCurrencyRates();
const currencyCodes = (currencyAnalyticsData.currencies || []).filter(code => currencyRateGroups.has(code));

function latestHistory(code) {
  return (currencyRateGroups.get(code) || []).slice(-currencyCurrentDays);
}

function chartTooltipConfig() {
  return {
    backgroundColor: "#2a2520",
    titleColor: "rgba(255,255,255,0.45)",
    bodyColor: "#fdfaf4",
    padding: 12,
    cornerRadius: 8,
    titleFont: { family: "Epilogue", size: 11 },
    bodyFont: { family: "Playfair Display", size: 13 },
    callbacks: {
      label: ctx => ` ${ctx.dataset.label}  ${Number(ctx.parsed.y).toFixed(4)} UAH`,
    },
  };
}

function xScale() {
  return {
    grid: { color: cssVar("--border") },
    ticks: { color: cssVar("--muted"), font: { family: "Epilogue", size: 11 } },
  };
}

function yScale() {
  return {
    grid: { color: cssVar("--border") },
    ticks: {
      color: cssVar("--muted"),
      font: { family: "Epilogue", size: 11 },
      callback: value => Number(value).toFixed(2),
    },
  };
}

function updateCurrencyStats(history) {
  const minElement = document.getElementById("currencyStatMin");
  const maxElement = document.getElementById("currencyStatMax");
  const avgElement = document.getElementById("currencyStatAvg");
  const minDateElement = document.getElementById("currencyStatMinDate");
  const maxDateElement = document.getElementById("currencyStatMaxDate");
  const changeElement = document.getElementById("currencyStatChange");

  if (!history.length) {
    [minElement, maxElement, avgElement, minDateElement, maxDateElement, changeElement].forEach(element => {
      if (element) element.textContent = "—";
    });
    return;
  }

  const values = history.map(item => item.rate);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  const minIndex = values.indexOf(min);
  const maxIndex = values.indexOf(max);
  const change = ((values.at(-1) - values[0]) / values[0]) * 100;
  const changeSign = change >= 0 ? "+" : "";

  minElement.textContent = min.toFixed(2);
  maxElement.textContent = max.toFixed(2);
  avgElement.textContent = avg.toFixed(2);
  minDateElement.textContent = formatChartDate(history[minIndex].date);
  maxDateElement.textContent = formatChartDate(history[maxIndex].date);
  changeElement.textContent = currencyTr(
    "currency.analytics_period_change",
    { change: `${changeSign}${change.toFixed(2)}%` },
    `${changeSign}${change.toFixed(2)}% за період`,
  );
  changeElement.style.color = change >= 0 ? cssVar("--income") : cssVar("--expense");
}

function renderCurrencyRateChart() {
  const select = document.getElementById("chartCurrency");
  if (!select || !window.Chart) return;

  const code = select.value || currencyCodes[0];
  const history = latestHistory(code);
  updateCurrencyStats(history);

  if (!history.length) return;

  const labels = history.map(item => formatChartDate(item.date));
  const values = history.map(item => item.rate);
  const change = ((values.at(-1) - values[0]) / values[0]) * 100;
  const lineColor = change >= 0 ? cssVar("--income") : cssVar("--expense");
  const fillColor = change >= 0 ? "rgba(58,122,80,0.07)" : "rgba(184,64,64,0.07)";

  if (currencyRateChart) currencyRateChart.destroy();

  currencyRateChart = new Chart(document.getElementById("rateChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: `${code} / UAH`,
        data: values,
        borderColor: lineColor,
        backgroundColor: fillColor,
        borderWidth: 2,
        pointRadius: currencyCurrentDays <= 7 ? 4 : 0,
        pointHoverRadius: 6,
        pointBackgroundColor: lineColor,
        pointBorderColor: cssVar("--paper"),
        pointBorderWidth: 2,
        tension: 0.35,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: chartTooltipConfig(),
      },
      scales: { x: xScale(), y: yScale() },
    },
  });
}

function buildCurrencySelect() {
  const select = document.getElementById("chartCurrency");
  if (!select) return;

  select.innerHTML = "";
  currencyCodes.forEach(code => {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = code;
    select.appendChild(option);
  });

  const preferred = currencyCodes.includes("USD") ? "USD" : currencyCodes[0];
  select.value = preferred || "";
  select.addEventListener("change", renderCurrencyRateChart);
}

function buildCompareChips() {
  const wrap = document.getElementById("compareChips");
  if (!wrap) return;

  wrap.innerHTML = "";
  currencyCodes.forEach(code => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `chip${currencyActiveCodes.includes(code) ? " active" : ""}`;
    chip.textContent = code;
    chip.addEventListener("click", () => {
      if (currencyActiveCodes.includes(code)) {
        if (currencyActiveCodes.length <= 1) return;
        currencyActiveCodes = currencyActiveCodes.filter(activeCode => activeCode !== code);
      } else {
        if (currencyActiveCodes.length >= 5) currencyActiveCodes.shift();
        currencyActiveCodes.push(code);
      }
      buildCompareChips();
      renderCurrencyCompareChart();
    });
    wrap.appendChild(chip);
  });
}

function renderCurrencyCompareChart() {
  if (!window.Chart || !currencyActiveCodes.length) return;

  const histories = currencyActiveCodes
    .map(code => ({ code, data: latestHistory(code) }))
    .filter(item => item.data.length);

  if (!histories.length) return;

  const labels = histories[0].data.map(item => formatChartDate(item.date));
  const datasets = histories.map((history, index) => {
    const color = CURRENCY_PALETTE[index % CURRENCY_PALETTE.length];
    return {
      label: history.code,
      data: history.data.map(item => item.rate),
      borderColor: color,
      backgroundColor: "transparent",
      borderWidth: 2,
      pointRadius: currencyCurrentDays <= 7 ? 3 : 0,
      pointHoverRadius: 5,
      pointBackgroundColor: color,
      tension: 0.35,
      fill: false,
      yAxisID: `y${index}`,
    };
  });

  const scales = { x: xScale() };
  histories.forEach((_, index) => {
    scales[`y${index}`] = {
      display: index === 0,
      position: "left",
      grid: { color: index === 0 ? cssVar("--border") : "transparent" },
      ticks: {
        color: cssVar("--muted"),
        font: { family: "Epilogue", size: 11 },
        callback: value => Number(value).toFixed(2),
      },
    };
  });

  if (currencyCompareChart) currencyCompareChart.destroy();

  currencyCompareChart = new Chart(document.getElementById("compareChart"), {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          display: true,
          position: "top",
          align: "end",
          labels: {
            color: cssVar("--text"),
            font: { family: "Epilogue", size: 11, weight: "600" },
            boxWidth: 12,
            boxHeight: 2,
            padding: 16,
          },
        },
        tooltip: chartTooltipConfig(),
      },
      scales,
    },
  });
}

function renderCurrencyCharts() {
  renderCurrencyRateChart();
  renderCurrencyCompareChart();
}

function initCurrencyAnalytics() {
  if (currencyAnalyticsInitialized) {
    currencyRateChart?.resize();
    currencyCompareChart?.resize();
    renderCurrencyCharts();
    return;
  }

  const emptyState = document.getElementById("emptyCurrencyAnalytics");
  if (!window.Chart || !currencyCodes.length) {
    if (emptyState) emptyState.style.display = "block";
    return;
  }

  currencyAnalyticsInitialized = true;
  currencyActiveCodes = ["USD", "EUR", "GBP", "PLN"].filter(code => currencyCodes.includes(code)).slice(0, 2);
  if (!currencyActiveCodes.length) currencyActiveCodes = currencyCodes.slice(0, 2);

  buildCurrencySelect();
  buildCompareChips();
  renderCurrencyCharts();
}

document.querySelectorAll("#currencyPeriodTabs .filter-tab").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll("#currencyPeriodTabs .filter-tab").forEach(item => item.classList.remove("active"));
    button.classList.add("active");
    currencyCurrentDays = Number(button.dataset.days || 30);
    renderCurrencyCharts();
  });
});

document.querySelectorAll("#currencyViewTabs .filter-tab").forEach(button => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    const isAnalytics = view === "analytics";

    document.querySelectorAll("#currencyViewTabs .filter-tab").forEach(item => item.classList.remove("active"));
    button.classList.add("active");

    document.getElementById("currencyRatesView").hidden = isAnalytics;
    document.getElementById("currencyAnalyticsView").hidden = !isAnalytics;

    if (isAnalytics) {
      requestAnimationFrame(initCurrencyAnalytics);
    }
  });
});
