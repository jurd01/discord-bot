import os
from csv import DictReader

from src.util.dataclasses import Subscription

SUBSCRIPTIONS = []

# do not catch exception
_sub_file = os.path.join(os.path.dirname(__file__), 'servers.csv')
with open(_sub_file, newline='') as f:
    reader = DictReader(f)
    for line in reader:
        line = {k: int(v) if v.isnumeric() else v for k, v in line.items()}
        SUBSCRIPTIONS.append(Subscription(**line))

CONTENT_LENGTH = 'Content-Length'
CONTENT_TYPE = 'Content-Type'
X_HUB_SIGNATURE = 'X-Hub-Signature'

HOST_NAME = '0.0.0.0'
HOST_PORT = int(os.getenv('HOST_PORT'))
LEASE_SECONDS = 864000  # 864000 seconds = 10 days = max

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

COMMAND_PREFIX = "!"

DISCORD_FORMATTING_CHARS = ['*', '_', '~', '`', '>']
