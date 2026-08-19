from pathlib import Path

from app.agent import orchestrator
from app.core.config import settings

requested = orchestrator.requested_profile_fields("Alamat dan Instagram Clevia apa?")

assert settings.APP_VERSION == "0.8.1", settings.APP_VERSION
assert requested == ("address", "instagram"), requested

path = Path(orchestrator.__file__).resolve()
repo_root = Path.cwd().resolve()
assert repo_root in path.parents, path

print("CLEVIA_PROFILE_HOTFIX_CONTRACT_OK")
print("app_version =", settings.APP_VERSION)
print("profile_fields =", requested)
print("orchestrator_file =", path)
