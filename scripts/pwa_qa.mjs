import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const { base, output, password, first, second, vehicle, price } = JSON.parse(await readFile(process.argv[2], 'utf8'));
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve('.playwright');
const { chromium } = await import('playwright');
// Activar la caché de historial normal del navegador para comprobar su aislamiento.
const browser = await chromium.launch({ headless: true, ignoreDefaultArgs: ['--disable-back-forward-cache'] });
const checks = [];
const errors = [];
const record = message => checks.push(message);
const offlineMessage = 'DriveSmart necesita conexión a internet para consultar vehículos, gestionar rentas y utilizar el asistente.';
const allowed = new Set(['/offline/', '/static/css/site.css', '/static/css/catalog.css',
    '/static/css/rentals.css', '/static/css/assistant.css', '/static/js/assistant.js',
    '/static/js/pwa.js', '/static/pwa/icons/icon-192.png', '/static/pwa/icons/icon-512.png']);

async function capture(page, name) {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, name);
    await page.screenshot({ path: resolve(output, `${name}.png`), fullPage: true });
}

async function login(page, username, admin = false) {
    await page.goto(base + (admin ? '/admin/' : '/cuentas/entrar/'));
    await page.locator('#id_username').fill(username);
    await page.locator('#id_password').fill(password);
    if (admin) await page.locator('input[type=submit]').click();
    else await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
}

async function inspectCaches(page, name) {
    const cachesData = await page.evaluate(async () => {
        const data = {};
        for (const key of await caches.keys()) {
            if (key.startsWith('drivesmart-public-')) {
                const cache = await caches.open(key);
                data[key] = (await cache.keys()).map(request => new URL(request.url).pathname + new URL(request.url).search);
            }
        }
        return data;
    });
    assert.equal(Object.keys(cachesData).length, 1, JSON.stringify(cachesData));
    for (const paths of Object.values(cachesData)) {
        assert.deepEqual(new Set(paths), allowed, name);
    }
    return cachesData;
}

