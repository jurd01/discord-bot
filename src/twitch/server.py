from http.server import HTTPServer

from src.util.constants import HOST_NAME, HOST_PORT, SUBSCRIBE_TO_LIVE_NOTIFS_NAMES
from src.twitch.request_handler import RequestHandlerFactory
from src.util.logging import get_logger

logger = get_logger(__name__)


class Server:
    def __init__(self, client, discord_bot):
        self.client = client
        request_handler_class = RequestHandlerFactory.build(client, discord_bot)
        self.server = HTTPServer((HOST_NAME, HOST_PORT), request_handler_class)

    def run(self):
        twitch_ids = {username: self.client.get_user_id(username) for username in SUBSCRIBE_TO_LIVE_NOTIFS_NAMES}
        for username, twitch_id in twitch_ids.items():
            logger.info(f'Sending webhook subscription request for {username}')
            self.client.subscribe_to_live_notifications(twitch_id)

        self.server.serve_forever()
        logger.info('Server started')

    def shutdown(self):
        self.server.shutdown()
        logger.info('Server shut down.')
