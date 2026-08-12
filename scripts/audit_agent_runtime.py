"""Audit canonical agent runtime Clevia.

Patch: clevia-p0-canonical-agent-runtime-v0.6.1

Script ini tidak memodifikasi source Python runtime. Ia memetakan penggunaan
``app.agent`` (canonical) dan ``app.agents`` (legacy), membuat baseline tech-debt,
dan menghasilkan report yang dapat dipakai untuk migrasi aman pada patch berikutnya.

Contoh:
    python scripts/audit_agent_runtime.py --write-baseline \
        --report-md docs/audits/agent-runtime-audit-v0.6.1.md \
        --report-json docs/audits/agent-runtime-audit-v0.6.1.json
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

IGNORE_DIRS = {
    '.git', '.idea', '.vscode', '.venv', 'venv', 'env', 'node_modules',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist',
    'build', '.next', '.clevia-installer-backups', '.clevia-patches',
}

CANONICAL_PREFIX = 'app.agent'
LEGACY_PREFIX = 'app.agents'


@dataclass(frozen=True, slots=True)
class ImportRef:
    file: str
    line: int
    module: str
    kind: str

    @property
    def key(self) -> str:
        return f'{self.file}:{self.line}:{self.module}:{self.kind}'


def _ignored(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in IGNORE_DIRS for part in rel.parts)


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob('*.py'):
        if not _ignored(path, root):
            yield path


def scan_imports(root: Path) -> list[ImportRef]:
    refs: list[ImportRef] = []
    for path in iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            source = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            source = path.read_text(encoding='utf-8', errors='replace')
        try:
            tree = ast.parse(source, filename=rel)
        except SyntaxError:
            # Syntax problem akan ditangani lint/test; audit dependency tetap berjalan
            # untuk file lain agar report tidak hilang seluruhnya.
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith((CANONICAL_PREFIX, LEGACY_PREFIX)):
                        refs.append(ImportRef(rel, node.lineno, alias.name, 'import'))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if module.startswith((CANONICAL_PREFIX, LEGACY_PREFIX)):
                    refs.append(ImportRef(rel, node.lineno, module, 'from'))
    return sorted(refs, key=lambda x: (x.file, x.line, x.module))


def scan_text_references(root: Path) -> list[dict[str, object]]:
    allowed_suffixes = {'.py', '.toml', '.yaml', '.yml', '.json', '.ini', '.cfg'}
    out: list[dict[str, object]] = []
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        if _ignored(path, root):
            continue
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            if CANONICAL_PREFIX in line or LEGACY_PREFIX in line:
                out.append({
                    'file': rel,
                    'line': index,
                    'canonical_ref': CANONICAL_PREFIX in line,
                    'legacy_ref': LEGACY_PREFIX in line,
                    'preview': line.strip()[:240],
                })
    return out


def _is_inside_legacy(file: str) -> bool:
    return file == 'app/agents.py' or file.startswith('app/agents/')


def _is_inside_canonical(file: str) -> bool:
    return file == 'app/agent.py' or file.startswith('app/agent/')


def build_audit(root: Path) -> dict[str, object]:
    imports = scan_imports(root)
    canonical = [ref for ref in imports if ref.module.startswith(CANONICAL_PREFIX)]
    legacy = [ref for ref in imports if ref.module.startswith(LEGACY_PREFIX)]
    external_legacy = [ref for ref in legacy if not _is_inside_legacy(ref.file)]
    canonical_to_legacy = [ref for ref in legacy if _is_inside_canonical(ref.file)]

    canonical_dir = root / 'app' / 'agent'
    legacy_dir = root / 'app' / 'agents'

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repo_name': root.name,
        'canonical_runtime': 'app/agent',
        'legacy_runtime': 'app/agents',
        'canonical_exists': canonical_dir.is_dir(),
        'legacy_exists': legacy_dir.is_dir(),
        'canonical_import_count': len(canonical),
        'legacy_import_count': len(legacy),
        'external_legacy_import_count': len(external_legacy),
        'canonical_imports_legacy_count': len(canonical_to_legacy),
        'canonical_imports': [asdict(x) for x in canonical],
        'legacy_imports': [asdict(x) for x in legacy],
        'external_legacy_imports': [asdict(x) for x in external_legacy],
        'canonical_imports_legacy': [asdict(x) for x in canonical_to_legacy],
        'text_references': scan_text_references(root),
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_baseline(root: Path, audit: dict[str, object]) -> Path:
    path = root / '.clevia-architecture' / 'legacy_agent_imports.baseline.json'
    payload = {
        'schema_version': 1,
        'purpose': 'Baseline utang teknis import app.agents; import legacy baru dilarang.',
        'canonical_runtime': 'app/agent',
        'legacy_runtime': 'app/agents',
        'generated_at': audit['generated_at'],
        'imports': audit['external_legacy_imports'],
    }
    write_json(path, payload)
    return path


def render_markdown(audit: dict[str, object]) -> str:
    ext = audit['external_legacy_imports']
    canon_bad = audit['canonical_imports_legacy']
    legacy_exists = bool(audit['legacy_exists'])

    lines = [
        '# Audit Canonical Agent Runtime — v0.6.1',
        '',
        f"Generated: `{audit['generated_at']}`",
        '',
        '## Keputusan arsitektur',
        '',
        '- Runtime canonical: `app/agent`.',
        '- `app/agents` diperlakukan sebagai legacy/deprecated apabila masih ada.',
        '- Patch ini tidak menghapus legacy runtime secara otomatis.',
        '- Import legacy baru diblokir melalui architecture test berbasis baseline.',
        '',
        '## Ringkasan',
        '',
        f"- `app/agent` tersedia: **{audit['canonical_exists']}**",
        f"- `app/agents` tersedia: **{audit['legacy_exists']}**",
        f"- Import canonical ditemukan: **{audit['canonical_import_count']}**",
        f"- Import legacy ditemukan: **{audit['legacy_import_count']}**",
        f"- Import legacy dari luar folder legacy: **{audit['external_legacy_import_count']}**",
        f"- Import legacy dari dalam canonical runtime: **{audit['canonical_imports_legacy_count']}**",
        '',
    ]

    if not audit['canonical_exists']:
        lines += [
            '## BLOCKER', '',
            '`app/agent` tidak ditemukan. Jangan melakukan runtime wiring sebelum struktur canonical dikonfirmasi.', '',
        ]
    elif canon_bad:
        lines += [
            '## BLOCKER', '',
            'Canonical runtime masih mengimpor legacy runtime. Dependency ini harus dimigrasikan sebelum `app/agents` dapat dinonaktifkan.', '',
        ]
    elif ext:
        lines += [
            '## Status migrasi', '',
            'Masih ada consumer yang mengimpor `app.agents`. Import tersebut dibaseline sebagai utang teknis dan **tidak dihapus otomatis**.', '',
        ]
    elif legacy_exists:
        lines += [
            '## Status migrasi', '',
            '`app/agents` masih ada tetapi tidak ditemukan import legacy eksternal berbasis AST. Tetap lakukan smoke/integration test sebelum menghapus folder karena dynamic import dapat tidak terdeteksi.', '',
        ]
    else:
        lines += ['## Status migrasi', '', 'Tidak ditemukan duplicate legacy directory.', '']

    if ext:
        lines += ['## Import legacy eksternal', '', '| File | Baris | Module |', '|---|---:|---|']
        for item in ext:
            lines.append(f"| `{item['file']}` | {item['line']} | `{item['module']}` |")
        lines.append('')

    lines += [
        '## Tindakan berikutnya', '',
        '1. Review report ini.',
        '2. Migrasikan consumer legacy satu per satu dengan test/eval evidence.',
        '3. Jangan menambah import `app.agents` baru.',
        '4. Setelah runtime canonical terbukti, lakukan provider factory/runtime wiring pada patch berikutnya.',
        '5. Hapus `app/agents` hanya setelah runtime, integration test, dan smoke test membuktikan tidak ada dependency aktif.',
        '',
    ]
    return '\n'.join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--write-baseline', action='store_true')
    parser.add_argument('--report-md', type=Path)
    parser.add_argument('--report-json', type=Path)
    parser.add_argument('--strict', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    audit = build_audit(root)

    if args.write_baseline:
        path = write_baseline(root, audit)
        print(f'baseline={path.relative_to(root).as_posix()}')

    if args.report_json:
        path = args.report_json if args.report_json.is_absolute() else root / args.report_json
        write_json(path, audit)
        print(f'report_json={path.relative_to(root).as_posix()}')

    if args.report_md:
        path = args.report_md if args.report_md.is_absolute() else root / args.report_md
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_markdown(audit), encoding='utf-8')
        print(f'report_md={path.relative_to(root).as_posix()}')

    print(f"canonical_exists={audit['canonical_exists']}")
    print(f"legacy_exists={audit['legacy_exists']}")
    print(f"canonical_imports={audit['canonical_import_count']}")
    print(f"external_legacy_imports={audit['external_legacy_import_count']}")
    print(f"canonical_imports_legacy={audit['canonical_imports_legacy_count']}")

    if args.strict:
        if not audit['canonical_exists']:
            return 2
        if audit['canonical_imports_legacy_count']:
            return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
