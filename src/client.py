import http.client
import json
import urllib.request
import hashlib

import requests

from oauth import make_request


def get_external_ip():
    return requests.get('https://api.ipify.org').text


# connection = http.client.HTTPSConnection('api.twitch.tv')
client_id = '936qcw2vc0rld477y9qd6uly3v0ejo'
auth = {
    'Client-ID': client_id
    # 'Authorization': 'Bearer {}'
}
secret = 'f8zjdmgctwfpo58t4zq1utxsbfxqvf'
lease_seconds = 300
callback = f'http://{get_external_ip()}:65535/'
print(callback)


def get_user_id(login_name):
    data = make_request(f'https://api.twitch.tv/helix/users?login={login_name}', requests.get)
    print(data)
    user_id = data.get('data')[0].get('id')
    # logger.info(f'Found user id {user_id}')
    return user_id


def subscribe_to_get_followers(user_id):
    headers = {'Content-type': 'application/json'}.update(auth)

    topic = f'https://api.twitch.tv/helix/users/follows?first=1&to_id={user_id}'

    foo = {
        'hub.mode': 'subscribe',
        'hub.topic': topic,
        'hub.callback': callback,
        'hub.lease_seconds': lease_seconds,
        'hub.secret': secret
    }

    response = make_request('https://api.twitch.tv/helix/webhooks/hub', requests.post, body=foo, expected_code=requests.codes.accepted)
    print('subscription successful')








