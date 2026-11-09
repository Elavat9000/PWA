// Una restauración del historial debe volver a comprobar la sesión en el servidor.
window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.reload();
});

if ('serviceWorker' in navigator && window.isSecureContext) {
    let notice;
    function sync(force = false) {
        if (!navigator.onLine) return;
        navigator.serviceWorker.ready.then(registration => {
            registration.active?.postMessage({ type: 'SYNC_PUBLIC_CATALOG', force });
        });
    }
    function connection() {
        if (navigator.onLine) {
            notice?.remove();
            notice = null;
            return;
        }
        if (notice) return;
        notice = document.createElement('div');
        notice.className = 'pwa-status wrap';
        notice.setAttribute('role', 'status');
        const text = document.createElement('span');
        text.textContent = 'Sin conexión. Necesitas internet para verificar fechas, precios y disponibilidad.';
        const link = document.createElement('a');
        link.href = '/vehiculos/';
        link.textContent = 'Ver catálogo sin conexión';
        notice.append(text, link);
        document.querySelector('main')?.prepend(notice);
    }
    navigator.serviceWorker.addEventListener('controllerchange', () => sync());
    window.addEventListener('offline', connection);
    window.addEventListener('online', () => { connection(); sync(true); });
    connection();
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
            .then(() => sync())
            .catch(() => console.warn('La PWA no pudo registrarse; la versión web sigue disponible.'));
    });
}
