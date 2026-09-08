import os
import discord
from discord.ext import commands

# Initialize bot with intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("TF-145 bot node is online and synchronized with ASOC.")
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")
  except Exception as e:
    print(e)


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
      embed_color = discord.Color.from_rgb(212, 175, 55)  # Fallback Gold

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
    color: str = "D4AF37",
):
  # Opens the popup modal so you get a real text area for line breaks
  await interaction.response.send_modal(EmbedModal(channel, color))


@bot.tree.command(
    name="tf145_application", description="Post the TF-145 Processing Application."
)
async def tf145_application(interaction: discord.Interaction):
  app_description = (
      "Hey — congratulations on beginning your TF‑145 Processing.\n"
      "You’re far, but close to joining the Task Force. Follow the instructions"
      " carefully — incorrect formats will be denied.\n\n"
      "**Rules**\n"
      "• All information must be accurate\n"
      "• Do not DM TF‑145 staff about your application\n"
      "• Do not ping leadership unless instructed\n"
      "• Follow the exact format below\n"
      "• Once submitted, wait for staff to review\n\n"
      "**Application Format**\n"
      "1. Candidate Information\n"
      "Name: \n"
      "Roblox Username: \n"
      "Discord Username: \n"
      "Timezone:\n\n"
      "**Required Ping**\n"
      "Ping: @Detachment Sergeant"
  )

  embed = discord.Embed(
      title="[TF-145] Processing Application",
      description=app_description,
      color=discord.Color.from_rgb(212, 175, 55),
  )
  embed.set_footer(text="Task Force 145 Directorate • Selection & Screening")

  await interaction.response.send_message(embed=embed)


# Run bot using Railway's environment variable
bot.run(os.getenv("DISCORD_TOKEN"))