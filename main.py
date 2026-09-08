import os
import aiohttp
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

SCREENING_CHANNEL_ID = 1546937759065702400
RESULT_CHANNEL_ID = 1546937814246232075
NOTIFICATION_CHANNEL_ID = 1546948806560718959
SUCCESS_CHANNEL_ID = 1546937759065702400
STAFF_ROLE_ID = 1546934264619081879

STAFF_ROLE_IDS = [
    1546594126257193070,
    1546593939581309028,
    1546593359403950184,
    1546934264619081879,
]


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("TF-145 bot node is online and synchronized with ASOC.")
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")
  except Exception as e:
    print(e)


@bot.event
async def on_message(message: discord.Message):
  if message.author.bot:
    return

  if message.channel.id == SCREENING_CHANNEL_ID and bot.user in message.mentions:
    notif_channel = message.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if notif_channel:
      embed = discord.Embed(
          title="[TF-145] New Screening Application",
          description=(
              f"**Candidate:** {message.author.mention}"
              f" (`{message.author.id}`)\n**Channel:**"
              f" {message.channel.mention}\n\n**Application"
              f" Preview:**\n{message.content[:900]}"
          ),
          color=discord.Color(0x111111),
      )
      embed.set_footer(
          text="Task Force 145 Security Directorate • Notification System"
      )
      embed.timestamp = discord.utils.utcnow()

      await notif_channel.send(
          content=f"<@&{STAFF_ROLE_ID}> New screening application submitted!",
          embed=embed,
      )

  await bot.process_commands(message)


class EmbedModal(discord.ui.Modal, title="Create Custom Embed"):
  embed_title = discord.ui.TextInput(
      label="Embed Title",
      placeholder="Enter the title here...",
      required=True,
      max_length=256,
  )

  embed_description = discord.ui.TextInput(
      label="Embed Description (Line breaks work here!)",
      style=discord.TextStyle.paragraph,
      placeholder=(
          "Type your description. Press Enter/Return for new lines freely!"
      ),
      required=True,
  )

  def __init__(self, channel, color_hex):
    super().__init__()
    self.channel = channel
    self.color_hex = color_hex

  async def on_submit(self, interaction: discord.Interaction):
    clean_color = self.color_hex.strip("#")
    try:
      embed_color = discord.Color(int(clean_color, 16))
    except ValueError:
      embed_color = discord.Color.from_rgb(17, 17, 17)

    embed = discord.Embed(
        title=self.embed_title.value,
        description=self.embed_description.value,
        color=embed_color,
    )
    embed.set_footer(text="Task Force 145 Directorate")
    embed.timestamp = discord.utils.utcnow()

    await self.channel.send(embed=embed)
    await interaction.response.send_message(
        f"Embed successfully deployed to {self.channel.mention}.", ephemeral=True
    )


@bot.tree.command(
    name="embed", description="Creates a custom TF-145 embed message"
)
async def custom_embed(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    color: str = "111111",
):
  await interaction.response.send_modal(EmbedModal(channel, color))


