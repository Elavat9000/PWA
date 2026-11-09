// Solo QA: se ejecuta contra la base temporal de assistant.browser_qa.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const fixture = JSON.parse(await readFile(process.argv[2], 'utf8'));
const { base, output, start, end } = fixture;
const modulePath = process.env.DRIVESMART_PLAYWRIGHT_MODULE;
const { chromium } = await import(modulePath ? pathToFileURL(modulePath).href : 'playwright');
const browser = await chromium.launch({ channel: 'chrome', headless: true, chromiumSandbox: true });
const checks = [];
const errors = [];
const transcript = [];
const record = text => checks.push(text);

async function ask(page, message) {
    await page.getByLabel('Tu pregunta', { exact: true }).fill(message);
    const pending = page.waitForResponse(r => r.url().endsWith('/asistente/consultar/'));
    await page.getByRole('button', { name: 'Enviar', exact: true }).click();
    const response = await pending;
    assert.equal(response.status(), 200);
    assert.match(response.headers()['cache-control'], /no-store/);
    const data = await response.json();
    await page.waitForFunction(() => !document.querySelector('#assistant-form').hasAttribute('aria-busy'));
    assert.equal(await page.locator('.assistant-message:not(.from-user)').last().innerText(), data.reply);
    transcript.push({ message, ...data });
    return data;
}

async function open(page) {
    await page.goto(base);
    await page.getByRole('button', { name: 'Asistente DriveSmart', exact: true }).click();
}

async function capture(page, name) {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    for (const selector of ['#assistant-panel', '#assistant-reset', '#assistant-message', '#assistant-form button']) {
        const box = await page.locator(selector).boundingBox();
        const size = page.viewportSize();
        assert.ok(box && box.x >= 0 && box.y >= 0 && box.x + box.width <= size.width + 1 && box.y + box.height <= size.height + 1, `${name}: ${selector}`);
    }
    assert.equal(await page.locator('#assistant-conversation').evaluate(el => el.scrollWidth <= el.clientWidth + 1), true);
    await page.screenshot({ path: resolve(output, name + '.png') });
    record(name + ': panel, controles y texto dentro de pantalla');
}

