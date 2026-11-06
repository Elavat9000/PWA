# DriveSmart — Resultados de la fase 3

Fecha: 6 de noviembre de 2026. Base de trabajo: `8035e99`, cierre auditado de Beta 0.1.
Fase 3 completada y verificada localmente. No se inició la fase 4.

## Funcionalidades implementadas

- Aplicación `rentals`, con `RentalRequest`: usuario y vehículo por ForeignKey,
  inicio, devolución, precio diario histórico, total Decimal, estado y creación.
- Estados Pendiente, Aprobada y Rechazada. Toda solicitud del flujo público nace pendiente.
- Desde el detalle: **Solicitar renta**. El usuario anónimo entra por login con `next`
  y regresa al formulario del vehículo seleccionado.
- Flujo sin JavaScript adicional: elegir fechas → **Calcular costo** → revisar días,
  precio y total → **Confirmar solicitud** → confirmación → **Mis rentas**.
  Tanto la vista previa como el cálculo definitivo se realizan en Python.
- No se permite inicio anterior a hoy ni devolución igual o anterior al inicio.
  La fecha actual se obtiene con `timezone.localdate()` en America/Mexico_City.
- Tres días entre el 10 y el 13: intervalos `[inicio, devolución)`. Una renta puede
  comenzar el día en que finaliza otra, sin superposición.
- Validación de disponibilidad centralizada en el modelo, usada por ModelForm y
  nuevamente al guardar: las pendientes pueden coincidir; las aprobadas bloquean;
  las rechazadas no bloquean. Vehículos no disponibles no aceptan solicitudes.
- `/mis-rentas/` muestra solo las solicitudes del usuario autenticado. La confirmación
  también comprueba pertenencia y responde 404 para otro usuario.
- Django Admin permite consultar, buscar por usuario/vehículo, filtrar estado y
  cambiarlo individualmente. No hay aprobación masiva que omita validaciones.
- Usuario, vehículo, fechas, días, importes y creación son de solo lectura en Admin;
  no se permite agregar ni borrar solicitudes desde Admin. ForeignKey PROTECT
  evita borrar usuarios o vehículos que ya tienen solicitudes.
- El precio diario se captura al guardar la solicitud y no cambia al modificar la
  tarifa del vehículo o al aprobar/rechazar la solicitud.
- Datos enviados por el cliente para usuario, vehículo, estado o importes no se
  utilizan: el formulario público solo admite las dos fechas.

## Archivos creados o modificados

Nuevos:

- `rentals/__init__.py`, `apps.py`, `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`.
- `rentals/migrations/__init__.py` y `0001_initial.py`.
- `rentals/tests.py` y `rentals/browser_tests.py`.
- `templates/rentals/form.html`, `confirmation.html`, `list.html` y `summary.html`.
- `static/css/rentals.css` y `scripts/rentals_qa.mjs`.
- Este documento.

Modificados:

- `config/settings.py`: registrar `rentals`, sin modificar ajustes de producción.
- `config/urls.py`: incluir sus tres rutas.
- `templates/base.html`: enlace Mis rentas y hoja de estilos adicional.
- `templates/vehicles/detail.html`: botón Solicitar renta o aviso de no disponibilidad.
- `templates/vehicles/list.html`: sustituir el aviso de funcionalidad futura por solicitudes simuladas.
- `README.md`, `AGENTS.md` y `docs/PROGRESO.md`: alcance y uso de la fase autorizada.

Se reutilizaron estilos, autenticación y modelos existentes. No se instalaron dependencias,
no se añadieron pagos y no se modificaron las pruebas de las fases anteriores.

## Migración y conservación de datos

`rentals.0001_initial` crea únicamente la tabla nueva y sus relaciones/restricciones:
devolución posterior al inicio e importes positivos. Se aplicó a la SQLite local.
`makemigrations --check --dry-run` confirmó que no falta ninguna migración.

Antes de migrar se guardó una copia SQLite local en
`test-results/phase3-20261106/db-before-migration.sqlite3` (ignorada por Git).
Se compararon conteos y hashes de todas las columnas de los registros existentes
de usuarios y vehículos, antes y después: coinciden. Se conservan seis vehículos
y un usuario. La base local queda con cero solicitudes: las pruebas utilizaron
bases temporales de Django. `PRAGMA integrity_check` devuelve `ok`.
No se borraron registros existentes ni se reinicializó la base local.

## Pruebas ejecutadas y resultados reales

