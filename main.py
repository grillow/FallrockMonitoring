import discord
import telegram
import model
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram

tg = telegram.Bot(token=os.getenv('TELEGRAM_TOKEN'))

# Discord

dd = discord.Client(self_bot=True)

session_manager = model.SessionManager(telegram_api=tg, telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID'))


@dd.event
async def on_ready():
    print(f'Logged in as {dd.user}')
    for guild in dd.guilds:
        for channel in guild.voice_channels:
            session_manager.create_session(channel)


@dd.event
async def on_user_update(before: discord.User, after: discord.User):
    # when name changes
    session_manager.user_updated(after)


@dd.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel is None and after.channel is not None:
        session_manager.member_connected(after.channel, member)
    elif before.channel is not None and after.channel is None:
        session_manager.member_disconnected(before.channel, member)
    elif before.channel is not None and after.channel is not None:
        if before.channel != after.channel:
            session_manager.member_disconnected(before.channel, member)
            session_manager.member_connected(after.channel, member)
        else:
            session_manager.member_updated(after.channel, member)


dd.run(os.getenv('DISCORD_TOKEN'))
