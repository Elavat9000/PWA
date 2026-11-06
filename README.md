# DriveSmart — Beta 0.1

Plataforma local de catálogo de vehículos con Django 5.2 LTS, Python 3.12 y SQLite.
Interfaz en español mediante Django Templates y CSS, autenticación nativa y CRUD en
Django Admin. No requiere servicios externos, Node ni skills para ejecutarse.

Consulta [INSTRUCTIONS.txt](INSTRUCTIONS.txt) para instalar y ejecutar en Windows.

```powershell
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir http://127.0.0.1:8000/ · Catálogo `/vehiculos/` · Administración `/admin/`.

Módulos: `config` (configuración), `core` (inicio), `accounts` (registro y pruebas
de Auth), `vehicles` (modelo, catálogo, Admin y carga demo), `rentals` (solicitudes
simuladas de renta), `templates`, `static` y `docs`.

El comando `load_demo` crea seis vehículos sin duplicarlos y conserva las ediciones.
Los precios y las características son datos de demostración, no una oferta comercial.
Las ilustraciones se incluyen localmente; ver [licencia de recursos](docs/IMAGENES.md).

Ver [progreso](docs/PROGRESO.md), [QA](docs/QA.md) y [entorno](docs/ENTORNO.md).
La fase 3 incorpora solicitudes simuladas de renta: entrar al detalle de un vehículo,
elegir fechas, revisar el costo y confirmar. Consulta tus solicitudes en `/mis-rentas/`;
su aprobación o rechazo se gestiona en Django Admin. No hay pagos.
Ver [resultados de la fase 3](docs/FASE_3_RESULTADOS.md).
El asistente y la PWA corresponden a fases posteriores.

Repositorio local en `main`. No se ha creado remoto ni publicado contenido.
Antes de publicar, revisar `git status` y crear un repositorio privado con autorización.
