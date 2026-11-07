# DriveSmart — Fase 5: PWA y entrega

Fecha: 6 de noviembre de 2026 (America/Mexico_City). Base: `da997a7`.
**Estado: APTO PARA ENTREGA como prueba técnica local. No apto para producción.**

## PWA mínima

Implementados:

- `/manifest.webmanifest`: name/short_name DriveSmart, start_url y scope `/`,
  display standalone, tema `#17604e` y fondo `#f6f5ef` del diseño existente.
- Iconos PNG locales de 192×192 y 512×512, iniciales DS y colores de DriveSmart.
- `/service-worker.js`, servido desde raíz con MIME JavaScript, scope `/` y no-cache.
- Registro progresivo en `static/js/pwa.js`: la web sigue funcionando si el navegador
  no admite Service Workers o falla el registro.
- `/offline/`: archivo estático con el aviso exacto de conexión requerida.
- Cabeceras no-store para las respuestas dinámicas y recarga al restaurar historial.

No se modificó la lógica de autenticación, rentas, usuarios, Vehicle o asistente.
No se instalaron dependencias ni se generaron migraciones. Solo se añadió middleware
de política de caché, probado sobre el defecto reproducido de falta de no-store en
Mis rentas. No se cambió configuración HTTPS de localhost ni de producción.

## Caché y comportamiento sin conexión

La caché `drivesmart-public-v1` contiene exactamente nueve recursos seleccionados:
offline, cuatro CSS, dos JavaScript estáticos y dos iconos. Se inspeccionaron las
claves reales del navegador antes y después de navegar por páginas privadas.
No contiene Admin, cuentas, Mis rentas, formularios/confirmaciones, HTML dinámico,
JSON del asistente, sesiones ni respuestas POST. Una URL estática con parámetros
no se incorpora a la lista. Las versiones antiguas se limpian al activar el worker;
otras cachés ajenas al prefijo no se eliminan.

Las consultas dinámicas GET usan red sin caché HTTP; los POST no son interceptados
ni se encolan. Si falta conexión al inicio, catálogo o detalle público, se muestra:

> DriveSmart necesita conexión a internet para consultar vehículos, gestionar rentas y utilizar el asistente.

No aparecen vehículos, solicitudes o chat simulados offline. Las páginas privadas y
POST fallan por falta de red, sin devolver una copia personal. Al recuperar conexión,
se consulta de nuevo el servidor. Se comprobó también el botón Atrás tras logout y
el inicio con otro usuario: únicamente se mostraron las solicitudes del usuario actual.

Para futuras modificaciones de estáticos se debe incrementar v1 en el worker.
No hay sincronización ni motor offline de rentas o conversaciones.

## Pruebas finales reales

