# Auditoría DriveSmart — Beta 0.1

Fecha: 6 de noviembre de 2026 (America/Mexico_City).
Revisión auditada: `1f39738`, rama `main`.

**Recomendación: APTO para avanzar a la fase 3 como desarrollo local.**
Las funciones de las fases 0, 1 y 2 verificadas funcionan. La configuración actual
**NO es apta para producción**: `check --deploy` emite seis advertencias.
No se inició la fase 3, no se hicieron commits ni push y no se modificó código de aplicación.

## Alcance y conservación de datos

Se leyeron AGENTS.md, README.md, INSTRUCTIONS.txt, docs/PROGRESO.md, documentación
de QA, dependencias, configuración, URLs, vistas, modelo, Admin, migración,
plantillas, CSS, comando demo y pruebas existentes.
La estructura mantiene `config`, `core`, `accounts` y `vehicles`, Django Auth/Admin,
Templates y SQLite. No se añadieron funcionalidades, dependencias al proyecto ni cambios de arquitectura.

La base original se consultó en modo SQLite de solo lectura. Contiene seis vehículos,
un usuario, cero imágenes subidas y cero vehículos fuera de los rangos de precio,
pasajeros y año comprobados. `PRAGMA integrity_check` devolvió `ok`.
Su SHA-256 inicial y final coincide:

```text
2593f1d297f3fe209848eff4eb212a2b3504d3d591e81a625851e2d1f877974c
```

Registro, sesiones, carga demo y CRUD de navegador se ejecutaron exclusivamente
contra una base nueva en `test-results/audit-20261106/audit.sqlite3`, con media
separada. Las eliminaciones del CRUD afectaron únicamente vehículos creados por
esta auditoría en esa base aislada. No se borraron datos ni archivos preexistentes.
Las pruebas Django utilizaron su base temporal en memoria.

## Resultados por componente

