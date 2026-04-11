const cards = document.querySelectorAll('.rate-card');
const sel = document.getElementById('convCurrency');
sel.innerHTML = '';

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
    // converter 

    const code = card.dataset.code;
    // додавання опцій
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = code;
    sel.appendChild(opt);
});