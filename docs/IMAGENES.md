# Recursos locales

Las tres ilustraciones geométricas SVG de `static/images/` fueron creadas para
DriveSmart en esta implementación. Se permite usarlas, modificarlas y distribuirlas
con el proyecto (CC0-1.0). No son fotografías ni representaciones exactas de marcas.
El catálogo las identifica como referencias. No necesita conexiones externas.
Las fotografías subidas por un administrador requieren sus propios derechos de uso.

## Fotografías de referencia — 8 de noviembre de 2026

Las seis fotografías se descargaron de Wikimedia Commons tras comprobar la ficha
individual de autor y licencia. Se conservan localmente en `static/catalog/` para
reproducir la demo sin descargas externas. No se retocaron ni se eliminó su fondo.
Dos archivos son miniaturas de Wikimedia a 1280 px; los restantes son originales.
La proporción se conserva mediante CSS, sin estirar los coches.

| Modelo | Año fotografiado | Autor | Licencia y fuente |
|---|---|---|---|
| Nissan March | 2021 | Bull-Doser | [Public domain](https://commons.wikimedia.org/wiki/File:2021_Nissan_March.jpg) · [Fuente](https://commons.wikimedia.org/wiki/File:2021_Nissan_March.jpg) |
| Suzuki Swift | 2025 | RL GNZLZ | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [Fuente](https://commons.wikimedia.org/wiki/File:Suzuki_Swift_1.2_GLX_2025.jpg) |
| Toyota Corolla | 2023 | Just a Man | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Fuente](https://commons.wikimedia.org/wiki/File:2023_Toyota_Corolla_2.0_XEi_(Brazil).jpg) |
| Kia Seltos | 2024 | Elise240SX | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [Fuente](https://commons.wikimedia.org/wiki/File:2024_Kia_Seltos_LX_in_Fusion_Black,_Front_Left,_05-23-2023.jpg) |
| Mazda CX-5 | 2024 | Chanokchon | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [Fuente](https://commons.wikimedia.org/wiki/File:2024_Mazda_CX-5_2.0_SP.jpg) |
| Volkswagen Jetta | 2025 | Kevauto | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [Fuente](https://commons.wikimedia.org/wiki/File:2025_Volkswagen_Jetta_SEL,_front_3.28.25.jpg) |

Las licencias se mantienen para estas fotografías; no se transfiere su autoría a
DriveSmart. Los archivos BY-SA y cualquier adaptación que se distribuya deben
conservar la licencia correspondiente. El manifiesto `static/catalog/credits.json`
conserva las URLs de origen, autor y licencia. La página `/creditos-imagenes/`
los expone al visitante, enlazada desde portada, detalle, catálogo y pie de página.

Los años y versiones fotografiados pueden diferir del registro demo; se advierte
expresamente en la interfaz. No son fotografías de unidades reales de una flota
DriveSmart ni se afirma relación comercial con sus fabricantes.

## Almacenamiento por vehículo

`Vehicle.image` ya existía: `ImageField(upload_to='vehicles/', blank=True)`.
SQLite conserva el nombre relativo y Django almacena el archivo en
`MEDIA_ROOT/vehicles/` (por defecto `media/vehicles/`). No se guardan binarios en SQLite.
Cada registro admite **una imagen principal**, sustituible desde Admin → Vehículos →
Imagen → Guardar. Catálogo y detalle muestran automáticamente la foto asignada.
Actualmente no hay galería de múltiples imágenes ni una tabla de modelos independiente.

Para asociar la colección de referencia, primero cargar los demos y ejecutar:

```powershell
.venv\Scripts\python.exe manage.py load_demo
.venv\Scripts\python.exe manage.py load_vehicle_images
```

El comando utiliza archivos locales; solo completa campos vacíos, coincide por marca
y modelo y no sustituye fotos subidas por el administrador. Repetirlo no crea nuevas
copias cuando las asociaciones ya existen. No altera precios, años ni disponibilidad.
Para la ejecución local se respaldó SQLite en `test-results/catalog-photos/` y se
asociaron seis imágenes; la segunda ejecución asoció cero.

`media/` y SQLite permanecen ignorados en Git y excluidos de los ZIP. La colección
pública de `static/catalog/`, sus fuentes y el comando sí forman parte del código
entregable. Así se puede reproducir la demo sin distribuir datos privados.
Las fotografías no se añadieron a la lista de caché PWA: siguen requiriendo conexión.
