from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.db.models.clinic import Clinic
from app.db.session import AsyncSessionLocal
from app.tools.registry import execute_tool


async def main() -> None:
    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(
            select(Clinic).where(Clinic.slug == settings.DEFAULT_CLINIC_SLUG)
        )
        if clinic is None:
            raise RuntimeError("Default clinic is not seeded.")

        glow = await execute_tool(
            db,
            clinic_id=clinic.id,
            conversation=None,  # read-only tool does not use conversation state
            name="search_services",
            arguments={"query": "Glow Facial Signature"},
        )

        services = glow.get("services", [])
        if len(services) != 1:
            raise RuntimeError(
                f"Expected one precise Glow Facial result, got {len(services)}: {services!r}"
            )

        service = services[0]
        assert service["name"] == "Glow Facial Signature"
        assert int(service["duration_minutes"]) == 60
        assert int(float(service["price_from"])) == 650000
        assert service["source_ref"].startswith("service:")

        laser = await execute_tool(
            db,
            clinic_id=clinic.id,
            conversation=None,
            name="search_services",
            arguments={"query": "Laser Rejuvenation"},
        )
        laser_services = laser.get("services", [])
        if len(laser_services) != 1 or laser_services[0]["name"] != "Laser Rejuvenation":
            raise RuntimeError(f"Laser lookup is not precise: {laser_services!r}")

        print("SPRINT2_SERVICE_SEARCH_OK")
        print("glow_sources =", [row["source_ref"] for row in services])
        print("laser_sources =", [row["source_ref"] for row in laser_services])


if __name__ == "__main__":
    asyncio.run(main())
