""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.5.0
"""

import os

import aiosqlite

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"


async def get_blacklisted_users() -> list:
    """
    This function will return the list of all blacklisted users.

    :param user_id: The ID of the user that should be checked.
    :return: True if the user is blacklisted, False if not.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchall()
            return result


async def is_blacklisted(user_id: int) -> bool:
    """
    This function will check if a user is blacklisted.

    :param user_id: The ID of the user that should be checked.
    :return: True if the user is blacklisted, False if not.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM blacklist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None


async def add_user_to_blacklist(user_id: int) -> int:
    """
    This function will add a user based on its ID in the blacklist.

    :param user_id: The ID of the user that should be added into the blacklist.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO blacklist(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def remove_user_from_blacklist(user_id: int) -> int:
    """
    This function will remove a user based on its ID from the blacklist.

    :param user_id: The ID of the user that should be removed from the blacklist.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def add_warn(user_id: int, server_id: int, moderator_id: int, reason: str) -> int:
    """
    This function will add a warn to the database.

    :param user_id: The ID of the user that should be warned.
    :param reason: The reason why the user should be warned.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await db.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await db.commit()
            return warn_id


async def remove_warn(warn_id: int, user_id: int, server_id: int) -> int:
    """
    This function will remove a warn from the database.

    :param warn_id: The ID of the warn.
    :param user_id: The ID of the user that was warned.
    :param server_id: The ID of the server where the user has been warned
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await db.commit()
        rows = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def get_warnings(user_id: int, server_id: int) -> list:
    """
    This function will get all the warnings of a user.

    :param user_id: The ID of the user that should be checked.
    :param server_id: The ID of the server that should be checked.
    :return: A list of all the warnings of the user.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list


async def get_wordchain_game(channel_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM wordchain_games WHERE channel_id=?", (channel_id,)
        ) as cursor:
            return await cursor.fetchone()


async def create_wordchain_game(channel_id: int, guild_id: int, start_word: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Reset game state and set is_active=1
        await db.execute(
            "INSERT OR REPLACE INTO wordchain_games(channel_id, guild_id, current_word, is_active) VALUES (?, ?, ?, 1)",
            (channel_id, guild_id, start_word),
        )
        # Clear used words for this channel (New Session)
        await db.execute("DELETE FROM wordchain_used_words WHERE channel_id=?", (channel_id,))
        # Clear session scores for this channel (New Session)
        await db.execute("DELETE FROM wordchain_session_scores WHERE channel_id=?", (channel_id,))
        await db.commit()

async def stop_wordchain_game(channel_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE wordchain_games SET is_active=0 WHERE channel_id=?",
            (channel_id,),
        )
        await db.commit()


async def update_wordchain_game(
    channel_id: int,
    current_word: str,
    current_user_id: int,
    last_user_id: int,
    word_count: int,
    base_score: int,
    y_count: int,
):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE wordchain_games SET current_word=?, current_user_id=?, last_user_id=?, word_count=?, base_score=?, y_count=? WHERE channel_id=?",
            (
                current_word,
                current_user_id,
                last_user_id,
                word_count,
                base_score,
                y_count,
                channel_id,
            ),
        )
        await db.commit()


async def add_used_word(channel_id: int, word: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO wordchain_used_words(channel_id, word) VALUES (?, ?)",
            (channel_id, word),
        )
        await db.commit()


async def is_word_used(channel_id: int, word: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM wordchain_used_words WHERE channel_id=? AND word=?",
            (channel_id, word),
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None


async def get_wordchain_score(user_id: int, guild_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT score FROM wordchain_scores WHERE user_id=? AND guild_id=?",
            (user_id, guild_id),
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def update_wordchain_score(user_id: int, guild_id: int, points: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO wordchain_scores(user_id, guild_id, score) VALUES (?, ?, ?) ON CONFLICT(user_id, guild_id) DO UPDATE SET score = score + ?",
            (user_id, guild_id, points, points),
        )
        await db.commit()

async def update_session_score(channel_id: int, user_id: int, points: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO wordchain_session_scores(channel_id, user_id, score) VALUES (?, ?, ?) ON CONFLICT(channel_id, user_id) DO UPDATE SET score = score + ?",
            (channel_id, user_id, points, points),
        )
        await db.commit()

async def get_session_score(channel_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT score FROM wordchain_session_scores WHERE channel_id=? AND user_id=?",
            (channel_id, user_id),
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

async def get_session_rank(channel_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, score FROM wordchain_session_scores WHERE channel_id=? ORDER BY score DESC",
            (channel_id,),
        ) as cursor:
            leaderboard = await cursor.fetchall()
            
    total_players = len(leaderboard)
    for rank, (uid, score) in enumerate(leaderboard, 1):
        try:
            if int(uid) == user_id:
                return rank, total_players, score
        except ValueError:
            continue
    return None, total_players, 0


async def get_session_leaderboard(channel_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, score FROM wordchain_session_scores WHERE channel_id=? ORDER BY score DESC",
            (channel_id,),
        ) as cursor:
            return await cursor.fetchall()


async def get_wordchain_leaderboard(guild_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, score FROM wordchain_scores WHERE guild_id=? ORDER BY score DESC",
            (guild_id,),
        ) as cursor:
            return await cursor.fetchall()


async def get_wordchain_global_leaderboard():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, SUM(score) as total_score FROM wordchain_scores GROUP BY user_id ORDER BY total_score DESC"
        ) as cursor:
            return await cursor.fetchall()

async def get_user_rank(user_id: int, guild_id: int):
    leaderboard = await get_wordchain_leaderboard(guild_id)
    total_players = len(leaderboard)
    for rank, (uid, score) in enumerate(leaderboard, 1):
        try:
            if int(uid) == user_id:
                return rank, total_players, score
        except ValueError:
            continue
    return None, total_players, 0

async def get_user_global_rank(user_id: int):
    leaderboard = await get_wordchain_global_leaderboard()
    total_players = len(leaderboard)
    for rank, (uid, total_score) in enumerate(leaderboard, 1):
        try:
            if int(uid) == user_id:
                return rank, total_players, total_score
        except ValueError:
            continue
    return None, total_players, 0

async def get_legacy_score(username: str, guild_id: int) -> int:
    """Check if a username has a score in the database (legacy migration)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT score FROM wordchain_scores WHERE user_id=? AND guild_id=?",
            (username, guild_id),
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def delete_legacy_score(username: str, guild_id: int):
    """Delete a legacy username score entry."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM wordchain_scores WHERE user_id=? AND guild_id=?",
            (username, guild_id),
        )
        await db.commit()

async def get_legacy_session_score(username: str, channel_id: int) -> int:
    """Check if a username has a session score in the database (legacy migration)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT score FROM wordchain_session_scores WHERE user_id=? AND channel_id=?",
            (username, channel_id),
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def delete_legacy_session_score(username: str, channel_id: int):
    """Delete a legacy username session score entry."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM wordchain_session_scores WHERE user_id=? AND channel_id=?",
            (username, channel_id),
        )
        await db.commit()


