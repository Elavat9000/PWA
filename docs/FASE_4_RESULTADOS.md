# DriveSmart — Fase 4: asistente virtual local

Fecha: 6 de noviembre de 2026 (America/Mexico_City).
Base de trabajo: `27d993c`, fase 3 verificada. Fase 4 completada y probada.
No se implementó la fase 5 ni se instaló ninguna dependencia nueva.

## Funcionamiento

La aplicación `assistant` utiliza la SQLite existente. No utiliza modelos de lenguaje,
APIs, claves de IA, servicios externos, ChromaDB ni LangChain.

`KnowledgeEntry` guarda pregunta, respuesta opcional, estado Pendiente/Publicada,
usuario opcional y fechas de creación/actualización. Una huella SHA-256 derivada de
la pregunta normalizada tiene un índice único para evitar duplicados normalizados.
No se almacena un historial completo de conversaciones.

`services.answer_question(question, user)` es el único punto de entrada de la vista:

1. Reconoce consultas de catálogo con filtros explícitos y consulta Vehicle por ORM.
2. En otras preguntas, busca una entrada publicada y suficientemente equivalente.
3. Cuando no hay una respuesta segura, guarda una pregunta pendiente si no existe
   una equivalente y devuelve exactamente:

> No tengo información suficiente para responder esa pregunta. La registraré para que el administrador pueda revisarla.

La búsqueda normaliza minúsculas, acentos, puntuación y espacios. Un diccionario
pequeño reconoce sinónimos y `difflib` corrige algunas erratas de ese vocabulario.
La comparación de contenido exige conjuntos equivalentes o coincidencias casi
idénticas, conserva negaciones y calificadores como amplia/limitada, y no elige
arbitrariamente entre respuestas similares contradictorias. Una coincidencia exacta
normalizada tiene prioridad. Compartir palabras comunes no es suficiente.

## Preguntas que entiende

Las ocho FAQ de demostración describen únicamente funciones implementadas:
registro, solicitud de renta, Mis rentas, cálculo del precio, ausencia de pagos,
aprobación administrativa, ausencia de edición/cancelación del usuario y disponibilidad.

En vehículos entiende consultas sencillas de categoría (Compacto, Sedán, SUV),
capacidad mínima en cifras, transmisión, marca/modelo presentes en el catálogo,
opciones económicas y límites de precio expresados con hasta, máximo, menos de,
desde o al menos. Puede combinar límites inferior y superior. Los importes se
comparan usando Decimal; las tarjetas muestran el precio real de la base de datos.

Ejemplos efectivamente comprobados:

| Pregunta | Resultado verificado |
|---|---|
| ¿Cómo puedo registarme? | Reconoce la errata y explica Crear cuenta |
| ¿Cómo puedo alquilar un coche? | Explica el flujo de solicitud de renta y su estado Pendiente |
| ¿Dónde consulto mis rentas? | Indica iniciar sesión y abrir Mis rentas |
| ¿Cómo se calcula el precio? | Precio diario al confirmar × diferencia de días; del 10 al 13 son tres días |
| ¿Puedo pagar aquí? | No. Las solicitudes son simuladas; DriveSmart no procesa pagos. |
| Busco una camionta para 5 personas | Devuelve los SUV reales con capacidad suficiente; dos en los datos demo del navegador |
| ¿Cuánto cuesta el Toyota Corolla? | Corolla 2026, $950.00 MXN/día en la demo de navegador; enlace al detalle real |
| Busco autos automáticos para 7 personas | En los fixtures unitarios devuelve únicamente el Mazda de siete plazas |
| Busco autos hasta 750.25 pesos | En los fixtures unitarios respeta el límite Decimal, incluido el valor exacto |
| ¿Cuánto cuesta el vehículo Fantasma? | No inventa un vehículo ni un precio; registra la consulta para revisión |
| ¿Los vehículos incluyen seguro de cobertura amplia? | Devuelve el mensaje de falta de información y registra una pendiente |

Los precios anteriores identifican los datos de prueba usados, no una tarifa fija
codificada en el asistente. Las consultas posteriores vuelven a leer la base.

Las recomendaciones muestran como máximo tres registros, ordenados por precio.
Por defecto solo incluyen vehículos marcados disponibles. Una consulta de precio
de un vehículo identificado puede mostrarlo aunque esté no disponible, indicando
su estado real. La disponibilidad por fechas sigue resolviéndose en el flujo de rentas.

Si una consulta añade condiciones desconocidas, como seguros, combustible o entrega,
el motor no las descarta para recomendar cualquier vehículo: solicita revisión.
Las consultas de precios reales tienen prioridad sobre una respuesta textual publicada
que pudiera contener una tarifa antigua.

