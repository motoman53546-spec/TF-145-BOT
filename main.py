import os
import aiohttp
import discord
from discord.ext import commands

# Initialize bot with intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration IDs
SCREENING_CHANNEL_ID = 1546937759065702400
RESULT_CHANNEL_ID = 1546937814246232075
NOTIFICATION_CHANNEL_ID = 1546948806560718959
SUCCESS_CHANNEL_ID = 1546937759065702400  # Target channel for accepted candidates
STAFF_ROLE_ID = 1546934264619081879

# Allowed Staff Role IDs
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

  # Check if someone pings the bot in the screening channel with their application
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

      # Send notification pinging staff
      await notif_channel.send(
          content=f"<@&{STAFF_ROLE_ID}> New screening application submitted!",
          embed=embed,
      )

  await bot.process_commands(message)


# Modal popup for multi-line text input
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
      embed_color = discord.Color.from_rgb(17, 17, 17)  # Fallback Near-black

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
      result_text = f"• Accepted — proceed to <#{SUCCESS_CHANNEL_ID}>"
      embed_color = discord.Color(0x2E8B57)  # Tactical Green
    else:
      result_text = "• Denied — you may reapply in 14 days"
      embed_color = discord.Color(0x111111)  # Near-black

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

  # Enforce command usage strictly in the results channel
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


# Run bot using Railway's environment variable
bot.run(os.getenv("DISCORD_TOKEN"))