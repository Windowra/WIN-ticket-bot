import discord
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

GUILD_ID = int(os.getenv("GUILD_ID"))
CATEGORY = int(os.getenv("TICKET_CATEGORY_ID"))
STAFF = int(os.getenv("STAFF_ROLE_ID"))
LOG = int(os.getenv("TICKET_LOG_ID"))

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🎮", description="Get help with the server"),
            discord.SelectOption(label="Bug Report", emoji="🐛", description="Report a bug or glitch"),
            discord.SelectOption(label="User Reports", emoji="🚨", description="Report a rule-breaking user"),
            discord.SelectOption(label="Staff Application", emoji="💼", description="Apply for staff")
        ]
        super().__init__(placeholder="Choose a ticket type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = bot.get_guild(GUILD_ID)
        for ch in guild.text_channels:
            if ch.name == f"ticket-{interaction.user.name.lower()}":
                return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.get_role(STAFF): discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=guild.get_channel(CATEGORY),
            overwrites=overwrites
        )

        embed = discord.Embed(title=f"{self.values[0]} Ticket", color=0x2b2d31)
        embed.description = f"Hello {interaction.user.mention}, staff will be with you shortly."

        if self.values[0] == "User Reports":
            embed.add_field(name="Please provide", value="• Username\n• User ID\n• Reason\n• Screenshots/Proof", inline=False)

        await channel.send(f"<@&{STAFF}>", embed=embed, view=CloseView())
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        log = bot.get_guild(GUILD_ID).get_channel(LOG)
        await log.send(f"Ticket {interaction.channel.name} closed by {interaction.user}")
        await interaction.channel.delete()

@bot.event
async def on_ready():
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Windowra Ticket Bot online - commands synced")
    except Exception as e:
        print(f"Sync failed (bot will still work): {e}")
        print("Windowra Ticket Bot online")

@tree.command(name="panel", description="Post ticket panel", guild=discord.Object(id=GUILD_ID))
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="Windowra Support", description="Select a reason below to open a ticket", color=0x5865F2)
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Panel posted", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
