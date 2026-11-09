# DriveSmart — Criterios visuales

La interfaz ayuda a elegir un vehículo y enviar una solicitud simulada.
Su carácter es claro, tranquilo y práctico, con fotografías y datos como protagonistas.
La modernidad se expresa con jerarquía, composición y consistencia.

## Identidad

- Verde principal #17604e y tinta #162e2c.
- Fondo crema #f6f5ef, superficies blancas, portada con navegación tinta y franja verde.
- Variables de color y espaciado compartidas en static/css/site.css.
- Segoe UI y fuentes del sistema, con títulos alineados a la izquierda.
- Precios y totales con numerales tabulares; el total destaca sobre la explicación.
- Escala de espacios: 4, 8, 12, 16, 24, 32, 48 y 64 px.
- Radios compartidos de 14 px para superficies y 8 px para controles.

## Composición

La portada toma la composición de la referencia del usuario: aviso fino, navegación
oscura, buscador blanco sobre una fotografía panorámica y titular amplio en una
franja verde. Conserva categorías y presupuesto como filtros reales; no simula
controles de sucursal, edad u horarios. En móvil el buscador queda antes de la foto.
La fotografía de referencia conserva su enlace a créditos y puede recortarse en
la portada; las imágenes del catálogo mantienen object-fit: contain.

El inicio lleva a explorar vehículos. El catálogo permite comparar. El detalle
separa imagen, características y acción. Las tarjetas agrupan entidades y resúmenes
comparables, sin encajonar cada fragmento de texto.

Los pasos Fechas → Revisión → Solicitud reflejan el recorrido real. Registrar una
solicitud no equivale a aprobarla. En escritorio, vehículo y formulario se presentan
en columnas. En móvil, el vehículo se resume en una fila.

Usar una acción principal por grupo y enlaces claros para las acciones secundarias.
Mantener la navegación visible y agrupar los controles de cuenta. El pie permanece
al final de la pantalla en las vistas cortas.

## Imágenes e iconos

Fotografías locales de referencia con autor y licencia en docs/IMAGENES.md.
No presentarlas como unidades reales ni como una versión o año exactos cuando difieren.
Conservar proporciones con object-fit: contain. Las fotos cargadas por Admin tienen
prioridad y sus propios requisitos de uso.

Iconos SVG geométricos de trazo uniforme y controles con nombre accesible.
El lanzador del asistente es compacto para reducir la obstrucción de contenido.
Las sombras expresan la elevación del asistente flotante.

## Interacción y adaptación

- Controles principales de al menos 44 px de alto; campos de 48 px.
- Foco visible y etiquetas persistentes, sin sustituirlas por placeholders.
- Filtros desplegables en móvil/tablet, abiertos cuando existen errores.
- Sin JavaScript los filtros siguen abiertos y funcionan mediante GET.
- Errores, espera, estados vacíos y disponibilidad reconocibles también por texto.
- El asistente se abre únicamente cuando se solicita.
- Probar 1440, 768, 390 y 320 px, y diálogos en pantallas horizontales bajas.
- Conservar la privacidad PWA e incrementar su versión de caché al cambiar los estilos cacheados.

## Evitar

Degradados decorativos, brillos, tarjetas de vidrio, efectos 3D, animaciones repetitivas,
publicidad vacía, métricas inventadas, reseñas ficticias, controles sin función,
exceso de etiquetas y ventanas no solicitadas. Las mejoras de presentación no añaden
frameworks ni funciones ajenas al recorrido existente.

## Validación

Aplicar las guías locales Impeccable (distill/polish) y revisar el resultado renderizado.
El detector de archivos es una señal parcial: no interpreta todos los tags Django.
Mantener Auth, permisos, validaciones, cálculo de renta y motor del asistente.
Ver docs/PROGRESO.md para el estado actual del proyecto.
