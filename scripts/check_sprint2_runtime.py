from pathlib import Path

from app.core import config as config_module
from app.core.config import settings
from app.llm import prompt_registry as prompt_module
from app.llm.prompt_registry import prompt_registry
from app.tools import registry as tool_registry
from app.tools.registry import TOOL_DEFINITIONS

prompt = prompt_registry.get("clevia-informational")

assert settings.APP_VERSION == "0.8.0", settings.APP_VERSION
assert prompt.version == "2.1.0", prompt.version
assert "search_services" in TOOL_DEFINITIONS

repo_root = Path.cwd().resolve()
for module_path in (
    Path(config_module.__file__).resolve(),
    Path(prompt_module.__file__).resolve(),
    Path(tool_registry.__file__).resolve(),
):
    if repo_root not in module_path.parents:
        raise RuntimeError(
            f"Imported stale installed package instead of bind-mounted source: {module_path}"
        )

print("SPRINT2_RUNTIME_CONTRACT_OK")
print("app_version =", settings.APP_VERSION)
print("prompt_version =", prompt.version)
print("search_services =", "registered")
print("config_file =", Path(config_module.__file__).resolve())
print("prompt_file =", Path(prompt_module.__file__).resolve())
print("registry_file =", Path(tool_registry.__file__).resolve())
