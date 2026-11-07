// Una restauración del historial debe volver a comprobar la sesión en el servidor.
window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.reload();
});

if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
            .catch(() => console.warn('La PWA no pudo registrarse; la versión web sigue disponible.'));
    });
}
