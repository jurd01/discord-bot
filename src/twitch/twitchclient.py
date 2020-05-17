import os

import requests

from src.util.constants import HOST_PORT, LEASE_SECONDS
from src.util.logging import get_logger

logger = get_logger(__name__)


class TwitchClient:
    def __init__(self, client_id, secret):
        self.client_id = client_id
        self.secret = secret
        self.token = None

    @staticmethod
    def _get_external_ip():
        return requests.get('https://api.ipify.org').text

    def _refresh_token(self):
        params = {
            'client_id': self.client_id,
            'client_secret': self.secret,
            'grant_type': 'client_credentials',
        }

        data = self._make_request('https://id.twitch.tv/oauth2/token', requests.post, params=params, use_token=False)
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

    def _make_request(self, url, method, params=None, body=None, expected_code=requests.codes.ok,
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

        logger.debug(f'Making {method.__name__.upper()} request to {url} with:'
                     f'headers: {headers}'
                     f'params: {params}'
                     f'body: {body}')

        r = method(url, headers=headers, params=params, json=body)

        if r.status_code == requests.codes.unauthorized:
            logger.error("Received 402 unauthorized. Refreshing token.")
            self._refresh_token()
            self._make_request(url, method, params, body, retry + 1)

        elif r.status_code != expected_code:
            # TODO exception
            # print(r.json())
            raise Exception(f'Received status code {r.status_code} but expected {expected_code}')

        if r.content:
            return r.json()

    def _get_user(self, user_id=None, user_name=None):
        if not (user_id or user_name):
            raise ValueError("user id or user name must not be null")
        params = {}
        if user_name:
            params['login'] = user_name
        if user_id:
            params['id'] = user_id
        return self._make_request('https://api.twitch.tv/helix/users', requests.get, params=params)['data'][0]

    def get_user_id(self, user_name):
        user_id = self._get_user(user_name=user_name).get('id')
        logger.info(f'Found user ID {user_id} for {user_name}')
        return user_id

    def get_user_name(self, user_id):
        user_name = self._get_user(user_id=user_id).get('login')
        logger.info(f'Found usesrname {user_name} for ID {user_id}')
        return user_name

    def get_game_name(self, game_id):
        logger.info(f'Getting game name for {game_id}')
        response = self._make_request(f'https://api.twitch.tv/helix/games', requests.get, params={'id': game_id})
        logger.debug(response)
        try:
            return response['data'][0]['name']
        except Exception as e:
            logger.exception(e)

    def subscribe_to_live_notifications(self, user_id):
        topic = f'https://api.twitch.tv/helix/streams?user_id={user_id}'
        callback = f'http://{self._get_external_ip()}:{HOST_PORT}/'
        logger.debug(f'Callback address: {callback}')
        body = {
            'hub.mode': 'subscribe',
            'hub.topic': topic,
            'hub.callback': callback,
            'hub.lease_seconds': LEASE_SECONDS,
            'hub.secret': self.secret
        }
        self._make_request('https://api.twitch.tv/helix/webhooks/hub', requests.post,
                           body=body, expected_code=requests.codes.accepted)