| Componente evaluado | Resultado | Evidencia obtenida | Problema detectado | Corrección realizada |
|---|---|---|---|---|
| Entorno y dependencias | APROBADO | Python 3.12.10; Django 5.2.19; Pillow 12.3.0; `pip check` correcto en ambos entornos | Ninguno en dependencias declaradas | Ninguna |
| Estructura y alcance | APROBADO | Módulos, rutas y recursos revisados; Auth/Admin nativos | Ninguna función de fases posteriores implementada | Ninguna |
| Django check | APROBADO | `check.txt`: cero incidencias | Ninguno | Ninguna |
| Suite Django | APROBADO | `tests.txt`: 9/9, 2,505 s; `repro-tests.txt`: 9/9, 2,295 s | Ninguna prueba de aplicación fallida | Ninguna |
| Cambios de modelos | APROBADO | `makemigrations --check --dry-run`: No changes detected | Ninguno | No se generaron migraciones |
| Migraciones actuales | APROBADO | `showmigrations` completo y `migrate --plan`: No planned migration operations | Ninguna pendiente | Ninguna |
| Inicio | APROBADO | HTTP 200; capturas escritorio, 390 y 320 px; servidor de entorno nuevo HTTP 200 | Ninguno observado | Ninguna |
| Registro | APROBADO | Usuario creado por UI; rechazo de contraseñas distintas; pruebas Django de registro inválido | Ninguno observado | Ninguna |
| Inicio/cierre de sesión | APROBADO | Login y logout por UI; sesión verificada por Django; GET logout devuelve 405 | Ninguno observado | Ninguna |
| CSRF | APROBADO | POST sin token devuelve 403 en Django y en petición desde contexto de navegador | Ninguno en el caso probado | Ninguna |
| Catálogo y filtros | APROBADO | Seis tarjetas; filtros SUV/compacto, limpiar y categoría inexistente | Ninguno observado | Ninguna |
| Detalle | APROBADO | Seis detalles por Django; navegación de UI; precio, características y disponibilidad; 404 esperado | Ninguno observado | Ninguna |
| Login administrativo | APROBADO | Anónimo redirigido a login; superusuario entra; captura `admin-inicio.png` | Ninguno observado | Ninguna |
| CRUD administrativo | APROBADO | Creación con PNG, modificación de modelo/precio/disponibilidad, eliminación y 404 posterior; también prueba Django | Ninguno observado | Ninguna |
| Usuario normal | APROBADO | Redirigido a login administrativo con mensaje de falta de autorización; Django bloquea acceso y POST de creación | Ninguno observado | Ninguna |
| Carga de ejemplos | APROBADO | Dos ejecuciones: 6 → 6 y filas idénticas en base aislada; repetido desde cero en entorno nuevo | Ninguno en ejecución secuencial | Ninguna |
| Imágenes | APROBADO | Tres SVG locales cargan; PNG de 400 px subido por Admin carga desde `/media/vehicles/` | Ninguno observado | Ninguna |
| Escritorio y móvil | APROBADO | 1440×1000, 390×844, 320×740; sin overflow horizontal en cuatro pantallas públicas; Admin móvil; filtro con toque sintetizado | Ningún defecto visual importante en las capturas revisadas | Ninguna |
| Base original | APROBADO | Integridad `ok`, consultas válidas, SHA-256 idéntico antes/después | Ninguno observado | Ninguna |
| Git y exclusiones | APROBADO | `git ls-files .env db.sqlite3 .venv` vacío; `git check-ignore` confirma exclusión; migración versionada | Ninguno observado | Ninguna |
| Secretos en código propio versionado | APROBADO | Revisión de configuración y `.env.example`; patrones habituales sin coincidencias sospechosas; ejemplos y contraseñas de pruebas identificados | Clave pública de desarrollo deliberada, no una credencial de producción | Ninguna; advertencia de producción separada |
| Configuración para producción | FALLIDO | `check --deploy`: W004, W008, W009, W012, W016, W018 | HSTS/HTTPS/cookies seguras sin configurar, clave de desarrollo y DEBUG activo | No se cambió configuración local ni se preparó despliegue |
| Protección contra producción sin clave | APROBADO | `DJANGO_DEBUG=0` sin secreto personalizado produce `ImproperlyConfigured` | Ninguno en esa protección | Ninguna |
| Reproducibilidad en Windows actual | APROBADO | Venv nuevo, instalación con requirements, migrate desde cero, dos cargas demo, tests y arranque HTTP 200 | Descarga inicial bloqueada por sandbox | Reintento de pip con permiso específico; sin cambiar sandbox |
| Otra computadora Windows | NO VERIFICADO | Prueba reproducida en entorno limpio del mismo equipo; instrucciones y rutas revisadas | No hubo un segundo equipo disponible | Ninguna |
| Playwright Interactive | NO VERIFICADO | SKILL.md exige `danger-full-access` | Incompatible con conservar las protecciones requeridas | Se utilizó Playwright convencional ya instalado |
| Impeccable | APROBADO | Contexto y detector ejecutados; revisión de capturas | Dos falsos positivos y resolución incompleta de etiquetas static de Django | No se rediseñó la interfaz |
| Code Simplification | APROBADO | Revisión de vistas, modelo, Admin y comando después de tests correctos | No se identificó complejidad que justificase una corrección en esta auditoría | Sin refactorizaciones |
| Dispositivo físico, lector de pantalla y otros motores | NO VERIFICADO | Chromium headless y viewports emulados; toque sintetizado en contexto móvil | Cobertura limitada a ese mecanismo | Ninguna |

## Número real de pruebas

- Suite Django existente: **9 pruebas distintas, ejecutadas dos veces, 18 ejecuciones aprobadas**.
  La primera ejecución usó `.venv`; la segunda, el entorno nuevo de reproducción.
- Navegador, flujo público: **16 grupos de comprobaciones aprobados**.
- Navegador, administración y seguridad: **10 grupos de comprobaciones aprobados**
  en la ejecución final. Ambos scripts finales terminaron con código 0 y sin `pageerror`.
- Total de escenarios distintos contabilizados: **9 pruebas Django + 26 grupos de navegador**.
  No se cuentan los asserts internos de cada grupo como pruebas adicionales.
