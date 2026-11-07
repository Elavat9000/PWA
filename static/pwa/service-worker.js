const CACHE_PREFIX = 'drivesmart-public-';
const CACHE_NAME = `${CACHE_PREFIX}v1`;
const PUBLIC_ASSETS = [
    '/offline/',
    '/static/css/site.css',
    '/static/css/catalog.css',
    '/static/css/rentals.css',
    '/static/css/assistant.css',
    '/static/js/assistant.js',
    '/static/js/pwa.js',
    '/static/pwa/icons/icon-192.png',
    '/static/pwa/icons/icon-512.png',
];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME)
        .then(cache => cache.addAll(PUBLIC_ASSETS))
        .then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
    event.waitUntil(caches.keys()
        .then(names => Promise.all(names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
            .map(name => caches.delete(name))))
        .then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    // No interceptar ni almacenar POST, ni recursos de otros orígenes.
    if (request.method !== 'GET' || url.origin !== self.location.origin) return;

    if (!url.search && PUBLIC_ASSETS.includes(url.pathname)) {
        event.respondWith(caches.open(CACHE_NAME).then(async cache =>
            (await cache.match(url.pathname)) || fetch(request, { cache: 'no-store' })));
        return;
    }

    // Las páginas y consultas dinámicas siempre van al servidor, sin caché HTTP.
    const isPublicPage = url.pathname === '/' || url.pathname === '/vehiculos/'
        || /^\/vehiculos\/\d+\/$/.test(url.pathname);
    event.respondWith(fetch(request, { cache: 'no-store' }).catch(async error => {
        if (request.mode === 'navigate' && isPublicPage) {
            const cache = await caches.open(CACHE_NAME);
            return (await cache.match('/offline/')) || Response.error();
        }
        throw error;
    }));
});
