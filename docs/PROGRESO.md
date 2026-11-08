# DriveSmart — Beta 0.1

- Fase 0: completada y auditada. Entorno Python 3.12, Git main y tres skills locales verificadas.
- Fase 1: completada y auditada. Inicio, registro, login, logout, permisos y Admin. Cuatro pruebas correctas.
- Fase 2: completada y auditada. Vehicle, CRUD en Admin, catálogo, filtros, detalle y seis demos sin duplicados.
  Nueve pruebas Django correctas; Playwright convencional: 16 comprobaciones correctas.
- Fase 3: completada y verificada. Solicitudes simuladas, cálculo en Python, Mis rentas,
  disponibilidad y aprobación/rechazo en Admin. 33 pruebas Django y 1 prueba de navegador
  con 15 grupos de comprobaciones correctos. Ver [resultados](FASE_3_RESULTADOS.md).
- Fase 4: completada y verificada. Asistente textual local, catálogo por ORM,
  preguntas pendientes y respuestas publicadas por Admin. 65 pruebas Django y 2 de navegador
  correctas. Ver [resultados](FASE_4_RESULTADOS.md).
- Fase 5: completada y verificada. PWA mínima sin datos privados en caché y entrega ZIP
  reproducida en entorno aislado. 73 pruebas Django y 3 de navegador correctas.
  Ver [resultados de entrega](FASE_5_RESULTADOS.md).

Fecha objetivo: 10 de noviembre de 2026, 10:00, America/Mexico_City.

Verificación ejecutada el 6 de noviembre de 2026: check sin incidencias, migraciones
aplicadas, carga demo ejecutada dos veces, CRUD probado con base temporal.
Impeccable se ejecutó sin hooks ni Live. Playwright Interactive quedó instalado;
se usó Playwright convencional para conservar las protecciones del entorno.
Code Simplification revisó únicamente código terminado después de las pruebas.
No se ha creado repositorio remoto ni ejecutado push.

## Mejora visual — 8 de noviembre de 2026

Completada: portada con vehículos reales del catálogo y tres pasos, tarjetas compartidas,
formularios y rentas con jerarquía unificada, chat adaptable y tokens CSS centralizados.
Se conservaron la paleta, Auth, Admin, modelos, cálculos y motor del asistente.
73 pruebas Django y 4 pruebas opcionales de navegador aprobadas; capturas a 1440, 768,
390 y 320 px. Caché PWA v2, con la misma política de privacidad y aviso offline.
ZIP visual independiente; el ZIP de fase 5 permanece intacto. Sin remoto ni push.
Ver [informe y evidencias](MEJORA_VISUAL.md).

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
