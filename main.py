import discord
from discord import app_commands
import os
import io

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", "0"))
CATEGORY_ID = int(os.getenv("CATEGORY_ID", "0"))
LOG_ID = int(os.getenv("LOG_ID", "0"))

WINDOWRA_LOGO = "https://media.discordapp.net/attachments/1496766733057261588/1514867543045705889/ticket_icon_transparent.png?ex=6a2cedd7&is=6a2b9c57&hm=709a6e5ca97fe1aa80f5879a59c77bfa933c58304549a2473bf18ef40ea4fc03&=&format=webp&quality=lossless&width=768&height=768"

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
            embed = discord.Embed(title="Ticket Closed", description=f"Closed by {interaction.user.mention}", color=0xff0000)
            file = discord.File(fp=io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.txt")
            await log_channel.send(embed=embed, file=file)

        await interaction.response.send_message("Closing...")
        await interaction.channel.delete()

    @discord.ui.button(label="📢 Claim", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("Staff only", ephemeral=True)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

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
        await interaction.response.defer(ephemeral=True, thinking=True)

        guild = interaction.guild
        # prevent double tickets
        for ch in guild.text_channels:
            if ch.topic and str(interaction.user.id) in ch.topic:
                return await interaction.followup.send(f"You already have {ch.mention}", ephemeral=True)

        category = guild.get_channel(CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"User ID: {interaction.user.id}"
        )

        embed = discord.Embed(title=f"{self.values[0]} Ticket", description=f"{interaction.user.mention} staff will be with you shortly", color=0x5865F2)
        embed.set_thumbnail(url=WINDOWRA_LOGO)
        await channel.send(f"<@&{STAFF_ROLE_ID}>", embed=embed, view=CloseView(), allowed_mentions=discord.AllowedMentions(roles=True))
        await interaction.followup.send(f"✅ Created {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
    except:
        pass
    print("Windowra Ticket Bot online")

@tree.command(name="panel", description="Post ticket panel", guild=discord.Object(id=GUILD_ID))
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 Windowra Support", description="🎮 General Support\n🐛 Bug Report\n🚨 User Reports\n💼 Staff Application", color=0x2b2d31)
    embed.set_thumbnail(url=WINDOWRA_LOGO)
    embed.set_footer(text="Windowra • 24/7")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Done", ephemeral=True)

bot.run(TOKEN)
