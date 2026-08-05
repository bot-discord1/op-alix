import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command(name="fakereact")
@commands.has_permissions(administrator=True)
async def fakereact(ctx, channel_id: int, message_id: int, emoji: str):
    try:
        # جلب الكانال والرسالة بالـ ID
        channel = bot.get_channel(channel_id)
        if not channel:
            await ctx.send("❌ ماقدرتش نلقى الكانال، تأكد من الـ ID!")
            return
            
        message = await channel.fetch_message(message_id)
        if not message:
            await ctx.send("❌ ماقدرتش نلقى الرسالة، تأكد من الـ ID ديالها!")
            return
            
        # إضافة التفاعل (Fake React)
        await message.add_reaction(emoji)
        await ctx.send("✅ تم التفاعل بنجاح!")
        
        # مسح الرسالة ديال الأمر باش يبقى كلشي نقي
        await ctx.message.delete()
        
    except Exception as e:
        await ctx.send(f"❌ وقع خطأ: {e}")

# حط هنا التوكن ديال البوت ديالك
bot.run("YOUR_BOT_TOKEN_HERE")
