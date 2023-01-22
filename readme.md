# FallrockMonitoring

Notify about Discord voice activity via Telegram.

Environment variables:

```shell
DISCORD_TOKEN=DISCORDTOKEN
DISCORD_GUILD_IDS=123,456
TELEGRAM_TOKEN=TELEGRAMTOKEN
TELEGRAM_CHAT_ID=123
```

If ```DISCORD_GUILD_IDS``` is not set, all joined guilds will be monitored

run:

```shell
python -m venv venv
pip install -r requirements.txt
python main.py
```
