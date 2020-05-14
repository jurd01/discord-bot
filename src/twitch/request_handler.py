import asyncio
import hmac
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from src.util.constants import CONTENT_LENGTH, CONTENT_TYPE, X_HUB_SIGNATURE, TWITCH_CLIENT_SECRET
from src.util.logging import get_logger

logger = get_logger(__name__)


# pythonic?
class RequestHandlerFactory:
    @staticmethod
    def build(client, discord_bot):
        class RequestHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super(RequestHandler, self).__init__(*args, **kwargs)

                self.client = client
                self.discord_bot = discord_bot

            def log_message(self, format, *args):
                logger.debug(format % args)

            def do_GET(self):
                """
                Handle the incoming challenge-response from Twitch to confirm webhook.

                :return:
                """
                query = urlparse(self.path).query
                challenge = None
                try:
                    query_components = dict(qc.split('=') for qc in query.split('&'))
                    challenge = query_components['hub.challenge']
                except:
                    pass

                if challenge:
                    logger.info(f'Received challenge: {challenge}')
                    self.send_response(200, None)
                    self.end_headers()
                    self.wfile.write(bytes(challenge, 'utf-8'))
                    logger.info("Challenge-response complete. Subscription confirmed.")
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
                    # TODO don't error
                    raise ConnectionError('Hash mismatch.')

                j = json.loads(post_data)
                logger.info("")
                data = j['data'][0]
                stream_status = data['type']
                """ example response
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
                """
                logger.info(f'Received status: {stream_status}')
                logger.info(j)  # TODO debug

                if stream_status == 'live':
                    asyncio.create_task(self.discord_bot.send_live_notif(data))

                self.send_response(200)
                self.end_headers()

        return RequestHandler
