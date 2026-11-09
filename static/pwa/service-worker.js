const CACHE_PREFIX = 'drivesmart-public-';
const CACHE_NAME = `${CACHE_PREFIX}v10`;
const CATALOG_PREFIX = 'drivesmart-catalog-v10-';
const CATALOG_URL = '/catalogo-sin-conexion/';
const PUBLIC_ASSETS = [
    '/offline/',
    '/static/css/site.css',
    '/static/css/catalog.css',
    '/static/css/rentals.css',
    '/static/css/assistant.css',
    '/static/js/assistant.js',
    '/static/js/pwa.js',
    '/static/css/offline.css',
    '/static/js/offline-catalog.js',
    '/static/images/compacto.svg',
    '/static/images/sedan.svg',
    '/static/images/suv.svg',
    '/static/pwa/icons/icon-192.png',
    '/static/pwa/icons/icon-512.png',
];

// Solo copias públicas generadas sin usuario ni CSRF. Nunca guardar HTML normal.
async function savedCatalog() {
    const names = (await caches.keys()).filter(name => name.startsWith(CATALOG_PREFIX)).sort().reverse();
    for (const name of names) {
        const cache = await caches.open(name);
        const response = await cache.match(CATALOG_URL);
        if (response) return { name, cache, response };
    }
    return null;
}

async function publicFetch(url) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
        const response = await fetch(url, { credentials: 'omit', cache: 'no-store', signal: controller.signal });
        if (!response.ok || response.redirected) throw new Error('Recurso público no disponible');
        return response;
    } finally { clearTimeout(timer); }
}

async function networkFetch(request) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try { return await fetch(request, { cache: 'no-store', signal: controller.signal }); }
    finally { clearTimeout(timer); }
}

let synchronization;
function syncCatalog(force = false) {
    if (synchronization) return synchronization;
    synchronization = updateCatalog(force).finally(() => { synchronization = null; });
    return synchronization;
}

async function updateCatalog(force) {
    const previous = await savedCatalog();
    const previousDate = previous?.response.headers.get('X-DriveSmart-Catalog-Date');
    if (!force && previous && Date.now() - Date.parse(previousDate) < 30 * 60 * 1000) {
        return { ready: true, date: previousDate };
    }
    const name = CATALOG_PREFIX + Date.now();
    try {
        const response = await publicFetch(CATALOG_URL);
        if (response.headers.get('X-DriveSmart-Public-Catalog') !== '1') throw new Error('Copia no válida');
        const html = await response.clone().text();
        const script = html.match(/<script id="offline-images" type="application\/json">([\s\S]*?)<\/script>/);
        if (!script) throw new Error('Sin lista de fotografías');
        const images = JSON.parse(script[1]);
        if (!Array.isArray(images)) throw new Error('Lista no válida');
        const cache = await caches.open(name);
        for (const image of images) {
            const url = new URL(image, self.location.origin);
            if (url.origin !== self.location.origin || url.search || url.hash
                || !/^\/(?:media\/vehicles\/|static\/images\/)/.test(url.pathname)) throw new Error('Imagen fuera del catálogo');
            const photo = await publicFetch(url.href);
            if (!photo.headers.get('Content-Type')?.startsWith('image/')) throw new Error('No es una imagen');
            await cache.put(url.href, photo);
        }
        // Publicar la copia solo después de descargar todas sus fotos.
        await cache.put(CATALOG_URL, response.clone());
        for (const old of await caches.keys()) {
            if (old.startsWith('drivesmart-catalog-') && old !== name) await caches.delete(old);
        }
        return { ready: true, date: response.headers.get('X-DriveSmart-Catalog-Date') };
    } catch (error) {
        await caches.delete(name);
        return { ready: Boolean(previous), date: previousDate, stale: true };
    }
}

self.addEventListener('message', event => {
    if (event.data?.type !== 'SYNC_PUBLIC_CATALOG') return;
    event.waitUntil(syncCatalog(event.data.force === true).then(result => {
        event.source?.postMessage({ type: 'PUBLIC_CATALOG_STATUS', ...result });
    }));
});

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME)
        .then(cache => cache.addAll(PUBLIC_ASSETS))
        .then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
    event.waitUntil(caches.keys()
        .then(names => Promise.all(names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
            .map(name => caches.delete(name))))
        .then(() => self.clients.claim())
        .then(() => syncCatalog()));
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
    const isPublicPage = url.pathname === '/' || url.pathname === '/vehiculos/' || url.pathname === CATALOG_URL
        || /^\/vehiculos\/\d+\/$/.test(url.pathname);
    event.respondWith((async () => {
        // Las imágenes permitidas provienen de la copia pública, no de una caché general de media.
        if (request.destination === 'image') {
            const saved = await savedCatalog();
            const photo = saved && await saved.cache.match(request.url);
            if (photo) {
                try { return await networkFetch(request); }
                catch (error) { return photo; }
            }
        }
        try {
            const response = await networkFetch(request);
            if (response.status < 500 || request.mode !== 'navigate') return response;
        } catch (error) {
            if (request.mode !== 'navigate') throw error;
        }
        if (isPublicPage) {
            const saved = await savedCatalog();
            if (saved) return saved.response;
        }
        const cache = await caches.open(CACHE_NAME);
        const fallback = await cache.match('/offline/');
        if (!fallback) return Response.error();
        return new Response(await fallback.text(), { status: 503,
            headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
    })());
});
