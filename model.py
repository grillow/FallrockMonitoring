import telegram
import datetime


class TelegramMessage:
    def __init__(self, api: telegram.Bot, chat_id: str, voice_name, started, connected_users=None):
        self.api = api
        self.chat_id = chat_id
        text = f'Channel: {voice_name}\n'
        text += f'Started: {started.strftime("%H:%M:%S %d.%m.%Y")}\n'
        if connected_users is not None:
            users_string = '\n'.join(connected_users)
            text += f'Users:\n'
            text += f'{users_string}'
        self.message_id = self.api.sendMessage(chat_id=chat_id, text=text).message_id

    def set_content(self, connected_users, voice_name, started, ended):
        users_string = '\n'.join(connected_users)
        text = f'Channel: {voice_name}\n'
        text += f'Started: {started.strftime("%H:%M:%S %d.%m.%Y")}\n'
        if ended is not None:
            text += f'Ended: {ended.strftime("%H:%M:%S %d.%m.%Y")}\n'
        else:
            text += f'Users:\n'
            text += f'{users_string}'

        self.api.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=text)


class VoiceSession:
    def __init__(self, voice_name: str, telegram_api, telegram_chat_id, connected_users=None):
        self.voice_name = voice_name
        self.started = datetime.datetime.now()
        self.ended = None
        if connected_users is not None:
            self.connected_users = connected_users
        else:
            self.connected_users = set()
        self.telegram_message = TelegramMessage(api=telegram_api, chat_id=telegram_chat_id, started=self.started,
                                                voice_name=self.voice_name, connected_users=self.connected_users)
        self.dead = False

    def user_connected(self, user_id: str):
        self.connected_users.add(user_id)
        self.telegram_message.set_content(self.connected_users, self.voice_name, self.started, self.ended)

    def user_disconnected(self, user_id: str):
        self.connected_users.discard(user_id)
        if len(self.connected_users) == 0:
            self.ended = datetime.datetime.now()
            self.dead = True
        self.telegram_message.set_content(self.connected_users, self.voice_name, self.started, self.ended)
