from pathlib import Path

from app.agent import orchestrator
from app.core.config import settings
from app.db.models.conversation import Conversation
from app.llm.prompt_registry import prompt_registry
from app.tools.registry import TOOL_DEFINITIONS

assert settings.APP_VERSION == "1.0.0", settings.APP_VERSION
assert prompt_registry.get("clevia-informational").version == "2.2.0"
assert "get_availability" in TOOL_DEFINITIONS
assert "create_appointment_request" in TOOL_DEFINITIONS
assert "booking_draft" in Conversation.__table__.columns
assert hasattr(orchestrator.CleviaAgent, "_direct_booking_flow")

repo_root = Path.cwd().resolve()
module_path = Path(orchestrator.__file__).resolve()
assert repo_root in module_path.parents, module_path

print("SPRINT4_RUNTIME_CONTRACT_OK")
print("app_version =", settings.APP_VERSION)
print("prompt_version = 2.2.0")
print("booking_draft =", "registered")
print("availability_tool =", "registered")
print("appointment_write_tool =", "registered")
