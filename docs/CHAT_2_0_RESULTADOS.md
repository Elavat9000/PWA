# DriveSmart — Chat 2.0

Fecha: 8 de noviembre de 2026. Alcance exclusivo del asistente existente.

## Resultado

Se conserva `services.answer_question(question, user)` y se admite el argumento
opcional `context`. El endpoint y sus campos `reply`, `vehicles` y `source` siguen
siendo compatibles. Se añaden sugerencias, estimaciones y datos de vehículos.
No se utilizan IA generativa, servicios externos ni dependencias de ejecución nuevas.

La aplicación tenía **88 pruebas Django**, no las 73 indicadas en el encargo.
Se conservan todas y se añaden 36: **124/124 aprobadas**. Una integración adicional
con Playwright convencional aprueba 15 comprobaciones en Chrome, con sandbox activo.

## Contexto breve

La sesión Django conserva únicamente filtros, fechas ISO, duración, hasta tres IDs
de resultados, vehículo seleccionado y la necesidad de elegir uno para cotizar.
No conserva preguntas, respuestas, precios, reservas ni historial conversacional.
El contexto caduca tras 30 minutos sin consultar y se descarta al cambiar el usuario
autenticado. Los usuarios anónimos quedan separados por su propia cookie de sesión.

Las nuevas búsquedas con «busco», «necesito», «quiero», «muéstrame» o un modelo
explícito reemplazan filtros anteriores. Elegir un modelo después de una cotización
ambigua conserva las condiciones de esa cotización. Las preguntas de otro tema
limpian el contexto de vehículos para evitar que contamine consultas posteriores.

«Nueva conversación» envía `{"action":"reset"}` al mismo endpoint, con CSRF.
Limpia únicamente el contexto del asistente y los mensajes visibles, sin cerrar
la sesión ni alterar otros datos. Se mantienen como máximo 60 nodos anteriores
en la presentación del navegador, sin localStorage ni historial persistido.

## Interpretación y protección de condiciones

- Marca/modelo reales, categorías Compacto/Sedán/SUV y transmisión.
- Sinónimos y erratas del normalizador existente, como camioneta/camionta.
- Capacidad mínima en cifras o palabras sencillas: cinco, siete, veinte, etc.
- Presupuestos diarios con hasta, máximo, mínimo, menos de, desde y al menos.
- Seguimientos «el más barato», «uno más grande», «otros vehículos» y mayor capacidad.
- Comparación de hasta tres registros actuales, incluidos modelos mencionados.
- Estimación por duración o por diferencia entre fechas.

No se descartan seguros, combustible, equipamiento ni otras condiciones que no
puedan comprobarse en Vehicle. Esas preguntas pasan al conocimiento revisado o a
pendientes. Negaciones y condiciones contradictorias mantienen la protección previa.
Se pide aclaración cuando faltan vehículo, criterio de recomendación o fechas fiables.

«Más grande» exige una capacidad superior a la mayor de los últimos resultados;
«algo más barato» exige un precio menor al mínimo anterior. Se conservan categoría,
presupuesto y fechas explícitos. Si no hay coincidencias, no se relajan condiciones.

## Disponibilidad y estimaciones

Admite dos fechas ISO `AAAA-MM-DD`, dos fechas `DD/MM/AAAA`, o intervalos como
«del 12 al 15 de noviembre de 2027». Sin año se utiliza el año actual, indicado
en la respuesta con fechas completas; nunca se traslada silenciosamente al año siguiente.
Las fechas inválidas, pasadas, aisladas o intervalos invertidos requieren aclaración.

La consulta ORM excluye vehículos no disponibles y aquellos con solicitudes
APROBADAS que cumplan `inicio < devolución solicitada` y `devolución > inicio solicitado`.
Son las mismas reglas que `RentalRequest.validate_availability`: intervalo
`[inicio, devolución)`; las pendientes y rechazadas no bloquean y los extremos
adyacentes no se superponen. No existe un servicio independiente de rentas que
pueda reutilizarse; se consultan sus modelos sin modificarlos. Las pruebas cubren
los límites y la aparición de una aprobación entre dos mensajes.

