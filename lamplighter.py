import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import json
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

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

os.makedirs(MUSIC_FOLDER, exist_ok=True)

current_track = {}  # Store current track index per guild

# Utility: get track titles
def get_track_title(filepath):
    try:
        audio = MP3(filepath, ID3=EasyID3)
        return audio.get("title", [os.path.basename(filepath)])[0]
    except:
        return os.path.basename(filepath)

def get_all_titles():
    return [get_track_title(os.path.join(MUSIC_FOLDER, f))
            for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3") or f.endswith(".wav")]

# Unmute helper
async def unmute_self(vc: discord.VoiceClient):
    await asyncio.sleep(0.5)
    bot_member = vc.guild.me
    await bot_member.edit(mute=False, deafen=False)
    print(f"✅ Bot unmuted in {vc.channel.name}")

# Music loop
async def play_music(vc: discord.VoiceClient, guild_id: int):
    global current_track
    while True:
        files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3") or f.endswith(".wav")]
        if not files:
            await asyncio.sleep(5)
            continue

        index = current_track.get(guild_id, 0)
        filepath = os.path.join(MUSIC_FOLDER, files[index])

        # Play with 68% volume
        vc.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filepath), volume=0.68))
        print(f"▶️ Playing: {get_track_title(filepath)}")
        while vc.is_playing():
            await asyncio.sleep(1)

        current_track[guild_id] = (index + 1) % len(files)

# /play command available everywhere
@app_commands.command(name="play", description="Play a track in Elevator")
@app_commands.describe(track="Choose the track")
@app_commands.checks.cooldown(1, 30)
async def play(interaction: discord.Interaction, track: str):
    guild = interaction.guild
    user_voice = interaction.user.voice
    if not user_voice or user_voice.channel.name != ELEVATOR_CHANNEL_NAME:
        await interaction.response.send_message(
            f"❌ You must be in the {ELEVATOR_CHANNEL_NAME} voice channel to use this command.",
            ephemeral=True
        )
        return

    vc = discord.utils.get(bot.voice_clients, guild=guild)
    if not vc:
        vc = await user_voice.channel.connect(self_deaf=False, self_mute=False)
        bot.loop.create_task(unmute_self(vc))

    files = [f for f in os.listdir(MUSIC_FOLDER) if f.endswith(".mp3") or f.endswith(".wav")]
    titles = [get_track_title(os.path.join(MUSIC_FOLDER, f)) for f in files]

    if track not in titles:
        await interaction.response.send_message(
            f"❌ Track not found. Available: {', '.join(titles)}", ephemeral=True)
        return

    index = titles.index(track)
    current_track[guild.id] = index
    if vc.is_playing():
        vc.stop()
    vc.play(discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(os.path.join(MUSIC_FOLDER, files[index])),
        volume=0.68
    ))
    await interaction.response.send_message(f"▶️ Now playing: {track}")

# Autocomplete for track selection
@play.autocomplete('track')
async def track_autocomplete(interaction: discord.Interaction, current: str):
    titles = get_all_titles()
    return [app_commands.Choice(name=t, value=t) for t in titles if current.lower() in t.lower()][:25]

bot.tree.add_command(play)

# Ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(status=discord.Status.idle,
                              activity=discord.Activity(type=discord.ActivityType.listening, name="music 🎶"))

    # Join Elevator in all guilds
    for guild in bot.guilds:
        channel = discord.utils.get(guild.voice_channels, name=ELEVATOR_CHANNEL_NAME)
        if channel:
            vc = await channel.connect(self_deaf=False, self_mute=False)
            bot.loop.create_task(unmute_self(vc))
            bot.loop.create_task(play_music(vc, guild.id))

    # Sync slash commands
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced!")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Stage events
@bot.event
async def on_stage_instance_create(stage_instance: discord.StageInstance):
    guild = stage_instance.guild
    for vc in bot.voice_clients:
        if vc.guild == guild:
            await vc.disconnect()
    await stage_instance.channel.connect(self_deaf=True, self_mute=True)

@bot.event
async def on_stage_instance_delete(stage_instance: discord.StageInstance):
    guild = stage_instance.guild
    channel = discord.utils.get(guild.voice_channels, name=ELEVATOR_CHANNEL_NAME)
    if channel:
        vc = await channel.connect(self_deaf=False, self_mute=False)
        bot.loop.create_task(unmute_self(vc))

bot.run(TOKEN)
s
