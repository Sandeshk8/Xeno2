import aiosqlite
import asyncio
import os

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/database/database.db"

async def check_schema():
    print(f"Checking database at {DATABASE_PATH}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("PRAGMA table_info(wordchain_games)") as cursor:
            columns = await cursor.fetchall()
            print("Columns in wordchain_games:")
            for col in columns:
                print(col)

if __name__ == "__main__":
    asyncio.run(check_schema())
