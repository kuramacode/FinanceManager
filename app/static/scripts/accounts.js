/* ============================================================
   accounts.js — API version
   Works with:
   GET    /api/accounts
   POST   /api/accounts
   PUT    /api/accounts/<id>
   DELETE /api/accounts/<id>
   ============================================================ */

let accounts = [];
let activeFilter = 'all';
let searchQuery   = '';

// ── EMOJI STATE ──────────────────────────────────────────────
let selectedAddEmoji  = '💳';
let selectedEditEmoji = '💳';

const EMOJIS = [
  '💳','💵','💶','💷','💸','🏦','🏧','💰','💹','📈',
  '🪙','💱','🤑','🧾','🏛️','📊','💼','🛍️','🛒','✈️',
  '🏠','🚗','📱','💊','🎓','🍔','⚡','🎮','🏋️','🌍',
  '☕','🎁','🎵','📚','🐾','🌿','🔑','🏖️','🚀','🍕'
];

const API_BASE = '/api/accounts';

// ── API ──────────────────────────────────────────────────────
async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  let data = null;
  try { data = await response.json(); } catch (_) { data = null; }

  if (!response.ok) {
    const message = data?.error || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return data;
}

async function loadAccounts() {
  try {
    const data = await apiRequest(API_BASE);
    accounts = Array.isArray(data) ? data.map(normalizeAccount) : [];
    renderCards();
  } catch (err) {
    console.error('Failed to load accounts:', err);
    alert(`Failed to load accounts: ${err.message}`);
  }
}

async function createAccount(payload) {
  return await apiRequest(API_BASE, { method: 'POST', body: JSON.stringify(payload) });
}

