# Imágenes públicas del README

Esta carpeta contiene los archivos que el README enlaza mediante rutas relativas.
Git puede versionarlos y el empaquetador los incluye como documentación. No contiene
la SQLite local, cuentas reales, credenciales, perfiles de navegador ni registros privados.

## Diagrama Archify

- `arquitectura.svg`: exportación vectorial nativa de Archify 3.2, incrustada en el README.
- `arquitectura.png`: alternativa rasterizada del mismo diagrama.
- El diagrama representa la vista lógica local del monolito, no un despliegue productivo.
- Las referencias se validaron contra `f8b6f22daac85f41fda13e2459bcfdc509c128bf`.
- La fuente editable y las herramientas de generación se conservan como respaldo
  fuera del proyecto. Las imágenes finales no necesitan esos archivos para mostrarse.

## Capturas Playwright

Generadas sobre la aplicación real con datos de demostración en SQLite temporal,
fotografías copiadas a un MEDIA_ROOT temporal y dos cuentas creadas solo para QA.
No se confirma ninguna solicitud ni se modifica la base de uso.

| Archivo | Vista | Resolución |
| --- | --- | --- |
| inicio-escritorio.png | Portada y buscador | 1440 × 1120 |
| catalogo-escritorio.png | Seis vehículos y filtros | 1440 × 1000 |
| filtros-escritorio.png | Dos SUV tras aplicar filtro | 1440 × 1000 |
| detalle-escritorio.png | Ficha de Corolla | 1440 × 1000 |
| acceso-escritorio.png | Acceso sin credenciales visibles | 1440 × 1000 |
| renta-escritorio.png | Revisión de costo, sin confirmar | 1440 × 1000 |
| asistente-escritorio.png | Consulta de capacidad de sedanes | 1440 × 1000 |
| administracion-escritorio.png | Vehículos con administrador temporal | 1440 × 1000 |
| inicio-movil.png | Portada móvil | 390 × 1000 |
| catalogo-movil.png | Catálogo y filtros plegados | 390 × 1120 |
| catalogo-sin-conexion.png | Catálogo público completo sin red | 1440 × 1000 |
| catalogo-sin-conexion-movil.png | Copia pública en móvil sin red | 390 × 844 |

Las capturas móviles emulan viewport y entrada táctil; no son pruebas en teléfono físico.

La entrega conserva únicamente los PNG, el SVG y esta documentación de créditos.
Los scripts, el registro de capturas y la fuente Archify están respaldados fuera
del proyecto; no son necesarios para abrir el README ni ejecutar DriveSmart.

## Créditos de las fotografías mostradas

Las imágenes de los vehículos conservan sus fondos y aparecen como referencias
visuales, no como una garantía de versión o año. La portada recorta la foto mediante
CSS; no se retocaron los originales para estas capturas.

| Vehículo | Autor | Licencia |
| --- | --- | --- |
| [Nissan March](https://commons.wikimedia.org/wiki/File:2021_Nissan_March.jpg) | Bull-Doser | Dominio público |
| [Suzuki Swift](https://commons.wikimedia.org/wiki/File:Suzuki_Swift_1.2_GLX_2025.jpg) | RL GNZLZ | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [Toyota Corolla](https://commons.wikimedia.org/wiki/File:2023_Toyota_Corolla_2.0_XEi_(Brazil).jpg) | Just a Man | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| [Kia Seltos](https://commons.wikimedia.org/wiki/File:2024_Kia_Seltos_LX_in_Fusion_Black,_Front_Left,_05-23-2023.jpg) | Elise240SX | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [Mazda CX-5](https://commons.wikimedia.org/wiki/File:2024_Mazda_CX-5_2.0_SP.jpg) | Chanokchon | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| [Volkswagen Jetta](https://commons.wikimedia.org/wiki/File:2025_Volkswagen_Jetta_SEL,_front_3.28.25.jpg) | Kevauto | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

Más información en [IMAGENES.md](../IMAGENES.md) y en
[credits.json](../../static/catalog/credits.json). Conservar estas atribuciones y
los términos de las fotografías al redistribuir las capturas.
