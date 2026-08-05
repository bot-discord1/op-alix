import os
import json
import asyncio
import random
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from discord.ui import Button, View, Select

# ==================== BOT CONFIGURATION ====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

WELCOME_CHANNEL_ID = 1444796667340656680
GOODBYE_CHANNEL_ID = 1444796667340656680

DATA_FILE = "data.json"
invites = {}

# ==================== DATA MANAGEMENT ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

def ensure_user_exists(data, user_id):
    str_id = str(user_id)
    if str_id not in data:
        data[str_id] = {"credits": 0, "claimed_ticket_reward": False, "invites_count": 0}
    return str_id

# ==================== TICKET SYSTEM COMPONENTS ====================
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 إغلاق التكت", style=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة فقط!", ephemeral=True)
            return
        
        await interaction.response.send_message("🔒 سيتم إغلاق التكت خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الدعم الفني والخدمات", value="support", emoji="🛠️", description="طلب مساعدة أو استفسار عام"),
            discord.SelectOption(label="التقديم على الطاقم", value="staff", emoji="📝", description="التقديم للانضمام لإدارة السيرفر"),
            discord.SelectOption(label="استلام جوائز المسابقات", value="claim", emoji="🎁", description="مطالبة بجوائز المتجر أو المسابقات"),
        ]
        super().__init__(placeholder="اختر نوع التكت المناسب...", min_values=1, max_values=1, options=options, custom_id="ticket_select_dropdown")

    async def callback(self, interaction: Interaction):
        guild = interaction.guild
        user = interaction.user
        category_name = self.values[0]

        channel_name = f"ticket-{user.name}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"❌ لديك تكت مفتوحة بالفعل: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم إنشاء التكت بنجاح: {ticket_channel.mention}", ephemeral=True)

        data = load_data()
        str_id = ensure_user_exists(data, user.id)
        reward_msg = ""

        if data[str_id].get("invites_count", 0) >= 1 and not data[str_id].get("claimed_ticket_reward", False):
            data[str_id]["credits"] += 500
            data[str_id]["claimed_ticket_reward"] = True
            save_data(data)
            reward_msg = "\n🎉 **مبروك! تمت إضافة 500 كريديت كمكافأة لفتح أول تكت مع وجود دعوات!**"

        embed = discord.Embed(
            title=f"🎫 تكت جديدة: {category_name.upper()}",
            description=f"أهلاً بك {user.mention}، يرجى كتابة تفاصيل طلبك وسيقوم فريق الإدارة بالرد عليك في أقرب وقت.{reward_msg}",
            color=discord.Color.green()
        )
        await ticket_channel.send(content=user.mention, embed=embed, view=TicketControlView())

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ==================== BOT EVENTS ====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")
    bot.add_view(TicketView())
    bot.add_view(TicketControlView())
    
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except Exception as e:
            print(f"Could not fetch invites for {guild.name}: {e}")
            
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# 🎉 تفعيل وترتيب رسالة Welcome
@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID) or guild.system_channel
    
    inviter_mention = "غير معروف"
    inviter_obj = None
    
    if guild.id in invites:
        old_invites = invites[guild.id]
        try:
            new_invites = await guild.invites()
            for invite in old_invites:
                for new_inv in new_invites:
                    if invite.code == new_inv.code and new_inv.uses > invite.uses:
                        inviter_mention = new_inv.inviter.mention
                        inviter_obj = new_inv.inviter
                        break
            invites[guild.id] = new_invites
        except Exception as e:
            print(f"Error tracking invites: {e}")

    if inviter_obj:
        data = load_data()
        str_id = ensure_user_exists(data, inviter_obj.id)
        data[str_id]["invites_count"] = data[str_id].get("invites_count", 0) + 1
        save_data(data)

    if welcome_channel:
        embed = discord.Embed(
            title="✨ أهلاً وسهلاً بك في السيرفر! 🎉",
            description=f"مرحباً بك يا {member.mention}\nنورت السيرفر وانضمامك يسعدنا جداً! ❤️",
            color=0x2b2d31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 العضو رقم", value=f"**#{guild.member_count}**", inline=True)
        embed.add_field(name="📩 تمت دعوته بواسطة", value=f"{inviter_mention}", inline=True)
        embed.set_footer(text=f"ID: {member.id} • نتمنى لك وقتاً ممتعاً!", icon_url=guild.icon.url if guild.icon else None)
        
        await welcome_channel.send(content=f"👋 أهلاً بك {member.mention}!", embed=embed)

@bot.event
async def on_member_remove(member):
    guild = member.guild
    goodbye_channel = bot.get_channel(GOODBYE_CHANNEL_ID) or guild.system_channel
    
    if goodbye_channel:
        embed = discord.Embed(
            title="💔 مغادرة عضو!",
            description=f"مع السلامة {member.mention}..\nنتمنى أن نراك مجدداً في السيرفر! 👋",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👥 الأعضاء المتبقين", value=f"**#{guild.member_count}**", inline=True)
        embed.set_footer(text=f"ID: {member.id}", icon_url=guild.icon.url if guild.icon else None)
        
        await goodbye_channel.send(embed=embed)

# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="profile", description="عرض الملف الشخصي والإحصائيات")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    data = load_data()
    str_id = ensure_user_exists(data, target.id)
    u_data = data[str_id]
    
    embed = discord.Embed(
        title=f"👤 Profile | {target.name}",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 الرصيد (Credits)", value=f"**{u_data.get('credits', 0)}** 💰", inline=True)
    embed.add_field(name="📩 عدد الدعوات (Invites)", value=f"**{u_data.get('invites_count', 0)}** دعوة", inline=True)
    
    joined_str = "غير معروف"
    if hasattr(target, 'joined_at') and target.joined_at:
        joined_str = f"<t:{int(target.joined_at.timestamp())}:R>"
    embed.add_field(name="📅 تاريخ الانضمام", value=joined_str, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="credit", description="عرض رصيدك الحالي من الكريديت")
async def credit(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    data = load_data()
    str_id = ensure_user_exists(data, target.id)
    credits_amt = data[str_id].get("credits", 0)
    
    embed = discord.Embed(
        title="💳 Balance | الرصيد",
        description=f"رصيد **{target.mention}** الحالي هو: **{credits_amt}** 💰",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# 👑 إضافة الكريديت مع شرط وجود صلاحية أدمن فقط
@bot.tree.command(name="addcredit", description="إضافة كريديت لعضو معين (للإدارة فقط)")
@app_commands.checks.has_permissions(administrator=True)
async def addcredit(interaction: discord.Interaction, user: discord.User, amount: int):
    # التحقق المباشر من صلاحيات العضو
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ هذا الأمر مخصص للإدارة وأصحاب صلاحية الأدمن فقط!", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ يجب أن يكون المبلغ أكبر من 0!", ephemeral=True)
        return
        
    data = load_data()
    str_id = ensure_user_exists(data, user.id)
    
    data[str_id]["credits"] += amount
    save_data(data)
    
    embed = discord.Embed(
        title="✅ تم إضافة الكريديت بنجاح",
        description=f"تمت إضافة **{amount}** كريديت إلى {user.mention}.\nالرصيد الجديد: **{data[str_id]['credits']}** 💰",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# التعامل مع خطأ عدم وجود صلاحية Admin
@addcredit.error
async def addcredit_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ لا تمتلك صلاحيات الأدمن (Administrator) لاستخدام هذا الأمر!", ephemeral=True)

@bot.tree.command(name="invites", description="عرض عدد الدعوات الخاصة بك ورابط السيرفر")
async def invites_command(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    data = load_data()
    str_id = ensure_user_exists(data, target.id)
    invite_count = data[str_id].get("invites_count", 0)
    
    channel = interaction.channel
    invite_link = await channel.create_invite(max_age=0, max_uses=0, unique=False)
    
    embed = discord.Embed(
        title="📩 Invite System | نظام الدعوات",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="👤 العضو", value=target.mention, inline=True)
    embed.add_field(name="📊 عدد الدعوات", value=f"**{invite_count}** دعوة", inline=True)
    embed.add_field(name="🔗 رابط الدعوة الخاص بالسيرفر", value=f"[اضغط هنا للنسخ]({invite_link.url})", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kick", description="طرد عضو من السيرفر (خاص بمالك السيرفر فقط)")
async def kick_user(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ هذا الأمر مخصص لمالك السيرفر (Server Owner) فقط!", ephemeral=True)
        return
        
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="🔨 تم طرد العضو",
            description=f"تم طرد {member.mention} بنجاح.\n**السبب:** {reason}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ حدث خطأ أثناء طرد العضو: {e}", ephemeral=True)

@bot.tree.command(name="closeticket", description="إغلاق التكت مع كتابة السبب (للإدارة فقط)")
@app_commands.checks.has_permissions(administrator=True)
async def closeticket(interaction: discord.Interaction, reason: str = "لم يتم ذكر سبب"):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ هذا الأمر يشتغل فقط داخل روم التكت!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔒 إغلاق التكت",
        description=f"سيتم إغلاق التكت بواسطة: {interaction.user.mention}\n**السبب:** {reason}\n\nسيتم حظر القناة خلال 5 ثوانٍ...",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(5)
    await interaction.channel.delete()

@bot.tree.command(name="renameticket", description="تغيير اسم التكت (للإدارة فقط)")
@app_commands.checks.has_permissions(administrator=True)
async def renameticket(interaction: discord.Interaction, new_name: str):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ هذا الأمر يشتغل فقط داخل روم التكت!", ephemeral=True)
        return

    old_name = interaction.channel.name
    formatted_name = f"ticket-{new_name.lower().replace(' ', '-')}"
    await interaction.channel.edit(name=formatted_name)
    await interaction.response.send_message(f"✅ تم تغيير اسم التكت من `{old_name}` إلى `{formatted_name}`")

@bot.tree.command(name="setup_tickets", description="إرسال لوحة فتح التكتات (للإدارة فقط)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_tickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 نظام التكتات والخدمات | Support Center",
        description="مرحباً بك! يرجى اختيار القسم المناسب من القائمة أسفله لفتح تكت والتواصل مع الإدارة.",
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ تم إرسال لوحة التكتات بنجاح!", ephemeral=True)

@bot.tree.command(name="giveaway", description="إنشاء مسابقة جديدة (يدعم s, m, h, d)")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, time_str: str, prize: str):
    unit = time_str[-1].lower()
    if unit not in ['s', 'm', 'h', 'd'] or not time_str[:-1].isdigit():
        await interaction.response.send_message("❌ صيغة الوقت غير صحيحة! استخدم مثلاً: `10s`, `5m`, `2h`, أو `1d`", ephemeral=True)
        return
        
    val = int(time_str[:-1])
    if unit == 's':
        seconds = val
    elif unit == 'm':
        seconds = val * 60
    elif unit == 'h':
        seconds = val * 3600
    elif unit == 'd':
        seconds = val * 86400

    embed = discord.Embed(
        title="🎉 **GIVEAWAY | مسابقة جديدة** 🎉",
        description=f"**الجائزة:** {prize}\n**الوقت:** {time_str}\n⚠️ **شرط الفوز:** يجب أن تكون لديك على الأقل **1 دعوة (Invite)** عند نهاية الوقت!\n\nاضغط على الزر أسفله للمشاركة!",
        color=discord.Color.gold()
    )
    
    await interaction.response.send_message("✅ تم إنشاء المسابقة!", ephemeral=True)
    
    class GiveawayView(View):
        def __init__(self):
            super().__init__(timeout=seconds)
            self.participants = set()

        @discord.ui.button(label="🎉 مشاركة", style=discord.ButtonStyle.primary)
        async def join(self, inter: Interaction, button: Button):
            self.participants.add(inter.user)
            await inter.response.send_message("✅ تم تسجيل مشاركتك في المسابقة بنجاح!", ephemeral=True)

    g_view = GiveawayView()
    await interaction.channel.send(embed=embed, view=g_view)
    await asyncio.sleep(seconds)

    if not g_view.participants:
        await interaction.channel.send(f"❌ انتهت المسابقة على **{prize}** ولم يشارك أحد!")
        return

    selected_winner = random.choice(list(g_view.participants))
    
    data = load_data()
    str_id = ensure_user_exists(data, selected_winner.id)
    invites_count = data[str_id].get("invites_count", 0)

    if invites_count >= 1:
        await interaction.channel.send(f"🎊 مبروك {selected_winner.mention}! لقد فزت بـ **{prize}** 🎉")
    else:
        await interaction.channel.send(f"❌ انتهت المسابقة على **{prize}** وحتى حد ماربح لأن العضو اللي طلع فـ السحب ما عندوش حتى دعوة (0 Invites)!")

# ==================== RUN BOT ====================
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set!")
