import os
import aiosqlite

from app.config import settings


async def get_db() -> aiosqlite.Connection:
    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA synchronous = NORMAL")
    await db.execute("PRAGMA busy_timeout = 5000")
    return db


async def init_db() -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA synchronous = NORMAL")
        await db.execute("PRAGMA busy_timeout = 5000")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS redirects (
                key TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def lookup_key(key: str) -> str | None:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT path FROM redirects WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["path"] if row else None


async def upsert_key(key: str, path: str) -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """INSERT INTO redirects (key, path, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET
                   path = excluded.path,
                   updated_at = CURRENT_TIMESTAMP""",
            (key, path),
        )
        await db.commit()


async def delete_key(key: str) -> bool:
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("DELETE FROM redirects WHERE key = ?", (key,))
        await db.commit()
        return cursor.rowcount > 0


async def list_all() -> list[dict[str, str]]:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT key, path, created_at, updated_at FROM redirects ORDER BY key"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
