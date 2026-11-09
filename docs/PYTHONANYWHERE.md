# Preparar DriveSmart para PythonAnywhere

Esta guía es únicamente para la futura instalación online. La ejecución local está
documentada en [INSTRUCTIONS.txt](../INSTRUCTIONS.txt). No subir datos hasta completar
y verificar los pasos de preparación.

## Alcance de la demo

DriveSmart es una demo Django con SQLite, rentas simuladas y sin pagos. PythonAnywhere
sirve la aplicación y sus archivos mediante una cuenta Linux y una aplicación WSGI.
No se debe copiar el virtualenv de Windows ni subir la SQLite o `media/` de esta PC.
La guía de PythonAnywhere describe cómo desplegar un proyecto Django existente con
un virtualenv: [Deploying an existing Django project](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/).

## 1. Crear la aplicación y su entorno

1. En PythonAnywhere, crear una web app con **Manual configuration** y la misma
   versión de Python para la web app y el virtualenv. Python 3.12 es la versión
   utilizada localmente; confirmar en el panel que esté disponible antes de elegirla.
2. Subir solo los archivos de código y recursos necesarios. No subir `.venv`,
   `db.sqlite3`, `.env`, `media/`, `staticfiles/`, credenciales ni datos personales.
3. En una consola Bash, crear y activar un virtualenv de esa versión e instalar
   dependencias:

   ```bash
   mkvirtualenv drivesmart --python=/usr/bin/python3.12
   workon drivesmart
   pip install -r ~/PWA/requirements.txt
   pip check
   ```

   Sustituir `~/PWA` por la ruta real donde se subió el proyecto. Asociar el mismo
   virtualenv desde **Web > Virtualenv**. Si PythonAnywhere no ofrece Python 3.12,
   no usar otra versión a ciegas: comprobar que la versión elegida sea compatible con
   Django 5.2 y Pillow 12.3 antes de continuar.

## 2. Configurar el WSGI y HTTPS

En **Web**, abrir el archivo WSGI generado por PythonAnywhere. Antes de llamar a
`get_wsgi_application()`, añadir las variables de producción con valores propios:

```python
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_DEBUG'] = '0'
os.environ['DJANGO_SECRET_KEY'] = '<clave aleatoria privada de al menos 50 caracteres>'
os.environ['DJANGO_ALLOWED_HOSTS'] = '<usuario>.pythonanywhere.com'
```

Conservar la ruta de proyecto de PythonAnywhere en `sys.path` y al final cargar la
aplicación WSGI de Django:

```python
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

Usar una clave nueva, única y secreta. No incluirla en Git, ZIPs, capturas ni mensajes.
Configurar también las mismas variables en Bash antes de ejecutar `manage.py`
(incluido `DJANGO_SECRET_KEY`); las variables del WSGI no se heredan necesariamente
en las consolas.

Activar HTTPS en el panel **Web** antes de probar la aplicación. La configuración
de producción de DriveSmart redirige a HTTPS, marca como seguras las cookies de
sesión/CSRF y espera que el proxy entregue `X-Forwarded-Proto: https`.
Comprobar el sitio y el inicio de sesión con la base vacía. Si aparece un bucle de
redirección o Django no detecta HTTPS, detenerse y revisar el comportamiento del
proxy antes de cargar datos.

Solo después de verificar HTTPS, puede activarse HSTS durante un año en WSGI y Bash:

```python
os.environ['DJANGO_SECURE_HSTS_SECONDS'] = '31536000'
```

Recargar la web app después de cambiar el WSGI. No activar HSTS antes de confirmar
que el dominio siempre estará disponible por HTTPS.

## 3. Inicializar SQLite vacía

Primero confirmar la ruta en `config/settings.py`: la base está definida como
`BASE_DIR / 'db.sqlite3'`. En Bash, con el virtualenv y variables de producción
configurados:

```bash
cd ~/PWA
python manage.py check
python manage.py migrate
python manage.py createsuperuser
```

Esto crea una base nueva en la cuenta, sin copiar la SQLite de Windows. Confirmar
que el usuario administrador pueda entrar y que las páginas no revelen errores de
configuración antes de introducir vehículos demo o contenido de conocimiento.

## 4. Publicar archivos estáticos y media

DriveSmart define `STATIC_ROOT = BASE_DIR / 'staticfiles'` y `MEDIA_ROOT = BASE_DIR / 'media'`.
En Bash:

```bash
cd ~/PWA
python manage.py collectstatic --noinput
```

En **Web > Static files**, agregar estos mapeos usando rutas absolutas de la cuenta:

| URL | Directorio |
|---|---|
| `/static/` | `/home/<usuario>/PWA/staticfiles` |
| `/media/` | `/home/<usuario>/PWA/media` |

El mapeo de `/media/` se necesita para imágenes subidas desde Admin. Crear la carpeta
antes de configurarlo si todavía no existe. Tras modificar estáticos, volver a ejecutar
`collectstatic` y recargar la aplicación. Ver la guía oficial de
[archivos estáticos en PythonAnywhere](https://help.pythonanywhere.com/pages/DjangoStaticFiles/).

Las imágenes de referencia incluidas en `static/catalog/` son estáticos del proyecto;
las imágenes cargadas con Admin se escriben en `media/`. Mantener ambos tipos separados.

## 5. Verificación antes de datos demo

- Abrir inicio, catálogo vacío, login, Admin, manifiesto PWA y service worker por HTTPS.
- Confirmar CSS, JavaScript e iconos; registrar el service worker en el navegador.
- Probar login, logout y CSRF, y verificar que no haya bucle de redirección.
- Confirmar que no se cacheen páginas privadas ni respuestas POST del asistente.
- Ejecutar `python manage.py check --deploy` con el entorno de producción.
- Revisar los logs de error de PythonAnywhere y resolver errores antes de continuar.

El service worker puede guardar una copia pública aislada del catálogo completo y
sus fotografías. No guarda el HTML normal de usuarios conectados. Las cuentas,
rentas, chat y comprobación de disponibilidad requieren conexión al servidor.
Tras actualizar esta función, ejecutar collectstatic, recargar la web app y comprobar
la descarga en segundo plano y el acceso offline. No hay avisos técnicos para el cliente. No se modifica la
instalación online automáticamente desde las pruebas locales.

## 6. Cargar contenido demo después de aprobar las pruebas

Solo tras confirmar despliegue, HTTPS, Admin, SQLite y archivos estáticos, decidir qué
contenido de demostración cargar. Si se autoriza:

```bash
python manage.py load_demo
python manage.py load_knowledge_base
python manage.py load_vehicle_images
```

Estos comandos cargan vehículos ficticios, conocimiento local e imágenes de referencia.
No copiar registros de la SQLite local ni fotos personales. Hacer respaldos de la base
y `media/` del hosting de acuerdo con las opciones de la cuenta.
