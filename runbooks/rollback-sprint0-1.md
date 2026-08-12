# Rollback — Sprint 0 + 1 update

The installer creates a timestamped backup under `.clevia-updates/` before overwriting files.
Use the included rollback PowerShell script and the backup folder printed by the installer.

Database downgrade is intentionally **not automatic** because production data may have been added
to new trace, feedback, and knowledge tables. Code rollback should be performed first, followed by a
reviewed database rollback if required.

If a severe issue occurs:

1. Stop or isolate the affected capability.
2. Preserve request/agent traces.
3. Restore code from the installer backup.
4. Rebuild/restart containers.
5. Review whether `alembic downgrade 20260808_0001` is safe for the affected environment.
