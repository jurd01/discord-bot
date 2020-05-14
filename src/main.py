import threading
import signal
import asyncio

from src.discord_bot.bot import Bot
from src.util.constants import TWITCH_CLIENT_SECRET, TWITCH_CLIENT_ID, DISCORD_BOT_TOKEN, COMMAND_PREFIX
from src.twitch.client import Client
from src.twitch.server import Server
from src.util.logging import get_logger

logger = get_logger(__name__)

server = None
bot = None

server_thread = None
bot_thread = None


def main():
    global server, bot, server_thread, bot_thread
    bot = Bot(DISCORD_BOT_TOKEN, COMMAND_PREFIX)
    client = Client(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    server = Server(client, bot)

    try:
        bot_thread = threading.Thread(target=bot.run)
        server_thread = threading.Thread(target=server.run)

        bot_thread.start()
        server_thread.start()

        bot_thread.join()
        server_thread.join()
    except KeyboardInterrupt:
        # defer to finally block
        pass
    except Exception as e:
        logger.error(f"Caught f{type(e)}: {e}")
        raise e
    finally:
        server_shut_thread = threading.Thread(target=server.shutdown)
        bot_shut_thread = threading.Thread(target=bot.shutdown)

        server_shut_thread.start()
        bot_shut_thread.start()

        server_shut_thread.join(1)
        bot_shut_thread.join(1)

        server_thread.join(5)
        bot_thread.join(5)


if __name__ == "__main__":
    main()
