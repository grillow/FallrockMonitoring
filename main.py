import discord
import telegram
import model
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram

tg = telegram.Bot(token=os.getenv('TELEGRAM_TOKEN'))

# Discord

intents = discord.Intents.none()
intents.voice_states = True
intents.guilds = True
dd = discord.Client(intents=intents)

sessions = {}


@dd.event
async def on_ready():
    print(f'Logged in as {dd.user}')
    for guild in dd.guilds:
        for voice in guild.voice_channels:
            if len(voice.members) != 0:
                sessions[voice.id] = model.VoiceSession(voice_name=voice.name, telegram_api=tg,
                                                        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                                                        connected_users=set(map(str, voice.members)))


@dd.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    voice_old = None
    voice_new = None

    if before.channel is None and after.channel is not None:
        voice_old = None
        voice_new = after.channel
    elif before.channel is not None and after.channel is None:
        voice_old = before.channel
        voice_new = None
    elif before.channel is not None and after.channel is not None:
        voice_old = before.channel
        voice_new = after.channel

    if voice_old is not None:
        sessions[voice_old.id].user_disconnected(str(member))
        if sessions[voice_old.id].dead:
            del sessions[voice_old.id]
    if voice_new is not None:
        if voice_new.id not in sessions:
            sessions[voice_new.id] = model.VoiceSession(voice_name=voice_new.name, telegram_api=tg,
                                                        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'),
                                                        connected_users=set(map(str, voice_new.members)))
        else:
            sessions[voice_new.id].user_connected(str(member))


dd.run(os.getenv('DISCORD_TOKEN'))
