from discord.ext import commands
import discord
import random
import aiohttp
import os
import json
from helpers import db_manager

# Load dictionary of words
# We'll try to find the file in the word_chain_data directory
FOLDER_NAME = 'word_chain_data/'
WORD_FILE = FOLDER_NAME + "words_alpha_3plus.txt"

if not os.path.exists(WORD_FILE):
    # Fallback or error if file not found, but for now assuming it exists as per previous code
    WORDS = set()
    print(f"Warning: {WORD_FILE} not found.")
else:
    with open(WORD_FILE, "r") as f:
        WORDS = set(line.strip() for line in f)

class WordChain(commands.Cog, name="wordchain"):
    def __init__(self, bot):
        self.bot = bot

    async def word_meaning(self, word):
        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    result_text = f"📖 **Definitions for '{word}':**\n"
                    
                    found_any = False
                    # Limit to first 3 meanings to avoid spam
                    for meaning in data[0]["meanings"][:3]:
                        part_of_speech = meaning["partOfSpeech"]
                        definition = meaning["definitions"][0]["definition"]
                        result_text += f"• **{part_of_speech}**: {definition}\n"
                        found_any = True
                    
                    if found_any:
                        return result_text
                    else:
                        return f"No definitions found for '{word}'"
                else:
                    return f"Could not find a definition for '{word}'"

    async def get_new_user_embed(self, base_score):
        embed = discord.Embed(
            title="👋 Welcome to XENO Word Chain V3!", 
            description="Join the fun and climb the leaderboard! Read the pinned rules to get started.", 
            color=0x00BFFF # Deep Sky Blue
        )
        embed.add_field(
            name="📜 Scoring System", 
            value=f"• **Base Point**: {base_score}\n• **Double Points**: If word starts & ends with same letter.\n• **Base Score Increases**: Every 1000 words.",
            inline=False
        )
        embed.add_field(
            name="🤖 Commands",
            value="• `.lb` - Session Leaderboard\n• `.slb` - Server Leaderboard\n• `.glb` - Global Leaderboard\n• `.bs` - Check Base Score\n• `.ms` - Check My Score",
            inline=False
        )
        embed.add_field(
            name="🔤 The 'Y' Rule", 
            value="The letter 'Y' is tricky! After 500 'Y' endings, the starting letter changes.", 
            inline=False
        )
        embed.add_field(
            name="📖 Word Meanings", 
            value="Type `.m` after a word to see its definition.\nExample: `harbinger.m`", 
            inline=False
        )
        embed.set_footer(text="Check threads or pins for updates!")
        return embed

    @commands.hybrid_group(name="wordchain", description="WordChain game commands.")
    async def wordchain(self, ctx: commands.Context):
        """WordChain game commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @wordchain.command(name='start', description="Start a new wordchain game session (Resets current session!)")
    @commands.has_permissions(administrator=True)
    async def start_game(self, ctx):
        letters = 'abcfhijmopquvwz'
        start_word = random.choice(letters)
        await db_manager.create_wordchain_game(ctx.channel.id, ctx.guild.id, start_word)
        await ctx.send(f"🆕 **New WordChain Session Started!**\nPrevious session data has been reset.\nThe starting letter is **{start_word}**.")

    @wordchain.command(name='stop', description="Stop the current wordchain game session")
    @commands.has_permissions(administrator=True)
    async def stop_game(self, ctx):
        await db_manager.stop_wordchain_game(ctx.channel.id)
        await ctx.send("🛑 **WordChain Session Stopped!**\nThanks for playing!")

    async def _show_leaderboard(self, ctx, title="Server Leaderboard"):
        leaderboard = await db_manager.get_wordchain_leaderboard(ctx.guild.id)
        view = LeaderboardView(ctx, leaderboard, title, self.get_leaderboard_embed)
        await ctx.send(embed=await view.get_embed(), view=view)

    @commands.hybrid_command(name="lb", description="Check the current session leaderboard")
    async def leaderboard(self, ctx):
        if not await db_manager.get_wordchain_game(ctx.channel.id):
            return
        leaderboard = await db_manager.get_session_leaderboard(ctx.channel.id)

        if not leaderboard:
            await ctx.send("No leaderboard data found for this session yet.")
            return

        view = LeaderboardView(ctx, leaderboard, "Session Leaderboard", self.get_leaderboard_embed)
        await ctx.send(embed=await view.get_embed(), view=view)

    @commands.hybrid_command(name="slb", description="Check the server leaderboard")
    async def server_leaderboard(self, ctx):
        if not await db_manager.get_wordchain_game(ctx.channel.id):
            return
        leaderboard = await db_manager.get_wordchain_leaderboard(ctx.guild.id)

        if not leaderboard:
            await ctx.send("No leaderboard data found for this server yet.")
            return

        view = LeaderboardView(ctx, leaderboard, "Server Leaderboard", self.get_leaderboard_embed)
        await ctx.send(embed=await view.get_embed(), view=view)

    @commands.hybrid_command(name='glb', description="Check word chain global leaderboard")
    async def glb(self, ctx):
        if not await db_manager.get_wordchain_game(ctx.channel.id):
            return
        leaderboard = await db_manager.get_wordchain_global_leaderboard()
        view = LeaderboardView(ctx, leaderboard, "Global Leaderboard", self.get_leaderboard_embed)
        await ctx.send(embed=await view.get_embed(), view=view)
    
    async def get_leaderboard_embed(self, ctx, leaderboard_data, title, page=1, items_per_page=5):
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        current_page_data = leaderboard_data[start_idx:end_idx]
        
        embed = discord.Embed(title=title, description="🏆 **XENO Word Chain Leaderboard**", color=0xFFD700) # Gold color
        
        if not current_page_data:
            embed.description += "\n\nNo data available."
            return embed

        description_text = ""

        for i, (user_id, score) in enumerate(current_page_data):
            rank = start_idx + i + 1
            medal = ""
            if rank == 1: medal = "🥇"
            elif rank == 2: medal = "🥈"
            elif rank == 3: medal = "🥉"
            else: medal = f"#{rank}"
            
            # Resolve username
            try:
                user_id_int = int(user_id)
                member = ctx.guild.get_member(user_id_int)
                if member:
                    username = member.display_name
                else:
                    user = ctx.bot.get_user(user_id_int)
                    if user:
                        username = user.name
                    else:
                        try:
                            user = await ctx.bot.fetch_user(user_id_int)
                            username = user.name
                        except (discord.NotFound, discord.HTTPException):
                            username = f"User {user_id}"
            except ValueError:
                # Legacy data where user_id is the username
                username = f"{user_id} (Legacy)"

            description_text += f"{medal} - **{username}**\n{score}\n\n"

        embed.description += f"\n\n{description_text}"

        total_pages = (len(leaderboard_data) + items_per_page - 1) // items_per_page
        embed.set_footer(text=f"Page {page}/{total_pages} • Total Players: {len(leaderboard_data)}")
        return embed

    @commands.hybrid_command(name='ms', description="Check your score in word chain")
    async def ms(self, ctx):
        await self.my_score(ctx)

    @wordchain.command(name='score', aliases=['ms'], description="Check your score in word chain")
    async def my_score(self, ctx):
        if not await db_manager.get_wordchain_game(ctx.channel.id):
            return
        # Fetch stats
        session_rank, session_total, session_score = await db_manager.get_session_rank(ctx.channel.id, ctx.author.id)
        server_rank, server_total, server_score = await db_manager.get_user_rank(ctx.author.id, ctx.guild.id)
        global_rank, global_total, global_score = await db_manager.get_user_global_rank(ctx.author.id)

        embed = discord.Embed(
            title=f"📊 WordChain Stats: {ctx.author.display_name}",
            color=0x00BFFF # Deep Sky Blue
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # Session Stats
        sess_rank_str = f"#{session_rank}" if session_rank else "Unranked"
        embed.add_field(
            name="🎲 Current Session",
            value=f"**Score**: {session_score}\n**Rank**: {sess_rank_str} / {session_total}",
            inline=False
        )

        # Server Stats
        s_rank_str = f"#{server_rank}" if server_rank else "Unranked"
        embed.add_field(
            name="🏰 Server Stats",
            value=f"**Score**: {server_score}\n**Rank**: {s_rank_str} / {server_total}",
            inline=True
        )

        # Global Stats
        g_rank_str = f"#{global_rank}" if global_rank else "Unranked"
        embed.add_field(
            name="🌍 Global Stats",
            value=f"**Score**: {global_score}\n**Rank**: {g_rank_str} / {global_total}",
            inline=True
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='basescore', aliases=['bs'], description="Check base score")
    async def base_score(self, ctx):
        game = await db_manager.get_wordchain_game(ctx.channel.id)
        if not game:
            await ctx.send("No active game in this channel.")
            return
        
        base_score = game[6]
        created_at = game[9]
            
        try:
            # Format: YYYY-MM-DD HH:MM:SS
            date_part = str(created_at).split(' ')[0]
            year, month, day = date_part.split('-')
            formatted_date = f"{day}/{month}/{year}"
        except:
            formatted_date = "Unknown"
        
        await ctx.send(f"**Base Score**: {base_score} (Increases every 1000 words)\n**Session Started**: {formatted_date}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        # Check if there is an active game in this channel
        game = await db_manager.get_wordchain_game(message.channel.id)
        if not game:
            return
            

        _, _, current_word_db, current_user_id_db, last_user_id_db, word_count, base_score, y_count, is_active, _ = game

        if not is_active:
             return

        content = message.content.lower().strip()
        meaning_flag = False
        if content.endswith('.m'):
            meaning_flag = True
            content = content[:-2]

        # Ignore invalid inputs
        if any(x in content for x in [' ', ':','.']):
            return

        if meaning_flag:
            meaning = await self.word_meaning(content)
            await message.channel.send(meaning)
            return

        # Check if it's the user's turn (prevent double posting)
        if str(message.author.id) == current_user_id_db:
            await message.channel.send("It's not your turn.")
            return

        # Check if the word starts with the correct letter
        required_letter = current_word_db
        if not content.startswith(required_letter):
            await message.channel.send(f"Apologies, the designated term lacks initiation with '{required_letter}'. Please try again.")
            return

        # Check if the word is valid and hasn't been used before
        if len(content) < 3:
            await message.channel.send("Word must exceed a three-letter threshold for consideration.")
        elif await db_manager.is_word_used(message.channel.id, content):
            await message.channel.send("Wait.. but the chosen term has already embedded itself in our lexicon... try again?")
        elif content not in WORDS:
            await message.channel.send(f"Within my lexicon's confines, the term '{content}' remains conspicuously absent.")
        else:
            # Add score
            # Check if user is new to the session before updating score
            current_session_score = await db_manager.get_session_score(message.channel.id, message.author.id)
            is_new_user = current_session_score == 0

            points = base_score * 2 if content[0] == content[-1] else base_score
            await db_manager.update_wordchain_score(message.author.id, message.guild.id, points)
            await db_manager.update_session_score(message.channel.id, message.author.id, points)
            
            if is_new_user:
                embed = await self.get_new_user_embed(base_score)
                await message.channel.send(embed=embed)

            # Update game state
            await db_manager.add_used_word(message.channel.id, content)
            
            new_last_user_id = message.author.id
            new_current_word = content[-1]
            new_word_count = word_count + 1
            new_y_count = y_count + 1 if content[-1] == 'y' else y_count
            new_base_score = base_score
            
            if new_word_count % 1000 == 0:
                new_base_score += 1

            await db_manager.update_wordchain_game(
                message.channel.id,
                new_current_word,
                str(new_last_user_id), # This argument name in update_wordchain_game is current_user_id
                str(last_user_id_db) if last_user_id_db else None, # This is last_user_id (previous)
                new_word_count,
                new_base_score,
                new_y_count
            )

            await message.add_reaction('✅')
            
            if meaning_flag:
                meaning = await self.word_meaning(content)
                await message.channel.send(meaning)
                
            if content[-1] == 'y' and new_y_count > 500:
                 # Reset letter logic
                 letters = 'abcfhijmopquvwz'
                 new_start_letter = random.choice(letters)
                 # We need to update the current_word to this new letter
                 # We can reuse update_wordchain_game
                 await db_manager.update_wordchain_game(
                    message.channel.id,
                    new_start_letter,
                    str(new_last_user_id),
                    str(last_user_id_db) if last_user_id_db else None,
                    new_word_count,
                    new_base_score,
                    new_y_count
                )
                 await message.channel.send(f"Y count reached limit! New starting letter is '{new_start_letter}'")


class LeaderboardView(discord.ui.View):
    def __init__(self, ctx, data, title, embed_factory):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.data = data
        self.title = title
        self.embed_factory = embed_factory
        self.page = 1
        self.items_per_page = 5
        self.total_pages = (len(data) + self.items_per_page - 1) // self.items_per_page

    async def get_embed(self):
        return await self.embed_factory(self.ctx, self.data, self.title, self.page, self.items_per_page)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            try:
                await interaction.response.edit_message(embed=await self.get_embed(), view=self)
            except discord.NotFound:
                await interaction.followup.send("This leaderboard message has expired or was deleted.", ephemeral=True)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            try:
                await interaction.response.edit_message(embed=await self.get_embed(), view=self)
            except discord.NotFound:
                await interaction.followup.send("This leaderboard message has expired or was deleted.", ephemeral=True)
        else:
            await interaction.response.defer()

async def setup(bot):
    await bot.add_cog(WordChain(bot))
