import os
import sys
import subprocess

# Auto-install missing packages
REQUIRED_PACKages = ["discord.py", "yt-dlp", "PyNaCl"]
for package in REQUIRED_PACKages:
    try:
        __import__(package.replace("-", "_").split(".")[0])
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
music_queues = {}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

def play_next(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        next_track = music_queues[guild_id].pop(0)
        vc = interaction.guild.voice_client
        if vc and vc.is_connected():
            coro = YTDLSource.from_url(next_track['url'], loop=bot.loop, stream=True)
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                player = fut.result()
                vc.play(player, after=lambda e: play_next(interaction))
                asyncio.run_coroutine_threadsafe(
                    interaction.channel.send(f"🎶 **Daba kay-l3b:** `{player.title}`"),
                    bot.loop
                )
            except Exception as e:
                print(f"Error playing next: {e}")

@bot.tree.command(name="play", description="L3b song aw search b smiya")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Khassk t-koun dakhil l-Voice Channel!", ephemeral=True)
        return

    await interaction.response.defer()
    voice_channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if not vc:
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)

    guild_id = interaction.guild_id
    if guild_id not in music_queues:
        music_queues[guild_id] = []

    if vc.is_playing() or vc.is_paused():
        music_queues[guild_id].append({'url': query})
        await interaction.followup.send(f"➕ **Zdnaha f-Queue:** `{query}`")
    else:
        try:
            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            vc.play(player, after=lambda e: play_next(interaction))
            await interaction.followup.send(f"🎶 **Daba kay-l3b:** `{player.title}`")
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur f play: {e}")

@bot.tree.command(name="pause", description="Wqqf l-musique")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ **Musique t-wqqfat.**")
    else:
        await interaction.response.send_message("❌ Ta 7aja ma kat-l3b.", ephemeral=True)

@bot.tree.command(name="resume", description="Kmmel l-musique")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ **Musique kmmlat.**")
    else:
        await interaction.response.send_message("❌ Musique ma-m-wqqfach.", ephemeral=True)

@bot.tree.command(name="skip", description="Douz l-song l-jayi")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await interaction.response.send_message("⏭️ **Dazt l-song l-jayi.**")
    else:
        await interaction.response.send_message("❌ Ta 7aja ma kat-l3b.", ephemeral=True)

@bot.tree.command(name="stop", description="Wqqf l-bot w khoroj")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    if guild_id in music_queues:
        music_queues[guild_id].clear()
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("🛑 **Wqqft l-bot w khrajt.**")
    else:
        await interaction.response.send_message("❌ L-bot ma-dakhilsh l-Voice.", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Music Bot Ready as: {bot.user}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("❌ DISCORD_TOKEN is missing!")
    bot.run(DISCORD_TOKEN)
