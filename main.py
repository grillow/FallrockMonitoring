import discord
import telegram
import model
import os

discord_token = os.getenv('DISCORD_TOKEN')
discord_guild_ids = os.getenv('DISCORD_GUILD_IDS')
if discord_guild_ids is None:
    discord_guild_ids = set()
else:
    discord_guild_ids = set(map(int, (os.getenv('DISCORD_GUILD_IDS') or '').replace(' ', '').split(',')))
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

tg = telegram.Bot(token=telegram_token)
dd = discord.Client(self_bot=True)

session_manager = model.SessionManager(telegram_api=tg, telegram_chat_id=telegram_chat_id)


@dd.event
async def on_ready():
    print(f'Logged in as {dd.user}')
    await dd.change_presence(status=discord.Status.offline)
    for guild in dd.guilds:
        if len(discord_guild_ids) == 0 or guild.id in discord_guild_ids:
            for channel in guild.voice_channels:
                await session_manager.create_session(channel)


@dd.event
async def on_user_update(before: discord.User, after: discord.User):
    await session_manager.user_updated(after)


@dd.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel is None and after.channel is not None:
        if len(discord_guild_ids) == 0 or after.channel.guild.id in discord_guild_ids:
            await session_manager.member_connected(after.channel, member)
    elif before.channel is not None and after.channel is None:
        if len(discord_guild_ids) == 0 or before.channel.guild.id in discord_guild_ids:
            await session_manager.member_disconnected(before.channel, member)
    elif before.channel is not None and after.channel is not None:
        if before.channel != after.channel:
            if len(discord_guild_ids) == 0 or before.channel.guild.id in discord_guild_ids:
                await session_manager.member_disconnected(before.channel, member)
            if len(discord_guild_ids) == 0 or after.channel.guild.id in discord_guild_ids:
                await session_manager.member_connected(after.channel, member)
        else:
            if len(discord_guild_ids) == 0 or after.channel.guild.id in discord_guild_ids:
                await session_manager.member_voice_updated(after.channel, member)


dd.run(discord_token)
