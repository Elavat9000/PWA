# Plan de mejora de comprensión del asistente

Alcance: ampliar el chat existente, sin IA externa ni cambios en modelos, rentas,
autenticación, administración, catálogo, diseño global o dependencias.

1. Reproducir las cinco frases aportadas en una base temporal y añadir regresiones.
2. Reconocer intenciones informales de orientación de renta, consulta de capacidad,
   mejora de resultados y solicitud de reserva. Mantener la búsqueda conservadora.
3. Pedir aclaración sobre criterios y fechas incompletas. Conservar filtros válidos,
   sin deducir qué jueves quiso decir el usuario ni crear una solicitud.
4. Reutilizar respuestas revisadas para orientación y datos actuales para capacidad.
   Las condiciones desconocidas siguen pendientes; no se omiten para recomendar.
5. Ejecutar la suite anterior y las nuevas pruebas, una conversación Playwright en
   base temporal y revisión de simplicidad del código nuevo. Documentar evidencia.

No se cambiarán normalización ni huellas de las preguntas ya guardadas. No se cargará
ni editará la SQLite de uso. No se cambiará el Service Worker si no cambian los
recursos estáticos. No se hará push ni se versionarán otros cambios pendientes.

Estado inicial: plan aprobado por el encargo del usuario; implementación en curso.
