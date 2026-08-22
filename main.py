import os
import discord
from discord.ext import commands
from discord import app_commands
import math

# Token m'n Environment Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Helper Function: Format Numbers (e.g., 10k, 1m) ---
def parse_amount(amount_str: str) -> int:
    val_clean = amount_str.lower().strip()
    if val_clean.endswith('k'):
        return int(float(val_clean[:-1]) * 1_000)
    elif val_clean.endswith('m'):
        return int(float(val_clean[:-1]) * 1_000_000)
    elif val_clean.endswith('b'):
        return int(float(val_clean[:-1]) * 1_000_000_000)
    return int(val_clean)

# --- Slash Command `/tax` ---
@bot.tree.command(name="tax", description="Hssb l-dariba w l-mablagh l-ikhmali")
@app_commands.describe(
    amount="L-mablagh (مثلاً: 10000 aw 10k)",
    tax_rate="Nisba dyal l-dariba f % (Default: 5%)"
)
async def tax(interaction: discord.Interaction, amount: str, tax_rate: float = 5.0):
    try:
        raw_amount = parse_amount(amount)
        if raw_amount <= 0:
            await interaction.response.send_message("❌ **L-mablagh khassu ikoun kbr m'n 0!**", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("❌ **L-mablagh ghalt!** Ktb r9m s7i7 aw st3ml `10k`, `1m`.", ephemeral=True)
        return

    # Hssab l-dariba
    # 1. Shhal ghadi i-t9t3 dyal l-dariba m'n l-mablagh
    tax_cut = math.ceil(raw_amount * (tax_rate / 100))
    
    # 2. L-mablagh l-safi li ghadi i-wsslek
    amount_after_tax = raw_amount - tax_cut

    # 3. Shhal khass l-shakhs i-khllss باش i-wsslek l-mablagh kaml safi (With Tax)
    amount_to_pay = math.ceil(raw_amount * (100 / (100 - tax_rate)))

    # Display Embed
    embed = discord.Embed(
        title="📊 **Tax Calculation / 💡 💡 💡 💡**",
        color=discord.Color.blue()
    )
    embed.add_field(name="👤 Requested By", value=interaction.user.mention, inline=False)
    embed.add_field(name="💰 Amount (L-mablagh)", value=f"`{raw_amount:,}`", inline=True)
    embed.add_field(name="📈 Tax Rate (Nisba)", value=f"`{tax_rate}%`", inline=True)
    embed.add_field(name="🔻 Tax Cut (Shhal i-t9t3)", value=f"`{tax_cut:,}`", inline=True)
    embed.add_field(name="💵 Net Received (Shhal i-wsslek)", value=f"`{amount_after_tax:,}`", inline=False)
    embed.add_field(name="💳 Required to Send (Shhal khasso i-khllss)", value=f"`{amount_to_pay:,}`", inline=False)
    
    embed.set_footer(text="Discord Tax Calculator")

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Tax Bot is ready as: {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN is missing!")
    bot.run(DISCORD_TOKEN)
