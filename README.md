# DriveSmart

Aplicación local con Python 3.12, Django 5.2 LTS y SQLite. Incluye catálogo con fotos,
cuentas de usuario, solicitudes simuladas de renta, asistente textual local y PWA
con aviso sin conexión. Interfaz en español con Django Templates y CSS nativo.

## Ejecutar

```powershell
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Abrir http://127.0.0.1:8000/ · Catálogo `/vehiculos/` · Administración `/admin/`.
Instalación desde cero y mantenimiento: [INSTRUCTIONS.txt](INSTRUCTIONS.txt).
No requiere Node, servicios externos ni herramientas de navegador para funcionar.
La guía independiente de publicación online está en
[docs/PYTHONANYWHERE.md](docs/PYTHONANYWHERE.md).

## Contenido conservado

- `accounts`, `assistant`, `config`, `core`, `rentals`, `vehicles`: aplicación,
  migraciones, comandos de datos y pruebas Django.
- `templates`, `static`: interfaz, PWA y fotografías con sus créditos.
- `media`, `db.sqlite3`: imágenes asignadas y datos locales; no se versionan.
- `.venv`: entorno Python local, ignorado por Git; se recrea con `requirements.txt`.
- `.agents/skills`: skills locales, ignoradas por Git y conservadas solo en esta PC.
- `.git`: historial de versiones local; sin remoto ni push.
- `scripts/package_beta.py`: empaquetado limpio para una entrega futura.
- Documentación de uso, arquitectura, progreso y licencias.

Los resultados de QA, informes históricos, ZIP y herramientas de navegador se
retiraron de esta carpeta. Sus fuentes y evidencias quedaron en el archivo externo
`DriveSmart_Archivo_20261108`, junto a la carpeta del proyecto. Las cachés y los
binarios reinstalables de Node/Playwright se eliminaron.

## Verificar

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test
```

Las pruebas usan datos temporales; no alteran la SQLite local.

[Progreso](docs/PROGRESO.md) · [Arquitectura](docs/ARQUITECTURA_Y_ESCALABILIDAD.md)
· [Imágenes y licencias](docs/IMAGENES.md) · [Criterios visuales](DESIGN.md).

## Conocimiento del asistente

Catálogo curado de 307 temas y 456 formulaciones: 245 respuestas públicas sobre
funciones comprobadas y 211 preguntas comerciales pendientes. Incluye fuentes,
niveles y una guía de revisión. La carga es repetible y conserva ediciones:

```powershell
.venv\Scripts\python.exe manage.py load_knowledge_base
```

Ver [guía del conocimiento](docs/BASE_CONOCIMIENTO.md).