## Aprendizaje administrado

1. El usuario pregunta desde el chat; puede hacerlo sin iniciar sesión.
2. El administrador entra en `/admin/assistant/knowledgeentry/` y filtra Pendiente.
3. Abre la pregunta, escribe una respuesta revisada, cambia Estado a Publicada y guarda.
4. Esa respuesta queda disponible inmediatamente para consultas equivalentes.

Una respuesta en borrador o pendiente nunca se utiliza como conocimiento aprobado.
Modelo y formulario administrativo rechazan publicar una respuesta vacía o con solo
espacios. No hay acción masiva de publicación que eluda esa validación. Los permisos
nativos de Django protegen las modificaciones: un usuario normal no puede publicar,
y ser staff sin permiso de la aplicación tampoco concede acceso de edición.
La API del chat no acepta respuestas ni estados del cliente como escrituras de conocimiento.

El flujo completo desconocida → pendiente → respuesta del Admin → publicación →
consulta similar → respuesta publicada se ejecutó en navegador con dos contextos
de usuario y un administrador. Las variantes equivalentes generaron una sola pendiente.
La respuesta de prueba era una cadena explícitamente revisada para QA, no una política
comercial sobre seguros.

## Interfaz y protecciones

Se añade el botón flotante Asistente DriveSmart mediante el template público común.
No se modifica el Admin ni el funcionamiento de autenticación, vehículos o rentas.
El panel utiliza un dialog nativo, con bienvenida, conversación, pregunta, Enviar,
indicador Consultando y Cerrar. Escape cierra, el foco regresa al botón y Enter envía
la pregunta; Shift+Enter permite saltos de línea. No conserva conversaciones al navegar.

El endpoint `POST /asistente/consultar/` recibe JSON y valida tipo, contenido y longitud
de 2–400 caracteres. Rechaza JSON inválido, controles no permitidos, cuerpos excesivos,
tipos de contenido incorrectos y métodos distintos de POST. Conserva el middleware
CSRF, el token del formulario y credenciales same-origin en fetch; se probaron rechazos
sin token y con un origen externo.

Textos de usuarios, respuestas y datos de vehículos se insertan con textContent,
sin innerHTML. Los enlaces de vehículo provienen de reverse sobre IDs reales.
Se comprobó una cadena con un img/onerror: permaneció como texto y no ejecutó código.
Hay recuperación ante error de red y el envío se deshabilita durante el procesamiento.

## Carga demo, migración y datos existentes

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py load_faq
```

`assistant.0001_initial` crea solo la tabla nueva en la base SQLite existente.
`load_faq` crea ocho preguntas publicadas sin duplicar ni sobrescribir entradas
existentes o ediciones del administrador; también comprueba equivalencia de texto.
La primera carga local creó ocho; las siguientes, cero. Se probó preservación de
una respuesta y de una pregunta reformulada por el administrador.

Antes de migrar se respaldó la base en `test-results/phase4-20261106/`, ignorado por Git.
Conteos y hashes de todas las columnas de usuarios, vehículos y solicitudes coinciden
antes y después: se conservaron seis vehículos, un usuario y una solicitud existente.
La integridad SQLite devuelve `ok`. Ninguna pregunta de QA se insertó en la base de uso;
en ella quedaron únicamente las ocho FAQ publicadas de esta fase.

## Pruebas y revisión

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py test assistant.browser_tests rentals.browser_tests --verbosity 2
```

| Verificación final | Resultado real |
|---|---|
| Check | Sin incidencias |
| Migrate | Aplicada; sin migraciones pendientes |
| Cambios sin migración | No changes detected |
| Suite Django | **65/65 correctas**: 33 anteriores + 32 del asistente; 5,356 s |
| Pruebas opcionales de navegador | **2/2 correctas**, 12,934 s |
| Grupos de comprobaciones del navegador | 14 del asistente y 15 de rentas, todos correctos |
| Dependencias | pip check sin conflictos; requirements y paquetes sin modificaciones |

Son **67 pruebas distintas aprobadas** entre ambas ejecuciones finales. Los 29 grupos
internos de navegador no se suman otra vez como pruebas independientes.

Las pruebas nuevas verifican FAQs, sinónimos, erratas, ambigüedad, calificadores,
filtros, importes, registros reales, falta de resultados, deduplicación, borradores,
publicación y permisos, CSRF/origen, validación del endpoint, repetición del comando
y ausencia de cambios en vehículos/rentas. Las pruebas anteriores pasan sin modificarlas.

