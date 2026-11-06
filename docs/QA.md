# Inventario de verificación

- Inicio: navegación, llamada al catálogo, enlace de registro, escritorio y móvil.
- Cuentas: registro válido, contraseñas distintas, login válido e inválido,
  cierre por POST, CSRF y usuario sin permisos administrativos.
- Catálogo: seis tarjetas, imágenes locales, precios, características, filtro SUV,
  limpiar filtro, detalle y regreso al catálogo.
- Estados alternativos: categoría inexistente, detalle inexistente, vehículo no disponible.
- Administración: crear, consultar, modificar y eliminar vehículo con superusuario;
  denegar acceso y escritura al usuario normal.
- Carga demo: dos ejecuciones sin duplicados y preservación de modificaciones.
- Visual: 1440, 390 y 320 píxeles; imágenes completas, desbordamiento horizontal,
  jerarquía, legibilidad y formularios. Evidencia local en `test-results/` (excluida de Git).

Pruebas Django: ` .venv\Scripts\python.exe manage.py test`.
Navegador opcional: `npm ci`, `npx.cmd playwright install chromium`, iniciar servidor,
`node scripts/browser_qa.mjs`. Usa el usuario local `qa_browser_drivesmart`;
eliminarlo antes de repetir la prueba. No usar esta prueba sobre datos de producción.
Si Chromium se instaló dentro del proyecto, antes de instalar o ejecutar establecer:
`$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\.playwright"`.

## Resultados del 6 de noviembre de 2026

- Fase 1: check y migraciones correctos; 4 pruebas Django pasaron.
- Fase 2: check y migraciones correctos; 9 pruebas Django pasaron en 2,7 segundos.
- `load_demo` ejecutado dos veces; seis registros, sin duplicados.
- Playwright Chromium headless: 16 comprobaciones correctas, cero pageerror;
  capturas en escritorio 1440×1000 y viewports 390×844 y 320×740.
- Revisión visual directa: inicio escritorio, catálogo escritorio/móvil, registro
  a 320 y detalle móvil; sin recortes de texto o imágenes ni solapamientos observados.
  La prueba numérica verificó ausencia de desbordamiento horizontal en inicio,
  catálogo, login y registro para los tres tamaños.
- No se probó un teléfono físico ni lectores de pantalla; esto no certifica WCAG.

## Revisión Impeccable

Integridad coherente con catálogo automotriz: navegación común, precios y categorías
consistentes, recursos locales e identidad verde de DriveSmart.

| Dimensión | Valoración (0–4) | Evidencia / límite |
|---|---:|---|
| Accesibilidad | 3 | Labels nativos, alt, foco visible, enlace de salto; sin lector de pantalla |
| Rendimiento | 4 | SVG locales, carga diferida de tarjetas, sin JS de aplicación ni fuentes externas |
| Tema | 2 | Tokens principales; algunos colores de ilustración y estados definidos directamente |
| Responsive | 3 | Tres anchos sin overflow; enlaces pequeños separados, sin prueba física táctil |
| Integridad | 4 | Dos avisos del detector son falsos positivos en los bordes de la carretera |

Valoración interna: 16/20. Sin bloqueos funcionales detectados.
P2: el detector no resuelve etiquetas static de Django; su análisis de color de las
plantillas es incompleto. P3: pueden centralizarse más colores si se amplía el tema.
No se añadió tema oscuro porque no forma parte de esta beta.

## Code Simplification

Lectura de vistas, modelo, Admin y comando demo después de pruebas correctas.
Se conservaron las funciones sencillas y componentes nativos de Django;
no se introdujeron abstracciones ni cambios de comportamiento. La legibilidad de
las hojas CSS se mejora en un commit separado de la funcionalidad.
