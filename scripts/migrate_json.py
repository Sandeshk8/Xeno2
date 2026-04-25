import sqlite3
import json
import os

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/database.db')
JSON_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'word_chain_data/global_leaderboard.json')
TARGET_GUILD_ID = '741885505737719819'

def migrate_json_to_db():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return

    print(f"Loading data from {JSON_FILE_PATH}...")
    with open(JSON_FILE_PATH, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON.")
            return

    if not data:
        print("No data found in JSON.")
        return

    print(f"Found {len(data)} entries. Migrating to database...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    count = 0
    for username, score in data.items():
        try:
            # We store the username in the user_id column temporarily
            # The on_message event will handle the claim process
            cursor.execute(
                "INSERT OR REPLACE INTO wordchain_scores(user_id, guild_id, score) VALUES (?, ?, ?)",
                (username, TARGET_GUILD_ID, score)
            )
            count += 1
        except Exception as e:
            print(f"Failed to migrate {username}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully migrated {count} scores to the database!")
    print("Users can now claim their scores by sending a message in the WordChain channel.")

if __name__ == "__main__":
    migrate_json_to_db()
