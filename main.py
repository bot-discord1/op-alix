import os
import discord
from discord.ext import commands
from discord import app_commands
import math
import re

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Target Channel ID (Default)
TARGET_CHANNEL_ID = 1538901960336609280

def parse_amount(amount_str: str) -> int:
    val_clean = amount_str.lower().strip().replace(',', '')
    if val_clean.endswith('k'):
        return int(float(val_clean[:-1]) * 1_000)
    elif val_clean.endswith('m'):
        return int(float(val_clean[:-1]) * 1_000_000)
    elif val_clean.endswith('b'):
        return int(float(val_clean[:-1]) * 1_000_000_000)
    return int(float(val_clean))

# --- Class dyal Copy Button ---
class CopyView(discord.ui.View):
    def __init__(self, probot_str: str):
        super().__init__(timeout=None)
        self.probot_str = probot_str

    @discord.ui.button(label="Copy ProBot Tax", style=discord.ButtonStyle.primary, emoji="🤖")
    async def copy_probot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"`{self.probot_str}`", ephemeral=True)

def build_tax_embed(user: discord.User, raw_amount: int) -> tuple[discord.Embed, CopyView]:
    probot_amount = math.ceil(raw_amount / 0.95)
    
    orig_str = f"{raw_amount:,}"
    probot_str = f"{probot_amount:,}"

    embed = discord.Embed(color=discord.Color.gold())
    embed.set_author(name="🛒 Tax Calculator")
    embed.set_thumbnail(url=user.display_avatar.url)
    
    embed.add_field(name="", value=f"👤 **Requested by:** {user.mention}", inline=False)
    embed.add_field(name="", value=f"🏛️ **Original Amount** — {orig_str}", inline=False)
    embed.add_field(name="", value=f"➡️ **ProBot Tax (5%)** — {probot_str}", inline=False)
    
    embed.add_field(name="", value="----------------------------------------", inline=False)
    embed.add_field(name="", value="🔄 Use the buttons below to copy the values", inline=False)

    view = CopyView(probot_str)
    return embed, view

# --- Slash Command `/tax` ---
@bot.tree.command(name="tax", description="Calculate ProBot tax (5%)")
@app_commands.describe(amount="The amount of credits (e.g. 30m, 50k, 1000000)")
async def tax(interaction: discord.Interaction, amount: str):
    try:
        raw_amount = parse_amount(amount)
        if raw_amount <= 0:
            await interaction.response.send_message("❌ **Amount must be greater than 0!**", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("❌ **Invalid format!** Enter a valid number or use `30m`, `50k`, etc.", ephemeral=True)
        return

    embed, view = build_tax_embed(interaction.user, raw_amount)
    await interaction.response.send_message(embed=embed, view=view)

# --- Slash Command `/taxchannel` ---
@bot.tree.command(name="taxchannel", description="Set the automatic tax calculator channel")
@app_commands.describe(channel="Select the tax channel")
@app_commands.checks.has_permissions(administrator=True)
async def taxchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    global TARGET_CHANNEL_ID
    TARGET_CHANNEL_ID = channel.id
    await interaction.response.send_message(f"✅ Auto Tax channel set to {channel.mention}!", ephemeral=True)

# --- Auto Tax on Message in Target Channel ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == TARGET_CHANNEL_ID:
        match = re.match(r"^(\d+(\.\d+)?)[kMbM]?$", message.content.strip(), re.IGNORECASE)
        if match:
            try:
                raw_amount = parse_amount(message.content)
                if raw_amount > 0:
                    embed, view = build_tax_embed(message.author, raw_amount)
                    await message.channel.send(embed=embed, view=view)
            except ValueError:
                pass

    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Tax Bot is ready as: {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN is missing!")
    bot.run(DISCORD_TOKEN)
