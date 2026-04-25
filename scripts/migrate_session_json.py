import sqlite3
import json
import os

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/database.db')
JSON_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'word_chain_data/leaderboard.json')

def migrate_session_json_to_db():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: {JSON_FILE_PATH} not found.")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Find active game channel
    cursor.execute("SELECT channel_id FROM wordchain_games WHERE is_active=1 LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("Error: No active game found. Please start a game first using !wordchain start")
        conn.close()
        return
        
    target_channel_id = result[0]
    print(f"Found active game in channel: {target_channel_id}")

    print(f"Loading data from {JSON_FILE_PATH}...")
    with open(JSON_FILE_PATH, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON.")
            conn.close()
            return

    if not data:
        print("No data found in JSON.")
        conn.close()
        return

    print(f"Found {len(data)} entries. Migrating to session scores...")
    
    count = 0
    for username, score in data.items():
        try:
            # We store the username in the user_id column temporarily
            # The on_message event will handle the claim process
            cursor.execute(
                "INSERT OR REPLACE INTO wordchain_session_scores(channel_id, user_id, score) VALUES (?, ?, ?)",
                (target_channel_id, username, score)
            )
            count += 1
        except Exception as e:
            print(f"Failed to migrate {username}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully migrated {count} session scores to the database!")
    print("Users can now claim their session scores by sending a message in the WordChain channel.")

if __name__ == "__main__":
    migrate_session_json_to_db()
