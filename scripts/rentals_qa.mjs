// Se ejecuta mediante rentals.browser_tests contra la base temporal de Django.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const fixture = JSON.parse(await readFile(process.argv[2], 'utf8'));
const { base, output, password, vehicle, unavailable, start, end, next_end } = fixture;
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve('.playwright');
const { chromium } = await import('playwright');
const browser = await chromium.launch({ headless: true });
const checks = [];
const errors = [];
const serverErrors = [];
const record = label => checks.push(label);
const createPath = `/vehiculos/${vehicle}/solicitar/`;

async function openPage(viewport, mobile = false) {
    const context = await browser.newContext({ viewport, isMobile: mobile, hasTouch: mobile });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
        if (response.status() >= 500 || (response.url().includes('/static/') && response.status() >= 400)) {
            serverErrors.push(response.url());
        }
    });
    return page;
}

async function capture(page, name) {
    assert.equal(await page.locator('link[rel=stylesheet]').evaluateAll(links =>
        links.length > 0 && links.every(link => link.sheet !== null)), true, `${name}: CSS`);
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

async function submitDates(page, first, last, name) {
    await page.goto(base + createPath);
    await page.locator('#id_start_date').fill(first);
    await page.locator('#id_end_date').fill(last);
    await capture(page, `${name}-formulario`);
    await page.getByRole('button', { name: 'Calcular costo', exact: true }).click();
    await page.getByRole('heading', { name: 'Revisa tu solicitud.' }).waitFor();
    await capture(page, `${name}-revision`);
    await page.getByRole('button', { name: 'Confirmar solicitud', exact: true }).click();
    await page.getByRole('heading', { name: 'Solicitud registrada.' }).waitFor();
    await capture(page, `${name}-confirmacion`);
    return Number(new URL(page.url()).pathname.match(/rentas\/(\d+)/)[1]);
}

try {
    const desktop = await openPage({ width: 1440, height: 1000 });
    await desktop.goto(`${base}/vehiculos/${vehicle}/`);
    await desktop.getByRole('link', { name: 'Solicitar renta', exact: true }).click();
    assert.ok(new URL(desktop.url()).pathname.includes('/cuentas/entrar/'));
    assert.equal(new URL(desktop.url()).searchParams.get('next'), createPath);
    await desktop.locator('#id_username').fill('qa_renter');
    await desktop.locator('#id_password').fill(password);
    await desktop.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
    await desktop.getByRole('heading', { name: 'Planea tu viaje.' }).waitFor();
    record('Anónimo inicia sesión y vuelve al formulario seleccionado');

    await desktop.getByRole('link', { name: 'Mis rentas', exact: true }).click();
    await desktop.getByRole('heading', { name: 'Aún no tienes solicitudes.' }).waitFor();
    await capture(desktop, 'desktop-vacio');
    record('Mis rentas muestra el estado vacío');

    await desktop.goto(base + createPath);
    await desktop.locator('#id_start_date').fill(start);
    await desktop.locator('#id_end_date').fill(start);
    await desktop.getByRole('button', { name: 'Calcular costo', exact: true }).click();
    await desktop.getByText('La devolución debe ser posterior a la fecha de inicio.', { exact: true }).waitFor();
    await capture(desktop, 'desktop-fechas-invalidas');
    record('Fechas iguales rechazadas con error visible');

    const first = await submitDates(desktop, start, end, 'desktop');
    assert.ok((await desktop.locator('.price').innerText()).includes('2250.75'));
    await desktop.getByRole('link', { name: 'Ver mis rentas', exact: true }).click();
    assert.equal(await desktop.locator('.rental-item').count(), 1);
    await desktop.getByText('Pendiente', { exact: true }).waitFor();
    await capture(desktop, 'desktop-mis-rentas');
    record('Escritorio: cálculo de 3 días, confirmación pendiente y lista propia');

    const mobile = await openPage({ width: 390, height: 844 }, true);
    await login(mobile, 'qa_other');
    await mobile.getByRole('link', { name: 'Mis rentas', exact: true }).click();
    await mobile.getByRole('heading', { name: 'Aún no tienes solicitudes.' }).waitFor();
    const second = await submitDates(mobile, start, end, 'mobile');
    await mobile.getByRole('link', { name: 'Ver mis rentas', exact: true }).click();
    assert.equal(await mobile.locator('.rental-item').count(), 1);
    assert.ok((await mobile.locator('.rental-item').innerText()).includes(`Solicitud #${second}`));
    await capture(mobile, 'mobile-mis-rentas');
    record('Móvil: segunda solicitud pendiente con fechas coincidentes permitida');
    assert.equal((await mobile.goto(`${base}/rentas/${first}/confirmacion/`)).status(), 404);
    record('Otro usuario no puede consultar la confirmación ajena');

    const admin = await openPage({ width: 1440, height: 1000 });
    await login(admin, 'qa_admin', true);
    await admin.goto(`${base}/admin/rentals/rentalrequest/?status__exact=PENDIENTE`);
    assert.equal(await admin.locator('#result_list tbody tr').count(), 2);
    await admin.locator('#searchbar').fill('qa_renter');
    await admin.locator('#changelist-search input[type=submit]').click();
    await admin.waitForURL(url => url.searchParams.get('q') === 'qa_renter');
    assert.equal(await admin.locator('#result_list tbody tr').count(), 1);
    record('Admin filtra pendientes y busca por usuario');

    await admin.goto(`${base}/admin/rentals/rentalrequest/${first}/change/`);
    assert.equal(await admin.locator('#id_user, #id_vehicle, #id_daily_price, #id_total_cost, #id_start_date').count(), 0);
    await admin.locator('#id_status').selectOption('APROBADA');
    await admin.locator('input[name=_save]').click();
    await admin.waitForURL(url => url.pathname === '/admin/rentals/rentalrequest/');
    record('Admin aprueba y los campos históricos no son editables');

    await admin.goto(`${base}/admin/rentals/rentalrequest/${second}/change/`);
    await admin.locator('#id_status').selectOption('APROBADA');
    await admin.locator('input[name=_save]').click();
    await admin.getByText('El vehículo ya tiene una renta aprobada que coincide con estas fechas.', { exact: true }).waitFor();
    await capture(admin, 'admin-conflicto');
    record('Admin rechaza aprobar una segunda reserva superpuesta');
    await admin.locator('#id_status').selectOption('RECHAZADA');
    await admin.locator('input[name=_save]').click();
    await admin.waitForURL(url => url.pathname === '/admin/rentals/rentalrequest/');
    await mobile.goto(base + '/mis-rentas/');
    await mobile.getByText('Rechazada', { exact: true }).waitFor();
    record('Admin rechaza; el solicitante ve el nuevo estado');

    await mobile.goto(base + createPath);
    await mobile.locator('#id_start_date').fill(start);
    await mobile.locator('#id_end_date').fill(end);
    await mobile.getByRole('button', { name: 'Calcular costo', exact: true }).click();
    await mobile.getByText('El vehículo ya tiene una renta aprobada que coincide con estas fechas.', { exact: true }).waitFor();
    await capture(mobile, 'mobile-fechas-ocupadas');
    record('Nueva solicitud bloqueada en fechas aprobadas');

    await submitDates(mobile, end, next_end, 'mobile-fechas-contiguas');
    record('Solicitud contigua permitida desde el día de devolución');
    await mobile.goto(`${base}/vehiculos/${unavailable}/`);
    assert.equal(await mobile.getByRole('link', { name: 'Solicitar renta', exact: true }).count(), 0);
    await mobile.goto(`${base}/vehiculos/${unavailable}/solicitar/`);
    await mobile.getByText('Este vehículo no está disponible para solicitar renta.', { exact: true }).waitFor();
    await capture(mobile, 'mobile-no-disponible');
    record('Vehículo no disponible no permite solicitar por detalle ni URL directa');

    await mobile.goto(`${base}/admin/rentals/rentalrequest/${first}/change/`);
    assert.ok(new URL(mobile.url()).pathname.includes('/admin/login/'));
    record('Usuario normal bloqueado al intentar cambiar estado en Admin');
    await desktop.goto(base + '/mis-rentas/');
    assert.equal(await desktop.locator('.rental-item').count(), 1);
    await desktop.getByText('Aprobada', { exact: true }).waitFor();
    await capture(desktop, 'desktop-aprobada');
    await desktop.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
    await desktop.goto(base + '/mis-rentas/');
    assert.ok(new URL(desktop.url()).pathname.includes('/cuentas/entrar/'));
    record('Lista sigue aislada por usuario y queda protegida después del logout');

    assert.deepEqual(errors, []);
    assert.deepEqual(serverErrors, []);
    await writeFile(resolve(output, 'report.json'), JSON.stringify({ passed: checks.length, checks, errors, serverErrors }, null, 2));
    console.log(JSON.stringify({ passed: checks.length, errors, serverErrors, evidence: output }, null, 2));
} finally {
    await browser.close();
}