class ScreeningResultModal(discord.ui.Modal, title="Submit Screening Result"):
  reviewer_notes = discord.ui.TextInput(
      label="Notes (Optional)",
      style=discord.TextStyle.paragraph,
      placeholder="Enter any additional reviewer notes here...",
      required=False,
  )

  def __init__(
      self,
      member: discord.Member,
      roblox_username: str,
      roblox_id: str,
      roblox_link: str,
      result_status: str,
      reviewer: discord.Member,
  ):
    super().__init__()
    self.member = member
    self.roblox_username = roblox_username
    self.roblox_id = roblox_id
    self.roblox_link = roblox_link
    self.result_status = result_status
    self.reviewer = reviewer

  async def on_submit(self, interaction: discord.Interaction):
    result_channel = interaction.guild.get_channel(RESULT_CHANNEL_ID)
    if not result_channel:
      await interaction.response.send_message(
          "❌ Result channel not found! Check the channel ID.", ephemeral=True
      )
      return

    if self.result_status == "Accepted":
      result_text = "# ACCEPTED"
      embed_color = discord.Color(0x2E8B57)
    else:
      result_text = "# DENIED"
      embed_color = discord.Color(0x111111)

    notes_content = (
        self.reviewer_notes.value
        if self.reviewer_notes.value
        else "No notes provided."
    )

    embed = discord.Embed(
        title="[TF-145] Screening Result", color=embed_color
    )
    embed.description = (
        f"<:tf145:1546615062276341820> **TF‑145 Screening Result**\n\n"
        f"**Roblox Username:** {self.roblox_username}\n"
        f"**Discord Username:** {self.member}\n"
        f"**Roblox Profile Link:** {self.roblox_link}\n"
        f"**Discord ID:** {self.member.id}\n\n"
        f"**Result:**\n{result_text}\n\n"
        f"**Reviewer:** {self.reviewer.mention}\n"
        f"**Notes (Optional):** {notes_content}"
    )
    embed.set_footer(
        text="Task Force 145 Security Directorate • Result Logged"
    )
    embed.timestamp = discord.utils.utcnow()

    await result_channel.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Screening result successfully posted to <#{RESULT_CHANNEL_ID}>.",
        ephemeral=True,
    )


@bot.tree.command(
    name="screen_result",
    description="Post a candidate screening result to the results channel.",
)
async def screen_result(
    interaction: discord.Interaction,
    member: discord.Member,
    roblox_username: str,
    result: str,
):
  is_owner = (
      interaction.guild and interaction.guild.owner_id == interaction.user.id
  )
  has_staff_role = any(
      role.id in STAFF_ROLE_IDS for role in interaction.user.roles
  )

  if not is_owner and not has_staff_role:
    await interaction.response.send_message(
        "❌ You do not have the required staff role to execute screening"
        " results.",
        ephemeral=True,
    )
    return

  if interaction.channel.id != RESULT_CHANNEL_ID:
    await interaction.response.send_message(
        f"❌ This command can only be used inside the results channel"
        f" (<#{RESULT_CHANNEL_ID}>).",
        ephemeral=True,
    )
    return

  if result.lower() not in ["accepted", "denied"]:
    await interaction.response.send_message(
        "❌ Invalid result. Please type either 'Accepted' or 'Denied'.",
        ephemeral=True,
    )
    return

  roblox_id = "Not Found"
  roblox_link = "N/A"

  async with aiohttp.ClientSession() as session:
    payload = {"usernames": [roblox_username], "excludeBannedUsers": True}
    async with session.post(
        "https://users.roblox.com/v1/usernames/users", json=payload
    ) as resp:
      if resp.status == 200:
        data = await resp.json()
        if data.get("data"):
          user_info = data["data"][0]
          roblox_id = user_info["id"]
          roblox_link = f"https://www.roblox.com/users/{roblox_id}/profile"

    status_formatted = "Accepted" if result.lower() == "accepted" else "Denied"
    await interaction.response.send_modal(
        ScreeningResultModal(
            member,
            roblox_username,
            roblox_id,
            roblox_link,
            status_formatted,
            interaction.user,
        )
    )


