(() => {
    const status = document.getElementById('offline-connection');
    const date = document.querySelector('time');
    const parsed = new Date(date.dateTime);
    if (!Number.isNaN(parsed.getTime())) date.textContent = parsed.toLocaleString('es-MX');
    const id = location.pathname.match(/^\/vehiculos\/(\d+)\/$/)?.[1];
    if (id) {
        const selected = document.querySelector(`[data-offline-vehicle="${id}"]`);
        if (selected) {
            document.querySelectorAll('[data-offline-vehicle]').forEach(card => { card.hidden = card !== selected; });
            selected.classList.add('offline-selected');
            selected.querySelector('details').open = true;
        } else document.getElementById('offline-missing').hidden = false;
    }
    document.getElementById('offline-filter-note').hidden = !location.search;
    function connection() {
        status.textContent = navigator.onLine
            ? 'La conexión parece disponible. Abre el catálogo en línea para comprobar la información actual.'
            : 'Estás sin conexión. Puedes explorar esta copia; conéctate para asegurar las fechas deseadas y la disponibilidad.';
    }
    document.querySelectorAll('[data-verify]').forEach(button => button.addEventListener('click', () => {
        if (navigator.onLine) location.href = button.dataset.verify;
        else {
            status.textContent = 'Necesitas conectarte a internet para verificar las fechas deseadas y la disponibilidad de este vehículo.';
            status.scrollIntoView({ block: 'center', behavior: 'auto' });
        }
    }));
    window.addEventListener('online', connection);
    window.addEventListener('offline', connection);
    connection();
})();
