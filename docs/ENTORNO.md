# Entorno verificado

- Windows y PowerShell; Python 3.12.10, pip 25.0.1.
- Node.js 26.13.0, npm.cmd 11.20.0; Git 2.56.0.windows.2.
- Codex CLI 0.164.0-alpha.11.1 disponible desde la extensión de VS Code.
- Django 5.2.19 y Pillow 12.3.0 en `.venv`; `pip check` sin conflictos.
- El lanzador `py -0p` no detectó instalaciones; `python` sí apunta a Python 3.12.
  Las instrucciones usan `python` y el ejecutable explícito de `.venv`.

## Skills del proyecto

Instaladas individualmente en `.agents/skills/`, sin colecciones adicionales:

- `playwright-interactive`: openai/skills, skills/.curated/playwright-interactive.
- `code-simplification`: addyosmani/agent-skills, skills/code-simplification.
- `impeccable`: instalador oficial con `--providers=codex --scope=project --no-hooks`.

Se consultaron las ayudas de skills e Impeccable. Las dos primeras se instalaron
mediante el instalador de skills de Codex, con destino explícito al proyecto.
Se leyeron sus SKILL.md. `skills list -a codex` identificó las tres como skills del
proyecto para Codex. Estarán disponibles automáticamente en el siguiente turno.
Impeccable incluye un binario local no versionado; puede restaurarse con su instalador.
No se habilitaron hooks ni Live. Node no es dependencia de la aplicación.

## Limitaciones y resolución

- Playwright Interactive exige `danger-full-access` según su SKILL.md. No se usó
  ese flujo ni se cambió el sandbox; se preparó Playwright convencional.
- npm falló con EACCES dentro del sandbox al acceder al registro; se reintentó la
  descarga con autorización de comandos específicos.
- `.git` está protegido contra escritura desde el sandbox. Los commits requirieron
  permiso y `git -c safe.directory=C:/Users/Diana/Documents/PWA`, limitado al comando,
  por diferencia de propietario entre el usuario de Windows y el del sandbox.
  No se modificó la configuración global ni se inventó identidad Git.
- Impeccable detect no resuelve `{% static %}` de Django. Sus dos avisos sobre
  bordes laterales corresponden a la ilustración de una carretera, no a tarjetas.