Comandos ejecutados:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py test assistant.browser_tests rentals.browser_tests core.browser_tests --verbosity 2
.\.venv\Scripts\python.exe manage.py check --deploy
```

| Verificación | Resultado |
|---|---|
| Check | Sin incidencias |
| Migraciones | No hay cambios de modelo ni operaciones pendientes |
| Suite Django | **73/73 correctas**, 5,791 s: 65 anteriores y 8 nuevas |
| Pruebas de navegador | **3/3 correctas**, 22,483 s |
| Grupos internos del navegador | 14 asistente + 15 rentas + 18 PWA, correctos |
| Instalación ZIP, suite repetida | **73/73 correctas**, 5,936 s en un entorno nuevo |
| Check --deploy | Seis advertencias de producción; no se consideran aprobación de despliegue |

Hay **76 pruebas distintas aprobadas** en la regresión principal. Los grupos internos
de navegador y la repetición desde ZIP no se suman como pruebas nuevas distintas.

Playwright convencional verificó escritorio 1440×1000 y móvil 390×844, manifiesto,
iconos HTTP 200, worker activo, control raíz, caché permitida, registro/login/logout,
precio real del asistente, reservas y aprendizaje del Admin mediante las pruebas
anteriores. También verificó falta de red, recuperación, aislamiento de usuarios y
actualización de caché. Las pruebas usan bases temporales, sin afectar la de uso.

La instalación física desde un menú del sistema o un teléfono real no se verificó.
Se verificaron los componentes web de la PWA en Chromium headless, no una instalación
nativa de sistema operativo ni una certificación de todos los navegadores.

## Instalación desde el ZIP

Se generó y extrajo el ZIP en:
`test-results/phase5-20261106/installation/DriveSmart/`.

En esa copia se creó una `.venv` nueva, se instalaron los requisitos declarados y
pip check terminó correctamente. Después se ejecutaron migrate, load_demo y load_faq;
ambos comandos demo se repitieron, conservando seis vehículos y ocho FAQ sin duplicados.
La suite Django de esa copia pasó completa. No se necesitó Node ni skills para ello.

Su servidor aislado en 127.0.0.1:8015 respondió HTTP 200 en inicio, catálogo, manifiesto,
worker, aviso offline y ambos iconos. El proceso de prueba se detuvo al terminar.
No se modificó ni eliminó el entorno principal. El paquete final se vuelve a generar
con la documentación cerrada y se comprueba que su código coincide con el instalado.

La descarga inicial de pip bajo el sandbox no resolvió PyPI; el reintento con permiso
específico para las dependencias del entorno aislado funcionó. No se cambió el sandbox
ni la política de ejecución y no se agregaron dependencias al proyecto.

## Paquete y reproducibilidad

Artefacto: **DriveSmart_Beta.zip**, en la raíz del workspace.
Ubicación de esta entrega: `C:\Users\Diana\Documents\PWA\DriveSmart_Beta.zip`.

El ZIP contiene una carpeta DriveSmart con código de config/core/accounts/vehicles/
rentals/assistant, migraciones, templates, estáticos, SVG demo, PNG PWA, requirements,
INSTRUCTIONS, README, .env.example, AGENTS, documentación y comandos demo. Incluye
scripts y package.json/lock únicamente para QA opcional; Node no es requisito de ejecución.

Se excluyen .git, .venv, .env, SQLite, node_modules, media personal, skills, test-results,
logs, cachés Python, archivos de claves y credenciales. Los passwords de fixtures en
los tests son valores de prueba, no credenciales de cuentas entregadas: el ZIP no
contiene usuarios ni bases personales. .env.example contiene solo marcadores locales.

El empaquetador `scripts/package_beta.py` usa una lista de carpetas/archivos permitidos,
rechaza rutas fuera del proyecto y evita enlaces simbólicos, binarios temporales y
patrones conocidos de claves privadas/tokens. Se inspeccionaron los nombres del ZIP.
Esta revisión no se presenta como un escaneo exhaustivo de seguridad.

INSTRUCTIONS.txt describe extraer, crear entorno, instalar, migrar, cargar ejemplos,
crear administrador, arrancar, probar y generar otra entrega. El empaquetador no
requiere Git, no publica y no borra datos locales. El ZIP es un artefacto generado,
ignorado por Git; se versionan su código y documentación, no el binario de entrega.

## Datos originales y revisión de calidad

El SHA-256 inicial y el observado en la revisión posterior difieren:

```text
Inicial:  86ad3408de16b6be9653d396c68633e7e2b5f0431febb7d8d9d2ce789975b228
Revisión: bce3b12c42a3f5badd759f20316f1062d5fd38f9f7cc731d21f1890e9c424c27
```

No se ejecutaron migraciones o comandos de carga sobre la base de uso en esta fase;
solo se consultó el plan. Migraciones y demos se ejecutaron en bases de prueba/copias.
La base local permaneció disponible y se observaron dos preguntas pendientes nuevas,
además de las ocho FAQ publicadas. Frente al snapshot anterior, vehículos y rentas
coinciden; no falta ningún usuario y su único campo cambiado es last_login. La integridad
SQLite es correcta. No se afirma identidad byte a byte ni se restaura una copia antigua:
se conserva esa actividad local sin eliminar registros. Esa base no forma parte del ZIP.

Impeccable revisó las capturas online/offline y la consistencia con el diseño existente.
Su detector advirtió sobre el fondo crema del aviso: se conserva porque es la paleta
establecida y la instrucción fue no rediseñar. No se detectaron recortes o cambios
visuales importantes en las vistas verificadas. No hay hooks ni Impeccable Live.

Code Simplification revisó solo las vistas PWA, middleware, worker, registro y
empaquetador nuevos. La selección de caché permanece explícita, las respuestas de
archivos comparten un helper y el paquete usa listas permitidas. No se añadieron
abstracciones ni se refactorizaron las aplicaciones anteriores.

Se corrigió un problema del harness de actualización: registrar de nuevo el mismo
script activo no garantizaba una activación nueva. La prueba ahora actualiza la URL
del script y espera su activación antes de revisar la eliminación de versiones antiguas.
Se volvió a ejecutar la regresión completa con resultado correcto.

Logs: `test-results/phase5-20261106/`. Los informes históricos hacen referencia a
evidencias locales que se omiten intencionalmente del ZIP. Pueden regenerarse con
las instrucciones de QA; las capturas pueden contener nombres/solicitudes de fixtures.

## Limitaciones y cierre

- Requiere una primera visita con conexión al servidor para registrar la PWA.
- No hay datos ni operaciones comerciales offline; tampoco pagos reales.
- Instalación y opciones de menú dependen del navegador. No se probó otro equipo físico.
- Se mantienen los límites de SQLite bajo concurrencia y búsqueda textual conservadora.
- Las advertencias W004, W008, W009, W012, W016 y W018 deben resolverse antes de publicar.
  No se forzó HTTPS de producción en localhost.
- No se configuró hosting, no se creó remoto ni se ejecutó push o carga a Google Drive.

Commit local de cierre: `feat: integrar PWA y preparar entrega DriveSmart`.
**APTO PARA ENTREGA LOCAL de la beta; preparación de producción fuera de alcance.**
