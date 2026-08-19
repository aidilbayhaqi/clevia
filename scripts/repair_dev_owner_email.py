from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import AsyncSessionLocal


OLD_EMAIL = "owner@clevia.local"
NEW_EMAIL = "owner@clevia.id"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        old_count = await db.scalar(
            text("SELECT COUNT(*) FROM users WHERE lower(email) = lower(:email)"),
            {"email": OLD_EMAIL},
        )
        new_count = await db.scalar(
            text("SELECT COUNT(*) FROM users WHERE lower(email) = lower(:email)"),
            {"email": NEW_EMAIL},
        )

        if new_count and new_count > 0:
            if old_count and old_count > 0:
                raise RuntimeError(
                    "Both old and new owner emails exist. Refusing ambiguous automatic repair."
                )
            print("OWNER_EMAIL_ALREADY_REPAIRED")
            return

        if not old_count:
            raise RuntimeError(
                f"Seed owner {OLD_EMAIL!r} was not found; cannot safely infer which user to modify."
            )

        await db.execute(
            text(
                "UPDATE users "
                "SET email = :new_email, updated_at = now() "
                "WHERE lower(email) = lower(:old_email)"
            ),
            {"new_email": NEW_EMAIL, "old_email": OLD_EMAIL},
        )
        await db.commit()

        print("OWNER_EMAIL_REPAIRED")
        print("email =", NEW_EMAIL)


if __name__ == "__main__":
    asyncio.run(main())