async function updateAccount(id, payload) {
  return await apiRequest(`${API_BASE}/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
}

async function deleteAccount(id) {
  return await apiRequest(`${API_BASE}/${id}`, { method: 'DELETE' });
}

// ── NORMALIZATION ────────────────────────────────────────────
function normalizeAccount(account) {
  return {
    id:            account?.id,
    name:          account?.name          ?? 'Untitled account',
    balance:       Number(account?.balance ?? 0),
    status:        account?.status        ?? 'active',
    currency_code: account?.currency_code ?? 'UAH',
    emoji:         account?.emoji         ?? '💳',
    type:          account?.type          ?? 'card',
    subtitle:      account?.subtitle      ?? '',
    note:          account?.note          ?? ''
  };
}

// ── UTILS ────────────────────────────────────────────────────
function currencySymbol(code) {
  return code === 'USD' ? '$'
       : code === 'EUR' ? '€'
       : code === 'GBP' ? '£'
       : '₴';
}

function fmtBalance(balance, code) {
  const sym = currencySymbol(code);
  const abs = Math.abs(balance).toLocaleString('uk-UA', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
  const known = ['UAH', 'USD', 'EUR', 'GBP'];
  if (known.includes(code)) return `${balance < 0 ? '-' : ''}${sym}${abs}`;
  return `${balance < 0 ? '-' : ''}${abs} ${code}`;
}

function statusBadgeClass(status) {
  const s = (typeof status === 'string' && status.trim()) ? status.trim() : 'active';
  if (s === 'active') return 'active';
  if (s === 'frozen') return 'frozen';
  return 'closed';
}

function statusLabel(status) {
  const s = (typeof status === 'string' && status.trim()) ? status.trim() : 'active';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── EMOJI STRIP ──────────────────────────────────────────────
function renderEmojiStrip(stripId, currentEmoji, onSelect) {
  const strip = document.getElementById(stripId);
  if (!strip) return;

  strip.innerHTML = '';

  EMOJIS.forEach(emoji => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'emoji-btn' + (emoji === currentEmoji ? ' selected' : '');
    btn.textContent = emoji;
    btn.title = emoji;

    btn.addEventListener('click', () => {
      strip.querySelectorAll('.emoji-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      onSelect(emoji);
    });

    strip.appendChild(btn);
  });
}

// ── SUMMARY ──────────────────────────────────────────────────
function updateSummary() {
  const activeAccounts = accounts.filter(a => a.status === 'active');
  const frozenCount    = accounts.filter(a => a.status === 'frozen').length;

  const netWorth        = activeAccounts.reduce((sum, a) => sum + a.balance, 0);
  const positiveBalance = activeAccounts.filter(a => a.balance > 0).reduce((s, a) => s + a.balance, 0);
  const negativeBalance = Math.abs(activeAccounts.filter(a => a.balance < 0).reduce((s, a) => s + a.balance, 0));

  const total       = accounts.length;
  const activeCount = activeAccounts.length;

  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('sum-net-worth', `₴${netWorth.toLocaleString('uk-UA')}`);
  set('sum-cash-bank', `₴${positiveBalance.toLocaleString('uk-UA')}`);
  set('sum-credit',    `₴${negativeBalance.toLocaleString('uk-UA')}`);
  set('sum-total',     total);
  set('sum-detail',    `${activeCount} active • ${frozenCount} frozen`);
}

// ── FILTERING ────────────────────────────────────────────────
function filteredAccounts() {
  return accounts.filter(a => {
    // FIX: was comparing a.status === activeFilter, but filter tabs are account TYPES
    const matchFilter = activeFilter === 'all'
      ? true
      : (a.type || '').toLowerCase() === activeFilter.toLowerCase();

    const matchSearch = a.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchFilter && matchSearch;
  });
}

// ── RENDER CARDS ─────────────────────────────────────────────
function renderCards() {
  const grid  = document.getElementById('accounts-grid');
  const empty = document.getElementById('accounts-empty');
  if (!grid || !empty) return;

  const list = filteredAccounts();
  grid.innerHTML = '';

  if (list.length === 0) {
    grid.style.display  = 'none';
    empty.style.display = 'block';
    renderTable([]);
    updateSummary();
    return;
  }

  grid.style.display  = 'grid';
  empty.style.display = 'none';

  list.forEach(a => {
    const balCls = a.balance >= 0 ? 'positive' : 'negative';
    const card = document.createElement('article');
    card.className  = 'account-card';
    card.dataset.id = a.id;

    card.innerHTML = `
      <div class="account-head">
        <div class="account-meta">
          <div class="account-icon">${escapeHtml(a.emoji)}</div>
          <div class="account-title-wrap">
            <div class="account-name">${escapeHtml(a.name)}</div>
            <div class="account-subline">${escapeHtml(a.subtitle)}</div>
          </div>
        </div>
        <span class="account-type">${statusLabel(a.type)}</span>
      </div>

      <div class="account-balance-block">
        <div class="account-balance ${balCls}">${fmtBalance(a.balance, a.currency_code)}</div>
        <div class="account-balance-sub">
          ${a.balance >= 0 ? 'Available balance' : 'Current outstanding debt'}
        </div>
      </div>

      <div class="account-stats">
        <div class="mini-stat">
          <div class="mini-stat-label">Currency</div>
          <div class="mini-stat-value">${escapeHtml(a.currency_code)}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-stat-label">Status</div>
          <div class="mini-stat-value">${statusLabel(a.status)}</div>
        </div>
        <div class="mini-stat">
          <div class="mini-stat-label">Account ID</div>
          <div class="mini-stat-value">#${a.id}</div>
        </div>
      </div>

      <div class="account-footer">
        <div class="account-note">${escapeHtml(a.note)}</div>
        <div class="account-actions">
          <button type="button" class="icon-btn btn-edit" data-id="${a.id}" title="Edit">
            <svg viewBox="0 0 15 15" fill="none">
              <path d="M10.9 2.2a1.5 1.5 0 112.1 2.1l-7.8 7.8-3 .7.7-3 8-7.6z"
                stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
            </svg>
          </button>
          <button type="button" class="icon-btn btn-delete" data-id="${a.id}" title="Delete">
            <svg viewBox="0 0 15 15" fill="none">
              <path d="M2.5 4h10M6 2.2h3M5 5.2v6M7.5 5.2v6M10 5.2v6
                       M3.8 4l.6 8c.04.6.54 1 1 1h3.84c.6 0 1.1-.4 1.14-1l.6-8"
                stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });

  grid.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', () => openEditModal(Number(btn.dataset.id)));
  });

  grid.querySelectorAll('.btn-delete').forEach(btn => {
    btn.addEventListener('click', () => openDeleteModal(Number(btn.dataset.id)));
  });

  renderTable(list);
  updateSummary();
}

