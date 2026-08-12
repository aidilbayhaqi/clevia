"""Audit titik wiring LLM pada canonical runtime Clevia.

Tidak mengubah source code. Output digunakan untuk menentukan patch wiring orchestrator
berikutnya tanpa menebak entrypoint/provider lama.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

WATCH_TERMS = (
    "provider_adapter",
    "gemini_provider",
    "provider_factory",
    "openai",
    "gemini",
    "generate_text",
    "complete",
    "responses.create",
    "chat.completions",
)


def scan_file(path: Path, repo: Path) -> dict[str, Any]:
    rel = path.relative_to(repo).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return {"file": rel, "syntax_error": str(exc), "imports": [], "hits": []}

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)

    hits: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        matched = [term for term in WATCH_TERMS if term.lower() in low]
        if matched:
            hits.append({"line": lineno, "terms": matched, "text": line.strip()[:300]})

    return {
        "file": rel,
        "imports": sorted(set(imports)),
        "hits": hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", dest="json_path", default="docs/audits/llm-runtime-wiring-v0.6.2.json")
    parser.add_argument("--md", dest="md_path", default="docs/audits/llm-runtime-wiring-v0.6.2.md")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    roots = [repo / "app" / "agent", repo / "app" / "api", repo / "app" / "llm"]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)

    records = [scan_file(path, repo) for path in sorted(set(files))]
    candidate_records = [r for r in records if r.get("hits")]
    canonical_orchestrator = repo / "app" / "agent" / "orchestrator.py"

    report = {
        "version": "0.6.2",
        "canonical_orchestrator_exists": canonical_orchestrator.exists(),
        "files_scanned": len(records),
        "files_with_llm_hits": len(candidate_records),
        "candidates": candidate_records,
    }

    json_path = repo / args.json_path
    md_path = repo / args.md_path
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Audit Wiring LLM Clevia v0.6.2",
        "",
        f"- Canonical orchestrator tersedia: `{report['canonical_orchestrator_exists']}`",
        f"- File dipindai: `{report['files_scanned']}`",
        f"- File dengan indikasi wiring LLM: `{report['files_with_llm_hits']}`",
        "",
        "## Kandidat wiring",
        "",
    ]
    if not candidate_records:
        lines.append("Tidak ditemukan indikasi wiring LLM pada area yang dipindai.")
    for record in candidate_records:
        lines.append(f"### `{record['file']}`")
        lines.append("")
        if record.get("imports"):
            relevant = [x for x in record["imports"] if x.startswith("app.llm") or "openai" in x.lower() or "gemini" in x.lower()]
            if relevant:
                lines.append("Import relevan:")
                for item in relevant:
                    lines.append(f"- `{item}`")
                lines.append("")
        for hit in record.get("hits", [])[:40]:
            safe = hit["text"].replace("`", "'")
            lines.append(f"- L{hit['line']}: `{safe}`")
        lines.append("")

    lines.extend([
        "## Keputusan",
        "",
        "Audit ini bersifat read-only. v0.6.2 memasang kontrak + factory, tetapi tidak menimpa orchestrator secara heuristik. "
        "Titik wiring dari report ini menjadi input patch berikutnya agar perubahan runtime bersifat eksplisit dan dapat diuji.",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"audit_json={json_path}")
    print(f"audit_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
