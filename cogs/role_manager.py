import discord
from datetime import timedelta
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Select, Button
from helpers import role_db_manager

class RoleNotificationView(View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="Keep Role", style=discord.ButtonStyle.green, custom_id="keep_role_button")
    async def keep_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Allows the user to keep or join the role."""
        if self.role in interaction.user.roles:
            await interaction.response.send_message(
                f"✅ You already have the **{self.role.name}** role and will continue to receive notifications.", 
                ephemeral=True
            )
        else:
            try:
                await interaction.user.add_roles(self.role)
                await interaction.response.send_message(
                    f"✅ You've been given the **{self.role.name}** role! You will now receive notifications for it.", 
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ I don't have permission to give you this role. Please check my role hierarchy.", 
                    ephemeral=True
                )

    @discord.ui.button(label="Remove Role", style=discord.ButtonStyle.red, custom_id="remove_role_button")
    async def remove_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Allows the user to remove the role from themselves."""
        if self.role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(self.role)
                await interaction.response.send_message(
                    f"🗑️ Successfully removed the **{self.role.name}** role. You won't be notified again.", 
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ I don't have permission to remove roles from you. Please check my role hierarchy.", 
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"❌ You don't have the **{self.role.name}** role.", 
                ephemeral=True
            )

# --- Confirmation Logic ---

class RoleActionConfirmView(View):
    def __init__(self, role: discord.Role, action: str):
        super().__init__(timeout=60)
        self.role = role
        self.action = action # "whitelist" or "unwhitelist"

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if self.action == "whitelist":
            await role_db_manager.add_role(interaction.guild.id, self.role.id)
            msg = f"✅ **{self.role.name}** added to the whitelist."
        else:
            await role_db_manager.remove_role(interaction.guild.id, self.role.id)
            msg = f"🗑️ **{self.role.name}** removed from the whitelist."
            
        await interaction.response.edit_message(content=msg, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="❌ Action cancelled.", view=None)

# --- Paginated Selection Logic ---

class RolePaginatedSelect(Select):
    def __init__(self, roles: list[discord.Role], page: int, total_pages: int, action: str):
        start = page * 25
        end = start + 25
        current_roles = roles[start:end]
        
        options = [
            discord.SelectOption(label=r.name, value=str(r.id))
            for r in current_roles
        ]
        
        placeholder = f"Select role to {action.capitalize()} (Page {page+1}/{total_pages})"
        super().__init__(placeholder=placeholder, options=options)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ Role not found.", ephemeral=True)

        view = RoleActionConfirmView(role, self.action)
        await interaction.response.edit_message(
            content=f"⚠️ Are you sure you want to **{self.action}** the role **{role.name}**?",
            view=view
        )

class RolePaginatedView(View):
    def __init__(self, roles: list[discord.Role], action: str, page: int = 0):
        super().__init__(timeout=60)
        self.roles = roles
        self.action = action
        self.page = page
        self.total_pages = (len(roles) - 1) // 25 + 1
        
        self.add_item(RolePaginatedSelect(roles, page, self.total_pages, action))
        
        if page > 0:
            back_button = Button(label="⬅️ Back", style=discord.ButtonStyle.gray)
            back_button.callback = self.back_callback
            self.add_item(back_button)
            
        if page < self.total_pages - 1:
            next_button = Button(label="Next ➡️", style=discord.ButtonStyle.gray)
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def back_callback(self, interaction: discord.Interaction):
        view = RolePaginatedView(self.roles, self.action, self.page - 1)
        await interaction.response.edit_message(view=view)

    async def next_callback(self, interaction: discord.Interaction):
        view = RolePaginatedView(self.roles, self.action, self.page + 1)
        await interaction.response.edit_message(view=view)

