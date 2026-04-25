import sqlite3
import json
import os
import time

# Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/database.db')
JSON_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'word_chain_data/used_words.json')
TARGET_CHANNEL_ID = '1103242944670085211'

def migrate_used_words():
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

    if not isinstance(data, list):
        print("Error: JSON data is not a list.")
        return

    print(f"Found {len(data)} words. Migrating to database...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Ensure table exists (just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `wordchain_used_words` (
          `id` INTEGER PRIMARY KEY AUTOINCREMENT,
          `channel_id` varchar(20) NOT NULL,
          `word` varchar(255) NOT NULL,
          `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    count = 0
    for word in data:
        try:
            cursor.execute(
                "INSERT INTO wordchain_used_words(channel_id, word) VALUES (?, ?)",
                (TARGET_CHANNEL_ID, word)
            )
            count += 1
        except Exception as e:
            print(f"Failed to migrate {word}: {e}")

    conn.commit()
    conn.close()
    print(f"Successfully migrated {count} used words to the database for channel {TARGET_CHANNEL_ID}!")

if __name__ == "__main__":
    migrate_used_words()
