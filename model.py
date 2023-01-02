import discord
import telegram
import datetime
from dataclasses import dataclass


@dataclass
class UserState:
    id: int
    name: str
    afk: bool
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    self_stream: bool
    self_video: bool
    # suppress: bool
    # requested_to_speak_at: datetime


def discord_member_to_user(member: discord.Member):
    return UserState(member.id, member.name, member.voice.afk, member.voice.deaf, member.voice.mute,
                     member.voice.self_deaf, member.voice.self_mute,
                     member.voice.self_stream, member.voice.self_video)


def build_user_string(user: UserState):
    def status(s: bool):
        return "◻️" if s else "◼"

    text = ''
    mic = not (user.mute or user.self_mute)
    headset = not (user.deaf or user.self_deaf)
    video = user.self_video
    stream = user.self_stream

    text += status(mic)
    text += status(headset)
    text += status(video)
    text += status(stream)
    text += user.name
    return text


def build_users_string(users: []):
    text = ''
    if len(users) != 0:
        text += f'Users:\n'
        text += '🎤🎧📷🖵\n'
        users_string = '\n'.join(map(build_user_string, users))
        text += f'{users_string}'
    return text


def build_message_string(server_name: str, channel_name: str, started: datetime, ended=None, connected_users=None):
    text = ''
    text += f'Server: {server_name}\n'
    text += f'Channel: {channel_name}\n'
    text += f'Started: {started.strftime("%H:%M:%S %d.%m.%Y")}\n'
    if ended is not None:
        text += f'Ended: {ended.strftime("%H:%M:%S %d.%m.%Y")}\n'
    else:
        text += build_users_string(connected_users)
    return text


class TelegramMessage:
    def __init__(self, api: telegram.Bot, chat_id: str, server_name: str, channel_name: str, started: datetime,
                 connected_users=None):
        self.api = api
        self.chat_id = chat_id
        text = build_message_string(server_name=server_name, channel_name=channel_name, started=started,
                                    connected_users=connected_users)
        self.message_id = self.api.sendMessage(chat_id=chat_id, text=text).message_id

    def set_content(self, connected_users, server_name: str, channel_name: str, started: datetime, ended=None):
        text = build_message_string(server_name=server_name, channel_name=channel_name, started=started,
                                    ended=ended, connected_users=connected_users)
        self.api.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=text)


class VoiceSession:
    def __init__(self, server_name: str, channel_name: str, telegram_api, telegram_chat_id, connected_members=None):
        self.server_name = server_name
        self.channel_name = channel_name
        self.started = datetime.datetime.now()
        self.ended = None
        self.connected_members = {}
        if connected_members is not None:
            for u in connected_members:
                self.connected_members[u.id] = u
        self.telegram_message = TelegramMessage(api=telegram_api, chat_id=telegram_chat_id, started=self.started,
                                                server_name=server_name,
                                                channel_name=self.channel_name,
                                                connected_users=self.connected_members.values())
        self.dead = False

    def user_connected(self, user_id: int, user: UserState):
        self.connected_members[user_id] = user
        self.telegram_message.set_content(self.connected_members.values(), self.server_name, self.channel_name,
                                          self.started, self.ended)

    def user_updated(self, user_id: int, user: UserState):
        self.connected_members[user_id] = user
        self.telegram_message.set_content(self.connected_members.values(), self.server_name, self.channel_name,
                                          self.started, self.ended)

    def user_disconnected(self, user_id: int):
        del self.connected_members[user_id]
        if len(self.connected_members) == 0:
            self.ended = datetime.datetime.now()
            self.dead = True
        self.telegram_message.set_content(self.connected_members.values(), self.server_name, self.channel_name,
                                          self.started, self.ended)


class SessionManager:
    def __init__(self, telegram_api: telegram.Bot, telegram_chat_id: str):
        self.sessions = {}
        self.telegram_api = telegram_api
        self.telegram_chat_id = telegram_chat_id

    def create_session(self, channel):
        if len(channel.members) != 0:
            self.sessions[channel.id] = VoiceSession(server_name=f'{channel.guild.name}',
                                                     channel_name=f'{channel.name}',
                                                     telegram_api=self.telegram_api,
                                                     telegram_chat_id=self.telegram_chat_id,
                                                     connected_members=list(
                                                         map(discord_member_to_user, channel.members)))

    def member_connected(self, channel: discord.VoiceChannel, member: discord.Member):
        if channel.id not in self.sessions:
            self.create_session(channel)
        else:
            self.sessions[channel.id].user_connected(member.id, discord_member_to_user(member))

    def user_updated(self, user: discord.User):
        for guild in user.mutual_guilds:
            for member in guild.members:
                if member.id == user.id:
                    self.sessions[member.voice.channel.id].user_updated(member.id, discord_member_to_user(member))
                    return

    def member_voice_updated(self, channel: discord.VoiceChannel, member: discord.Member):
        if channel.id in self.sessions:
            self.sessions[channel.id].user_updated(member.id, discord_member_to_user(member))

    def member_disconnected(self, channel: discord.VoiceChannel, member: discord.Member):
        self.sessions[channel.id].user_disconnected(member.id)
        if self.sessions[channel.id].dead:
            del self.sessions[channel.id]