class RoleManager(commands.Cog, name="role_manager"):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    @tasks.loop(hours=1)
    async def cleanup_task(self):
        """Automatically cleans up old logs every hour."""
        await role_db_manager.cleanup_old_logs()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens for role mentions and handles notifications & anti-spam."""
        if message.author.bot or not message.guild:
            return

        # Check if the feature is enabled for this server
        if not await role_db_manager.is_enabled(message.guild.id):
            return

        if not message.role_mentions:
            return

        # Get whitelisted roles
        whitelisted_ids = await role_db_manager.get_whitelisted_roles(message.guild.id)
        
        # Filter for whitelisted roles mentioned in this message
        mentioned_whitelisted = [r for r in message.role_mentions if r.id in whitelisted_ids]
        if not mentioned_whitelisted:
            return

        # --- Anti-Spam Check ---
        # Administrators are exempt
        if not message.author.guild_permissions.administrator:
            # 1. Check Total Limit (Max 3 across all roles)
            total_mentions = await role_db_manager.get_total_mention_count(message.guild.id, message.author.id)
            if total_mentions >= 3:
                await self.apply_timeout(message, "Total daily role mention limit exceeded (Max 3).")
                return

            # 2. Check Per-Role Limit (Max 1 per specific role)
            for role in mentioned_whitelisted:
                role_mentions = await role_db_manager.get_role_mention_count(message.guild.id, message.author.id, role.id)
                if role_mentions >= 1:
                    await self.apply_timeout(message, f"Daily limit for **{role.name}** exceeded (Max 1).")
                    return

            # Log all mentions from this message
            for role in mentioned_whitelisted:
                await role_db_manager.add_mention_log(message.guild.id, message.author.id, role.id)

        # Proceed with normal notification for the first whitelisted role mentioned
        for role in mentioned_whitelisted:
            view = RoleNotificationView(role)
            await message.reply(
                content=f"🔔 Members of **{role.name}** were tagged.\nDo you want to keep this role for future notifications?",
                view=view,
                allowed_mentions=discord.AllowedMentions.none()
            )
            break

    async def apply_timeout(self, message, reason):
        """Helper to apply timeout and notify user."""
        try:
            duration = timedelta(minutes=10)
            await message.author.timeout(duration, reason=reason)
            await message.reply(
                f"⚠️ {message.author.mention}, you have been timed out for 10 minutes.\n**Reason**: {reason}"
            )
        except discord.Forbidden:
            pass

    @commands.hybrid_group(
        name="rolemanager",
        description="Commands to manage role notification settings.",
    )
    @commands.has_permissions(administrator=True)
    async def rolemanager(self, ctx: commands.Context):
        """Group command for Role Manager settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rolemanager.command(name="toggle", description="Enable or disable the role manager.")
    async def toggle(self, ctx: commands.Context, status: bool):
        """Toggles the feature on/off."""
        await role_db_manager.set_enabled(ctx.guild.id, status)
        state = "enabled" if status else "disabled"
        await ctx.send(f"✅ Role Manager has been **{state}** for this server.")

    @rolemanager.command(name="whitelist", description="Open a menu to add a role to the whitelist.")
    async def whitelist_menu(self, ctx: commands.Context):
        """Opens a paginated menu to whitelist a role."""
        whitelisted_ids = await role_db_manager.get_whitelisted_roles(ctx.guild.id)
        all_roles = [r for r in ctx.guild.roles if r.id != ctx.guild.id and r.id not in whitelisted_ids]
        
        if not all_roles:
            return await ctx.send("❌ No available roles to whitelist.")

        view = RolePaginatedView(all_roles, "whitelist")
        await ctx.send("➕ **Whitelist Manager**\nSelect a role to add to the tracking list:", view=view)

    @rolemanager.command(name="unwhitelist", description="Open a menu to remove roles from the whitelist.")
    async def unwhitelist_menu(self, ctx: commands.Context):
        """Opens a paginated menu to unwhitelist a role."""
        role_ids = await role_db_manager.get_whitelisted_roles(ctx.guild.id)
        if not role_ids:
            return await ctx.send("❌ No roles are currently whitelisted.")
        
        valid_roles = [ctx.guild.get_role(rid) for rid in role_ids if ctx.guild.get_role(rid)]
        if not valid_roles:
            return await ctx.send("❌ No valid whitelisted roles found.")

        view = RolePaginatedView(valid_roles, "unwhitelist")
        await ctx.send("📋 **Unwhitelist Manager**\nSelect a role to remove from the tracking list:", view=view)

    @rolemanager.command(name="list", description="List all whitelisted roles with counts.")
    async def list_roles(self, ctx: commands.Context):
        """Lists all roles that are currently whitelisted with counts."""
        role_ids = await role_db_manager.get_whitelisted_roles(ctx.guild.id)
        
        total_server_roles = len([r for r in ctx.guild.roles if r.id != ctx.guild.id])
        whitelisted_count = 0
        role_names = []

        for rid in role_ids:
            role = ctx.guild.get_role(rid)
            if role:
                role_names.append(f"• **{role.name}**")
                whitelisted_count += 1
            else:
                await role_db_manager.remove_role(ctx.guild.id, rid)

        non_whitelisted_count = total_server_roles - whitelisted_count

        embed = discord.Embed(title="📜 Role Whitelist Summary", color=0x00BFFF)
        embed.add_field(name="✅ Whitelisted", value=str(whitelisted_count), inline=True)
        embed.add_field(name="❌ Non-Whitelisted", value=str(non_whitelisted_count), inline=True)
        
        if role_names:
            embed.description = "**Currently Whitelisted Roles:**\n" + "\n".join(role_names)
        else:
            embed.description = "*No roles are currently whitelisted.*"

        await ctx.send(embed=embed)

async def setup(bot):
    await role_db_manager.init_db()
    await bot.add_cog(RoleManager(bot))
