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
simuladas de renta), `assistant` (chat y conocimiento revisado), `templates`, `static` y `docs`.

El comando `load_demo` crea seis vehículos sin duplicarlos y conserva las ediciones.
Los precios y las características son datos de demostración, no una oferta comercial.
Las ilustraciones se incluyen localmente; ver [licencia de recursos](docs/IMAGENES.md).

Ver [progreso](docs/PROGRESO.md), [QA](docs/QA.md) y [entorno](docs/ENTORNO.md).
La fase 3 incorpora solicitudes simuladas de renta: entrar al detalle de un vehículo,
elegir fechas, revisar el costo y confirmar. Consulta tus solicitudes en `/mis-rentas/`;
su aprobación o rechazo se gestiona en Django Admin. No hay pagos.
Ver [resultados de la fase 3](docs/FASE_3_RESULTADOS.md).
La fase 4 añade el botón Asistente DriveSmart a las páginas públicas. Responde con
FAQ publicadas y vehículos reales; registra las preguntas desconocidas para revisión
en Django Admin. Cargar sus ocho FAQ sin sobrescribir ediciones:

```powershell
.venv\Scripts\python.exe manage.py load_faq
```

No necesita APIs, claves ni modelos de IA. Ver [resultados de fase 4](docs/FASE_4_RESULTADOS.md).
La fase 5 incorpora una PWA mínima: manifiesto, iconos y aviso estático sin conexión.
Vehículos, rentas y asistente requieren acceso al servidor. No se cachean datos privados.
Las instrucciones actualizadas permiten instalar la entrega desde cero en Windows.
Ver [arquitectura y escalabilidad](docs/ARQUITECTURA_Y_ESCALABILIDAD.md)
y [resultados de la entrega](docs/FASE_5_RESULTADOS.md).

Para generar el ZIP limpio (no requiere Git ni skills):

```powershell
.venv\Scripts\python.exe scripts/package_beta.py
```

`DriveSmart_Beta.zip` contiene una carpeta DriveSmart con código, migraciones,
templates, estáticos, imágenes, documentación e instrucciones. Excluye bases de datos,
entornos, .env, media personal, dependencias de desarrollo instaladas y resultados de QA.
Las pruebas de navegador son opcionales; la instalación normal solo requiere Python.

Repositorio local en `main`. No se ha creado remoto ni publicado contenido.
Antes de publicar, revisar `git status` y crear un repositorio privado con autorización.
