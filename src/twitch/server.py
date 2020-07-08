from http.server import HTTPServer
from socketserver import ThreadingMixIn

from src.abc.service import Service
from src.discord_client.discord_client import DiscordClient
from src.twitch.twitchclient import TwitchClient
from src.util.constants import HOST_NAME, HOST_PORT, SUBSCRIPTIONS
from src.twitch.request_handler import RequestHandlerFactory
from src.util.logging import get_logger

logger = get_logger(__name__)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class Server(Service):
    def __init__(self, client: TwitchClient, discord_bot: DiscordClient):
        self.client = client
        request_handler_class = RequestHandlerFactory.build(client, discord_bot)
        self.server = ThreadedHTTPServer((HOST_NAME, HOST_PORT), request_handler_class)

    def run(self):
        streamer_names = set([sub.user_name for sub in SUBSCRIPTIONS])
        twitch_ids = {username: self.client.get_user_id(username) for username in streamer_names}
        for username, twitch_id in twitch_ids.items():
            logger.info(f'Sending webhook subscription request for {username}')
            self.client.subscribe_to_live_notifications(twitch_id)

        self.server.serve_forever()
        logger.info('Server started')

    def shutdown(self):
        self.server.shutdown()
        logger.info('Server shut down.')