// ── RENDER TABLE ─────────────────────────────────────────────
function renderTable(list) {
  const tbody   = document.getElementById('accounts-table-body');
  const wrap    = document.getElementById('accounts-list-wrap');
  const countEl = document.getElementById('table-count');
  if (!tbody || !wrap || !countEl) return;

  tbody.innerHTML  = '';
  countEl.textContent = `Showing ${list.length} account${list.length !== 1 ? 's' : ''}`;

  if (list.length === 0) { wrap.style.display = 'none'; return; }
  wrap.style.display = 'block';

  list.forEach((a, idx) => {
    const row = document.createElement('div');
    row.className = 'account-row';
    if (idx === list.length - 1) row.style.borderBottom = 'none';

    const balCls = a.balance >= 0 ? 'amount-positive' : 'amount-negative';

    row.innerHTML = `
      <div class="account-cell-main">
        <div class="account-cell-icon">${escapeHtml(a.emoji)}</div>
        <div>
          <div class="account-cell-name">${escapeHtml(a.name)}</div>
          <div class="account-cell-sub">ID ${a.id}</div>
        </div>
      </div>
      <div class="account-cell-text">${escapeHtml(a.type)}</div>
      <div class="account-cell-text">${escapeHtml(a.currency_code)}</div>
      <div class="account-cell-text ${balCls}">${fmtBalance(a.balance, a.currency_code)}</div>
      <div>
        <span class="account-badge ${statusBadgeClass(a.status)}">${statusLabel(a.status)}</span>
      </div>
    `;

    tbody.appendChild(row);
  });
}

// ── FILTER TABS ──────────────────────────────────────────────
function initFilterTabs() {
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeFilter = tab.dataset.filter;
      renderCards();
    });
  });
}

function initSearch() {
  const input = document.getElementById('search-input');
  if (!input) return;
  input.addEventListener('input', e => {
    searchQuery = e.target.value.trim();
    renderCards();
  });
}

// ── MODAL HELPERS ────────────────────────────────────────────
function openOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('open');
  document.body.style.overflow = '';
}

function closeOnBackdrop(overlayId) {
  const el = document.getElementById(overlayId);
  if (!el) return;
  el.addEventListener('click', e => {
    if (e.target === e.currentTarget) closeOverlay(overlayId);
  });
}

// ── ADD ──────────────────────────────────────────────────────
function openAddModal() {
  const form = document.getElementById('add-form');
  if (form) form.reset();

  selectedAddEmoji = '💳';
  renderEmojiStrip('add-emoji-strip', selectedAddEmoji, emoji => {
    selectedAddEmoji = emoji;
  });

  openOverlay('modal-add');
}

async function submitAdd() {
  try {
    const name          = document.getElementById('add-name')?.value.trim();
    const balance       = parseFloat(document.getElementById('add-balance')?.value || '0');
    const status        = document.getElementById('add-status')?.value    || 'active';
    const currency_code = document.getElementById('add-currency')?.value  || 'UAH';
    const type          = document.getElementById('add-type')?.value      || 'card';
    const subtitle      = document.getElementById('add-subline')?.value   || '';
    const note          = document.getElementById('add-note')?.value      || '';
    const emoji         = selectedAddEmoji;  // FIX: was missing from payload

    if (!name) { alert('Account name is required.'); return; }

    const payload = { name, balance, status, currency_code, emoji, type, subtitle, note };
    const created = await createAccount(payload);

    accounts.push(normalizeAccount(created));
    renderCards();
    closeOverlay('modal-add');
  } catch (err) {
    console.error('Create account failed:', err);
    alert(`Create failed: ${err.message}`);
  }
}

