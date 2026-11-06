// Fixtures y datos pertenecen exclusivamente al servidor temporal de assistant.browser_tests.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const { base, password, output, vehicle, price } = JSON.parse(await readFile(process.argv[2], 'utf8'));
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve('.playwright');
const { chromium } = await import('playwright');
const browser = await chromium.launch({ headless: true });
const checks = [];
const errors = [];
const resourceErrors = [];
const unknown = 'No tengo información suficiente para responder esa pregunta. La registraré para que el administrador pueda revisarla.';
const reviewed = 'Respuesta revisada por el administrador de esta prueba local.';
const record = label => checks.push(label);

async function newPage(width, height, mobile = false) {
    const context = await browser.newContext({ viewport: { width, height }, isMobile: mobile, hasTouch: mobile });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
        if (response.status() >= 500 || (response.url().includes('/static/') && response.status() >= 400)) {
            resourceErrors.push(response.url());
        }
    });
    return page;
}

async function capture(page, name) {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, name);
    assert.equal(await page.locator('link[rel=stylesheet]').evaluateAll(links =>
        links.length > 0 && links.every(link => link.sheet !== null)), true, `${name}: CSS`);
    const panel = page.locator('#assistant-panel[open]');
    if (await panel.count()) {
        for (const selector of ['.assistant-close', '#assistant-message', '#assistant-form button']) {
            const box = await page.locator(selector).boundingBox();
            assert.ok(box && box.x >= 0 && box.y >= 0 && box.x + box.width <= page.viewportSize().width + 1
                && box.y + box.height <= page.viewportSize().height + 1, `${name}: ${selector}`);
        }
    }
    await page.screenshot({ path: resolve(output, `${name}.png`), fullPage: true });
}

async function openChat(page) {
    await page.getByRole('button', { name: 'Asistente DriveSmart', exact: true }).click();
    await page.getByRole('dialog', { name: 'Asistente DriveSmart', exact: true }).waitFor();
}

async function ask(page, message) {
    await page.getByLabel('Tu pregunta', { exact: true }).fill(message);
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/asistente/consultar/'));
    await page.getByLabel('Tu pregunta', { exact: true }).press('Enter');
    const response = await responsePromise;
    assert.equal(response.status(), 200);
    const payload = await response.json();
    await page.waitForFunction(() => document.querySelector('#assistant-form').getAttribute('aria-busy') === null);
    assert.equal(await page.locator('.assistant-message:not(.from-user)').last().innerText(), payload.reply);
    return payload;
}

async function login(page, username, admin = false) {
    await page.goto(base + (admin ? '/admin/' : '/cuentas/entrar/'));
    await page.locator('#id_username').fill(username);
    await page.locator('#id_password').fill(password);
    if (admin) await page.locator('input[type=submit]').click();
    else await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
}

