# DriveSmart — Progreso

Fases 0, 1 y 2 completadas y auditadas: entorno, cuentas, catálogo y administración.
Fase 3 completada: solicitudes simuladas, fechas, costos e historial por usuario.
Fase 4 completada: asistente textual local y conocimiento revisado en Admin.
Fase 5 completada: PWA mínima, privacidad de caché y empaquetado limpio.

Las mejoras visuales incorporan fotografías de referencia con créditos, filtros,
portada y tarjetas consistentes, formularios de renta con pasos y un asistente compacto.
Los criterios vigentes están en DESIGN.md. Se conservan SQLite y las imágenes locales.

## Limpieza del proyecto — 8 de noviembre de 2026

Se retiraron los ZIP, informes históricos, resultados y fuentes de QA de navegador
al archivo externo DriveSmart_Archivo_20261108, junto al proyecto.
Se eliminaron node_modules, la caché npm y los navegadores locales de Playwright.
Se mantienen la aplicación, las migraciones, las pruebas Django, el entorno Python,
las skills completas, Git, las instrucciones y las licencias de imágenes.

La verificación habitual es manage.py check, makemigrations --check --dry-run y test.
El conjunto Django contiene 79 pruebas y no requiere Node.
No se creó commit ni se realizó push durante la limpieza.

Las auditorías y capturas anteriores se conservan fuera de esta carpeta; no son
requisitos de ejecución. El proyecto sigue destinado a uso local.

Verificación posterior a la limpieza: check correcto, sin migraciones pendientes,
79/79 pruebas Django aprobadas, SQLite íntegra e imágenes presentes.
La carpeta test-results se retiró tras verificar por SHA256 sus 20.809 archivos copiados.

## Base de conocimiento ampliada — 8 de noviembre de 2026

Investigadas ocho fuentes oficiales del sector. Catálogo de 307 temas y 456
formulaciones en 27 categorías: 245 publicadas sobre la beta y 211 pendientes de
políticas comerciales. Carga idempotente y protección de respuestas humanas.
88 pruebas Django aprobadas y siete consultas HTTP con CSRF verificadas.
Sin cambios del esquema, motor del asistente ni dependencias.
Ver [fuentes y mantenimiento](BASE_CONOCIMIENTO.md). SQLite continúa ignorada en Git.

## Portada inspirada en la referencia — 8 de noviembre de 2026

Nueva composición de inicio: aviso fino, cabecera oscura, buscador blanco sobre
fotografía y titular en franja verde. Conserva la identidad verde, crema y lima,
los filtros GET existentes y los créditos de imagen. Reglas adaptativas para móvil.
Sin cambios en modelos, lógica de negocio ni dependencias. Caché pública PWA v6;
se conserva la lista de estáticos permitidos y la exclusión de datos privados.
Check correcto y 88/88 pruebas Django aprobadas. Portada y filtrado GET comprobados.
La inspección visual en navegador queda pendiente: el host de acceso a navegadores
y la conexión nativa de Computer Use no estaban disponibles en esta sesión.
Sin commit ni push.

## Tarjetas de vehículos — 8 de noviembre de 2026

Tarjeta compartida de portada y catálogo con fondo verde tinta, modelo destacado,
características con iconos, fotografía amplia, disponibilidad y precio diario en
lima. Conserva los datos, las imágenes originales y el enlace a detalle. Caché
pública PWA v7 sin ampliar su lista permitida. Check correcto y 88/88 pruebas
Django aprobadas; renderizado Django de catálogo, portada y detalle comprobado.
La revisión visual de escritorio y móvil sigue pendiente por indisponibilidad del
host de navegador. Sin dependencias nuevas, commit ni push.

Rollback solicitado: se restauró el diseño anterior de las tarjetas blancas en
portada y catálogo. La nueva composición de la portada se conserva. Caché PWA v8
para retirar los estilos de tarjetas descartados. Sin modificar el historial Git.

## Chat 2.0 — 8 de noviembre de 2026

Mejora exclusiva del asistente existente: contexto breve por sesión, búsquedas
combinadas, seguimiento, fechas con disponibilidad real, comparación y estimaciones
Decimal. Reinicio explícito, tarjetas compactas y sugerencias dentro del widget.
Se conservan el aprendizaje administrado, CSRF y las reglas de no caché privada.
No se modifican modelos ni funcionalidades externas al chat. Service Worker v9,
sin ampliar la lista de recursos permitidos. 124/124 pruebas Django aprobadas,
incluidas las 88 anteriores; integración Playwright adicional 1/1 con 15 comprobaciones.
Bases temporales y evidencias externas; sin cambios en la SQLite de uso ni ZIP.
Ver [resultados, ejemplos y limitaciones](CHAT_2_0_RESULTADOS.md).

## Catálogo PWA sin conexión — 8 de noviembre de 2026

Ampliación solicitada: copia pública aislada del catálogo completo, fotos y fichas,
sin guardar HTML con sesión. Aviso visible de copia lista, fecha de guardado y
verificación online de precios, fechas deseadas y disponibilidad. Actualización
manual, reutilización automática de 30 minutos y conservación de la última copia
completa ante fallos. Worker v10. Se preservan CSRF, no-store en páginas normales,
permisos y reglas de rentas. No se cachean sesiones, POST ni JSON del chat.

156/156 pruebas Django; dos integraciones Playwright aprobadas con diez comprobaciones
PWA y 18 del chat. Se usaron bases y fotografías temporales; no se modificó SQLite
de uso. Sin migraciones pendientes. README, instrucciones, arquitectura y entregable
actualizados. Capturas públicas offline en docs/images y evidencia técnica en TEMP.
Implementado localmente; no se ha publicado en PythonAnywhere ni hecho push.
Ver [alcance y comprobaciones](PWA_CATALOGO_OFFLINE.md).

Ajuste posterior solicitado: descarga y actualización silenciosas, sin aviso de
copia lista, fecha ni botones de mantenimiento en la navegación con conexión.
El aviso aparece solo al perder la conexión y desaparece al recuperarla. Worker v11;
se conserva el formato de la copia pública existente para no invalidarla innecesariamente.
