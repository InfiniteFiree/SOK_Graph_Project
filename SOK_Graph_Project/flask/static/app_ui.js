function toggleDropdown(id) {
    const menu = document.getElementById(id);
    if (menu) {
        menu.classList.toggle('open');
    }
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('open');
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('open');
    }
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.tb-dropdown')) {
        document.querySelectorAll('.tb-dropdown-menu').forEach(function(menu) {
            menu.classList.remove('open');
        });
    }

    if (e.target.classList.contains('app-modal')) {
        e.target.classList.remove('open');
    }
});