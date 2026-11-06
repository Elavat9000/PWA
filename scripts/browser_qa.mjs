import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const base = process.env.DRIVESMART_URL || 'http://127.0.0.1:8000';
const output = 'test-results';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
const checks = [];
try {
  for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844], ['small', 320, 740]]) {
    const context = await browser.newContext({ viewport: { width, height } });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    for (const [route, title] of [['/', 'inicio'], ['/vehiculos/', 'catalogo'], ['/cuentas/entrar/', 'login'], ['/cuentas/registro/', 'registro']]) {
      assert.equal((await page.goto(base + route)).status(), 200);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${name} ${route}: overflow`);
      assert.equal(await page.locator('img').evaluateAll(images => images.every(img => img.complete && img.naturalWidth > 0)), true);
      await page.screenshot({ path: `${output}/${name}-${title}.png`, fullPage: true });
      checks.push(`${name}: ${title}, sin desbordamiento ni imágenes rotas`);
    }
    await page.getByRole('link', { name: 'Catálogo', exact: true }).click();
    assert.equal(await page.locator('.vehicle-card').count(), 6);
    await page.getByLabel('Categoría', { exact: true }).selectOption('suv');
    await page.getByRole('button', { name: 'Filtrar', exact: true }).click();
    assert.equal(await page.locator('.vehicle-card').count(), 2);
    await page.screenshot({ path: `${output}/${name}-filtro.png`, fullPage: true });
    await page.getByRole('link', { name: 'Ver Kia' }).click();
    await page.getByRole('heading', { name: 'Kia Seltos' }).waitFor();
    await page.screenshot({ path: `${output}/${name}-detalle.png`, fullPage: true });
    await page.getByRole('link', { name: 'Volver al catálogo' }).click();
    assert.equal(await page.locator('.vehicle-card').count(), 6);
    await page.goto(base + '/vehiculos/?categoria=inexistente');
    await page.getByRole('heading', { name: 'No hay vehículos en esta categoría.' }).waitFor();
    await page.getByRole('link', { name: 'Ver todos los vehículos' }).click();
    checks.push(`${name}: filtrar SUV, detalle, volver y categoría vacía`);
    await context.close();
  }
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(base + '/cuentas/registro/');
  await page.locator('#id_username').fill('qa_browser_drivesmart');
  await page.locator('#id_password1').fill('Carretera!8973x');
  await page.locator('#id_password2').fill('no-coincide');
  await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  assert.ok(await page.locator('.errorlist').count());
  await page.screenshot({ path: `${output}/registro-error.png`, fullPage: true });
  await page.locator('#id_password1').fill('Carretera!8973x');
  await page.locator('#id_password2').fill('Carretera!8973x');
  await page.getByRole('button', { name: 'Crear cuenta', exact: true }).click();
  await page.getByText('Hola, qa_browser_drivesmart').waitFor();
  assert.equal(await page.getByRole('link', { name: 'Administración', exact: true }).count(), 0);
  await page.getByRole('button', { name: 'Cerrar sesión' }).click();
  await page.getByRole('link', { name: 'Iniciar sesión', exact: true }).click();
  await page.locator('#id_username').fill('qa_browser_drivesmart');
  await page.locator('#id_password').fill('Carretera!8973x');
  await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
  await page.getByText('Hola, qa_browser_drivesmart').waitFor();
  await page.getByRole('button', { name: 'Cerrar sesión' }).click();
  checks.push('Registro inválido y válido, login, logout y ausencia de enlace administrativo para usuario normal');
  assert.deepEqual(errors, []);
  await writeFile(`${output}/browser-report.json`, JSON.stringify({ checks, errors }, null, 2));
  console.log(JSON.stringify({ passed: checks.length, errors }, null, 2));
} finally {
  await browser.close();
}
