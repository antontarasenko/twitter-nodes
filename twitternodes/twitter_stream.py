import json
import re
import requests
from requests_oauthlib import OAuth1
from urllib.parse import parse_qs
from pip.backwardcompat import raw_input

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
STATUSES_FILTER_URL = "https://stream.twitter.com/1.1/statuses/filter.json"

from config import *

def setup_oauth():
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


def get_oauth():
    oauth = OAuth1(client_key=TW_API_KEY,
                   client_secret=TW_API_SECRET,
                   resource_owner_key=TW_ACCESS_TOKEN,
                   resource_owner_secret=TW_TOKEN_SECRET)
    return oauth


def save_stream(n=100, track="", saveas="", params={}):
    file = saveas if len(saveas) > 0 else re.sub(r"([^\w_])+", "", track) + "-" + str(n) + ".json"
    payload = {'track': track}
    payload.update(params.items())
    r = requests.get(url=STATUSES_FILTER_URL,
                     auth=get_oauth(),
                     stream=True, params=payload)
    with open(file, "w") as f:
        tweets = list()
        for c, tweet in enumerate(r.iter_lines()):
            if c >= n: break
            if tweet:
                tweets += [{k: v for k, v in json.loads(tweet.decode("utf-8")).items()}]
                if (c % 10 == 0): print("%d tweets fetched" % c)
        json.dump(tweets, f)
    r.connection.close()