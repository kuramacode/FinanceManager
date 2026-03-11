const ICONS = {
  Food: '🍜', Housing: '🏠', Transport: '🚇', Health: '💊',
  Shopping: '🛍️', Entertainment: '🎬', Salary: '💰', Other: '📦'
};

const transactions = [
  { id: 1, desc: 'Monthly Salary',     amount: 4850,   type: 'income',  cat: 'Salary',        date: '2026-03-01' },
  { id: 2, desc: 'Apartment Rent',      amount: 1200,   type: 'expense', cat: 'Housing',       date: '2026-03-02' },
  { id: 3, desc: 'Whole Foods Market',  amount: 134.50, type: 'expense', cat: 'Food',          date: '2026-03-03' },
  { id: 4, desc: 'Metro Monthly Pass',  amount: 85,     type: 'expense', cat: 'Transport',     date: '2026-03-04' },
  { id: 5, desc: 'Freelance Project',   amount: 920,    type: 'income',  cat: 'Salary',        date: '2026-03-05' },
  { id: 6, desc: 'Netflix',            amount: 17.99,  type: 'expense', cat: 'Entertainment', date: '2026-03-06' },
  { id: 7, desc: 'ZARA – Jacket',       amount: 79.90,  type: 'expense', cat: 'Shopping',      date: '2026-03-07' },
  { id: 8, desc: 'Dentist Visit',       amount: 95,     type: 'expense', cat: 'Health',        date: '2026-03-08' },
  { id: 9, desc: 'Pharmacy',           amount: 28.50,  type: 'expense', cat: 'Health',        date: '2026-03-09' },
  { id: 10,desc: 'Uber rides',         amount: 43.20,  type: 'expense', cat: 'Transport',     date: '2026-03-10' },
];

function fmt(n) {
  return '$' + Math.abs(n).toLocaleString('en-US', {
    minimumFractionDigits: 2, maximumFractionDigits: 2
  });
}

function fmtDate(str) {
  return new Date(str + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric'
  });
}