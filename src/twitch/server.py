import json
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


from src.twitch.client import Client
from src.util.logging import get_logger

logger = get_logger(__name__)

CONTENT_LENGTH = 'Content-Length'
CONTENT_TYPE = 'Content-Type'
X_HUB_SIGNATURE = 'X-Hub-Signature'

HOST_NAME = '0.0.0.0'
HOST_PORT = 65535

secret = None


class RequestHandler(BaseHTTPRequestHandler):
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
            logger.info("Challenge-response complete.")
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

        expected_hash = hmac.new(secret.encode(), post_data, algorithm)
        if not hmac.compare_digest(received_hash.encode(), expected_hash.hexdigest().encode()):
            raise ConnectionError('Hash mismatch.')

        j = json.loads(post_data)
        data = j['data'][0]
        stream_status = data['stream_status']
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
        logger.debug(j)

        # TODO discord bot send message

        self.send_response(200)
        self.end_headers()


class Server:

    def __init__(self):
        self.client = Client()

        global secret
        secret = self.client.client_secret

    def start(self):

        twitch_id = self.client.get_user_id('stabbystabby')
        self.client.subscribe_to_live_notifications(twitch_id)

        server = HTTPServer((HOST_NAME, HOST_PORT), RequestHandler)
        try:
            server.serve_forever()
            logger.info('Server started')

        except KeyboardInterrupt:
            server.server_close()
            logger.info('Server closing')