Playwright convencional usa StaticLiveServerTestCase y una base temporal. Se probaron
escritorio 1440×1000, móvil 390×844 y una vista reducida 320×480. Se verificaron carga
de CSS, ausencia de overflow, posición de Cerrar/campo/Enviar, foco, indicador de
procesamiento, enlaces, recuperación de red, tratamiento seguro de HTML y aprendizaje
administrado. No se desactivó el sandbox ni se cambiaron políticas de seguridad.

Logs finales: `test-results/phase4-20261106/`.
Capturas/informe del asistente: `test-results/phase4-browser-20261106-170416-981377/`.
Regresión de rentas: `test-results/phase3-browser-20261106-170423-158824/`.
Los fixtures de navegador contienen contraseñas aleatorias de la base temporal;
esos archivos son locales y están excluidos de Git.

Se revisaron las capturas de bienvenida, respuesta publicada, vehículos, error,
texto seguro y vista reducida. Impeccable revisó la consistencia con la paleta existente,
sin rediseño, Live ni hooks. El detector de templates/assistant y assistant.css devolvió
lista vacía y código 0. No se afirma certificación WCAG ni prueba de teléfono físico.

Code Simplification revisó exclusivamente el código nuevo: normalización y extracción
de palabras relevantes se comparten, la huella se calcula una vez por búsqueda y
el comando demo reutiliza la misma comparación. Se evitaron capas adicionales y
se repitieron las pruebas después de los ajustes.

## Problemas encontrados y corregidos

- La ordenación de Vehicle hacía que distinct sobre marca incluyera también campos
  de ordenación y devolviera marcas repetidas. Se ordena por el campo consultado
  antes de distinct; el test comprueba el precio de una marca con varios modelos.
- Se reforzó el caso exacto y la abstención ante respuestas similares contradictorias.
- Se cubrieron explícitamente las dos formulaciones del cálculo del precio, con y
  sin “de una renta”, evitando registrar como desconocido un ejemplo requerido.
- Se normalizan espacios y saltos de línea del campo de pregunta, manteniendo el
  rechazo de controles no permitidos. Enter y Enviar se probaron en el flujo real.
- El comando demo reutiliza equivalencias para preservar preguntas reformuladas,
  además de respuestas editadas. No se eliminaron ni modificaron datos existentes.

## Archivos y ejecución local

Nuevos: `assistant/` (modelo, servicio, endpoint, Admin, comando, migración y pruebas),
`templates/assistant/widget.html`, `static/css/assistant.css`, `static/js/assistant.js`,
`scripts/assistant_qa.mjs` y este documento.
Modificados: `config/settings.py`, `config/urls.py`, `templates/base.html`, `README.md`,
`AGENTS.md` y `docs/PROGRESO.md`. No se modificó código de rentas, usuarios o vehículos.

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir http://127.0.0.1:8000/ y pulsar Asistente DriveSmart. Para responder pendientes:
http://127.0.0.1:8000/admin/assistant/knowledgeentry/ con un administrador autorizado.
No hay credenciales predeterminadas. Reiniciar un servidor antiguo iniciado con
`--noreload` para que cargue la nueva aplicación y sus URLs.

## Límites y posible evolución

- Es búsqueda textual conservadora, no comprensión general ni IA generativa.
  Algunas reformulaciones, erratas de marcas, números escritos con palabras,
  múltiples alternativas o filtros no implementados quedarán pendientes.
- No entiende disponibilidad por fechas ni modifica o crea rentas desde el chat.
- Solo el administrador conoce y valida las políticas comerciales. La publicación
  humana es responsable de la veracidad y vigencia de esas respuestas.
- No hay historial persistente de conversaciones, notificaciones, streaming,
  moderación automática ni limitador de frecuencia. El chat público es para esta
  demostración local; no se ha sometido a una prueba de abuso o carga concurrente.
- No usar bulk_create, QuerySet.update o SQL directo para publicar conocimiento:
  esas escrituras evitan la validación de save. El Admin implementado no las ofrece.
- Las evidencias son de Chromium emulado, sin lector de pantalla ni teléfono físico.
  Se mantienen las limitaciones de producción documentadas en la auditoría de Beta 0.1.

SQLite evita infraestructura adicional y permite revisar preguntas en el mismo Admin.
La búsqueda textual facilita entender, probar y ajustar la beta sin servicios de pago.
En una fase autorizada futura, la selección de candidatos de matching_entry podría
sustituirse por un índice vectorial que devolviera IDs de KnowledgeEntry publicadas.
Se conservarían permisos, control de publicación, política de abstención, consulta real
de Vehicle y contrato de answer_question, sin reescribir vistas ni el modelo Vehicle.
No se ha implementado esa integración.

La fase se guarda con el commit local `feat: implementar asistente virtual y base de conocimiento`.
Sin remoto nuevo ni push. Fase 5 pendiente.
