import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
process.env.PLAYWRIGHT_BROWSERS_PATH ||= resolve('.playwright');
const {chromium}=await import('playwright');
const f=JSON.parse((await readFile(process.argv[2],'utf8')).replace(/^\uFEFF/,''));
const {createServer}=await import('node:http');
const browser=await chromium.launch({headless:true});
const results=[]; const errors=[];
try {
 for(const width of [1440,768,390,320]) {
  const context=await browser.newContext({viewport:{width,height:1000},isMobile:width<500,hasTouch:width<500});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  async function capture(name){
   await page.locator('link[rel=stylesheet]').evaluateAll(links=>Promise.all(links.map(l=>l.sheet?true:new Promise(r=>l.onload=r))));
   const quality = await page.evaluate(() => ({
    controls: [...document.querySelectorAll('button, input:not([type=hidden]), select, textarea')].filter(e=>e.getClientRects().length).filter(e=>e.getBoundingClientRect().height<44).map(e=>e.outerHTML.slice(0,90)),
    columns: document.querySelector('.vehicle-grid') ? getComputedStyle(document.querySelector('.vehicle-grid')).gridTemplateColumns.split(' ').length : null
   }));
   assert.deepEqual(quality.controls,[],`${width}-${name}: controles táctiles`);
   if (quality.columns) assert.equal(quality.columns,width>=1000?3:width>=640?2:1);
   await page.screenshot({path:resolve(f.output,`${width}-${name}.png`),fullPage:true});
   results.push({width,name,overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),quality,brokenImages:await page.locator('img').evaluateAll(images=>images.filter(i=>!i.complete||i.naturalWidth===0).length)});
  }
  for(const [name,path] of [['inicio','/'],['catalogo','/vehiculos/'],['detalle',`/vehiculos/${f.vehicle}/`],['registro','/cuentas/registro/'],['login','/cuentas/entrar/']]){await page.goto(f.base+path);await capture(name);}
  await page.locator('#id_username').focus();
  assert.equal(await page.locator('#id_username').evaluate(e=>getComputedStyle(e).outlineStyle),'solid');
  assert.equal(await page.locator('#id_username').evaluate(e=>e.labels.length>0),true);
  await page.locator('#id_username').fill('visual_user');await page.locator('#id_password').fill(f.password);await page.locator('.auth button').click();
  await page.goto(f.base+`/vehiculos/${f.vehicle}/solicitar/`);await capture('fechas');
  await page.locator('#id_start_date').fill(f.start);await page.locator('#id_end_date').fill(f.end);await page.getByRole('button',{name:'Calcular costo',exact:true}).click();await capture('revision');
  await page.goto(f.base+`/rentas/${f.rental}/confirmacion/`);await capture('confirmacion');
  await page.goto(f.base+'/mis-rentas/');await capture('rentas');
  await page.locator('#assistant-launcher').click();await page.locator('#assistant-message').fill('precio del Toyota Corolla');await page.locator('#assistant-form button').click();await page.locator('.assistant-vehicle').first().waitFor();await capture('asistente');
  await page.getByRole('button',{name:'Cerrar asistente',exact:true}).click();assert.equal(await page.locator('#assistant-panel').evaluate(e=>e.open),false);
  await page.goto(f.base+'/vehiculos/');
  await page.locator('#categoria').selectOption('sedan');await page.getByRole('button',{name:'Filtrar',exact:true}).click();
  assert.equal(await page.locator('.vehicle-card').count(),2);
  assert.ok((await page.locator('.vehicle-card').allTextContents()).every(s=>s.includes('Sedán')));
  await page.goto(f.base+'/');await page.evaluate(()=>document.body.style.fontSize='32px');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'texto ampliado');
  await context.close();
 }
 await writeFile(resolve(f.output,'report.json'),JSON.stringify({results,errors},null,2));
 console.log(JSON.stringify({screenshots:results.length,overflows:results.filter(r=>r.overflow),broken:results.filter(r=>r.brokenImages),errors}));
 assert.equal(errors.length,0);
 assert.equal(results.filter(r=>r.overflow||r.brokenImages).length,0);
 await verifyCacheUpgrade();
} finally {await browser.close();}

async function verifyCacheUpgrade() {
 const currentWorker=await readFile('static/pwa/service-worker.js','utf8');
 const currentCss=await readFile('static/css/site.css','utf8');
 // Fixture de una hoja anterior: permite verificar la renovación sin necesitar Git.
 const oldCss=currentCss.replace('--control-radius: 8px','--control-radius: 5px');
 let upgraded=false;
 const server=createServer(async(req,res)=>{
  try {
   if(req.url==='/service-worker.js') {res.writeHead(200,{'Content-Type':'application/javascript','Cache-Control':'no-cache','Service-Worker-Allowed':'/'});res.end(upgraded?currentWorker:currentWorker.replace('${CACHE_PREFIX}v2','${CACHE_PREFIX}v1'));return;}
   if(req.url==='/static/css/site.css') {res.writeHead(200,{'Content-Type':'text/css','Cache-Control':'no-store'});res.end(upgraded?currentCss:oldCss);return;}
   const response=await fetch(f.base+req.url,{redirect:'manual'});
   res.writeHead(response.status,{'Content-Type':response.headers.get('content-type')||'application/octet-stream'});res.end(Buffer.from(await response.arrayBuffer()));
  } catch(error) {res.writeHead(500);res.end(String(error));}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const context=await browser.newContext();const page=await context.newPage();
 try {
  const base=`http://127.0.0.1:${server.address().port}`;
  await page.goto(base);await page.evaluate(()=>navigator.serviceWorker.ready);await page.waitForFunction(()=>navigator.serviceWorker.controller);
  assert.ok(await page.evaluate(async()=>(await caches.keys()).includes('drivesmart-public-v1')));
  await page.reload();
  assert.equal(await page.locator('.button').first().evaluate(e=>getComputedStyle(e).borderRadius),'5px');
  await page.evaluate(()=>window.previousController=navigator.serviceWorker.controller);
  upgraded=true;
  await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();});
  await page.waitForFunction(async()=>{const keys=await caches.keys();return keys.includes('drivesmart-public-v2')&&!keys.includes('drivesmart-public-v1');});
  await page.waitForFunction(()=>navigator.serviceWorker.controller!==window.previousController);
  await page.reload();
  assert.equal(await page.locator('.button').first().evaluate(e=>getComputedStyle(e).borderRadius),'8px');
  assert.equal(await page.evaluate(async()=>{const c=await caches.open('drivesmart-public-v2');return(await c.match('/static/css/site.css')).text();}),currentCss);
  await writeFile(resolve(f.output,'cache-upgrade.json'),JSON.stringify({from:'v1',to:'v2',oldRemoved:true,cssMatchesSource:true,computedButtonRadius:'8px'},null,2));
  console.log('Actualización real v1 → v2: CSS nuevo, caché anterior eliminada.');
 } finally {await context.close();await new Promise(r=>server.close(r));}
}
