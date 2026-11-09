"""Generar una entrega limpia sin Git, SQLite, skills ni el entorno local."""
import argparse
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile


SOURCE_DIRS = ('config', 'core', 'accounts', 'vehicles', 'rentals', 'assistant',
               'templates', 'static', 'docs', 'scripts')
ROOT_FILES = ('manage.py', 'requirements.txt', 'INSTRUCTIONS.txt', 'README.md', 'ENTREGABLE.md',
              '.env.example', 'AGENTS.md', 'DESIGN.md', '.gitignore')
EXCLUDED_DIRS = {'.git', '.agents', '.venv', 'node_modules', 'test-results',
                 '__pycache__', 'media', 'staticfiles'}
EXCLUDED_SUFFIXES = {'.pyc', '.pyo', '.sqlite3', '.sqlite', '.db', '.log', '.tmp',
                     '.zip', '.pem', '.key', '.p12', '.pfx'}


def collect_files(root):
    root = Path(root).resolve()
    candidates = [root / name for name in ROOT_FILES]
    for directory in SOURCE_DIRS:
        candidates.extend((root / directory).rglob('*'))
    selected = []
    for path in candidates:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            continue
        relative = path.relative_to(root)
        if set(relative.parts) & EXCLUDED_DIRS or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if path.name.startswith('.env') and relative.as_posix() != '.env.example':
            continue
        if 'credentials' in path.name.lower() or 'secrets' in path.name.lower():
            continue
        selected.append(path)
    return sorted(set(selected))


def build_archive(root, destination):
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    if not destination.is_relative_to(root):
        raise ValueError('El ZIP debe generarse dentro del directorio del proyecto.')
    files = collect_files(root)
    for path in files:
        if path.suffix.lower() in {'.py', '.txt', '.md', '.json', '.js', '.html', '.example'}:
            content = path.read_text(encoding='utf-8')
            patterns = (r'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----', r'gh[pousr]_[A-Za-z0-9]{30,}',
                        r'AKIA[A-Z0-9]{16}', r'sk-(?:proj-)?[A-Za-z0-9_-]{40,}')
            if any(re.search(pattern, content) for pattern in patterns):
                raise ValueError(f'Posible secreto en {path.relative_to(root)}; revisar antes de empaquetar.')
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, 'DriveSmart/' + path.relative_to(root).as_posix())
    return len(files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='DriveSmart_Beta.zip')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    output = project / args.output
    count = build_archive(project, output)
    print(f'ZIP: {output.resolve()} ({count} archivos)')
