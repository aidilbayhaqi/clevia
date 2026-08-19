from pathlib import Path

from app.agent import orchestrator
from app.core.config import settings
from app.services import lead_capture
from app.tools.registry import TOOL_DEFINITIONS

assert settings.APP_VERSION == "0.9.0", settings.APP_VERSION
assert "capture_lead" in TOOL_DEFINITIONS
assert hasattr(orchestrator.CleviaAgent, "_direct_lead_collection")
assert lead_capture.normalize_phone_number("081234567890") == "+6281234567890"

repo_root = Path.cwd().resolve()
for module in (orchestrator, lead_capture):
    module_path = Path(module.__file__).resolve()
    assert repo_root in module_path.parents, module_path

print("SPRINT3_RUNTIME_CONTRACT_OK")
print("app_version =", settings.APP_VERSION)
print("deterministic_lead_collection =", "enabled")
print("phone_normalization =", "enabled")