// ── EDIT ─────────────────────────────────────────────────────
function openEditModal(id) {
  const a = accounts.find(x => x.id === id);
  if (!a) return;

  // FIX: was missing type, subtitle, note, emoji
  document.getElementById('edit-id').value       = a.id;
  document.getElementById('edit-name').value     = a.name;
  document.getElementById('edit-balance').value  = a.balance;
  document.getElementById('edit-currency').value = a.currency_code;
  document.getElementById('edit-status').value   = a.status;
  document.getElementById('edit-type').value     = a.type;
  document.getElementById('edit-subline').value  = a.subtitle;
  document.getElementById('edit-note').value     = a.note;

  selectedEditEmoji = a.emoji || '💳';
  renderEmojiStrip('edit-emoji-strip', selectedEditEmoji, emoji => {
    selectedEditEmoji = emoji;
  });

  openOverlay('modal-edit');
}

async function submitEdit() {
  try {
    const id = Number(document.getElementById('edit-id').value);
    if (!accounts.find(x => x.id === id)) return;

    const name          = document.getElementById('edit-name')?.value.trim();
    const balance       = parseFloat(document.getElementById('edit-balance')?.value || '0');
    const status        = document.getElementById('edit-status')?.value    || 'active';
    const currency_code = document.getElementById('edit-currency')?.value  || 'UAH';
    const type          = document.getElementById('edit-type')?.value      || 'card';  // FIX
    const subtitle      = document.getElementById('edit-subline')?.value   || '';       // FIX
    const note          = document.getElementById('edit-note')?.value      || '';       // FIX
    const emoji         = selectedEditEmoji;                                            // FIX

    if (!name) { alert('Account name is required.'); return; }

    // FIX: was only sending 4 fields — now sends all 8
    const payload = { name, balance, status, currency_code, emoji, type, subtitle, note };
    const updated = await updateAccount(id, payload);

    const index = accounts.findIndex(x => x.id === id);
    if (index !== -1) accounts[index] = normalizeAccount(updated);

    renderCards();
    closeOverlay('modal-edit');
  } catch (err) {
    console.error('Update account failed:', err);
    alert(`Update failed: ${err.message}`);
  }
}

// ── DELETE ───────────────────────────────────────────────────
function openDeleteModal(id) {
  const a = accounts.find(x => x.id === id);
  if (!a) return;

  document.getElementById('delete-id').value              = id;
  document.getElementById('delete-target-name').textContent = a.name;
  openOverlay('modal-delete');
}

async function submitDelete() {
  const confirmBtn = document.getElementById('btn-delete-confirm');
  try {
    if (confirmBtn) confirmBtn.disabled = true;
    const id = Number(document.getElementById('delete-id').value);
    await deleteAccount(id);
    accounts = accounts.filter(x => x.id !== id);
    renderCards();
    closeOverlay('modal-delete');
  } catch (err) {
    console.error('Delete account failed:', err);
    alert(`Delete failed: ${err.message}`);
  } finally {
    if (confirmBtn) confirmBtn.disabled = false;
  }
}

// ── HELPERS ──────────────────────────────────────────────────
function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

// ── INIT ─────────────────────────────────────────────────────
let accountsPageInitialized = false;

async function initAccountsPage() {
  if (accountsPageInitialized) return;
  accountsPageInitialized = true;

  initFilterTabs();
  initSearch();

  // FIX: all click handlers use e.preventDefault() to stop any possible form submission
  document.getElementById('btn-add-account')?.addEventListener('click', e => {
    e.preventDefault();
    openAddModal();
  });
  document.getElementById('btn-add-submit')?.addEventListener('click', e => {
    e.preventDefault();
    submitAdd();
  });
  document.getElementById('btn-edit-submit')?.addEventListener('click', e => {
    e.preventDefault();
    submitEdit();
  });
  document.getElementById('btn-delete-confirm')?.addEventListener('click', e => {
    // FIX: critical — prevents the button from submitting any enclosing form (POST bug)
    e.preventDefault();
    e.stopPropagation();
    submitDelete();
  });

  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      closeOverlay(btn.dataset.close);
    });
  });

  ['modal-add', 'modal-edit', 'modal-delete'].forEach(closeOnBackdrop);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') ['modal-add', 'modal-edit', 'modal-delete'].forEach(closeOverlay);
  });

  await loadAccounts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAccountsPage);
} else {
  initAccountsPage();
}
