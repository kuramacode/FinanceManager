/* ── DATA ── */
const EMOJIS = ['🛒','🍔','🚗','🏠','💊','🎮','✈️','📚','☕','🎬','💪','🐾','👗','⚡','📱','🎵','🏥','🎁','💈','🌱','💼','🏦','💰','📈','🎓','🔧'];

let categories = [];

function tr(key, replacements = {}, fallback = '') {
    return window.ledgerI18n?.t(key, replacements, fallback) || fallback || key;
}

async function loadCategories() {
    try {
        const response = await fetch(`api/category`);
        if (!response.ok) throw new Error(`Failed to fetch categories: ${response.status}`);
        categories = await response.json();
        render();
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

let editId        = null;
let selectedEmoji = EMOJIS[0];
let selectedType  = 'expense';
let activeFilter  = 'all';
let searchQuery   = '';

/* ── HELPERS ── */
function escHtml(s) {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

/* ── RENDER ── */
function render() {
    const q = searchQuery.toLowerCase();

    const filtered = categories.filter(c => {
        const matchFilter = activeFilter === 'all' || c.type === activeFilter;
        const matchSearch = c.name.toLowerCase().includes(q) || (c.desc || '').toLowerCase().includes(q);
        return matchFilter && matchSearch;
    });

    const expenses = filtered.filter(c => c.type === 'expense');
    const incomes  = filtered.filter(c => c.type === 'income');

    renderGrid('grid-expense', 'empty-expense', 'section-expense', 'count-expense', expenses, activeFilter === 'income');
    renderGrid('grid-income',  'empty-income',  'section-income',  'count-income',  incomes,  activeFilter === 'expense');
}

function renderGrid(gridId, emptyId, sectionId, countId, items, hidden) {
    const section = document.getElementById(sectionId);
    const grid    = document.getElementById(gridId);
    const empty   = document.getElementById(emptyId);
    const count   = document.getElementById(countId);

    if (hidden) { section.style.display = 'none'; return; }
    section.style.display = '';
    count.textContent = items.length;

    if (items.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    grid.innerHTML = items.map((c, i) => `
        <div class="cat-card ${c.type}-card${c.built_in ? ' builtin-card' : ''}"
             style="animation-delay:${i * 0.04}s" data-id="${c.id}">
            <div class="cat-icon">${c.emoji}</div>
            <div class="cat-info">
                <div class="cat-name-row">
                    <span class="cat-name">${escHtml(c.name)}</span>
                    ${c.built_in ? `<span class="cat-builtin-badge">${escHtml(tr('common.built_in_category'))}</span>` : ''}
                </div>
                <div class="cat-meta">${c.desc ? escHtml(c.desc) : ''}</div>
            </div>
            <span class="cat-badge ${c.type}">${c.type === 'income' ? escHtml(tr('common.types.income')) : escHtml(tr('common.types.expense'))}</span>
            ${!c.built_in ? `
            <div class="cat-actions">
                <button class="cat-action-btn edit" data-id="${c.id}" title="${escHtml(tr('common.buttons.edit'))}">
                    <svg viewBox="0 0 15 15" fill="none" width="13" height="13">
                        <path d="M10.5 1.5l3 3-9 9H1.5v-3l9-9z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
                    </svg>
                </button>
                <button class="cat-action-btn delete" data-id="${c.id}" title="${escHtml(tr('common.buttons.delete'))}">
                    <svg viewBox="0 0 15 15" fill="none" width="13" height="13">
                        <path d="M2 4h11M6 4V2.5h3V4M5.5 4v7.5h4V4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>` : ''}
        </div>
    `).join('');

    grid.querySelectorAll('.cat-action-btn.edit').forEach(btn =>
        btn.addEventListener('click', e => { e.stopPropagation(); openEdit(+btn.dataset.id); })
    );
    grid.querySelectorAll('.cat-action-btn.delete').forEach(btn =>
        btn.addEventListener('click', e => { e.stopPropagation(); deleteCategory(+btn.dataset.id); })
    );
}

/* ── EMOJI PICKER ── */
function buildEmojiPicker() {
    const row = document.getElementById('emoji-row');
    row.innerHTML = EMOJIS.map(e => `
        <button class="emoji-btn${e === selectedEmoji ? ' selected' : ''}" data-emoji="${e}">${e}</button>
    `).join('');
    row.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            selectedEmoji = btn.dataset.emoji;
            row.querySelectorAll('.emoji-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
        });
    });
}

/* ── MODAL ── */
function openAdd() {
    editId        = null;
    selectedEmoji = EMOJIS[0];
    selectedType  = 'expense';

    document.getElementById('modal-title').innerHTML  = tr('categories.modal_new_title');
    document.getElementById('modal-sub').textContent  = tr('categories.modal_new_subtitle');
    document.getElementById('field-name').value       = '';
    document.getElementById('field-desc').value       = '';
    document.getElementById('btn-submit').textContent = tr('common.buttons.create');

    const actions = document.getElementById('modal-actions');
    const delBtn  = actions.querySelector('.btn-delete');
    if (delBtn) delBtn.remove();

    syncTypeToggle();
    buildEmojiPicker();
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('field-name').focus();
}

function openEdit(id) {
    const cat = categories.find(c => c.id === id);
    if (!cat) return;

    editId        = id;
    selectedEmoji = cat.emoji;          // fix: was cat.icon
    selectedType  = cat.type;

    document.getElementById('modal-title').innerHTML  = tr('categories.modal_edit_title');
    document.getElementById('modal-sub').textContent  = tr('categories.modal_edit_subtitle');
    document.getElementById('field-name').value       = cat.name;
    document.getElementById('field-desc').value       = cat.desc || '';
    document.getElementById('btn-submit').textContent = tr('common.buttons.save');

    const actions = document.getElementById('modal-actions');
    if (!actions.querySelector('.btn-delete')) {
        const delBtn = document.createElement('button');
        delBtn.className   = 'btn-delete';
        delBtn.textContent = tr('common.buttons.delete');
        delBtn.addEventListener('click', () => { deleteCategory(editId); closeModal(); });
        actions.insertBefore(delBtn, actions.firstChild);
    }

    syncTypeToggle();
    buildEmojiPicker();
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('field-name').focus();
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('open');
}

function syncTypeToggle() {
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === selectedType);
    });
}

/* ── API ACTIONS ── */
async function submitModal() {
    const name = document.getElementById('field-name').value.trim();
    if (!name) {
        document.getElementById('field-name').focus();
        return;
    }

    const desc = document.getElementById('field-desc').value.trim();
    const payload = {
        emoji: selectedEmoji,
        name,
        desc,
        type: selectedType
    };

    try {
        const isEdit = editId !== null;
        const url = isEdit ? `api/category/${editId}` : `api/category`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(JSON.stringify(data));
        }

        if (isEdit) {
            const idx = categories.findIndex(c => c.id === editId);
            if (idx !== -1) {
                categories[idx] = data;
            }
        } else {
            categories.push(data);
        }

        closeModal();
        render();
    } catch (err) {
        console.error('Failed to save category:', err);
        alert(tr('categories.save_failed'));
    }
}

async function deleteCategory(id) {
    if (!confirm(tr('categories.delete_confirm'))) return;

    try {
        const res = await fetch(`api/category/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());

        categories = categories.filter(c => c.id !== id);
        render();
    } catch (err) {
        console.error('Failed to delete category:', err);
        alert(tr('categories.delete_failed'));
    }
}

/* ── EVENT WIRING ── */
document.getElementById('btn-add-cat').addEventListener('click', openAdd);
document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('btn-cancel').addEventListener('click',  closeModal);
document.getElementById('btn-submit').addEventListener('click',  submitModal);

document.getElementById('modal-overlay').addEventListener('click', e => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
});

document.querySelectorAll('.type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        selectedType = btn.dataset.type;
        syncTypeToggle();
    });
});

document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        activeFilter = tab.dataset.filter;
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        render();
    });
});

document.getElementById('search-input').addEventListener('input', e => {
    searchQuery = e.target.value;
    render();
});

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
    if (e.key === 'Enter' && document.getElementById('modal-overlay').classList.contains('open')) submitModal();
});

/* ── INIT ── */
loadCategories();
