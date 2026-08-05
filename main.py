import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction

# ==================== BOT CONFIGURATION ====================
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ==================== VOICE ROOM COMMANDS ====================

@bot.tree.command(name="joinvoice", description="دخول البوت إلى الروم الصوتي الذي تتواجد فيه")
async def joinvoice(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ يجب عليك أن تكون داخل روم صوتي أولاً لكي يستطيع البوت دخوله!", ephemeral=True)
        return
    
    voice_channel = interaction.user.voice.channel
    
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(voice_channel)
        await interaction.response.send_message(f"✅ تم نقل البوت إلى الروم الصوتي: **{voice_channel.name}**")
    else:
        await voice_channel.connect()
        await interaction.response.send_message(f"✅ دخل البوت إلى الروم الصوتي بنجاح: **{voice_channel.name}** 🎧")

@bot.tree.command(name="leavevoice", description="خروج البوت من الروم الصوتي")
async def leavevoice(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🛑 خرج البوت من الروم الصوتي بنجاح.")
    else:
        await interaction.response.send_message("❌ البوت ليس متصلاً بأي روم صوتي حالياً!", ephemeral=True)

# ==================== RUN BOT ====================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set!")
