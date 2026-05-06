import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
import aiosqlite
import os
from datetime import datetime, timedelta, timezone

from helpers import checks

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/f1_data.db"

class F1Reminders(commands.Cog, name="f1_reminders"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.logger.info(f"DEBUG F1: Using database at {DATABASE_PATH}")
        self.f1_reminder_task.start()

    def cog_unload(self):
        self.f1_reminder_task.cancel()

    @tasks.loop()
    async def f1_reminder_task(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("DEBUG F1: f1_reminder_task loop iteration started!")
        try:
            now_unix = int(datetime.now(timezone.utc).timestamp())
            next_race = None

            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM f1_races WHERE race_time > ? AND is_reminded = 0 ORDER BY race_time ASC LIMIT 1", (now_unix,)) as cursor:
                    next_race = await cursor.fetchone()

            if next_race:
                self.bot.logger.info(f"DEBUG F1: Found next race: {next_race['race_id']} at {next_race['race_time']}")
                race_time = datetime.fromtimestamp(next_race['race_time'], tz=timezone.utc)
                reminder_time = race_time - timedelta(hours=1)
                now = datetime.now(timezone.utc)
                
                # Dynamic fetch: Every 24h on Fri/Sat/Sun, otherwise sleep until Friday
                if reminder_time > now:
                    time_until = (reminder_time - now).total_seconds()
                    current_weekday = now.weekday() # 0=Mon, 4=Fri, 5=Sat, 6=Sun
                    
                    if current_weekday in (4, 5, 6):
                        max_sleep_seconds = 86400 # 24 hours
                    else:
                        days_until_friday = 4 - current_weekday
                        max_sleep_seconds = days_until_friday * 86400
                        
                    if time_until > max_sleep_seconds:
                        await discord.utils.sleep_until(now + timedelta(seconds=max_sleep_seconds))
                        return  # Loop again
                    else:
                        await discord.utils.sleep_until(reminder_time)
                    
                now = datetime.now(timezone.utc)
                # After waking up (or if reminder time is slightly past but race hasn't started)
                if now < race_time:
                    await self.send_reminder(next_race)
                    async with aiosqlite.connect(DATABASE_PATH) as db:
                        await db.execute("UPDATE f1_races SET is_reminded = 1 WHERE race_id = ?", (next_race['race_id'],))
                        await db.commit()
                
                # Wait until the race actually starts before looping again
                now = datetime.now(timezone.utc)
                if now < race_time:
                    await discord.utils.sleep_until(race_time)
            else:
                # No upcoming races found.
                # Sleep for 5 minutes and retry.
                now = datetime.now(timezone.utc)
                await discord.utils.sleep_until(now + timedelta(minutes=5))
                
        except Exception as e:
            self.bot.logger.error(f"F1 Reminder Task Error: {e}")
            await discord.utils.sleep_until(datetime.now(timezone.utc) + timedelta(minutes=15))

    async def send_reminder(self, race):
        # Hardcoded for testing
        channel_id = 1214174806765731891
        role_id = 1500777392954806383
        
        channel = self.bot.get_channel(channel_id)
        if channel:
            role_ping = f"<@&{role_id}>"
            race_name = race['race_name']
            circuit_name = race['circuit_name']
            race_time_unix = race['race_time']
            
            embed = discord.Embed(
                title=f"🏎️ {race_name} is starting soon!",
                description=f"The race will begin in less than an hour! (<t:{race_time_unix}:R>)\n\n**Circuit:** {circuit_name}",
                color=0xFF1801
            )
            embed.set_footer(text="F1 Reminders")
            await channel.send(content=f"{role_ping} The race is about to start!", embed=embed)
            self.bot.logger.info(f"F1 Reminder sent for {race_name}")
        else:
            self.bot.logger.info(f"DEBUG F1: channel {channel_id} not found by get_channel!")

    @commands.hybrid_group(name="f1", description="Commands for F1 reminders and content.")
    async def f1(self, context: Context):
        """
        Base command for F1.
        """
        if context.invoked_subcommand is None:
            await context.send("Invalid F1 command passed. Use the proper subcommands.")

    @f1.command(name="next", description="Get the next F1 race information.")
    async def f1_next(self, context: Context):
        """
        Get the next F1 race information.
        """
        try:
            now_unix = int(datetime.now(timezone.utc).timestamp())
            next_race = None
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM f1_races WHERE race_time > ? ORDER BY race_time ASC LIMIT 1", (now_unix,)) as cursor:
                    next_race = await cursor.fetchone()
            
            if next_race:
                race_time_unix = next_race['race_time']
                circuit_name = next_race['circuit_name']
                embed = discord.Embed(
                    title=f"🏎️ Next F1 Race: {next_race['race_name']}",
                    description=f"**Circuit:** {circuit_name}\n**Date & Time:** <t:{race_time_unix}:F> (<t:{race_time_unix}:R>)",
                    color=0xFF1801
                )
                await context.send(embed=embed)
            else:
                await context.send("Could not find any upcoming F1 races in the current season.")
        except Exception as e:
            self.bot.logger.error(f"F1 next command error: {e}")
            await context.send("An error occurred while fetching the next F1 race.")

async def setup(bot):
    await bot.add_cog(F1Reminders(bot))
