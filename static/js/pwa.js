// Una restauración del historial debe volver a comprobar la sesión en el servidor.
window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.reload();
});

if ('serviceWorker' in navigator && window.isSecureContext) {
    const notice = document.createElement('div');
    notice.className = 'pwa-status wrap';
    notice.setAttribute('role', 'status');
    const text = document.createElement('span');
    const preview = document.createElement('a');
    preview.href = '/catalogo-sin-conexion/';
    preview.textContent = 'Ver copia';
    const refresh = document.createElement('button');
    refresh.type = 'button';
    refresh.textContent = 'Actualizar catálogo guardado';
    notice.append(text, preview, refresh);
    notice.hidden = true;
    document.querySelector('main')?.prepend(notice);
    function sync(force = false) {
        refresh.disabled = true;
        navigator.serviceWorker.ready.then(registration => {
            registration.active?.postMessage({ type: 'SYNC_PUBLIC_CATALOG', force });
        });
    }
    refresh.addEventListener('click', () => {
        text.textContent = 'Guardando catálogo y fotografías…';
        sync(true);
    });
    navigator.serviceWorker.addEventListener('message', event => {
        if (event.data?.type !== 'PUBLIC_CATALOG_STATUS') return;
        notice.hidden = false;
        refresh.disabled = false;
        preview.hidden = !event.data.ready;
        const date = new Date(event.data.date);
        text.textContent = event.data.ready
            ? `Catálogo listo sin conexión · guardado ${date.toLocaleString('es-MX')}.${event.data.stale ? ' No se pudo actualizar la copia.' : ''}`
            : 'No se pudo guardar el catálogo completo. Mantén la conexión y vuelve a intentarlo.';
    });
    navigator.serviceWorker.addEventListener('controllerchange', () => sync());
    window.addEventListener('online', () => sync(true));
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
            .then(() => sync())
            .catch(() => console.warn('La PWA no pudo registrarse; la versión web sigue disponible.'));
    });
}
