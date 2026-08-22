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

# Target Channel ID (Default: 1538901960336609280)
TARGET_CHANNEL_ID = 1538901960336609280

def parse_amount(amount_str: str) -> int:
    val_clean = amount_str.lower().strip()
    if val_clean.endswith('k'):
        return int(float(val_clean[:-1]) * 1_000)
    elif val_clean.endswith('m'):
        return int(float(val_clean[:-1]) * 1_000_000)
    elif val_clean.endswith('b'):
        return int(float(val_clean[:-1]) * 1_000_000_000)
    return int(val_clean)

def build_tax_embed(user: discord.User, raw_amount: int) -> discord.Embed:
    TAX_RATE = 0.05
    tax_cut = math.ceil(raw_amount * TAX_RATE)
    net_amount = raw_amount - tax_cut
    amount_to_send = math.ceil(raw_amount * (20 / 19))

    embed = discord.Embed(
        title="📊 **ProBot Tax Calculator**",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Requested By", value=user.mention, inline=False)
    embed.add_field(name="💰 Amount", value=f"`{raw_amount:,}`", inline=True)
    embed.add_field(name="🔻 Tax Cut (5%)", value=f"`{tax_cut:,}`", inline=True)
    embed.add_field(name="💵 Net Received", value=f"`{net_amount:,}`", inline=True)
    embed.add_field(name="💳 Amount to Send (Exact)", value=f"`{amount_to_send:,}`", inline=False)
    embed.set_footer(text="ProBot Tax Calculator • 5% Tax Rate")
    return embed

# --- Slash Command `/tax` ---
@bot.tree.command(name="tax", description="Calculate ProBot tax (5%)")
@app_commands.describe(amount="The amount of credits (e.g. 10000, 10k, 1m)")
async def tax(interaction: discord.Interaction, amount: str):
    try:
        raw_amount = parse_amount(amount)
        if raw_amount <= 0:
            await interaction.response.send_message("❌ **Amount must be greater than 0!**", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("❌ **Invalid format!** Enter a valid number or use `10k`, `1m`.", ephemeral=True)
        return

    embed = build_tax_embed(interaction.user, raw_amount)
    await interaction.response.send_message(embed=embed)

# --- Slash Command `/settax` (To change the channel dynamically) ---
@bot.tree.command(name="settax", description="Set the automatic tax calculator channel")
@app_commands.describe(channel="Select the tax channel")
@app_commands.checks.has_permissions(administrator=True)
async def settax(interaction: discord.Interaction, channel: discord.TextChannel):
    global TARGET_CHANNEL_ID
    TARGET_CHANNEL_ID = channel.id
    await interaction.response.send_message(f"✅ Auto Tax channel set to {channel.mention}!", ephemeral=True)

# --- Auto Tax on Message in Target Channel ---
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == TARGET_CHANNEL_ID:
        # Check if the message is a number/amount (e.g., 50k, 100000, 2.5m)
        match = re.match(r"^(\d+(\.\d+)?)[kMbM]?$", message.content.strip(), re.IGNORECASE)
        if match:
            try:
                raw_amount = parse_amount(message.content)
                if raw_amount > 0:
                    embed = build_tax_embed(message.author, raw_amount)
                    await message.channel.send(embed=embed)
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
