import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands

# ==================== ⚙️ BOT INITIALIZATION ====================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("Advanced Ticket Bot is ready!")
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} slash commands.")
  except Exception as e:
    print(f"Failed to sync commands: {e}")


# ==================== 🎫 TICKET SYSTEM ====================


class TicketReasonModal(discord.ui.Modal, title="سبب إغلاق التذكرة"):
  reason_input = discord.ui.TextInput(
      label="السبب",
      style=discord.TextStyle.paragraph,
      placeholder="اكتب سبب إغلاق التذكرة هنا...",
      required=True,
      max_length=300,
  )

  async def on_submit(self, interaction: discord.Interaction):
    reason = self.reason_input.value
    channel = interaction.channel
    closed_by = interaction.user

    # محاولة إيجاد صاحب التذكرة من اسم الروم أو أصحاب الروم
    ticket_owner = None
    for member, overwrite in channel.overwrites.items():
      if (
          isinstance(member, discord.Member)
          and not member.bot
          and overwrite.read_messages
      ):
        ticket_owner = member
        break

    await interaction.response.send_message(
        f"🔒 سيتم إغلاق التذكرة بواسطة {closed_by.mention}\n**السبب:** {reason}\nسيتم"
        " حذف القناة خلال 3 ثوانٍ..."
    )

    # إرسال رسالة خاصة لصاحب التذكرة
    if ticket_owner:
      try:
        embed_dm = discord.Embed(
            title="🎫 تم إغلاق تذكرتك",
            description=f"مرحباً، تم إغلاق تذكرتك في سيرفر **{interaction.guild.name}**.",
            color=discord.Color.red(),
        )
        embed_dm.add_field(
            name="اسم التذكرة", value=channel.name, inline=False
        )
        embed_dm.add_field(name="من طرف", value=closed_by.mention, inline=False)
        embed_dm.add_field(name="السبب", value=reason, inline=False)
        await ticket_owner.send(embed=embed_dm)
      except Exception:
        pass

    await asyncio.sleep(3)
    try:
      await channel.delete()
    except Exception:
      pass


class TicketCloseView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="🔒 إغلاق التذكرة",
      style=discord.ButtonStyle.red,
      custom_id="close_ticket_modal",
  )
  async def close_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    # فتح نافذة كتابة السبب
    await interaction.response.send_modal(TicketReasonModal())


class TicketView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="🎫 فتح تذكرة جديدة",
      style=discord.ButtonStyle.green,
      custom_id="open_ticket",
  )
  async def open_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    guild = interaction.guild
    user = interaction.user

    existing_channel = discord.utils.get(
        guild.text_channels, name=f"ticket-{user.name.lower()}"
    )
    if existing_channel:
      await interaction.response.send_message(
          f"❌ لديك تذكرة مفتوحة بالفعل: {existing_channel.mention}",
          ephemeral=True,
      )
      return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, attach_files=True
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, manage_channels=True
        ),
    }

    ticket_channel = await guild.create_text_channel(
        name=f"ticket-{user.name}", overwrites=overwrites
    )

    embed = discord.Embed(
        title="🎫 تذكرة دعم فني جديدة",
        description=(
            f"مرحباً بك {user.mention}!\nيرجى كتابة مشكلتك أو طلبك بالتفصيل"
            " وسيقوم طاقم الإدارة بالرد عليك قريباً."
        ),
        color=discord.Color.blue(),
    )
    embed.set_footer(text="City Life Support System")

    await ticket_channel.send(embed=embed, view=TicketCloseView())
    await interaction.response.send_message(
        f"✅ تم فتح تذكرتك بنجاح في: {ticket_channel.mention}", ephemeral=True
    )


@bot.tree.command(
    name="setupticket", description="إرسال لوحة التذاكر في القناة الحالية"
)
@app_commands.checks.has_permissions(administrator=True)
async def setupticket(interaction: discord.Interaction):
  embed = discord.Embed(
      title="🎫 مركز المساعدة والدعم الفني",
      description=(
          "هل تحتاج إلى مساعدة، لديك استفسار أو مشكلة؟\nاضغط على الزر أدناه لفتح"
          " تذكرة خاصة."
      ),
      color=discord.Color.dark_theme(),
  )
  embed.set_footer(text="City Life Roleplay")

  await interaction.channel.send(embed=embed, view=TicketView())
  await interaction.response.send_message(
      "✅ تم إرسال لوحة التذاكر بنجاح!", ephemeral=True
  )


# ==================== ✏️ COMMAND /rename ====================


@bot.tree.command(name="rename", description="تغيير اسم روم التذكرة الحالية")
@app_commands.checks.has_permissions(manage_channels=True)
async def rename(interaction: discord.Interaction, new_name: str):
  if not interaction.channel.name.startswith("ticket-"):
    await interaction.response.send_message(
        "❌ هذا الأمر مخصص لقنوات التذاكر فقط!", ephemeral=True
    )
    return

  await interaction.channel.rename(name=new_name)
  await interaction.response.send_message(
      f"✅ تم تغيير اسم التذكرة بنجاح إلى: **{new_name}**", ephemeral=True
  )


# ==================== 🚨 COMMAND /support (Admin DM) ====================


@bot.tree.command(
    name="support",
    description=(
        "إرسال تنبيه في رسالة خاصة لجميع المسؤولين (Admins) في السيرفر"
    ),
)
async def support(interaction: discord.Interaction, *, reason: str):
  await interaction.response.send_message(
      "🔄 جاري إرسال طلب المساعدة إلى جميع المسؤولين...", ephemeral=True
  )

  guild = interaction.guild
  count = 0

  embed = discord.Embed(
      title="🚨 طلب مساعدة عاجل (Support Alert)",
      description=(
          f"طلب دعم جديد من العضو {interaction.user.mention} في سيرفر"
          f" **{guild.name}**"
      ),
      color=discord.Color.gold(),
  )
  embed.add_field(name="السبب / التفاصيل", value=reason, inline=False)
  embed.set_footer(text=f"ID: {interaction.user.id}")

  for member in guild.members:
    if member.guild_permissions.administrator and not member.bot:
      try:
        await member.send(embed=embed)
        count += 1
      except Exception:
        pass

  await interaction.followup.send(
      f"✅ تم إرسال رسالة الدعم بنجاح إلى ({count}) مسؤول في السيرفر في الخاص"
      " (DM).",
      ephemeral=True,
  )


# ==================== 📢 COMMANDS /ann & /text ====================


@bot.tree.command(name="ann", description="إرسال إعلان رسمي بـ Embed")
@app_commands.checks.has_permissions(administrator=True)
async def ann(interaction: discord.Interaction, *, message: str):
  embed = discord.Embed(
      title="📢 إعلان رسمي / Announcement",
      description=message,
      color=discord.Color.blue(),
  )
  embed.set_footer(
      text=f"بواسطة: {interaction.user.name}",
      icon_url=interaction.user.display_avatar.url,
  )

  await interaction.channel.send(embed=embed)
  await interaction.response.send_message(
      "✅ تم إرسال الإعلان بنجاح!", ephemeral=True
  )


@bot.tree.command(
    name="text", description="جعل البوت يكتب أي نص تريده في القناة"
)
@app_commands.checks.has_permissions(administrator=True)
async def text(interaction: discord.Interaction, *, content: str):
  await interaction.channel.send(content)
  await interaction.response.send_message(
      "✅ تم نشر النص بنجاح!", ephemeral=True
  )


bot.run(os.getenv("DISCORD_TOKEN"))
