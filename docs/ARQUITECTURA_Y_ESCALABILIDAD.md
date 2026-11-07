# DriveSmart — Arquitectura y escalabilidad

## Propósito y tecnologías

DriveSmart permite explorar vehículos, crear usuarios, solicitar rentas simuladas y
consultar un asistente con conocimiento revisado. Utiliza Python 3.12, Django 5.2 LTS,
SQLite, Django Templates, HTML, CSS y JavaScript nativo. Pillow valida imágenes.
No procesa pagos ni usa APIs de IA, modelos de lenguaje o servicios externos.

Django aporta Auth, permisos, formularios, migraciones, CSRF y Admin. SQLite permite
instalar la prueba en Windows sin configurar un servidor adicional. config, core,
accounts, vehicles, rentals y assistant comparten una aplicación y una base de datos.

## Flujos implementados

- Autenticación: Django Auth y UserCreationForm; logout por POST. Admin con permisos.
- Catálogo: Vehicle y CRUD en Admin; precios Decimal, categorías, características,
  imágenes locales y disponibilidad. Los usuarios consultan catálogo y detalle.
- Rentas: RentalRequest referencia usuario/vehículo y captura tarifa y total. La
  devolución es exclusiva: del 10 al 13 son tres días. Pendientes pueden coincidir;
  aprobadas bloquean intervalos superpuestos. Solo el propietario ve sus solicitudes.
  Admin aprueba/rechaza, con los datos históricos de solo lectura.
- Asistente: endpoint JSON consulta Vehicle por ORM o KnowledgeEntry publicadas.
  Normaliza acentos, puntuación, espacios y sinónimos; usa difflib conservadoramente.
  Lo desconocido queda pendiente. Admin responde y publica; una respuesta vacía se
  rechaza. No hay entrenamiento automático ni historial persistente de conversaciones.
- PWA: manifiesto, iconos y worker raíz. Solo precarga CSS, JS estático, iconos y el
  aviso estático offline. Datos dinámicos, privados y POST no se guardan en el worker.

El asistente lee precios y características reales. No genera políticas por suposición.
La revisión humana es responsable de mantener correctas las respuestas publicadas.
Una base vectorial no se justificó para ocho FAQ y un catálogo pequeño. En el futuro,
matching_entry podría recuperar IDs desde un índice, conservando permisos, publicación,
abstención, ORM de Vehicle y contrato de answer_question. No está implementado.

## Caché y privacidad

El worker usa lista cerrada y caché versionada; limpia solo versiones anteriores de
DriveSmart. Las páginas públicas sin red reciben un aviso, no datos antiguos. Las
privadas y POST fallan sin recuperar información personal. Las respuestas dinámicas
envían Cache-Control: no-store y el historial vuelve a consultar la sesión al restaurarse.
No hay sincronización ni cola de envíos para simular rentas o chat offline.

Referencias técnicas: [Service Workers y localhost](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers)
y [caché de historial y no-store en Chrome](https://developer.chrome.com/docs/web-platform/bfcache-ccns).
El comportamiento de la beta se comprueba con pruebas reales de navegador.

## Crecimiento, costos y riesgos

Con diez veces más uso, primero mediríamos tráfico, latencia, consultas, escrituras,
imágenes y carga de revisión. No se afirma capacidad sin pruebas de carga. Las primeras
medidas serían paginación, índices basados en consultas observadas, optimización de
imágenes y pruebas concurrentes de reservas. La búsqueda textual recorre entradas;
se mediría antes de elegir otra tecnología.

Ante escrituras que excedan SQLite se evaluaría una base de servidor y una garantía
de exclusión de reservas concurrentes, con pruebas de migración y respaldos. El ORM
reduce cambios de aplicación, pero no elimina esa verificación. No se añadieron bases,
workers ni infraestructura a la beta.

No se contratan APIs ni hosting en esta entrega. El crecimiento podría requerir gasto
en equipo, alojamiento, almacenamiento, tráfico, respaldos, supervisión y revisión.
No se inventan importes sin volumen, proveedor, mediciones y requisitos reales.

Límites: SQLite puede bloquear escrituras concurrentes; búsqueda conservadora; chat
sin limitador de frecuencia; respuestas dependientes de revisión humana. No hay pagos,
edición/cancelación por usuario, calendario avanzado, notificaciones ni datos offline.
No se certifican WCAG, carga o instalación física en todos los navegadores.

Problemas resueltos: rutas de herramientas y permisos específicos sin quitar sandbox;
recursos locales; distinct corregido para marcas; validación de reservas centralizada;
servidor de pruebas con estáticos; prevención de caché de información privada.

## Local frente a producción

Fases 0–5 terminan entorno, autenticación, catálogo/Admin, rentas simuladas, asistente
administrado y PWA informativa. INSTRUCTIONS.txt permite reproducir la entrega.
La configuración usa runserver en loopback, DEBUG local y una clave de desarrollo
pública sin datos personales incluidos. **No está lista para producción.**

Antes de publicar deben resolverse las advertencias de check --deploy: clave privada
aleatoria, DEBUG desactivado, hosts reales y HTTPS, HSTS y cookies seguras; además de
servidor apropiado, estáticos/media, respaldos y observabilidad. No se fuerzan esos
ajustes HTTPS sobre localhost. Los resultados están en docs/FASE_5_RESULTADOS.md.
