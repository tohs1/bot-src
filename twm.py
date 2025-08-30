import discord
from discord.ext import commands
import json

# Load tokens from bots.json
with open("bots.json", "r") as f:
    tokens = json.load(f)

TOKEN = tokens["twm_token"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# When bot is ready
@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="the niko island 💡")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user} and synced commands.")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# /say slash command
@bot.tree.command(name="say", description="Make the bot say something (mods only).")
async def say(interaction: discord.Interaction, msg: str):
    # Check if user has the @mod role
    has_role = any(role.name.lower() == "mod" for role in interaction.user.roles)
    if not has_role:
        await interaction.response.send_message("Permission Denied!", ephemeral=True)
        return

    # Replace \n with real newlines and allow escaped chars
    processed_msg = msg.encode("utf-8").decode("unicode_escape")
    await interaction.response.send_message(processed_msg)

bot.run(TOKEN)
