# WordChain Module Documentation (`cogs/wordchain.py`)

## Overview
The `WordChain` module is a core `discord.py` Cog that implements a continuous word-chaining minigame directly within text channels. In this game, players take turns sending words that begin with the last letter of the previously accepted word. The module handles all gameplay enforcement, scoring computations, pagination for leaderboards, and integrates with a third-party dictionary API to provide word definitions on the fly.

---

## Commands & Interfaces

These commands are prefixed with your bot's configured prefix (or can be invoked as hybrid slash commands if synced).

### Admin Commands (Requires Administrator Permissions)
- **`start`** (`wordchain start`): Initializes a brand new wordchain session in the current channel. Generates a random starting letter and resets any existing session data for that channel.
- **`stop`** (`wordchain stop`): Halts the active wordchain game in the channel, preventing further game messages from being processed.

### Player Commands
- **`lb`**: Displays the interactive **Session Leaderboard** (scores accumulated in the current channel's active game).
- **`slb`**: Displays the interactive **Server Leaderboard** (scores over time within the entire Discord server).
- **`glb`**: Displays the interactive **Global Leaderboard** (highest scores across all servers the bot is in).
- **`score` / `ms`**: Sends an embedded scorecard showing the invoking user's rank and score in the session, server, and globally.
- **`basescore` / `bs`**: Displays the current point value for standard words. The base multiplier increases as more words are chained.

---

## Core Logic

The module's gameplay loop primarily runs via the `on_message` listener.

### Step-by-Step Execution:
1. **Event Trigger**: When a user sends a message, `on_message` fires. Bot messages and invalid inputs containing spaces/punctuation are instantly ignored.
2. **Context Resolution**: The bot calls `db_manager.get_wordchain_game()` to verify if an active game exists in the message's channel. If no game is active, processing terminates.
3. **Data Unpacking**: The database tuple for the game configuration is unpacked (channel ID, required letter, last user, word count, base score multipliers, etc.).
4. **Validation Pipeline**:
    - **Turn Order**: Blocks sequential messages from the same user to prevent solo chaining.
    - **Letter Matching**: Ensures the string starts with the designated required letter.
    - **Length Rule**: Rejects strings under 3 characters.
    - **Duplication Check**: Queries the DB to ensure the word hasn't been used in this session before.
    - **Lexicon Verification**: Checks if the term exists in the memory-loaded dictionary `WORDS` (read from `word_chain_data/words_alpha_3plus.txt`).
5. **Scoring**: Calculates points. A base score is awarded, but is doubled (`* 2`) if the word starts and ends with the identical letter.
6. **State Mutation**:
    - Adds the used word and points to the `db_manager`.
    - Updates the new "required letter" for the next player (the last character of the current word).
    - Increments global/session counters. Base score naturally increments for every 1000 logged words.
7. **Reactions**: Reacts with ✅ to indicate a successful turn.

---

## The "Y" Rule

A unique edge case exists to combat "Y-Trapping" (English has many words ending in 'Y' but very few starting with 'Y').
- The module maintains a `y_count` record. 
- If a user plays a word ending in 'Y', the counter increments.
- Once `y_count` exceeds **500**, the required starting letter is forcefully scrambled and randomly assigned a new consonant or vowel from `abcfhijmopquvwz` to reset the board.

---

## Dictionary Definition Feature
If a user appends `.m` to their word (e.g., `apple.m`), a flag is triggered (`meaning_flag`).
1. The `.m` is sliced off before the word undergoes normal validation.
2. If the word is valid, the bot makes an asynchronous HTTP GET request to `dictionaryapi.dev`.
3. The response JSON is parsed, capturing up to 3 definitions and their parts of speech.
4. An embedded message is dispatched detailing the definition alongside marking their word as correct.

---

## Example Usage

**Starting the game:**
```
User: !wordchain start
Bot: 🆕 New WordChain Session Started!
Previous session data has been reset.
The starting letter is d.
```

**Playing a turn with a definition lookup:**
```
User: dinosaur.m
Bot: [Reacts ✅]
Bot: 📖 Definitions for 'dinosaur':
• noun: A member of the clade Dinosauria...
```

**Invalid turn handling:**
```
User: red
Bot: Apologies, the designated term lacks initiation with 'r'. Please try again.
```

---

## Edge Cases and Error Handling

| Edge Case | How It's Handled |
| :--- | :--- |
| **Missing Lexicon File** | Fails gracefully initialization. `WORDS` defaults to an empty set and logs a console Warning if `words_alpha_3plus.txt` cannot be found. |
| **User Deletion / Missing User Data** | When generating leaderboards, if a user ID can't be fetched (left server or Discord API error), they are displayed as `User {id}` or optionally `Legacy` if working with old name schemas. |
| **Punctuation & Spaces** | Guard clauses intercept strings containing spaces, colons, or periods (besides the `.m` flag prefix) and quietly drop the event processing to prevent database strain. |
| **API Failure in Dictionary** | If `dictionaryapi.dev` is offline or returns `404 Not Found`, the code yields a polite "Could not find a definition" fallback rather than crashing the loop constraint. |

---

## Dependencies & Integrations

1. **`discord.ext.commands` & `discord.ui`**: Uses standard cog architectures for interactions and `discord.ui.View` for the pagination logic powering `LeaderboardView`.
2. **`aiohttp`**: Asynchronous HTTP handling for interacting externally with the `dictionaryapi.dev` API.
3. **`helpers.db_manager`**: Heavily dependent on custom SQLite queries located in the `db_manager` package. It abstracts away all `INSERT` and `SELECT` query strings.
4. **Local Data files**: Expects a local flat text file configured at `word_chain_data/words_alpha_3plus.txt` to act as the primary dictionary for all string validation.
