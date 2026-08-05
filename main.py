import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

# جلب التوكن من الـ Environment الخاص باللوحة
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip().strip('"').strip("'")

intents = discord.Intents.default()
intents.members = True

class AnnounceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تمت مزامنة الأوامر بنجاح!")

bot = AnnounceBot()

@bot.event
async def on_ready():
    print(f"البوت شغال دابا باسم: {bot.user.name}")

@bot.tree.command(name="announce", description="إرسال رسالة خاصة (DM) لجميع أعضاء السيرفر")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("🔄 جاري إرسال الرسائل الخاصة لجميع الأعضاء، يرجى الانتظار...", ephemeral=True)
    
    success_count = 0
    fail_count = 0
    
    if not interaction.guild.chunked:
        await interaction.guild.chunk()

    for member in interaction.guild.members:
        if member.bot:
            continue
            
        try:
            await member.send(message)
            success_count += 1
            await asyncio.sleep(1)
        except Exception:
            fail_count += 1

    await interaction.edit_original_response(
        content=f"✅ **سالي الإرسال بنجاح!**\n- **تم الإرسال لـ:** {success_count} عضو\n- **فشل (مسادين DMs):** {fail_count} عضو"
    )

@announce.error
async def announce_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "❌ ماعندكش الصلاحية باش تستعمل هاد الأمر (مخصص للأدمنية فقط)."
    else:
        msg = f"❌ وقع خطأ: {error}"
        
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

if not TOKEN:
    print("❌ خطأ: التوكن غير موجود في متغيرات البيئة للوحة!")
else:
    bot.run(TOKEN)
