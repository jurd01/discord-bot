import asyncio
import hmac
import json
from http.server import BaseHTTPRequestHandler
from multiprocessing.pool import Pool
from urllib.parse import urlparse, unquote

from src.util.constants import CONTENT_LENGTH, CONTENT_TYPE, X_HUB_SIGNATURE, TWITCH_CLIENT_SECRET
from src.util.dataclasses import Notification
from src.util.logging import get_logger

logger = get_logger(__name__)


# pythonic?
class RequestHandlerFactory:
    @staticmethod
    def build(client, discord_bot):
        class RequestHandler(BaseHTTPRequestHandler):

            def __init__(self, *args, **kwargs):
                self.client = client
                self.discord_bot = discord_bot
                super(RequestHandler, self).__init__(*args, **kwargs)

            def log_message(self, format, *args):
                logger.debug(format % args)

            def _get_query_components(self, path):
                return dict(qc.split('=') for qc in urlparse(path).query.split('&'))

            def do_GET(self):
                """
                Handle the incoming challenge-response from Twitch to confirm webhook.

                :return:
                """
                query_components = self._get_query_components(self.path)
                challenge = query_components.get('hub.challenge')
                if challenge:
                    logger.info(f'Received challenge with query: {query_components}.')
                    self.send_response(200, None)
                    self.end_headers()
                    self.wfile.write(bytes(challenge, 'utf-8'))

                    user_id = self._get_query_components(unquote(query_components['hub.topic']))['user_id']
                    user_name = self.client.get_user_name(user_id)
                    logger.info(f"Challenge-response complete. Subscription confirmed for user {user_name}.")
                else:
                    self.send_response(200, None)
                    self.end_headers()
                    self.wfile.write(bytes('howdy stranger :)', 'utf-8'))

            def do_POST(self):
                """
                Handle the incoming webhook payload and send a notification if stream is live.

                :return:
                """
                expected_headers = [CONTENT_LENGTH, CONTENT_TYPE, X_HUB_SIGNATURE]

                if not all(header in self.headers for header in expected_headers):
                    raise ValueError('Missing headers.')

                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                content_type = str(self.headers['Content-Type'])    # unused
                hub_signature = str(self.headers['X-Hub-Signature'])
                algorithm, received_hash = hub_signature.split('=')
                logger.debug(f'Message received with hash: {received_hash} and algorithm {algorithm}')

                expected_hash = hmac.new(TWITCH_CLIENT_SECRET.encode(), post_data, algorithm)
                if not hmac.compare_digest(received_hash.encode(), expected_hash.hexdigest().encode()):
                    raise ConnectionError('Hash mismatch.')

                j = json.loads(post_data)
                logger.info(j)
                if j and j['data']:
                    notif = Notification(**j['data'][0])
                    if notif.type == 'live':
                        logger.info(
                            f'User: {notif.user_name} went live with title: {notif.title}; game: {notif.game_id}')
                        loop = asyncio.get_event_loop()
                        if not loop:
                            loop = asyncio.new_event_loop()
                        asyncio.run_coroutine_threadsafe(self.discord_bot.send_live_notif(notif), loop)
                else:
                    logger.info('Stream ended.')  # TODO strikethrough stream message
                self.send_response(200)
                self.end_headers()
        return RequestHandler


""" example live response
{
'data': [{
'id': '0123456789',
'user_id': '5678',
'user_name': 'wjdtkdqhs',
'game_id': '21779',
'community_ids': [],
'type': 'live',
'title': 'Best Stream Ever',
'viewer_count': 417,
'started_at': '2017-12-01T10:09:45Z',
'language': 'en',
'thumbnail_url': 'https://link/to/thumbnail.jpg'
}]
}


example offline response
{'data': []}
"""
