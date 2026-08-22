import os
import discord
from discord.ext import commands
from discord import app_commands
import math

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def parse_amount(amount_str: str) -> int:
    val_clean = amount_str.lower().strip()
    if val_clean.endswith('k'):
        return int(float(val_clean[:-1]) * 1_000)
    elif val_clean.endswith('m'):
        return int(float(val_clean[:-1]) * 1_000_000)
    elif val_clean.endswith('b'):
        return int(float(val_clean[:-1]) * 1_000_000_000)
    return int(val_clean)

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

    # ProBot Tax = 5%
    TAX_RATE = 0.05
    
    # 1. Tax cut amount
    tax_cut = math.ceil(raw_amount * TAX_RATE)
    
    # 2. Net received if amount is sent directly
    net_amount = raw_amount - tax_cut

    # 3. Required amount to send so recipient receives exact net amount (ProBot Formula)
    amount_to_send = math.ceil(raw_amount * (20 / 19))

    embed = discord.Embed(
        title="📊 **ProBot Tax Calculator**",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Requested By", value=interaction.user.mention, inline=False)
    embed.add_field(name="💰 Amount", value=f"`{raw_amount:,}`", inline=True)
    embed.add_field(name="🔻 Tax Cut (5%)", value=f"`{tax_cut:,}`", inline=True)
    embed.add_field(name="💵 Net Received", value=f"`{net_amount:,}`", inline=True)
    embed.add_field(name="💳 Amount to Send (Exact)", value=f"`{amount_to_send:,}`", inline=False)
    
    embed.set_footer(text="ProBot Tax Calculator • 5% Tax Rate")

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Tax Bot is ready as: {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN is missing!")
    bot.run(DISCORD_TOKEN)
