import aiosqlite
import asyncio
import os

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}/database/database.db"

async def migrate():
    print(f"Migrating database at {DATABASE_PATH}")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if is_active column exists in wordchain_games
        async with db.execute("PRAGMA table_info(wordchain_games)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if "is_active" not in column_names:
                print("Adding is_active column to wordchain_games...")
                try:
                    await db.execute("ALTER TABLE wordchain_games ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
                    print("Added is_active column.")
                except Exception as e:
                    print(f"Error adding column: {e}")
            else:
                print("is_active column already exists.")

        # Create wordchain_session_scores if not exists
        print("Creating wordchain_session_scores table if not exists...")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS `wordchain_session_scores` (
              `channel_id` varchar(20) NOT NULL,
              `user_id` varchar(20) NOT NULL,
              `score` int(11) NOT NULL DEFAULT 0,
              PRIMARY KEY (`channel_id`, `user_id`)
            );
        """)
        
        await db.commit()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