Cada respuesta vuelve a consultar SQLite. Solo una consulta con fechas válidas
indica que se comprobó disponibilidad para ese intervalo. Una consulta de tarifa
puede mostrar un vehículo no disponible, señalándolo expresamente.

La estimación utiliza Decimal y el precio diario actual multiplicado por días.
Con fechas se usa la misma diferencia de días que rentals. No incluye conceptos
comerciales no definidos ni crea, aprueba o modifica solicitudes. Se debe confirmar
en el formulario de renta, donde se vuelve a validar disponibilidad.
Si hay varios vehículos, se solicita elegir un modelo antes de calcular el total.

## Aprendizaje y seguridad

Se conservan el modelo KnowledgeEntry, su Admin, el registro de desconocidas,
la deduplicación conservadora y la publicación explícita. Los borradores siguen
sin poder responder. Las respuestas administradas atienden preguntas generales;
precios y fechas actuales se resuelven antes con los modelos reales.

El cliente no puede suministrar filtros, IDs, respuestas o estados de conocimiento
para guardarlos. CSRF, validación JSON, límites de tamaño y no-store se mantienen.
Los textos se insertan con textContent; los enlaces aceptan únicamente rutas locales
de detalle con ID numérico. Datos que parezcan una contraseña declarada, un correo
o una secuencia larga de identificación no se guardan como pregunta pendiente.
Es una protección heurística, no un detector completo de datos personales: el widget
mantiene el aviso de no compartir información sensible.

## Interfaz y PWA

Se mantiene el dialog y el lanzador actuales. Se añaden tarjetas compactas con
precio, características, disponibilidad y enlace «Ver vehículo», sugerencias y
«Nueva conversación». La última respuesta queda visible desde su comienzo.
El formulario se compacta en móvil y en horizontal, con foco visible y Escape.
No se modifican cabecera, portada, catálogo, formularios de renta ni estilos globales.

El único cambio del Service Worker es la versión v8 → v9. Su lista permitida
permanece igual: ningún POST, JSON del chat, sesión, reserva ni página privada entra
en CacheStorage. Se verificó activación v9, eliminación de una caché anterior,
conversación tras recargar y aviso offline del catálogo.

## Pruebas ejecutadas

| Verificación | Resultado |
|---|---|
| Suite Django completa, incluidas las 88 anteriores | 124/124 |
| Regresiones nuevas de conversación, dentro de la suite | 36/36 |
| Integración opcional assistant.browser_qa | 1/1, 15 comprobaciones |
| manage.py check | Sin errores |
| makemigrations --check --dry-run | Sin cambios |
| migrate --plan | Sin operaciones pendientes |
| node --check static/js/assistant.js | Correcto |
| Git diff --check | Sin errores de espacios; avisos LF/CRLF del repositorio |

Las migraciones y los fixtures de QA se ejecutaron en bases temporales del runner.
No se ejecutaron cargas, consultas del chat ni migraciones que escribieran en la
SQLite de uso. No se tocaron modelos ni lógica de vehículos, rentas o autenticación.

Conversación completa ejecutada en Chrome, con fechas dinámicas diez días después
de la prueba y devolución tres días después del inicio:

1. «Busco una camioneta automática para siete personas» → Mazda CX-5 2026 del fixture.
2. «Del [inicio ISO] al [devolución ISO]» → comprueba fechas conservando filtros.
3. «¿Y el más barato?» → conserva SUV, automática, siete plazas y fechas.
4. «¿Cuánto cuesta rentarlo tres días?» → tarifa de prueba $1,400.00 × 3 = $4,200.00 MXN.
5. «Nueva conversación» → limpia contexto; «¿Cuál es el más barato?» devuelve Corolla
   a $750.25 en ese fixture, no conserva la condición SUV.
