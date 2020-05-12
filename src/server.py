from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from urllib.parse import urlparse

import hmac
import json

import client

# wvmcwvubyojvenemtw
# oqyt9-5m8ptoaekldsfm


class Server(BaseHTTPRequestHandler):

    def do_GET(self):
        print('handling get')
        query = urlparse(self.path).query
        try:
            query_components = dict(qc.split('=') for qc in query.split('&'))
            challenge = query_components['hub.challenge']
        except:
            query_components = None
            challenge = None

        if challenge:
            s = ''.join(x for x in challenge if x.isdigit())
            print(s)
            print(challenge)
            self.send_response(200, None)
            self.end_headers()
            self.wfile.write(bytes(challenge, "utf-8"))
        else:
            self.send_response(200, None)
            self.end_headers()
            self.wfile.write(bytes("hello", "utf-8"))

    def do_POST(self):
        print('handlign post')
        if 'Content-Length' in self.headers:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

        if 'Content-Type' in self.headers:
            content_type = str(self.headers['Content-Type'])
        if 'X-Hub-Signature' in self.headers:
            hub_signature = str(self.headers['X-Hub-Signature'])
            algo, hsh = hub_signature.split('=')
            print(hsh)
            print(algo)

            secret = client.secret

            if post_data and algo and hsh:
                gg = hmac.new(secret.encode(), post_data, algo)
                if not hmac.compare_digest(hsh.encode(), gg.hexdigest().encode()):
                    raise ConnectionError("Hash mismatch.")

        if None in (content_length, content_type, hub_signature):
            raise ValueError("missing headers")

        if post_data:
            j = json.loads(post_data)
            userid = (j["data"][0]["from_id"])
            print(userid)
            print(j)
            self.send_response(200)
            self.end_headers()


def main():
    host_name = "0.0.0.0"
    host_port = 65535
    twitch_id = client.get_user_id('stabbystabby')
    # client.subscribe_to_get_followers(twitch_id)

    server = HTTPServer((host_name, host_port), Server)
    try:
        print('test')
        x = Thread(target=server.serve_forever)
        x.start()
        print("server started")

        client.subscribe_to_get_followers(twitch_id)

    except KeyboardInterrupt:
        server.server_close()
        print("server closing")


if __name__ == '__main__':
    main()