- Se guardaron **25 capturas**: 19 del flujo público y 6 del administrativo.
- Check, migraciones, integridad, instalación y guardia de producción son verificaciones
  adicionales; no se suman artificialmente al número de pruebas Django.

Los nueve tests Django cubren: CSRF; inicio/formularios; registro/login inválidos;
registro/login/logout y permisos; CRUD administrativo y denegación; catálogo/detalles/filtro;
carga demo repetible con conservación de ediciones; estados vacíos/404/no disponible;
validación de precio/pasajeros/año.

## Problemas e incidencias

1. **Configuración de producción pendiente.** `check --deploy` terminó con código 0,
   pero emitió seis advertencias, que no se interpretan como aprobación de despliegue.
   Los valores actuales son adecuados únicamente para el uso local documentado.
   Antes de publicar se necesitará una clave aleatoria privada, DEBUG desactivado y
   configuración de HTTPS, cookies seguras y HSTS conforme al despliegue elegido.
   No se hicieron esos cambios porque no se está desplegando la aplicación.
2. **Primer intento del script adicional de navegador fallido por sincronización del test.**
   Tras tocar Filtrar se leyó el DOM anterior (6 tarjetas) antes de finalizar la
   navegación. Se añadió `waitForURL` al script local de auditoría; la repetición
   verificó 2 compactos y 6 vehículos al limpiar. No se atribuye ese fallo a Django.
3. **Pip bloqueado por WinError 10013 dentro del sandbox.** El reintento autorizado
   instaló exactamente requirements en el entorno nuevo; no se cambiaron políticas.
4. **Detector Impeccable limitado con Django Templates.** No resuelve `{% static %}`
   al leer HTML fuente; los avisos `side-tab` en site.css:218–219 son bordes de la
   carretera decorativa, no tarjetas. No justifican cambios de diseño.

No se detectaron defectos funcionales de aplicación que requiriesen correcciones.

## Revisión visual y de simplicidad

Las capturas revisadas directamente incluyen inicio y catálogo de escritorio,
catálogo y detalle móvil, registro a 320 px, error de registro, Admin de edición
móvil, bloqueo de Admin para usuario normal y detalle con imagen subida.
No se observaron textos recortados, superposiciones ni imágenes rotas en esas vistas.
La navegación y los formularios mantienen etiquetas, foco visible y recursos locales.

Valoración interna Impeccable, no certificación WCAG ni medición de rendimiento:

| Dimensión | Puntuación / 4 | Evidencia y límite |
|---|---:|---|
| Accesibilidad | 3 | Labels, alt, foco y salto al contenido; no lector de pantalla ni auditoría completa de contraste |
| Rendimiento | 3 | Recursos locales pequeños y sin frameworks JS; no se realizó perfilado de rendimiento |
| Tema | 2 | Variables principales y colores puntuales directos; no hay requisito de múltiples temas |
| Responsive | 3 | Tres anchos, Admin móvil y toque sintetizado; sin teléfono físico |
| Integridad | 4 | Composición consistente, precios/categorías claros y dos falsos positivos contextualizados |
| Total | **15/20** | Buena base para la beta local |

No se identificaron incidencias P0/P1 visuales en la cobertura realizada. La ausencia
de esas incidencias no certifica accesibilidad completa. No se proponen rediseños.
Code Simplification no encontró motivos para cambiar las funciones cortas existentes
ni sustituir los componentes nativos. Los comentarios de scaffold y las plantillas
compactas no se modificaron: son asuntos de estilo, no defectos comprobados.

## Reproducibilidad

INSTRUCTIONS.txt describe creación de `.venv`, instalación, variables en PowerShell,
migraciones, creación de administrador, demo, runserver y pruebas. Explica correctamente
que `.env.example` no se carga automáticamente y que las skills no son requisitos
de ejecución. No requiere activar scripts ni cambiar la política de PowerShell.

