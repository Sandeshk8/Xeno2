import os
import aiosqlite

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/role_manager.db"

async def init_db():
    """Initializes the role manager database and creates tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS whitelisted_roles (
                guild_id INTEGER,
                role_id INTEGER,
                PRIMARY KEY (guild_id, role_id)
            )
        """)
        await db.commit()

async def is_enabled(guild_id: int) -> bool:
    """Checks if the role manager is enabled for a specific guild."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT enabled FROM guild_settings WHERE guild_id=?", (guild_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] == 1 if result else False

async def set_enabled(guild_id: int, enabled: bool):
    """Enables or disables the role manager for a specific guild."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO guild_settings(guild_id, enabled) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET enabled=?",
            (guild_id, 1 if enabled else 0, 1 if enabled else 0)
        )
        await db.commit()

async def add_role(guild_id: int, role_id: int):
    """Adds a role ID to the whitelist for a guild."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO whitelisted_roles(guild_id, role_id) VALUES (?, ?)", (guild_id, role_id))
        await db.commit()

async def remove_role(guild_id: int, role_id: int):
    """Removes a role ID from the whitelist for a guild."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM whitelisted_roles WHERE guild_id=? AND role_id=?", (guild_id, role_id))
        await db.commit()

async def get_whitelisted_roles(guild_id: int) -> list:
    """Returns a list of whitelisted role IDs for a guild."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT role_id FROM whitelisted_roles WHERE guild_id=?", (guild_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
