import threading
from typing import List, Iterable

from src.abc.service import Service
from src.discord_bot.discord_client import DiscordClient
from src.util.constants import TWITCH_CLIENT_SECRET, TWITCH_CLIENT_ID, DISCORD_BOT_TOKEN, COMMAND_PREFIX, \
    SUBSCRIPTIONS
from src.twitch.twitchclient import TwitchClient
from src.twitch.server import Server
from src.util.logging import get_logger

logger = get_logger(__name__)


def init(services: List[Service]):
    threads = []
    for service in services:
        thread = threading.Thread(target=service.run,
                                  name=f"start {service.__class__.__name__}")
        thread.start()
        threads.append(thread)
    return threads


def shutdown(services: List[Service]):
    threads = []
    for service in services:
        thread = threading.Thread(target=service.shutdown,
                                  name=f"shutdown {service.__class__.__name__}")
        thread.start()
        threads.append(thread)
    return threads


def join(threads: Iterable[threading.Thread], timeout: int = None):
    for thread in threads:
        thread.join(timeout)


def main():
    client = TwitchClient(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    bot = DiscordClient(DISCORD_BOT_TOKEN, COMMAND_PREFIX, client)
    server = Server(client, bot)

    services = [bot, server]
    threads = []
    try:
        threads.extend(init(services))
        join(threads)

    except KeyboardInterrupt:
        # defer to finally block
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        threads.extend(shutdown(services))
        join(threads, timeout=5)


if __name__ == "__main__":
    main()
