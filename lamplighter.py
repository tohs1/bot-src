import discord
from discord.ext import commands
import os
import asyncio
import json

# Load tokens from bots.json
with open("bots.json", "r") as f:
    tokens = json.load(f)

TOKEN = tokens["lamplighter_token"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

MUSIC_FOLDER = "./music"
ELEVATOR_CHANNEL_NAME = "Elevator"

# Ensure music folder exists
os.makedirs(MUSIC_FOLDER, exist_ok=True)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Set status
    activity = discord.Activity(type=discord.ActivityType.listening, name="music 🎶")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Join Elevator voice channel automatically
    for guild in bot.guilds:
        channel = discord.utils.get(guild.voice_channels, name=ELEVATOR_CHANNEL_NAME)
        if channel:
            vc = await channel.connect(self_deaf=False, self_mute=False)
            bot.loop.create_task(play_music(vc))
    print("🎶 Music bot ready!")

async def play_music(vc: discord.VoiceClient):
    """Loop through all files in the music folder."""
    while True:
        for filename in os.listdir(MUSIC_FOLDER):
            if filename.endswith(".mp3") or filename.endswith(".wav"):
                filepath = os.path.join(MUSIC_FOLDER, filename)
                vc.play(discord.FFmpegPCMAudio(filepath))
                while vc.is_playing():
                    await asyncio.sleep(1)
        # Loop forever
        await asyncio.sleep(1)

# Detect Stage events
@bot.event
async def on_stage_instance_create(stage_instance: discord.StageInstance):
    print("🎤 Stage started:", stage_instance.topic)
    guild = stage_instance.guild
    stage_channel = stage_instance.channel

    # Leave Elevator
    for vc in bot.voice_clients:
        if vc.guild == guild:
            await vc.disconnect()

    # Join Stage muted
    await stage_channel.connect(self_deaf=True, self_mute=True)

@bot.event
async def on_stage_instance_delete(stage_instance: discord.StageInstance):
    print("🎤 Stage ended:", stage_instance.topic)
    guild = stage_instance.guild
    channel = discord.utils.get(guild.voice_channels, name=ELEVATOR_CHANNEL_NAME)
    if channel:
        await channel.connect(self_deaf=False, self_mute=False)

bot.run(TOKEN)
