import threading

from src.discord_bot.discord_client import DiscordClient
from src.util.constants import TWITCH_CLIENT_SECRET, TWITCH_CLIENT_ID, DISCORD_BOT_TOKEN, COMMAND_PREFIX
from src.twitch.twitchclient import TwitchClient
from src.twitch.server import Server
from src.util.logging import get_logger

logger = get_logger(__name__)


class Bot:
    def __init__(self):
        client = TwitchClient(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
        bot = DiscordClient(DISCORD_BOT_TOKEN, COMMAND_PREFIX, client)
        server = Server(client, bot)

        self.services = [bot, server]
        self.threads = []

    def _start(self):
        for service in self.services:
            thread = threading.Thread(target=service.run,
                                      name=f"start {service.__class__.__name__}")
            thread.start()
            self.threads.append(thread)

    def _shutdown(self):
        for service in self.services:
            thread = threading.Thread(target=service.shutdown,
                                      name=f"shutdown {service.__class__.__name__}")
            thread.start()
            self.threads.append(thread)

    def _join(self, timeout=None):
        for thread in self.threads:
            thread.join(timeout)

    def run(self):
        try:
            self._start()
            self._join()
        except KeyboardInterrupt:
            # defer to finally block
            pass
        except Exception as e:
            logger.exception(e)
        finally:
            self._shutdown()
            self._join(5)