try {
    const desktop = await newPage(1440, 1000);
    for (const route of ['/', '/vehiculos/', `/vehiculos/${vehicle}/`, '/cuentas/entrar/', '/cuentas/registro/']) {
        assert.equal((await desktop.goto(base + route)).status(), 200);
        await desktop.getByRole('button', { name: 'Asistente DriveSmart', exact: true }).waitFor();
    }
    record('Botón disponible en inicio, catálogo, detalle, login y registro');
    await desktop.goto(base + '/');
    await capture(desktop, 'desktop-cerrado');
    await openChat(desktop);
    await capture(desktop, 'desktop-bienvenida');
    assert.equal(await desktop.getByLabel('Tu pregunta', { exact: true }).evaluate(el => el === document.activeElement), true);
    record('Panel abre con bienvenida y foco en el campo de pregunta');

    await desktop.route('**/asistente/consultar/', async route => {
        await new Promise(resolve => setTimeout(resolve, 200));
        await route.continue();
    });
    await desktop.getByLabel('Tu pregunta', { exact: true }).fill('¿Cómo puedo registarme?');
    await desktop.getByRole('button', { name: 'Enviar', exact: true }).click();
    await desktop.getByText('Consultando…', { exact: true }).waitFor();
    assert.equal(await desktop.getByRole('button', { name: 'Enviar', exact: true }).isDisabled(), true);
    await desktop.getByText('Usa Crear cuenta y completa el nombre de usuario y las dos contraseñas. Al terminar el registro se inicia tu sesión.', { exact: true }).waitFor();
    await desktop.unroute('**/asistente/consultar/');
    record('Procesamiento visible y FAQ reconocida con error de escritura');

    const inventory = await ask(desktop, '¿Cuánto cuesta el Toyota Corolla?');
    assert.equal(inventory.source, 'vehicles');
    assert.equal(inventory.vehicles[0].id, vehicle);
    assert.equal(inventory.vehicles[0].daily_price, price);
    await capture(desktop, 'desktop-precio-real');
    await desktop.locator('.assistant-vehicle a').last().click();
    await desktop.waitForURL(url => url.pathname === `/vehiculos/${vehicle}/`);
    record('Precio coincide con SQLite y enlace abre el detalle real');

    await openChat(desktop);
    assert.equal((await ask(desktop, '¿Los vehículos incluyen seguro de cobertura amplia?')).reply, unknown);
    await capture(desktop, 'desktop-desconocida');
    await desktop.getByRole('button', { name: 'Cerrar asistente', exact: true }).click();
    assert.equal(await desktop.locator('#assistant-launcher').evaluate(el => el === document.activeElement), true);
    record('Pregunta desconocida queda pendiente; cerrar devuelve el foco');

    const mobile = await newPage(390, 844, true);
    await login(mobile, 'qa_chat_user');
    await openChat(mobile);
    assert.equal((await ask(mobile, '¿Incluyen seguro de cobertura amplia los coches?')).reply, unknown);
    await capture(mobile, 'mobile-pendiente');
    record('Móvil consulta equivalente sin responder como conocimiento aprobado');

    const admin = await newPage(1440, 1000);
    await login(admin, 'qa_chat_admin', true);
    await admin.goto(base + '/admin/assistant/knowledgeentry/?status__exact=PENDIENTE');
    assert.equal(await admin.locator('#result_list tbody tr').count(), 1);
    await admin.locator('#searchbar').fill('seguro');
    await admin.locator('#changelist-search input[type=submit]').click();
    await admin.waitForURL(url => url.searchParams.get('q') === 'seguro');
    await admin.getByRole('link', { name: '¿Los vehículos incluyen seguro de cobertura amplia?', exact: true }).click();
    const entryId = new URL(admin.url()).pathname.match(/knowledgeentry\/(\d+)\/change/)[1];
    await admin.locator('#id_status').selectOption('PUBLICADA');
    await admin.locator('input[name=_save]').click();
    await admin.getByText('Escribe una respuesta antes de publicar.', { exact: true }).waitFor();
    await capture(admin, 'admin-respuesta-vacia');
    record('Admin encuentra una sola pendiente equivalente y bloquea publicación vacía');

    await admin.locator('#id_answer').fill(reviewed);
    await admin.locator('#id_status').selectOption('PUBLICADA');
    await admin.locator('input[name=_save]').click();
    await admin.waitForURL(url => url.pathname === '/admin/assistant/knowledgeentry/');
    record('Administrador escribe y publica la respuesta');

    const learned = await ask(mobile, '¿Los autos incluyen seguro de cobertura amplia?');
    assert.equal(learned.source, 'knowledge');
    assert.equal(learned.reply, reviewed);
    await capture(mobile, 'mobile-respuesta-publicada');
    record('Consulta similar posterior reutiliza la respuesta publicada');

    const suv = await ask(mobile, 'Busco una camionta para 5 personas');
    assert.equal(suv.source, 'vehicles');
    assert.equal(suv.vehicles.length, 2);
    assert.ok(suv.vehicles.every(v => v.passengers >= 5));
    await capture(mobile, 'mobile-vehiculos');
    record('Error camionta, capacidad y opciones reales funcionan en móvil');
    assert.equal((await ask(mobile, '¿Incluyen seguro de cobertura limitada los autos?')).source, 'pending');
    record('No confunde cobertura limitada con la respuesta sobre cobertura amplia');

    const attack = '<img src=x onerror="window.__chatInjected=1"> ¿Hay cobertura especial?';
    await ask(mobile, attack);
    assert.equal(await mobile.locator('#assistant-conversation img').count(), 0);
    assert.equal(await mobile.evaluate(() => window.__chatInjected), undefined);
    await capture(mobile, 'mobile-texto-seguro');
    record('HTML enviado por el usuario aparece como texto, sin ejecutar código');

    await mobile.setViewportSize({ width: 320, height: 480 });
    await capture(mobile, 'mobile-viewport-reducido');
    await mobile.keyboard.press('Escape');
    assert.equal(await mobile.locator('#assistant-panel').evaluate(el => el.open), false);
    await mobile.goto(`${base}/admin/assistant/knowledgeentry/${entryId}/change/`);
    assert.ok(new URL(mobile.url()).pathname.includes('/admin/login/'));
    record('Vista reducida mantiene controles; Escape cierra y usuario normal no publica');

    await desktop.goto(base + '/');
    await openChat(desktop);
    await desktop.route('**/asistente/consultar/', route => route.abort('failed'));
    await desktop.getByLabel('Tu pregunta', { exact: true }).fill('¿Puedo pagar aquí?');
    await desktop.getByRole('button', { name: 'Enviar', exact: true }).click();
    await desktop.getByText('No pude consultar en este momento. Intenta nuevamente.', { exact: true }).waitFor();
    await desktop.unroute('**/asistente/consultar/');
    assert.equal((await ask(desktop, '¿Puedo pagar aquí?')).reply,
        'No. Las solicitudes son simuladas; DriveSmart no procesa pagos.');
    record('Error de red recuperable; reintento devuelve información real de pagos');

    assert.deepEqual(errors, []);
    assert.deepEqual(resourceErrors, []);
    await writeFile(resolve(output, 'report.json'), JSON.stringify({ passed: checks.length, checks, errors, resourceErrors }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, errors, resourceErrors, evidence: output }, null, 2));
} finally {
    await browser.close();
}
