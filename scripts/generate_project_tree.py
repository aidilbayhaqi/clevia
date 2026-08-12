"""Generate PROJECT_TREE.txt yang bersih dari cache/generated dependency.

Jalankan dari root repo:
    python scripts/generate_project_tree.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

IGNORE = {
    '.git', '.idea', '.vscode', '.venv', 'venv', 'env', 'node_modules',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.next',
    'dist', 'build', '.clevia-installer-backups', '.clevia-patches',
}


def build_tree(root: Path, max_depth: int = 5) -> str:
    lines = [f'{root.name}/']

    def walk(directory: Path, prefix: str, depth: int) -> None:
        if depth >= max_depth:
            return
        items = [p for p in directory.iterdir() if p.name not in IGNORE]
        items.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
        for idx, path in enumerate(items):
            last = idx == len(items) - 1
            branch = '└── ' if last else '├── '
            suffix = '/' if path.is_dir() else ''
            lines.append(f'{prefix}{branch}{path.name}{suffix}')
            if path.is_dir():
                walk(path, prefix + ('    ' if last else '│   '), depth + 1)

    walk(root, '', 0)
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=Path('PROJECT_TREE.txt'))
    parser.add_argument('--max-depth', type=int, default=5)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    output.write_text(build_tree(root, args.max_depth), encoding='utf-8')
    print(f'generated={output.relative_to(root).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