try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await open(page);
    for (const [message, expected] of [
        ['Como puedo pedir un carrop', 'knowledge'],
        ['como se renta esto ?', 'knowledge'],
        ['cuantas personas caben en un sedan', 'vehicles'],
        ['yo quiero tener un mejor resultado', 'clarification'],
        ['crea una renta para el jueves', 'clarification'],
    ]) {
        const result = await ask(page, message);
        assert.equal(result.source, expected, message);
        if (message.includes('jueves')) assert.match(result.reply, /no crear solicitudes.*jueves/s);
        if (message.includes('caben')) assert.equal(result.vehicles[0].passengers, 5);
    }
    await capture(page, 'lenguaje-cotidiano');
    await page.getByRole('button', { name: 'Nueva conversación', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('#assistant-reset').disabled);
    record('Cinco preguntas originales reciben orientación, capacidad o aclaración sin inventar ni reservar');
    let data = await ask(page, 'Busco una camioneta automática para siete personas');
    assert.equal(data.vehicles.length, 1);
    assert.match(data.vehicles[0].name, /Mazda/);
    record('Búsqueda combinada y capacidad en palabras');
    data = await ask(page, `Del ${start} al ${end}`);
    assert.equal(data.vehicles[0].availability_checked, true);
    data = await ask(page, '¿Y el más barato?');
    assert.match(data.vehicles[0].name, /Mazda/);
    data = await ask(page, '¿Cuánto cuesta rentarlo tres días?');
    assert.equal(data.estimate.total, '4200.00');
    record('Conversación de cuatro mensajes con fechas, filtros y cotización');
    await ask(page, 'yo quiero tener un mejor resultado');
    const criterionResponse = page.waitForResponse(r => r.url().endsWith('/asistente/consultar/'));
    await page.getByRole('button', { name: 'Precio', exact: true }).click();
    const criterion = await (await criterionResponse).json();
    assert.match(criterion.vehicles[0].name, /Mazda/);
    await page.waitForFunction(() => !document.querySelector('#assistant-form').hasAttribute('aria-busy'));
    record('Elegir criterio desde sugerencias conserva SUV, transmisión, plazas y fechas');
    assert.ok(await page.getByRole('link', { name: 'Ver vehículo', exact: true }).last().getAttribute('href'));
    await capture(page, 'desktop');
    // Reinicio nativo, independiente de volver a cargar la página.
    await page.getByRole('button', { name: 'Nueva conversación', exact: true }).click();
    await page.waitForFunction(() => !document.querySelector('#assistant-reset').disabled);
    assert.equal(await page.locator('.assistant-message').count(), 1);
    assert.equal(await page.locator('.assistant-vehicle').count(), 0);
    data = await ask(page, '¿Cuál es el más barato?');
    assert.match(data.vehicles[0].name, /Corolla/);
    record('Nueva conversación elimina filtros y presentación anterior');
    data = await ask(page, 'Compara los SUV disponibles');
    assert.equal(data.vehicles.length, 2);
    assert.match(data.reply, /900.50/);
    record('Comparación de vehículos reales');
    const foreign = await browser.newContext();
    const other = await foreign.newPage();
    await open(other);
    data = await ask(other, '¿Cuál es el más barato?');
    assert.match(data.vehicles[0].name, /Corolla/);
    await foreign.close();
    record('Separación de sesiones');
    await ask(page, '¿Los vehículos incluyen seguro de cobertura amplia?');
    const xss = '<img src=x onerror="window.chatXss=true">';
    await ask(page, xss);
    assert.equal(await page.evaluate(() => window.chatXss), undefined);
    assert.equal(await page.locator('#assistant-conversation img').count(), 0);
    assert.equal(await page.locator('.from-user').last().innerText(), xss);
    record('XSS mostrado como texto');
    const csrf = await context.request.post(base + '/asistente/consultar/', { data: { message: 'Hola' } });
    assert.equal(csrf.status(), 403);
    record('POST sin CSRF rechazado');
    await page.getByRole('button', { name: 'Cerrar asistente' }).click();
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.reload();
    await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
    // Simular una caché anterior, comprobar que la activación v10 la retira.
    await page.evaluate(async () => {
        await caches.open('drivesmart-public-chat2-old');
        const registration = await navigator.serviceWorker.ready;
        await registration.unregister();
    });
    await page.reload();
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.waitForFunction(async () => !(await caches.keys()).includes('drivesmart-public-chat2-old'));
    await page.getByRole('button', { name: 'Asistente DriveSmart', exact: true }).click();
    data = await ask(page, 'Precio del Corolla tres días');
    assert.equal(data.estimate.total, '2250.75');
    const cached = await page.evaluate(async () => {
        const result = {};
        for (const name of await caches.keys()) result[name] = (await (await caches.open(name)).keys()).map(r => new URL(r.url).pathname);
        return result;
    });
    assert.ok(cached['drivesmart-public-v10']);
    for (const paths of Object.values(cached)) assert.ok(paths.every(path => path === '/offline/' || path === '/catalogo-sin-conexion/' || path.startsWith('/static/') || path.startsWith('/media/vehicles/')));
    record('Activación PWA v10, retiro de caché anterior y chat operativo sin datos privados en CacheStorage');
    await page.waitForFunction(() => document.querySelector('.pwa-status')?.textContent.includes('Catálogo listo sin conexión'));
    await context.setOffline(true);
    await page.goto(base + '/vehiculos/');
    assert.match(await page.locator('body').innerText(), /Necesitas conexión a internet/);
    await context.setOffline(false);
    record('Catálogo público offline, sin almacenar conversación ni páginas privadas');
    await context.close();
    for (const [width, height] of [[768, 900], [390, 844], [320, 568], [844, 390]]) {
        const mobile = await browser.newContext({ viewport: { width, height } });
        const mobilePage = await mobile.newPage();
        mobilePage.on('pageerror', error => errors.push(error.message));
        await open(mobilePage);
        await ask(mobilePage, 'Compara los SUV disponibles');
        await capture(mobilePage, `viewport-${width}x${height}`);
        await mobilePage.keyboard.press('Escape');
        assert.equal(await mobilePage.locator('#assistant-panel').evaluate(el => el.open), false);
        assert.equal(await mobilePage.locator('#assistant-launcher').evaluate(el => el === document.activeElement), true);
        await mobile.close();
    }
    record('Escape y devolución del foco en cuatro tamaños');
    assert.deepEqual(errors, []);
    await writeFile(resolve(output, 'results.json'), JSON.stringify({ checks, errors, transcript, cached }, null, 2));
    console.log(JSON.stringify({ count: checks.length, checks, output }));
} finally {
    await browser.close();
}
