// ───────────── MOCK DATA ─────────────
const budgetData = [
  {
    name: "Food & Dining",
    icon: "🍔",
    current: 420,
    limit: 700,
    period: "Monthly • Apr 1 – Apr 30",
    note: "Spending pace is normal for this point in the month."
  },
  {
    name: "Transport",
    icon: "🚗",
    current: 245,
    limit: 300,
    period: "Monthly • Apr 1 – Apr 30",
    note: "Approaching limit faster than expected."
  },
  {
    name: "Entertainment",
    icon: "🎬",
    current: 190,
    limit: 150,
    period: "Monthly • Apr 1 – Apr 30",
    note: "Budget exceeded already."
  },
  {
    name: "Groceries",
    icon: "🛒",
    current: 310,
    limit: 500,
    period: "Monthly • Apr 1 – Apr 30",
    note: "Comfortable margin remains."
  }
];

let budgets = [...budgetData];

// ───────────── HELPERS ─────────────
function calculateStatus(current, limit) {
  const percent = (current / limit) * 100;

  if (percent > 100) return { text: "Exceeded", class: "over" };
  if (percent >= 80) return { text: "Warning", class: "warn" };
  return { text: "On Track", class: "good" };
}

function buildCard(budget, index) {
  const { name, icon, current, limit, period, note } = budget;

  const percent = (current / limit) * 100;
  const progress = Math.min(percent, 100);
  const remaining = limit - current;

  const status = calculateStatus(current, limit);

  return `
    <article class="budget-card" data-index="${index}">
      <div class="budget-head">
        <div class="budget-meta">
          <div class="budget-icon">${icon}</div>
          <div class="budget-title-wrap">
            <div class="budget-name">${name}</div>
            <div class="budget-period">${period}</div>
          </div>
        </div>
        <span class="budget-status ${status.class}">${status.text}</span>
      </div>

      <div class="budget-amounts">
        <div>
          <div class="budget-current">$${current}</div>
          <div class="budget-limit">of $${limit} limit</div>
        </div>
        <div class="budget-left">
          <div class="budget-left-value ${remaining < 0 ? "over" : "safe"}">
            ${remaining < 0 ? `$${Math.abs(remaining)} over` : `$${remaining} left`}
          </div>
          <div class="budget-left-label">
            ${remaining < 0 ? "Exceeded" : "Remaining"}
          </div>
        </div>
      </div>

      <div class="budget-progress-wrap">
        <div class="budget-progress-top">
          <span class="budget-progress-label">Usage</span>
          <span class="budget-progress-value">${percent.toFixed(0)}%</span>
        </div>
        <div class="budget-progress">
          <div class="budget-progress-bar ${status.class}" style="width:${progress}%"></div>
        </div>
      </div>

      <div class="budget-footer">
        <div class="budget-note">${note}</div>
        <div class="budget-actions">
          <button class="icon-btn edit-btn" data-index="${index}">✏️</button>
          <button class="icon-btn delete-btn" data-index="${index}">🗑️</button>
        </div>
      </div>
    </article>
  `;
}

// ───────────── RENDER ─────────────
function renderBudgets(list = budgets) {
  const grid = document.querySelector(".budget-grid");

  if (!list.length) {
    grid.innerHTML = "<p>No budgets</p>";
    return;
  }

  grid.innerHTML = list.map(buildCard).join("");
  updateSummary();
}

// ───────────── SUMMARY ─────────────
function updateSummary() {
  const total = budgets.reduce((s, b) => s + b.limit, 0);
  const spent = budgets.reduce((s, b) => s + b.current, 0);
  const remaining = total - spent;

  document.querySelectorAll(".card-value")[0].textContent = `$${total}`;
  document.querySelectorAll(".card-value")[1].textContent = `$${remaining}`;
  document.querySelectorAll(".card-value")[2].textContent = `$${spent}`;
  document.querySelectorAll(".card-value")[3].textContent = budgets.length;
}

// ───────────── MODALS ─────────────
const modal = document.getElementById("budgetModalOverlay");
const deleteModal = document.getElementById("deleteModalOverlay");

let editingIndex = null;
let deletingIndex = null;

function openModal() {
  modal.classList.add("open");
}

function closeModal() {
  modal.classList.remove("open");
}

function openDeleteModal(index) {
  deletingIndex = index;
  deleteModal.classList.add("open");
}

function closeDeleteModal() {
  deleteModal.classList.remove("open");
}

// ───────────── ADD / EDIT ─────────────
document.getElementById("openAddBudgetModal").onclick = () => {
  editingIndex = null;
  document.getElementById("budgetForm").reset();
  openModal();
};

document.getElementById("budgetForm").onsubmit = (e) => {
  e.preventDefault();

  const newBudget = {
    name: budgetName.value,
    icon: budgetIcon.value,
    current: +budgetCurrent.value,
    limit: +budgetLimit.value,
    period: budgetPeriod.value,
    note: budgetNote.value
  };

  if (editingIndex !== null) {
    budgets[editingIndex] = newBudget;
  } else {
    budgets.unshift(newBudget);
  }

  closeModal();
  renderBudgets();
};

// ───────────── EDIT / DELETE CLICK ─────────────
document.querySelector(".budget-grid").addEventListener("click", (e) => {
  if (e.target.classList.contains("edit-btn")) {
    const i = e.target.dataset.index;
    editingIndex = i;

    const b = budgets[i];

    budgetName.value = b.name;
    budgetIcon.value = b.icon;
    budgetCurrent.value = b.current;
    budgetLimit.value = b.limit;
    budgetPeriod.value = b.period;
    budgetNote.value = b.note;

    openModal();
  }

  if (e.target.classList.contains("delete-btn")) {
    openDeleteModal(e.target.dataset.index);
  }
});

// ───────────── DELETE CONFIRM ─────────────
document.getElementById("confirmDeleteBtn").onclick = () => {
  budgets.splice(deletingIndex, 1);
  closeDeleteModal();
  renderBudgets();
};

// ───────────── INIT ─────────────
renderBudgets();