"""Architecture guard untuk canonical agent runtime Clevia.

Test tidak memaksa legacy debt lama hilang sekaligus. Baseline dari installer
menjadi daftar debt yang sudah diketahui; import ``app.agents`` baru akan gagal.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / '.clevia-architecture' / 'legacy_agent_imports.baseline.json'
IGNORE_PARTS = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.clevia-installer-backups', '.clevia-patches',
}


def _legacy_imports() -> set[tuple[str, int, str, str]]:
    found: set[tuple[str, int, str, str]] = set()
    for path in ROOT.rglob('*.py'):
        rel = path.relative_to(ROOT)
        if any(part in IGNORE_PARTS for part in rel.parts):
            continue
        rel_posix = rel.as_posix()
        if rel_posix.startswith('app/agents/'):
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=rel_posix)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('app.agents'):
                        found.add((rel_posix, node.lineno, alias.name, 'import'))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if module.startswith('app.agents'):
                    found.add((rel_posix, node.lineno, module, 'from'))
    return found


def _baseline_imports() -> set[tuple[str, int, str, str]]:
    if not BASELINE.exists():
        return set()
    payload = json.loads(BASELINE.read_text(encoding='utf-8'))
    return {
        (item['file'], int(item['line']), item['module'], item['kind'])
        for item in payload.get('imports', [])
    }


def test_canonical_agent_runtime_exists() -> None:
    assert (ROOT / 'app' / 'agent').is_dir(), (
        'Canonical runtime app/agent tidak ditemukan. Jangan membuat runtime baru '
        'sebelum boundary arsitektur dikonfirmasi.'
    )


def test_canonical_runtime_does_not_depend_on_legacy_runtime() -> None:
    bad = [item for item in _legacy_imports() if item[0].startswith('app/agent/')]
    assert not bad, f'app/agent masih bergantung pada app/agents: {sorted(bad)}'


def test_no_new_legacy_agent_imports() -> None:
    current = _legacy_imports()
    baseline = _baseline_imports()
    new = current - baseline
    assert not new, (
        'Import baru ke app.agents dilarang. Gunakan app.agent sebagai canonical runtime. '
        f'Import baru: {sorted(new)}'
    )
