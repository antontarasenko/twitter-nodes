import json
import re
from urllib.parse import parse_qs

import requests
from requests_oauthlib import OAuth1
from pip.backwardcompat import raw_input


REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
STATUSES_FILTER_URL = "https://stream.twitter.com/1.1/statuses/filter.json"

# Change these in config.py
TW_API_KEY = ""
TW_API_SECRET = ""
TW_ACCESS_TOKEN = ""
TW_TOKEN_SECRET = ""

from twitternodes.config import *


class Stream:
    def __init__(self):
        self.tweets = list()
        self.tracked = list()

    def setup_oauth(self):
        """Authorize your app via identifier."""
        # Request token
        oauth = OAuth1(client_key=TW_API_KEY, client_secret=TW_API_SECRET)
        r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
        credentials = parse_qs(r.content)

        resource_owner_key = credentials.get('oauth_token')[0]
        resource_owner_secret = credentials.get('oauth_token_secret')[0]

        # Authorize
        authorize_url = AUTHORIZE_URL + resource_owner_key
        print('Please go here and authorize: ' + authorize_url)

        verifier = raw_input('Please enter the verifier: ')
        oauth = OAuth1(client_key=TW_API_KEY,
                       client_secret=TW_API_SECRET,
                       resource_owner_key=resource_owner_key,
                       resource_owner_secret=resource_owner_secret,
                       verifier=verifier)

        # Finally, Obtain the Access Token
        r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
        credentials = parse_qs(r.content)
        token = credentials.get('oauth_token')[0]
        secret = credentials.get('oauth_token_secret')[0]

        return token, secret


    def get_oauth(self):
        oauth = OAuth1(client_key=TW_API_KEY,
                       client_secret=TW_API_SECRET,
                       resource_owner_key=TW_ACCESS_TOKEN,
                       resource_owner_secret=TW_TOKEN_SECRET)
        return oauth


    def fetch_live(self, n=100, track="", params={}):
        """
        Populate self.tweets with more tweets. Return the list of just fetched tweets.
        :param n: Max number of tweets
        :param track: Keywords, like "#tags" or "@mentions"
        :param params: See https://dev.twitter.com/docs/streaming-apis/parameters
        :return:
        """
        self.tracked.append(track)
        payload = {}
        if len(track) > 0: payload.update({'track': track}.items())
        payload.update(params.items())
        r = requests.get(url=STATUSES_FILTER_URL,
                         auth=self.get_oauth(),
                         stream=True, params=payload)
        print("Fetching...")
        s = 0
        for c, tweet in enumerate(r.iter_lines()):
            if c >= n: break
            if tweet:
                # TODO remove dict to dict conversion
                try:
                    self.tweets.append({k: v for k, v in json.loads(tweet.decode("utf-8")).items()})
                    s += 1
                    if (s % 10 == 0): print("%d tweets fetched" % s)
                except:
                    pass
        print("Streaming of %d/%d tweets for '%s' is completed" % (s, n, re.sub(r"([^\w_])+", "", track)))
        r.connection.close()
        return self.tweets[-s::]


    def save_tweets(self, saveas=""):
        """
        Save fetched tweets to a json file.
        :param saveas:
        :return:
        """
        file = saveas if len(saveas) > 0 else "stream-%d.json" % len(self.tweets)
        with open(file, "w") as f:
            json.dump(self.tweets, f)
        print("Saved to", file)
        return file