Se creó `test-results/audit-20261106/repro-venv` y se instalaron las dos dependencias
directas de requirements, sin Node ni skills para ejecutar Django. Una configuración
local de prueba apuntó a `repro.sqlite3`, nueva y separada: migrate correcto, demo
dos veces con seis registros, nueve tests correctos, pip check correcto y servidor
en 127.0.0.1:8012 con inicio y catálogo HTTP 200. También se comprobó la ayuda del
comando createsuperuser; el login de un superusuario real se probó en el otro entorno aislado.
La única adaptación de rutas fue el nombre del entorno y de la base de auditoría.

## Evidencia local

Directorio conservado y excluido de Git: `test-results/audit-20261106/`.
Sus bases, usuarios y contraseñas de fixtures se usan solo para esta auditoría.
No deben emplearse para operación real. Los servidores iniciados para la auditoría
se detuvieron al terminar las verificaciones.

- [Tests Django](../test-results/audit-20261106/tests.txt).
- [Plan de migraciones](../test-results/audit-20261106/migration-plan.txt).
- [Advertencias de despliegue](../test-results/audit-20261106/deploy.txt).
- [Informe del flujo público](../test-results/audit-20261106/browser/browser-report.json).
- [Informe de Admin y seguridad](../test-results/audit-20261106/admin/report.json).
- [Tests del entorno limpio](../test-results/audit-20261106/repro-tests.txt).
- [Comprobaciones de reproducción](../test-results/audit-20261106/repro-report.json).
- [Revisión de secretos y hash original](../test-results/audit-20261106/security.json).
- [Inicio escritorio](../test-results/audit-20261106/browser/desktop-inicio.png).
- [Catálogo móvil](../test-results/audit-20261106/browser/mobile-catalogo.png).
- [Edición Admin móvil](../test-results/audit-20261106/admin/admin-editar-mobile.png).
- [Usuario normal bloqueado](../test-results/audit-20261106/admin/normal-admin-bloqueado-mobile.png).

La copia del script público cambia únicamente el destino de evidencia y usa la URL
aislada mediante DRIVESMART_URL. El script administrativo adicional y los runners
son artefactos locales de auditoría; no se modificó scripts/browser_qa.mjs.

## Archivos y Git al finalizar

Único archivo nuevo visible en Git: `docs/AUDITORIA_BETA_01.md` (sin seguimiento).
Archivos existentes de aplicación, pruebas, dependencias y documentación: sin cambios.
Se crearon scripts, logs, capturas, bases y un venv dentro de `test-results/`, ignorado.
No se eliminó ningún archivo existente.

Historial conservado:

```text
1f39738 style: facilitar lectura de hojas CSS sin cambiar comportamiento
4b51371 feat: implementar catalogo y administracion de vehiculos
15d92b0 feat: crear base Django y autenticacion
757623d chore: preparar entorno y herramientas DriveSmart
```

`git ls-files .env db.sqlite3 .venv` no devuelve entradas. La migración
`vehicles/migrations/0001_initial.py` y requirements.txt sí están versionados.
No hay remoto configurado. No se cambió el historial, no se creó commit y no hubo push.

## Riesgos pendientes y decisión

- Preparación de producción pendiente; no exponer el servidor de desarrollo.
- No se ejecutó un escaneo exhaustivo de vulnerabilidades de dependencias ni una
  auditoría de seguridad externa. La revisión de secretos por patrones y lectura
  no garantiza la ausencia de cualquier secreto posible.
- No se verificaron teléfonos físicos, Safari/Firefox ni lectores de pantalla.
- No se probó otra computadora; sí un entorno Python nuevo en este Windows.
- La carga demo se comprobó secuencialmente, no con ejecuciones concurrentes.
- El script público original usa un nombre de usuario fijo; para repetirlo conviene
  otra base de auditoría nueva, sin eliminar usuarios del entorno real.

**APTO para comenzar el desarrollo local de la fase 3 cuando el usuario lo indique.**
Las advertencias de despliegue deben resolverse antes de producción y no se consideran
un bloqueo para seguir desarrollando localmente. Esta auditoría no autoriza ni inicia
la fase 3 y deja su documento sin commit para revisión.
