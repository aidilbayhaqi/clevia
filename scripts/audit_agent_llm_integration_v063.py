"""Audit read-only untuk menentukan titik wiring Agent -> LLMRuntime berikutnya."""
from __future__ import annotations

import ast
import json
from pathlib import Path


CALL_TERMS = (
    "provider_adapter",
    "provider_factory",
    "gemini_provider",
    "gemini_adapter",
    "llm_bridge",
    "llmruntime",
    "create_llm_provider",
    "generate_text",
    ".generate(",
    ".complete(",
    "chat.completions",
    "responses.create",
)


def scan(path: Path, repo: Path) -> dict:
    rel = path.relative_to(repo).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    result = {"file": rel, "imports": [], "classes": [], "functions": [], "hits": []}
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        result["syntax_error"] = str(exc)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result["imports"].extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                result["imports"].append(f"{mod}.{alias.name}" if mod else alias.name)
        elif isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append(node.name)

    for lineno, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        matched = [term for term in CALL_TERMS if term.lower() in low]
        if matched:
            result["hits"].append({"line": lineno, "terms": matched, "text": line.strip()[:500]})

    result["imports"] = sorted(set(result["imports"]))
    result["classes"] = sorted(set(result["classes"]))
    result["functions"] = sorted(set(result["functions"]))
    return result


def main() -> int:
    repo = Path(".").resolve()
    targets = []
    for base in (repo / "app" / "agent", repo / "app" / "api"):
        if base.exists():
            targets.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)

    records = [scan(p, repo) for p in sorted(set(targets))]
    relevant = [r for r in records if r.get("hits") or any(i.startswith("app.llm") for i in r.get("imports", []))]
    orch = repo / "app" / "agent" / "orchestrator.py"

    report = {
        "version": "0.6.3",
        "canonical_orchestrator_exists": orch.exists(),
        "bridge_exists": (repo / "app" / "agent" / "llm_bridge.py").exists(),
        "runtime_exists": (repo / "app" / "llm" / "runtime.py").exists(),
        "files_scanned": len(records),
        "relevant": relevant,
    }

    out_dir = repo / "docs" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "agent-llm-integration-v0.6.3.json"
    md_path = out_dir / "agent-llm-integration-v0.6.3.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Audit Integrasi Agent ↔ LLM Runtime v0.6.3",
        "",
        f"- Canonical orchestrator: `{report['canonical_orchestrator_exists']}`",
        f"- Agent LLM bridge: `{report['bridge_exists']}`",
        f"- LLM runtime: `{report['runtime_exists']}`",
        f"- File dipindai: `{report['files_scanned']}`",
        "",
        "## Titik integrasi yang ditemukan",
        "",
    ]
    if not relevant:
        lines.append("Tidak ada call site LLM yang terdeteksi pada app/agent atau app/api.")
    for rec in relevant:
        lines.append(f"### `{rec['file']}`")
        lines.append("")
        llm_imports = [x for x in rec.get("imports", []) if x.startswith("app.llm")]
        if llm_imports:
            lines.append("Import LLM:")
            lines.extend(f"- `{x}`" for x in llm_imports)
            lines.append("")
        if rec.get("classes"):
            lines.append("Class: " + ", ".join(f"`{x}`" for x in rec["classes"]))
            lines.append("")
        for hit in rec.get("hits", [])[:60]:
            safe = hit["text"].replace("`", "'")
            lines.append(f"- L{hit['line']}: `{safe}`")
        lines.append("")

    lines.extend([
        "## Status wiring",
        "",
        "Patch v0.6.3 memasang runtime bridge dan trace contract yang siap digunakan oleh orchestrator. "
        "Audit ini tetap read-only terhadap orchestrator agar perubahan business flow tidak dilakukan secara heuristik.",
        "",
        "## Gate sebelum mengubah orchestrator",
        "",
        "1. Identifikasi class/function entrypoint orchestrator aktif.",
        "2. Identifikasi call site LLM lama dan bentuk return value-nya.",
        "3. Ganti dependency ke `AgentLLMBridge` secara eksplisit.",
        "4. Propagasikan `request_id`, `trace_id`, `clinic_id`, `conversation_id`, dan `prompt_version` ke `LLMCallContext`.",
        "5. Jalankan unit + integration + agent eval sebelum menghapus provider path lama.",
        "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"audit_md={md_path}")
    print(f"audit_json={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
