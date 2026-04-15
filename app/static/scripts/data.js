function searchTransactions() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  const items = document.querySelectorAll('.tx-item');

  items.forEach(item => {
    const name = item.querySelector('.tx-name').textContent.toLowerCase();
    const cat  = item.querySelector('.tx-cat').textContent.toLowerCase();
    const date = item.querySelector('.tx-date').textContent.toLowerCase();

    const match = name.includes(query) || cat.includes(query) || date.includes(query);
    item.style.display = match ? '' : 'none';
  });
}

const PER_PAGE = 7;
let currentPage = 1;

function getVisibleItems() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  const items = Array.from(document.querySelectorAll('.tx-item'));

  return items.filter(item => {
    const name = item.querySelector('.tx-name').textContent.toLowerCase();
    const cat  = item.querySelector('.tx-cat').textContent.toLowerCase();
    const date = item.querySelector('.tx-date').textContent.toLowerCase();
    return name.includes(query) || cat.includes(query) || date.includes(query);
  });
}

function renderPage(page) {
  currentPage = page;
  const visible = getVisibleItems();
  const totalPages = Math.ceil(visible.length / PER_PAGE);

  // ховаємо всі
  document.querySelectorAll('.tx-item').forEach(item => item.style.display = 'none');

  // показуємо тільки поточну сторінку
  const start = (page - 1) * PER_PAGE;
  const end   = start + PER_PAGE;
  visible.slice(start, end).forEach(item => item.style.display = '');

  // page-info: "1–7 of 23"
  const from = visible.length === 0 ? 0 : start + 1;
  const to   = Math.min(end, visible.length);
  document.getElementById('pageInfo').textContent =
    visible.length === 0 ? 'No results' : `${from}–${to} of ${visible.length}`;

  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const container = document.getElementById('pageBtns');
  container.innerHTML = '';

  if (totalPages <= 1) return;

  // кнопка "назад"
  const prev = document.createElement('button');
  prev.className = 'page-btn';
  prev.textContent = '←';
  prev.disabled = currentPage === 1;
  prev.onclick = () => renderPage(currentPage - 1);
  container.appendChild(prev);

  // номери сторінок
  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
    btn.textContent = i;
    btn.onclick = () => renderPage(i);
    container.appendChild(btn);
  }

  // кнопка "вперед"
  const next = document.createElement('button');
  next.className = 'page-btn';
  next.textContent = '→';
  next.disabled = currentPage === totalPages;
  next.onclick = () => renderPage(currentPage + 1);
  container.appendChild(next);
}

function searchTransactions() {
  renderPage(1);
}

document.addEventListener('DOMContentLoaded', () => renderPage(1));