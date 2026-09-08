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


@bot.tree.command(
    name="tf145_embed", description="Generate an ASOC TF-145 operational embed."
)
async def tf145_embed(
    interaction: discord.Interaction, title: str, description: str
):
  embed = discord.Embed(
      title=f"[TF-145] {title}",
      description=description,
      color=discord.Color.from_rgb(
          46, 139, 87
      ),  # Tactical green accent matching the unit styling
  )
  embed.set_author(
      name="ASOC // Task Force 145 Command", icon_url=bot.user.avatar.url
  )
  embed.set_footer(
      text="U.S. Army Roleplay Operations • Authorized Personnel Only"
  )
  embed.timestamp = discord.utils.utcnow()

  await interaction.response.send_message(embed=embed)


# Run bot using Railway's environment variable
bot.run(os.getenv("DISCORD_TOKEN"))