6. «Compara los SUV disponibles» → Seltos y CX-5, usando sus precios registrados.

Estos importes son fixtures temporales, no precios codificados del catálogo de uso.
También se comprobaron estimación ambigua y selección posterior, cambio de modelo,
disponibilidad aprobada/pendiente, separación de sesiones, aprendizaje con Admin,
XSS, CSRF, datos sensibles y conservación de condiciones desconocidas.

Capturas revisadas a 1440×900, 768×900, 390×844, 320×568 y 844×390.
La integración comprueba controles dentro de pantalla, ausencia de desbordamiento,
Escape y devolución de foco. Evidencias y conversación JSON fuera del proyecto:
`%TEMP%\DriveSmart_chat2_55mj65sb` (verificación final; capturas revisadas también
en la ejecución equivalente `%TEMP%\DriveSmart_chat2_xukhsm9w`).

Playwright Interactive no se utilizó: su instrucción local exige desactivar sandbox,
lo cual contradice AGENTS.md. Se empleó Playwright convencional y Chrome instalado,
con `chromiumSandbox: true`. Playwright se recuperó, con autorización, en
`%TEMP%\DriveSmartChat2Tools`; no se reinstaló node_modules dentro del proyecto.
Impeccable se aplicó a la revisión del widget; Code Simplification al código nuevo,
extrayendo la consulta ORM a una función pequeña sin cambiar su comportamiento.

Repetición de QA opcional en PowerShell, si esa herramienta temporal existe:

```powershell
$env:DRIVESMART_PLAYWRIGHT_MODULE="$env:TEMP\DriveSmartChat2Tools\node_modules\playwright\index.mjs"
.\.venv\Scripts\python.exe manage.py test assistant.browser_qa --verbosity 1
```

## Defectos corregidos durante el desarrollo

- Duplicación de marcas al combinar distinct con el orden predeterminado del modelo.
- Pérdida del vehículo seleccionado o de la duración al continuar una cotización.
- Conservación accidental de un modelo al pedir una alternativa de mayor capacidad.
- Posible omisión de capacidades de tres cifras y condiciones desconocidas junto a fechas inválidas.
- Conversación demasiado baja en pantallas horizontales y salto directo a sugerencias.

## Archivos de esta etapa y Git

- assistant/conversation.py: interpretación, contexto, filtros, fechas y estimaciones.
- assistant/services.py y assistant/views.py: entrada compatible, privacidad y sesiones.
- assistant/test_conversation.py: 36 pruebas nuevas.
- assistant/browser_qa.py y assistant/qa/chat.mjs: integración opcional aislada.
- templates/assistant/widget.html, static/js/assistant.js, static/css/assistant.css.
- static/pwa/service-worker.js: únicamente versión de caché.
- docs/CHAT_2_0_RESULTADOS.md y docs/PROGRESO.md.

El árbol ya contenía cambios anteriores sin commit, incluida la ampliación del
conocimiento y ajustes visuales. El commit de Chat 2.0 debe incluir exclusivamente
esta etapa; aquellos cambios permanecen pendientes. No se hace push ni se modifican
remotos, historial previo o ZIP. La fase siguiente no se inicia.

## Limitaciones

Es un intérprete local de patrones, no un modelo de lenguaje. Entiende un conjunto
acotado de frases; no promete interpretar cualquier texto, fechas relativas o
abreviaturas de meses. No recomienda por seguros, consumo, potencia o equipamiento.
No tiene notificaciones automáticas al administrador ni devuelve respuestas por correo.
No garantiza disponibilidad futura: solo una consulta del estado actual, sujeta a
la comprobación final del formulario. Una cookie compartida entre pestañas comparte
el contexto; dos pestañas no representan conversaciones independientes.
Las pruebas de móvil usan emulación de viewport, no un dispositivo físico ni su teclado.
