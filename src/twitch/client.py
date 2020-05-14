import os

import requests

from src.util.constants import HOST_PORT, LEASE_SECONDS
from src.util.logging import get_logger

logger = get_logger(__name__)


class Client:
    def __init__(self, client_id, secret):
        self.client_id = client_id
        self.secret = secret
        self.token = None

    @staticmethod
    def get_external_ip():
        return requests.get('https://api.ipify.org').text

    def _refresh_token(self):
        params = {
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'client_credentials',
        }

        # don't use make_request
        data = self.make_request('https://id.twitch.tv/oauth2/token', requests.post, params=params, use_token=False)
        logger.info('Got token from twitch API')
        logger.debug(data)
        with open('./token', 'w') as f:
            f.write(data['access_token'])

        self.token = data['access_token']

    def _get_token_from_file(self):
        line = None
        if os.path.exists('./token'):
            with open('./token', 'r') as f:
                line = f.readline()

        if line:
            self.token = line.replace('\n', '').replace('\r', '')

    def make_request(self, url, method, params=None, body=None, expected_code=requests.codes.ok,
                     use_token=True, retry=0):
        """

        :param url:
        :param method:      requests.get or requests.post TODO constants
        :param params:
        :param body:
        :param expected_code:
        :param use_token:
        :param retry:
        :return:
        """
        if retry >= 3:
            # TODO exception
            raise Exception("Cannot authenticate.")

        if use_token and not self.token:
            self._get_token_from_file()
            if not self.token:
                self._refresh_token()

        headers = {
            'Client-ID': self.client_id
        }
        if use_token:
            headers.update({'Authorization': f'Bearer {self.token}'})

        logger.debug(f'Making {method.__name__.upper()} request to {url} with:')
        logger.debug(f'headers: {headers}')
        logger.debug(f'params: {params}')
        logger.debug(f'body: {body}')
        r = method(url, headers=headers, params=params, json=body)

        if r.status_code == requests.codes.unauthorized:
            logger.error("Received 402 unauthorized. Refreshing token.")
            self._refresh_token()
            self.make_request(url, method, params, body, retry + 1)

        elif r.status_code != expected_code:
            # TODO exception
            print(r.json())
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
        callback = f'http://{self.get_external_ip()}:{HOST_PORT}/'
        logger.debug(f'Callback address: {callback}')
        body = {
            'hub.mode': 'subscribe',
            'hub.topic': topic,
            'hub.callback': callback,
            'hub.lease_seconds': LEASE_SECONDS,
            'hub.secret': self.secret
        }
        self.make_request('https://api.twitch.tv/helix/webhooks/hub', requests.post,
                          body=body, expected_code=requests.codes.accepted)
        logger.info('Webhook subscription request complete')
