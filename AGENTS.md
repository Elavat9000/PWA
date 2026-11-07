# DriveSmart

Trabajar con Python 3.12, Django 5.2 LTS, SQLite y Django Templates.
Preferir componentes nativos de Auth y Admin. Mantener simplicidad y español.
No añadir React, Docker ni servicios de IA. Rentas simuladas autorizadas en fase 3, sin pagos.
Asistente textual local autorizado en fase 4: SQLite y difflib, sin APIs de IA ni modelos de lenguaje.
PWA mínima autorizada en fase 5: solo caché de estáticos seleccionados y aviso offline.
Nunca almacenar páginas privadas, sesiones, JSON del asistente ni POST en el worker.
Entrega limpia con scripts/package_beta.py; excluir datos locales, entornos y skills del ZIP.
No cambiar políticas de Windows ni desactivar el sandbox.
Ejecutar `.venv\Scripts\python.exe manage.py check`, `migrate` y `test` por fase.
Usar skills locales de `.agents/skills`: Playwright para QA si los permisos lo permiten,
Impeccable para revisar UI funcional y Code Simplification después de pruebas.
No usar Impeccable Live ni hooks elevados. Las skills son opcionales para ejecutar.
No publicar ni crear remotos ni hacer push sin confirmación explícita.