Primero se ejecutaron las nueve pruebas de Beta 0.1 sin cambios: correctas.
Después de la implementación y las correcciones se ejecutó:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py test rentals.browser_tests --verbosity 2
```

Resultados finales:

| Verificación | Resultado |
|---|---|
| Django check | Sin incidencias |
| Migrate | Migración aplicada; última verificación sin operaciones pendientes |
| Cambios de modelos | No changes detected |
| Suite automática | **33/33 correctas**: 9 anteriores y 24 nuevas; 4,277 segundos |
| Prueba opcional de navegador | **1/1 correcta**, 7,612 segundos |
| Grupos dentro de la prueba de navegador | **15/15 correctos**, cero pageerror, cero HTTP 500 o recursos static con error |
| Dependencias | pip check sin conflictos; requirements sin cambios |

Las 24 pruebas nuevas cubren: login y retorno; vista previa sin persistencia;
cálculo Decimal y estado pendiente; fechas pasadas, iguales, anteriores, faltantes e
inválidas; inicio hoy; vehículo no disponible; pendientes coincidentes; solicitudes
nuevas sobre aprobadas; aprobación con cuatro formas de cruce; fechas contiguas y
vehículos distintos; rechazo que no bloquea y liberación de fechas; tarifa histórica;
privacidad de lista/confirmación; manipulación de valores POST; usuario normal sin
aprobación; validación del Admin; campos históricos protegidos; PROTECT; 404/estado
vacío; CSRF; integración del botón de detalle y ocultación para no disponibles.

Playwright convencional, mediante `StaticLiveServerTestCase`, prueba el flujo real
con dos usuarios y un administrador en una base temporal. Escritorio 1440×1000 y
móvil emulado 390×844: login desde detalle, solicitud, costo, confirmación, lista,
coincidencia pendiente, aislamiento entre usuarios, búsqueda/filtro de Admin,
aprobación, conflicto al aprobar, rechazo, fechas ocupadas/contiguas, no disponible
y logout. Comprueba CSS cargado y ausencia de desbordamiento horizontal en capturas.
No se desactivó el sandbox ni se cambiaron políticas o permisos de seguridad.

La prueba de navegador es opcional y no forma parte de `manage.py test` normal.
Requiere el Node, Playwright y Chromium de desarrollo ya instalados. La aplicación
y su suite Django normal siguen ejecutándose sin Node ni skills.
El script recibe fixtures generados por la prueba; no contiene credenciales reales
y no debe ejecutarse directamente contra la base local de uso.

## Evidencias y revisión visual

Logs finales: `test-results/phase3-20261106/{check,migrate,model-drift,unit-tests,browser-tests}.txt`.
Evidencia final de navegador: `test-results/phase3-browser-20261106-163745-720301/`.
El informe `report.json`, las capturas y los fixtures son locales, ignorados por Git.
Los fixtures contienen contraseñas aleatorias para usuarios de la base temporal,
que deja de existir al finalizar la prueba.

Se revisaron visualmente formulario, revisión, confirmación, Mis rentas, estados de
error y conflicto de Admin, en escritorio y móvil. Las capturas previas a la última
corrección de mensajes están en `phase3-browser-20261106-163633-045613/`; la ejecución
final vuelve a producirlas con la corrección aplicada.

Impeccable se utilizó para revisar la consistencia con el diseño existente, sin Live
ni hooks. El detector sobre `templates/rentals` y `static/css/rentals.css` terminó
con código 0 y lista vacía de hallazgos. Los formularios mantienen etiquetas, foco
visible, contraste de la paleta existente y navegación responsive.
No se rediseñaron las fases previas ni se afirma una certificación WCAG.

Code Simplification revisó exclusivamente el código nuevo después de las pruebas.
La validación vive en el modelo y el resumen visual se comparte mediante include;
no se añadieron capas, servicios ni abstracciones adicionales. No fue necesario
un refactor general. Se repitieron pruebas tras las correcciones.

## Problemas encontrados y corregidos

- Un reemplazo de texto con acentos desde PowerShell no aplicó el botón de detalle.
  Se corrigió usando lectura/escritura UTF-8 y se añadió una prueba de integración.
- La primera ejecución de Playwright buscaba Chromium en la ubicación global.
  Se configuró la ruta local antes de importar Playwright, sin descargar dependencias.
- Una comprobación de búsqueda del Admin se adelantaba a la navegación. Se añadió
  una espera por la URL de resultados.
- El primer servidor temporal no servía los estáticos, aunque el flujo funcional
  pasaba. Se sustituyó por StaticLiveServerTestCase y se añadieron comprobaciones
  de carga de CSS y errores de recursos antes de aceptar las capturas.
- Una fecha inválida mostraba, además del mensaje español, el nombre técnico de
  una restricción. El error se asoció al campo para evitar duplicación; el test
  comprueba que el nombre interno no llegue a la interfaz.

Todos esos casos se verificaron nuevamente antes del commit.

## URLs y uso local

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

- Inicio: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/vehiculos/
- Solicitud: `http://127.0.0.1:8000/vehiculos/<id>/solicitar/`, desde el botón del detalle.
- Mis solicitudes: http://127.0.0.1:8000/mis-rentas/
- Confirmación propia: `http://127.0.0.1:8000/rentas/<id>/confirmacion/`.
- Gestión: http://127.0.0.1:8000/admin/rentals/rentalrequest/

Reiniciar cualquier servidor que estuviera iniciado con `--noreload` antes de esta
fase para que cargue la aplicación y URLs nuevas. No hay credenciales de administrador
predeterminadas; usar el usuario local existente o `manage.py createsuperuser`.

## Limitaciones conocidas

- Son solicitudes simuladas; no existen pagos, edición/cancelación del usuario ni calendario avanzado.
- La comprobación de cruces se realiza en Python al validar y guardar dentro de
  transacciones. No se ha probado carga concurrente; SQLite puede devolver bloqueo
  ante escrituras simultáneas. Esta fase está destinada a desarrollo local.
- No usar `QuerySet.update`, `bulk_create` ni SQL directo para aprobar: esas operaciones
  omiten la validación del modelo. El Admin implementado no ofrece esos caminos.
- La tarifa definitiva es la vigente al confirmar; la vista previa no bloquea precios
  ni reserva fechas. Guardar nuevamente un POST puede generar otra pendiente.
- Las relaciones históricas conservan usuario/vehículo; sus nombres reflejan futuras
  ediciones de esos registros. Las tarifas y totales de la solicitud sí quedan capturados.
- No se probaron un dispositivo físico, otros motores de navegador ni lectores de pantalla.
- Las advertencias de producción de Beta 0.1 permanecen: no se configuró ni publicó producción.

La fase se guarda mediante el commit local `feat: implementar solicitudes simuladas de renta`.
Sin remoto nuevo ni push. Fases 4 y 5 pendientes.