try {
    for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
        const context = await browser.newContext({ viewport: { width, height }, isMobile: name === 'mobile', hasTouch: name === 'mobile' });
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(error.message));
        assert.equal((await page.goto(base + '/')).status(), 200);
        await page.evaluate(() => navigator.serviceWorker.ready);
        await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
        const registration = await page.evaluate(async () => {
            const worker = await navigator.serviceWorker.ready;
            return { scope: worker.scope, script: worker.active.scriptURL, state: worker.active.state };
        });
        assert.equal(registration.scope, base + '/');
        assert.equal(registration.script, base + '/service-worker.js');
        assert.equal(registration.state, 'activated');
        const manifest = await page.evaluate(async () => (await fetch('/manifest.webmanifest')).json());
        assert.equal(manifest.name, 'DriveSmart');
        assert.equal(manifest.display, 'standalone');
        for (const icon of manifest.icons) {
            const response = await context.request.get(base + icon.src);
            assert.equal(response.status(), 200);
            assert.ok(response.headers()['content-type'].includes('image/png'));
        }
        await inspectCaches(page, name);
        await capture(page, `${name}-online`);
        record(`${name}: manifiesto, iconos, worker activo y alcance raíz correctos`);

        const registered = `qa_pwa_registered_${name}`;
        await page.goto(base + '/cuentas/registro/');
        await page.locator('#id_username').fill(registered);
        await page.locator('#id_password1').fill(password);
        await page.locator('#id_password2').fill(password);
        await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
        await page.getByText(`Hola, ${registered}`, { exact: true }).waitFor();
        await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
        record(`${name}: registro y logout funcionan con el worker activo`);

        await login(page, 'qa_pwa_one');
        for (const route of ['/mis-rentas/', `/rentas/${first}/confirmacion/`, `/vehiculos/${vehicle}/solicitar/`]) {
            const response = await page.goto(base + route);
            assert.equal(response.status(), 200);
            assert.ok(response.headers()['cache-control'].includes('no-store'));
        }
        await page.goto(base + '/mis-rentas/');
        assert.equal(await page.locator('.rental-item').count(), 1);
        assert.ok((await page.locator('.rental-item').innerText()).includes(`Solicitud #${first}`));
        assert.ok(!(await page.locator('.rental-item').innerText()).includes(`Solicitud #${second}`));
        record(`${name}: lista, formulario y confirmación consultan red y envían no-store`);

        await page.getByRole('button', { name: 'Asistente DriveSmart', exact: true }).click();
        await page.getByLabel('Tu pregunta', { exact: true }).fill('¿Cuánto cuesta el Toyota Corolla?');
        const chatResponse = page.waitForResponse(response => response.url().endsWith('/asistente/consultar/'));
        await page.getByRole('button', { name: 'Enviar', exact: true }).click();
        const response = await chatResponse;
        assert.equal(response.status(), 200);
        assert.ok(response.headers()['cache-control'].includes('no-store'));
        const chat = await response.json();
        assert.equal(chat.vehicles[0].id, vehicle);
        assert.equal(chat.vehicles[0].daily_price, price);
        await page.getByRole('button', { name: 'Cerrar asistente', exact: true }).click();
        await page.evaluate(() => fetch('/static/css/site.css?private_marker=never_store'));
        const cacheBeforeOffline = await inspectCaches(page, name);
        record(`${name}: chat POST devuelve precio real y no altera la caché pública`);

        await context.setOffline(true);
        assert.equal((await page.goto(base + '/vehiculos/')).status(), 200);
        await page.getByText(offlineMessage, { exact: true }).waitFor();
        assert.equal(await page.locator('.vehicle-card, .rental-item, #assistant-panel').count(), 0);
        await capture(page, `${name}-offline`);
        await page.getByRole('link', { name: 'Volver a intentar', exact: true }).click();
        await page.getByText(offlineMessage, { exact: true }).waitFor();
        record(`${name}: navegación pública y reintento offline muestran solo el aviso estático`);
        const offlinePost = await page.evaluate(async () => {
            try {
                return (await fetch('/asistente/consultar/', { method: 'POST', body: '{}' })).status;
            } catch { return 'network-failure'; }
        });
        assert.equal(offlinePost, 'network-failure');
        let privateFailed = false;
        try { await page.goto(base + '/mis-rentas/'); } catch { privateFailed = true; }
        assert.equal(privateFailed, true);
        assert.ok(!(await page.locator('body').innerText()).includes(`Solicitud #${first}`));
        await context.setOffline(false);
        await page.goto(base + '/mis-rentas/');
        assert.deepEqual(await inspectCaches(page, name), cacheBeforeOffline);
        record(`${name}: privados y POST fallan offline; no se simulan rentas ni chat`);

        await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
        await page.goBack({ waitUntil: 'domcontentloaded' });
        await page.waitForURL(url => url.pathname === '/cuentas/entrar/');
        assert.ok(!(await page.locator('body').innerText()).includes(`Solicitud #${first}`));
        await login(page, 'qa_pwa_two');
        await page.goto(base + '/mis-rentas/');
        const ownRentals = await page.locator('.rental-item').innerText();
        assert.ok(ownRentals.includes(`Solicitud #${second}`));
        assert.ok(!ownRentals.includes(`Solicitud #${first}`));
        await capture(page, `${name}-segundo-usuario`);
        await inspectCaches(page, name);
        record(`${name}: Atrás después del logout y cambio de usuario no recuperan datos ajenos`);

        await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
        await login(page, 'qa_pwa_admin', true);
        const adminResponse = await page.goto(base + '/admin/');
        assert.ok(adminResponse.headers()['cache-control'].includes('no-store'));
        await inspectCaches(page, name);
        record(`${name}: Admin sigue protegido y no entra en Cache Storage`);

        await page.goto(base + '/');
        await page.evaluate(async () => {
            await caches.open('drivesmart-public-obsolete');
            await caches.open('unrelated-test-cache');
            // Una URL de script nueva provoca una actualización real, no reutiliza el activo.
            const next = await navigator.serviceWorker.register('/service-worker.js?qa-update=1', { scope: '/' });
            const worker = next.installing || next.waiting || next.active;
            if (worker.state !== 'activated') {
                await new Promise(resolve => worker.addEventListener('statechange', () => {
                    if (worker.state === 'activated') resolve();
                }));
            }
        });
        for (let attempt = 0; attempt < 50; attempt++) {
            if (await page.evaluate(async () => !(await caches.keys()).includes('drivesmart-public-obsolete'))) break;
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        assert.equal(await page.evaluate(async () => (await caches.keys()).includes('drivesmart-public-obsolete')), false);
        assert.equal(await page.evaluate(async () => (await caches.keys()).includes('unrelated-test-cache')), true);
        await inspectCaches(page, name);
        record(`${name}: activación limpia solo versiones antiguas de DriveSmart`);
        await context.close();
    }
    assert.deepEqual(errors, []);
    await writeFile(resolve(output, 'report.json'), JSON.stringify({ passed: checks.length, checks, errors }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, errors, evidence: output }, null, 2));
} finally {
    await browser.close();
}
