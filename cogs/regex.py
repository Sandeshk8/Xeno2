import re
from discord.ext import commands

class Regex(commands.Cog, name="regex", description=""):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='s', description="Modify a message with regex substitution")
    async def modify_message(self, ctx, pattern: str, replacement: str, flag: str = ''):
        # Check if the pattern allows zero repetitions
        if re.search(r'\*\??|\{\s*0\s*,', pattern):
            await ctx.send("Warning: Your pattern contains a quantifier that can match zero characters, which might lead to unintended results.")

        # Get the message being replied to
        if ctx.message.reference:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if referenced_message:
                # Perform global substitution if 'g' is passed, otherwise local substitution
                new_content, count = re.subn(pattern, replacement, referenced_message.content, count=0 if flag == 'g' else 1)
                
                if count > 0:
                    await referenced_message.reply(new_content)
                else:
                    await ctx.send(f"No matches found for pattern `{pattern}` in the referenced message.")
                
                await ctx.message.delete()
        else:
            await ctx.send("Please reply to the message you want to modify.")
            await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Regex(bot))
