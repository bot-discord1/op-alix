import os
import discord
from discord.ext import commands

# ==================== BOT CONFIGURATION ====================
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True  # ضروري باش يقرأ علامة التعجب !

bot = commands.Bot(command_prefix="!", intents=intents)

# حط هنا الأيدي (ID) ديال الروم الصوتي اللي بغيت البوت يدخل ليه أول ما يخدم
VOICE_CHANNEL_ID = 1444796667340656680 

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    
    # محاولة دخول البوت للروم الصوتي أوتوماتيكياً
    for guild in bot.guilds:
        voice_channel = guild.get_channel(VOICE_CHANNEL_ID)
        if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
            try:
                if not guild.voice_client:
                    await voice_channel.connect()
                    print(f"🔊 دخل البوت أوتوماتيكياً إلى الروم: {voice_channel.name}")
            except Exception as e:
                print(f"❌ ماقدرش البوت يدخل للروم الصوتي: {e}")

# ==================== CHAT COMMANDS ====================

# 1. أمر قفل الروم (!lock)
@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 تم قفل هذه الروم بنجاح!")

@lock_channel.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ ماعندكش صلاحيات لإستخدام هذا الأمر!")

# 2. أمر فتح الروم (!unlock)
@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 تم فتح هذه الروم بنجاح!")

@unlock_channel.error
async def unlock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ ماعندكش صلاحيات لإستخدام هذا الأمر!")

# 3. أمر مسح الرسائل (!delet <عدد>)
@bot.command(name="delet")
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: int = 5):
    if amount <= 0:
        await ctx.send("❌ حدد عدد صحيح أكبر من 0 للمسح!", delete_after=5)
        return
    
    await ctx.message.delete()
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🗑️ تم مسح `{len(deleted)}` رسالة بنجاح.")
    await asyncio.sleep(4)
    try:
        await msg.delete()
    except:
        pass

@delete_messages.error
async def delete_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ ماعندكش صلاحيات لمسح الرسائل!")

# ==================== RUN BOT ====================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set!")
