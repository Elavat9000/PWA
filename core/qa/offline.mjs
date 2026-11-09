import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { base, output, vehicle, password } = JSON.parse(await readFile(process.argv[2], 'utf8'));
const modulePath = process.env.DRIVESMART_PLAYWRIGHT_MODULE;
const { chromium } = await import(modulePath ? pathToFileURL(modulePath).href : 'playwright');
const browser = await chromium.launch({ channel: 'chrome', headless: true, chromiumSandbox: true });
const checks = [];
const errors = [];
try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    // Iniciar sesión antes de descargar; la copia debe seguir siendo anónima.
    await page.goto(base + '/cuentas/entrar/');
    await page.locator('#id_username').fill('PRIVATE_OFFLINE_MARKER');
    await page.locator('#id_password').fill(password);
    await page.locator('.auth form button').click();
    await page.locator('.pwa-status').getByText(/Catálogo listo sin conexión/).waitFor({ timeout: 45000 });
    checks.push('Descarga completa desde una sesión autenticada');
    await page.screenshot({ path: resolve(output, 'catalogo-listo.png') });
    const inspect = async () => page.evaluate(async () => {
        const result = [];
        for (const name of await caches.keys()) {
            for (const req of await (await caches.open(name)).keys()) {
                const response = await (await caches.open(name)).match(req);
                const type = response.headers.get('Content-Type') || '';
                result.push({ name, path: new URL(req.url).pathname, text: type.includes('text/html') ? await response.text() : '' });
            }
        }
        return result;
    });
    const cached = await inspect();
    assert.equal(cached.filter(r => r.path.startsWith('/media/vehicles/')).length, 6);
    assert.ok(cached.every(r => !/^\/(?:cuentas|admin|mis-rentas|rentas|asistente)\//.test(r.path)));
    assert.ok(cached.every(r => !r.text.includes('PRIVATE_OFFLINE_MARKER') && !r.text.includes('csrfmiddlewaretoken')));
    checks.push('Seis fotos y catálogo público; sin usuario, CSRF ni páginas privadas');
    await context.setOffline(true);
    await page.goto(base + '/');
    assert.equal(await page.locator('[data-offline-vehicle]').count(), 6);
    await page.getByText(/Estás sin conexión/).waitFor();
    await page.waitForFunction(() => [...document.images].every(img => img.complete && img.naturalWidth > 0));
    assert.match(await page.locator('body').innerText(), /precio guardado/);
    checks.push('Inicio sin red muestra todo el catálogo, incluidas fotos nunca visitadas');
    const failedRefresh = await page.evaluate(() => new Promise(resolve => {
        function receive(event) {
            if (event.data?.type === 'PUBLIC_CATALOG_STATUS') {
                navigator.serviceWorker.removeEventListener('message', receive);
                resolve(event.data);
            }
        }
        navigator.serviceWorker.addEventListener('message', receive);
        navigator.serviceWorker.controller.postMessage({ type: 'SYNC_PUBLIC_CATALOG', force: true });
    }));
    assert.equal(failedRefresh.ready, true);
    assert.equal(failedRefresh.stale, true);
    assert.equal((await inspect()).filter(r => r.path === '/catalogo-sin-conexion/').length, 1);
    checks.push('Actualización fallida conserva la última copia completa y elimina la parcial');
    await page.screenshot({ path: resolve(output, 'catalogo-offline.png') });
    await page.goto(base + '/vehiculos/' + vehicle + '/');
    assert.equal(await page.locator('[data-offline-vehicle]:visible').count(), 1);
    assert.match(await page.locator('.offline-selected').innerText(), /Corolla/);
    await page.getByRole('button', { name: 'Verificar fechas en línea' }).click();
    assert.match(await page.locator('#offline-connection').innerText(), /Necesitas conectarte a internet/);
    checks.push('Ficha guardada y aviso al intentar verificar fechas sin conexión');
    await page.screenshot({ path: resolve(output, 'detalle-offline.png') });
    await page.goto(base + '/vehiculos/?categoria=suv');
    assert.equal(await page.locator('[data-offline-vehicle]').count(), 6);
    assert.equal(await page.locator('#offline-filter-note').isVisible(), true);
    checks.push('No simula que los filtros en línea se aplicaron sin conexión');
    await page.goto(base + '/mis-rentas/');
    assert.match(await page.locator('body').innerText(), /Necesitas conexión a internet/);
    assert.equal(await page.locator('body').innerText().then(t => t.includes('PRIVATE_OFFLINE_MARKER')), false);
    checks.push('Ruta privada sin red solo recibe aviso genérico; no datos del usuario');
    const postStatus = await page.evaluate(async () => {
        try {
            await fetch('/asistente/consultar/', { method: 'POST', body: '{}', headers: { 'Content-Type': 'application/json' } });
            return 'unexpected';
        } catch { return 'network-error'; }
    });
    assert.equal(postStatus, 'network-error');
    checks.push('POST del chat sin red falla; no se simula respuesta ni se encola');
    await context.setOffline(false);
    await page.goto(base + '/vehiculos/');
    assert.equal(await page.locator('.vehicle-card').count(), 6);
    await page.getByRole('button', { name: 'Actualizar catálogo guardado' }).click();
    await page.waitForFunction(() => !document.querySelector('.pwa-status button').disabled);
    assert.equal((await inspect()).filter(r => r.path === '/catalogo-sin-conexion/').length, 1);
    checks.push('Reconexión, actualización explícita y sustitución de la copia anterior');
    await context.setOffline(true);
    await page.goto(base + '/vehiculos/');
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: resolve(output, 'movil-offline.png') });
    checks.push('Catálogo guardado adaptable a móvil');
    await context.close();
    assert.deepEqual(errors, []);
    await writeFile(resolve(output, 'results.json'), JSON.stringify({ checks, cached, errors }, null, 2));
    console.log(JSON.stringify({ checks: checks.length, results: checks, output }));
} finally { await browser.close(); }