@bot.tree.command(
    name="background_check",
    description=(
        "Run a public security background check on a candidate including Roblox"
        " & Discord stats, badges, and risk analysis."
    ),
)
async def background_check(
    interaction: discord.Interaction,
    member: discord.Member,
    roblox_username: str,
):
  is_owner = (
      interaction.guild and interaction.guild.owner_id == interaction.user.id
  )
  has_staff_role = any(
      role.id in STAFF_ROLE_IDS for role in interaction.user.roles
  )

  if not is_owner and not has_staff_role:
    await interaction.response.send_message(
        "❌ You do not have the required staff role to run background checks.",
        ephemeral=True,
    )
    return

  await interaction.response.defer(ephemeral=True)

  # Discord Data
  disc_created = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
  disc_joined = (
      member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
      if member.joined_at
      else "Unknown"
  )
  disc_roles_count = len(member.roles) - 1

  from datetime import datetime, timezone

  disc_age_days = (datetime.now(timezone.utc) - member.created_at).days

  # Roblox API Data Holders
  roblox_id = "Not Found"
  roblox_display = "N/A"
  roblox_created = "N/A"
  roblox_age_days = 0
  roblox_banned = "No"
  roblox_description = "N/A"
  friends_count = 0
  followers_count = 0
  following_count = 0
  badge_count = "N/A"

  async with aiohttp.ClientSession() as session:
    payload = {"usernames": [roblox_username], "excludeBannedUsers": False}
    async with session.post(
        "https://users.roblox.com/v1/usernames/users", json=payload
    ) as resp:
      if resp.status == 200:
        data = await resp.json()
        if data.get("data"):
          user_info = data["data"][0]
          roblox_id = user_info["id"]
          roblox_display = user_info.get("displayName", roblox_username)
          roblox_banned = (
              "Yes" if user_info.get("isBanned", False) else "No"
          )

    if roblox_id != "Not Found":
      async with session.get(
          f"https://users.roblox.com/v1/users/{roblox_id}"
      ) as r_resp:
        if r_resp.status == 200:
          r_data = await r_resp.json()
          created_raw = r_data.get("created", "")
          if created_raw:
            roblox_created = created_raw.split("T")[0]
            created_dt = datetime.fromisoformat(
                created_raw.replace("Z", "+00:00")
            )
            roblox_age_days = (
                datetime.now(timezone.utc) - created_dt
            ).days

          roblox_description = r_data.get("description", "")
          if not roblox_description:
            roblox_description = "None"
          elif len(roblox_description) > 100:
            roblox_description = roblox_description[:97] + "..."

      async with session.get(
          f"https://friends.roblox.com/v1/users/{roblox_id}/friends/count"
      ) as f_resp:
        if f_resp.status == 200:
          f_data = await f_resp.json()
          friends_count = f_data.get("count", 0)

      async with session.get(
          f"https://friends.roblox.com/v1/users/{roblox_id}/followers/count"
      ) as fo_resp:
        if fo_resp.status == 200:
          fo_data = await fo_resp.json()
          followers_count = fo_data.get("count", 0)

      async with session.get(
          f"https://friends.roblox.com/v1/users/{roblox_id}/followings/count"
      ) as fing_resp:
        if fing_resp.status == 200:
          fing_data = await fing_resp.json()
          following_count = fing_data.get("count", 0)

      try:
        cursor = ""
        b_count = 0
        while cursor is not None:
          badge_url = f"https://badges.roblox.com/v1/users/{roblox_id}/badges?limit=100"
          if cursor:
            badge_url += f"&cursor={cursor}"
          async with session.get(badge_url) as b_resp:
            if b_resp.status == 200:
              b_data = await b_resp.json()
              b_count += len(b_data.get("data", []))
              cursor = b_data.get("nextPageCursor")
            else:
              break
        badge_count = b_count
      except Exception:
        badge_count = "Unavailable"

  roblox_link = (
      f"https://www.roblox.com/users/{roblox_id}/profile"
      if roblox_id != "Not Found"
      else "N/A"
  )

  # Risk Analysis Algorithm
  risk_level = "🟢 LOW RISK (Good to Accept)"
  risk_reasons = []

  if roblox_banned == "Yes":
    risk_level = "🔴 HIGH RISK (Platform Banned)"
    risk_reasons.append("• Roblox account is currently banned.")
  if roblox_age_days < 30 and roblox_id != "Not Found":
    risk_level = "🟡 MEDIUM / 🔴 HIGH RISK (Alt Account Suspected)"
    risk_reasons.append(
        f"• Roblox account is very young (~{roblox_age_days} days old)."
    )
  if disc_age_days < 14:
    risk_level = "🟡 MEDIUM / 🔴 HIGH RISK (New Discord Alt)"
    risk_reasons.append(
        f"• Discord account is very young (~{disc_age_days} days old)."
    )
  if roblox_id == "Not Found":
    risk_level = "🔴 HIGH RISK (Invalid User)"
    risk_reasons.append("• Roblox username could not be verified/found.")

  if not risk_reasons:
    risk_reasons.append(
        "• All security checks passed cleanly. Account metrics look normal."
    )

  risk_summary = f"**Assessment:** {risk_level}\n" + "\n".join(risk_reasons)

  embed = discord.Embed(
      title="[TF-145] Security Background Check Report",
      color=discord.Color(
          0x2E8B57
          if "LOW" in risk_level
          else (0xE74C3C if "HIGH" in risk_level else 0xF39C12)
      ),
  )
  embed.description = (
      f"<:tf145:1546615062276341820> **Comprehensive Dossier & Audit**\n\n"
      f"🔍 **Automated Risk Analysis**\n{risk_summary}\n\n"
      f"👤 **Discord Profile Information**\n"
      f"• **User:** {member.mention} (`{member.id}`)\n"
      f"• **Account Created:** {disc_created} (~{disc_age_days} days old)\n"
      f"• **Server Join Date:** {disc_joined}\n"
      f"• **Roles Count:** {disc_roles_count}\n\n"
      f"🎮 **Roblox Account Information**\n"
      f"• **Username / Display:** {roblox_username} / {roblox_display}\n"
      f"• **Roblox ID:** `{roblox_id}`\n"
      f"• **Profile Link:** {roblox_link}\n"
      f"• **Account Created:** {roblox_created} (~{roblox_age_days} days"
      f" old)\n"
      f"• **Platform Banned:** {roblox_banned}\n"
      f"• **Total Badges:** {badge_count}\n"
      f"• **Socials:** {friends_count} Friends | {followers_count} Followers |"
      f" {following_count} Following\n"
      f"• **Bio/Description:** *{roblox_description}*"
  )
  embed.set_footer(
      text=f"Requested by {interaction.user} • Security & Vetting Directorate"
  )
  embed.timestamp = discord.utils.utcnow()

  notif_channel = interaction.guild.get_channel(NOTIFICATION_CHANNEL_ID)
  if notif_channel:
    notification_content = (
        f"[TF-145] New Background Check Audit\n"
        f"Candidate: {member.mention} (`{member.id}`)\n"
        f"Channel: <#{interaction.channel.id}>\n"
        f"Roblox Username: {roblox_username}\n"
        f"Discord Username: {member}\n"
        f"Roblox Profile Link: {roblox_link}\n"
        f"Discord ID: {member.id}\n\n"
        f"Required Ping: <@&{STAFF_ROLE_ID}>"
    )
    await notif_channel.send(content=notification_content, embed=embed)

  await interaction.followup.send(
      f"✅ Background check executed and logged with risk analysis to"
      f" <#{NOTIFICATION_CHANNEL_ID}>.",
      ephemeral=True,
  )


@bot.tree.command(
    name="tf145_application", description="Post the TF-145 Processing Application."
)
async def tf145_application(interaction: discord.Interaction):
  app_description = (
      "<:tf145:1546615062276341820> Hey — congratulations on beginning your"
      " TF‑145 Processing.\nYou’re far, but close to joining the Task Force."
      " Follow the instructions carefully — incorrect formats will be"
      " denied.\n\n**Rules**\n• All information must be accurate\n• Do not DM"
      " TF‑145 staff about your application\n• Do not ping leadership unless"
      " instructed\n• Follow the exact format below\n• Once submitted, wait for"
      " staff to review\n\n**Application Format & Candidate"
      " Information**\nName: \nRoblox Username: \nDiscord Username:"
      " \nTimezone:\n\n**Required Ping**\nPing: <@&1546627489231544330>"
  )

  embed = discord.Embed(
      title="[TF-145] Processing Application",
      description=app_description,
      color=discord.Color(0x111111),
  )
  embed.set_footer(text="Task Force 145 Directorate • Selection & Screening")

  await interaction.response.send_message(embed=embed)


bot.run(os.getenv("DISCORD_TOKEN"))