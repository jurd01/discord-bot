import os

import requests

from src.config.config import parse_config
from src.util.logging import get_logger

logger = get_logger(__name__)


def get_external_ip():
    return requests.get('https://api.ipify.org').text


callback = f'http://{get_external_ip()}:65535/'
lease_seconds = 864000  # TODO refresh
secret = os.getenv('TWITCH_CLIENT_SECRET')
logger.debug(f'callback url: {callback}')


class Client:
    def __init__(self):
        self.client_id = "936qcw2vc0rld477y9qd6uly3v0ejo"
        self.token = None

    def _refresh_token(self):
        params = {
            'client_id': self.client_id,
            'client_secret': secret,
            'grant_type': 'client_credentials',
        }
        data = self.make_request('https://id.twitch.tv/oauth2/token', requests.post, params=params)
        logger.info('Got token from API')
        logger.debug(data)
        with open('./token', 'w') as f:
            f.write(data['access_token'])
        return data['access_token']

    def _get_token_from_file(self):
        line = None
        if os.path.exists('./token'):
            with open('./token', 'r') as f:
                line = f.readline()

        if line:
            self.token = line.replace('\n', '').replace('\r', '')

    def make_request(self, url, method, params=None, body=None, expected_code=requests.codes.ok, retry=0):
        """

        :param url:
        :param method:          requests.get or requests.post TODO constants
        :param params:
        :param body:
        :param expected_code:
        :param retry:
        :return:
        """
        if retry >= 3:
            # TODO exception
            raise Exception("Cannot authenticate.")

        if not self.token:
            self._get_token_from_file()
            if not self.token:
                self._refresh_token()

        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.token}'
        }

        r = method(url, headers=headers, params=params, json=body)

        if r.status_code == requests.codes.unauthorized:
            logger.error("Received 402 unauthorized. Refreshing token.")
            self._refresh_token()
            self.make_request(url, method, params, body, retry + 1)

        elif r.status_code != expected_code:
            # TODO exception
            raise Exception(f'Received status code {r.status_code} but expected {expected_code}')

        if r.content:
            return r.json()

    def get_user_id(self, login_name):
        logger.info(f'Getting user ID for {login_name}')
        data = self.make_request(f'https://api.twitch.tv/helix/users?login={login_name}', requests.get)
        user_id = data.get('data')[0].get('id')
        logger.info(f'Found user ID {user_id} for {login_name}')
        return user_id

    def subscribe_to_live_notifications(self, user_id):
        topic = f'https://api.twitch.tv/helix/streams?user_id={user_id}'
        body = {
            'hub.mode': 'subscribe',
            'hub.topic': topic,
            'hub.callback': callback,
            'hub.lease_seconds': lease_seconds,
            'hub.secret': secret
        }
        self.make_request('https://api.twitch.tv/helix/webhooks/hub', requests.post,
                          body=body, expected_code=requests.codes.accepted)
