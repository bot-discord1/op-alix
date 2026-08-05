import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# إعداد الصلاحيات
intents = discord.Intents.default()
intents.members = True  # ضروري جداً لقراءة أعضاء السيرفر

class AnnounceBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # مزامنة الـ Slash Commands أوتوماتيك أول ما يخدم البوت
        await self.tree.sync()
        print("تمت مزامنة الأوامر بنجاح!")

bot = AnnounceBot()

@bot.event
async def on_ready():
    print(f"البوت شغال دابا باسم: {bot.user.name}")

# إنشاء الـ Slash Command بطريقة صحيحة
@bot.tree.command(name="announce", description="إرسال رسالة خاصة (DM) لجميع أعضاء السيرفر")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message: str):
    # الرد الأول مؤقت باش البوت مايتحبسش في Discord
    await interaction.response.send_message("🔄 جاري إرسال الرسائل الخاصة لجميع الأعضاء، يرجى الانتظار...", ephemeral=True)
    
    success_count = 0
    fail_count = 0
    
    # التأكد من جلب الأعضاء كاملين من السيرفر
    if not interaction.guild.chunked:
        await interaction.guild.chunk()

    for member in interaction.guild.members:
        if member.bot:
            continue
            
        try:
            await member.send(message)
            success_count += 1
            # فاصل زمني 1 ثانية باش ديسكورد مايبللوش البوت (Rate Limit)
            await asyncio.sleep(1)
        except Exception:
            # إذا كان العضو مساد الخاص أو مداير بلوك للبوت
            fail_count += 1

    # تحديث الرسالة بالنتيجة النهائية
    await interaction.edit_original_response(
        content=f"✅ **سالي الإرسال بنجاح!**\n- **تم الإرسال لـ:** {success_count} عضو\n- **فشل (مسادين DMs):** {fail_count} عضو"
    )

# معالجة خطأ الصلاحيات إذا ماكانش المستخدم أدمن
@announce.error
async def announce_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        if interaction.response.is_done():
            await interaction.followup.send("❌ ماعندكش الصلاحية باش تستعمل هاد الأمر (مخصص للأدمنية فقط).", ephemeral=True)
        else:
            await interaction.response.send_message("❌ ماعندكش الصلاحية باش تستعمل هاد الأمر (مخصص للأدمنية فقط).", ephemeral=True)
    else:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ وقع خطأ: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ وقع خطأ: {error}", ephemeral=True)

# حط التوكن ديال البوت ديالك هنا
bot.run("YOUR_BOT_TOKEN_HERE")
