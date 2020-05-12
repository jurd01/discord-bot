from json import JSONDecodeError

import client
import os

import requests

token = None


def _get_token_from_api():
    params = {
        'client_id': client.client_id,
        'client_secret': client.secret,
        'grant_type': 'client_credentials',
    }
    data = requests.post('https://id.twitch.tv/oauth2/token', params=params).json()
    # logger.debug(data)
    with open('./token', 'w') as f:
        f.write(data['access_token'])
    return data['access_token']


def _get_token_from_file():
    line = None
    if os.path.exists('./token'):
        with open('./token', 'r') as f:
            line = f.readline()

    if line:
        return line.replace('\n', '').replace('\r', '')
    return None


def refresh_token():
    global token
    token = _get_token_from_api()
    return token


def make_request(url, method, params=None, body=None, expected_code=requests.codes.ok, retry=0):
    global token
    if retry >= 3:
        raise Exception("Cannot authenticate.")  # TODO

    if not token:
        token = _get_token_from_file()
        if not token:
            token = refresh_token()

    headers = {
        'Authorization': f'Bearer {token}'
    }
    headers.update(client.auth)
    print(headers)

    r = method(url, headers=headers, params=params, json=body)

    if r.status_code == requests.codes.unauthorized:
        print(r.json())
        refresh_token()
        make_request(url, method, params, body, retry + 1)

    elif r.status_code != expected_code:
        # try:
        #     logger.error(r.json())
        # except JSONDecodeError:
        #     logger.error(r.content)
        raise Exception(f'Received status code {r.status_code} but expected {expected_code}')

    if r.content:
        return r.json()
