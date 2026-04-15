const EMOJI_OPTIONS = [
  '🍜','🍕','🍔','☕','🍷','🛒','🏠','💡','🚇','✈️',
  '🚗','⛽','💊','🏋️','💅','🎬','🎮','📚','🎵','🎁',
  '💰','💻','📈','💼','🏦','💳','🔧','🎓','🐾','🌿',
  '🛍️','👗','👟','🧴','🔑','📱','🖥️','📷','⚽','🎯',
  '↔️','🔄','💸','🏷️','🎪','🌍','🏖️','🍀','⭐','🎉',
];


const COLOR_OPTIONS = [
  '#3a7a50', '#2c6e8a', '#6b4c9a', '#b84040',
  '#7a6230', '#4a7a7a', '#8a4a60', '#9a9080',
  '#5a7a3a', '#3a5a8a', '#7a4a3a', '#4a4a7a',
];


function openModal() {
    document.getElementById('f_date').value = new Date().toISOString().split('T')[0];
    document.getElementById('f_name').value = '';
    document.getElementById('f_amount').value = 0;
    document.getElementById('f_name').style.borderColor = '';
    document.getElementById('f_amount').style.borderColor = '';
    document.getElementById('modalOverlay').classList.add('open');
    setTimeout(() => document.getElementById('f_name').focus(), 80);
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
}

function handleOverlayClick(event) {
    if (event.target == event.currentTarget) closeModal();
}