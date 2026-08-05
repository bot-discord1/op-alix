import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True  # ضروري باش يقرا الأعضاء

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # مزامنة الـ Slash Commands مع ديسكورد أول ما يخدم البوت
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(e)
    print(f"Logged in as {bot.user.name}")

# تعريف Slash Command
@bot.tree.command(name="announce", description="إرسال رسالة خاصة (DM) لجميع أعضاء السيرفر")
@discord.app_commands.checks.has_permissions(administrator=True) # مخصص للأدمنية فقط
async def announce(interaction: discord.Interaction, message: str):
    # الرد الأول مؤقت باش ديسكورد ما يعطيش Erreur (حيت العملية كتاخد وقت)
    await interaction.response.send_message("🔄 جاري إرسال الرسائل الخاصة لجميع الأعضاء، عافية الانتظار...", ephemeral=True)
    
    success_count = 0
    fail_count = 0
    
    # الدوران على جميع الأعضاء (باستثناء البوتات)
    for member in interaction.guild.members:
        if member.bot:
            continue
            
        try:
            await member.send(message)
            success_count += 1
            # تأخير بسيط باش مايتحظرش البوت بسبب السپام
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=1))
        except Exception:
            fail_count += 1

    # تعديل الميساج باش يعطيك النتيجة النهائية
    await interaction.edit_original_response(
        content=f"✅ **سالی الإرسال بنجاح!**\n- **تم الإرسال لـ:** {success_count} عضو\n- **فشل (موسّدين DMs):** {fail_count} عضو"
    )

# حط التوكن ديالك هنا
bot.run("YOUR_BOT_TOKEN_HERE")
