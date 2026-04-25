# Xeno Discord Bot

Xeno is a feature-rich, high-performance Discord Bot built with `discord.py`. Originally conceptualized around interactive chat games, Xeno manages servers, acts as a utility, and hosts an engaging implementation of the **Word Chain** minigame.

## 🌟 Features

### 🏆 The Word Chain Game
Xeno's flagship feature is an active dictionary-validated Word Chain game!
- **Channel Isolation:** Play multiple game sessions simultaneously in different channels.
- **Intelligent Validation:** Protects against duplicate words, checks string validity, and makes sure terms exist in the loaded dictionary lexicon.
- **Point System:** Earn standard points, or get double points for starting and ending a word with the same letter! Points scale up every 1,000 words.
- **The "Y-Rule" Defense:** English suffers from 'Y-Trapping'. Xeno tracks 'Y' endings and automatically scrambles the starting letter to keep the game alive after 500 triggers.
- **In-Game Dictionary:** Players can append `.m` to any guess (e.g. `apple.m`) to safely parse and display actual definitions from an external dictionary API.
- **Leaderboards:** Fully tracked, paginated leaderboards to compare `.lb` (Session), `.slb` (Server), and `.glb` (Global) ranks!

### 🛡️ Moderation & Utilities
Beyond the minigame, Xeno handles standard guild functionality perfectly thanks to modular implementation:
- Full Cog-based architecture (`general`, `moderation`, `regex`, etc.).
- Robust error handling and permissions checks.
- Synchronized hybrid interactions (slash commands and prefix).

---

## 🚀 Setup & Installation

To run Xeno locally, you'll need Python 3.10+ installed.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sandeshk8/Xeno2.git
   cd Xeno2
   ```

2. **Configure your environment:**
   Create a `config.json` file in the root directory (make sure it's in your `.gitignore` to protect your token) modeled after standard configuration:
   ```json
   {
     "prefix": "!",
     "token": "YOUR_BOT_TOKEN_HERE",
     "permissions": "8",
     "application_id": "YOUR_APP_ID",
     "owners": [123456789],
     "sync_commands_globally": true
   }
   ```

3. **Set up Virtual Environment & Dependencies:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/MacOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

4. **Boot the Bot:**
   ```bash
   python bot.py
   ```
   *Note: Upon boot, the script will automatically invoke `check_schema.py` and seed standard SQL into `database.db` via `aiosqlite`.*

---

## 🛠️ Project Architecture 

- **`/cogs/`**: All command features (WordChain, General, Moderation) split into modular files.
- **`/database/`**: Contains `schema.sql` for table references and the local sqlite database `database.db`.
- **`/scripts/`**: Utility scripts for database schemas, JSON-to-SQL logic migrations, and project zipping operations.
- **`/word_chain_data/`**: Fallback JSON backups of ranks, and custom text file lexicons used to validate words.
- **`/docs/`**: Deep dive technical documentation, including logic explanations of the WordChain system.

## 🤝 Acknowledgements 
- Dictionary parsing powered by [Free Dictionary API](https://dictionaryapi.dev/).
- Built using the `discord.py` structure.
