import discord
from discord import app_commands
import os
import io

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))
CATEGORY_ID = int(os.getenv("CATEGORY_ID", "0"))
LOG_ID = int(os.getenv("LOG_ID", "0"))

WINDOWRA_LOGO = "https://i.imgur.com/6X4QX5n.png"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        messages = [msg async for msg in interaction.channel.history(limit=200, oldest_first=True)]
        transcript = f"Transcript for {interaction.channel.name}\n\n"
        for m in messages:
            transcript += f"[{m.created_at.strftime('%H:%M')}] {m.author.display_name}: {m.content}\n"

        log_channel = interaction.guild.get_channel(LOG_ID)
        if log_channel:
            embed = discord.Embed(title="Ticket Closed", description=f"**{interaction.channel.name}** closed by {interaction.user.mention}", color=0xff0000)
            embed.set_thumbnail(url=WINDOWRA_LOGO)
            file = discord.File(fp=io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.txt")
            await log_channel.send(embed=embed, file=file)

        await interaction.response.send_message("Closing...")
        await interaction.channel.delete()

    @discord.ui.button(label="📢 Claim", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("Staff only", ephemeral=True)
        embed = discord.Embed(description=f"✅ Claimed by {interaction.user.mention}", color=0x00ff00)
        await interaction.response.send_message(embed=embed)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🎮", value="General Support"),
            discord.SelectOption(label="Bug Report", emoji="🐛", value="Bug Report"),
            discord.SelectOption(label="User Reports", emoji="🚨", value="User Reports"),
            discord.SelectOption(label="Staff Application", emoji="💼", value="Staff Application"),
        ]
        super().__init__(placeholder="Choose a reason...", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True) # <-- GIVE BOT PERMS
        }

        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)

        embed = discord.Embed(title=f"{self.values[0]} Ticket", description=f"Hey {interaction.user.mention}, staff will help you shortly.", color=0x5865F2)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=WINDOWRA_LOGO)

        # Don't ping with <@&> — just mention in embed to avoid 403
        await channel.send(content=f"{staff_role.mention} {interaction.user.mention}", embed=embed, view=CloseView(), allowed_mentions=discord.AllowedMentions(roles=True, users=True))
        await interaction.response.send_message(f"✅ {channel.mention}", ephemeral=True)
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        embed = discord.Embed(title=f"{self.values[0]} Ticket", description=f"Hey {interaction.user.mention}, staff will help you shortly.", color=0x5865F2)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url=WINDOWRA_LOGO)
        await channel.send(content=f"<@&{STAFF_ROLE_ID}>", embed=embed, view=CloseView())
        await interaction.response.send_message(f"✅ {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    print("Windowra Ticket Bot online - commands synced")
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
    except: pass

@tree.command(name="panel", description="Post ticket panel", guild=discord.Object(id=GUILD_ID))
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 Windowra Support Center", description="Select below to open a ticket\n🎮 General Support\n🐛 Bug Report\n🚨 User Reports\n💼 Staff Application", color=0x2b2d31)
    embed.set_thumbnail(url=WINDOWRA_LOGO)
    embed.set_footer(text="Windowra • 24/7 Support", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Panel posted", ephemeral=True)

bot.run(TOKEN)
