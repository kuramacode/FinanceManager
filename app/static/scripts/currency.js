const cards = document.querySelectorAll('.rate-card');
cards.forEach(card => {
    // 1. Отримуємо число з data-value
    const change = parseFloat(card.dataset.value);

    // 2. Визначаємо напрямок та знак
    const changeDir = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';
    const changeSign = change > 0 ? '+' : '';
    
    // 3. Формуємо SVG або символ
    const changeArrow = change > 0
        ? '<svg width="9" height="9" viewBox="0 0 9 9" fill="none"><path d="M4.5 7V2M2 4.5L4.5 2 7 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round""")/>></svg>'
        : change < 0
        ? '<svg width="9" height="9" viewBox="0 0 9 9" fill="none"><path d="M4.5 2v5M7 4.5L4.5 7 2 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round""")/>></svg>'
        : '—';

    // 4. Шукаємо контейнер для бейджа ТІЛЬКИ всередині цієї картки
    const badgeContainer = card.querySelector('.rate-change-badge');

    if (badgeContainer) {
        badgeContainer.className = `rate-change-badge ${changeDir}`; // Оновлюємо класи
        badgeContainer.innerHTML = `
            ${changeArrow}
            <span>${changeSign}${change.toFixed(2)}%</span>
        `;
    }
});

// Continent filters
const chipWrap = document.getElementById('chipWrap');
const emptyRates = document.getElementById('emptyRates');

function getFilterLabel(key, fallback) {
    const label = chipWrap?.dataset[`${key}Label`];
    return label && !label.startsWith('currency.continents.') ? label : fallback;
}

function buildContinentFilters() {
    if (!chipWrap) return;

    const availableContinents = new Set(Array.from(cards).map(card => card.dataset.continent || 'other'));
    const filters = [
        { key: 'all', label: getFilterLabel('all', 'All') },
        { key: 'europe', label: getFilterLabel('europe', 'Europe') },
        { key: 'asia', label: getFilterLabel('asia', 'Asia') },
        { key: 'america', label: getFilterLabel('america', 'Americas') },
        { key: 'other', label: getFilterLabel('other', 'Other') },
    ];

    chipWrap.innerHTML = '';
    filters
        .filter(filter => filter.key === 'all' || availableContinents.has(filter.key))
        .forEach((filter, index) => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = `chip${index === 0 ? ' active' : ''}`;
            chip.dataset.filter = filter.key;
            chip.setAttribute('aria-pressed', index === 0 ? 'true' : 'false');
            chip.textContent = filter.label;
            chip.addEventListener('click', () => applyContinentFilter(filter.key));
            chipWrap.appendChild(chip);
        });
}

function applyContinentFilter(filter) {
    let visibleCount = 0;

    cards.forEach(card => {
        const isVisible = filter === 'all' || card.dataset.continent === filter;
        card.hidden = !isVisible;
        if (isVisible) visibleCount += 1;
    });

    chipWrap?.querySelectorAll('.chip').forEach(chip => {
        const isActive = chip.dataset.filter === filter;
        chip.classList.toggle('active', isActive);
        chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    if (emptyRates) {
        emptyRates.style.display = visibleCount ? 'none' : 'block';
    }
}

buildContinentFilters();

// ── CONVERTER SELECTS ──
const CURRENCIES = ['UAH', ...Array.from(cards).map(c => c.dataset.code)];

function populateSelects() {
    const selFrom = document.getElementById('convFrom');
    const selTo   = document.getElementById('convTo');
    selFrom.innerHTML = '';
    selTo.innerHTML   = '';

    CURRENCIES.forEach(code => {
        const a = document.createElement('option');
        a.value = code; a.textContent = code;
        selFrom.appendChild(a);

        const b = document.createElement('option');
        b.value = code; b.textContent = code;
        selTo.appendChild(b);
    });

    // defaults: UAH → first foreign
    selFrom.value = 'UAH';
    selTo.value   = CURRENCIES[1] || 'USD';
}

populateSelects();

function swapCurrencies() {
    const selFrom = document.getElementById('convFrom');
    const selTo   = document.getElementById('convTo');
    const swapBtn = document.getElementById('swapBtn');

    [selFrom.value, selTo.value] = [selTo.value, selFrom.value];

    swapBtn.classList.add('spinning');
    setTimeout(() => swapBtn.classList.remove('spinning'), 350);

    convertFrom();
}

async function convertFrom() {
    const amount = parseFloat(document.getElementById('convAmount').value);
    const from   = document.getElementById('convFrom').value;
    const to     = document.getElementById('convTo').value;

    if (!amount || !from || !to) return;
    if (from === to) {
        document.getElementById('convResult').value = amount.toFixed(2);
        return;
    }

    try {
        const res  = await fetch(`/api/convert?from=${from}&to=${to}&amount=${amount}`);
        const data = await res.json();
        document.getElementById('convResult').value = data.result ?? data.amount ?? '';
    } catch (e) {
        console.error('Conversion failed:', e);
    }
}
