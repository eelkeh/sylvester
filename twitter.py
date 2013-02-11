import requests 
from requests_oauthlib import OAuth1
import unittest 
from time import sleep
import datetime
import time
import sqlite3
import json
from itertools import cycle

conn = sqlite3.connect('locks.db')
conn.isolation_level = None
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS locks
             (key text, uri text, release integer, UNIQUE(key, uri) ON CONFLICT REPLACE)''')
pools = {}
blocked = {}

with open('keys.json') as keys_json:
    _keys = json.load(keys_json)['keys']
    
keys = cycle(_keys)
key = keys.next()

BASE_URL = u'https://api.twitter.com/1.1/'
WINDOW = 15 * 60

class PoolExpired(Exception):
    pass

class RateLimitExceeded(Exception):
    pass

class TwitterError(Exception):
    pass


def request(uri, params):
    """
    Twitter REST OAuth request
    Returns the requests response object
    Use r.json() to parse the results as a dict
        
        >>> response = twitter.request('help/configuration.json')
        >>> results = response.json()
        >>> response.status_code
        200
    """    
    global key
    
    # Is this particular key with the uri locked because it reached the rate limit?
    cursor.execute("SELECT release FROM locks WHERE key = ? AND uri = ?", (key['client_key'], uri))
    locked = cursor.fetchone()
    if locked:
        timetosleep = locked[0] - int(time.time()) 
        if timetosleep > 0:
            print timetosleep
            # @TODO Not so efficient, should sleep only when 
            sleep(1)

            # Try the next key
            key = keys.next()
            request(uri, params)
        else:
            cursor.execute("DELETE FROM locks WHERE key = ? AND uri = ?", (key['client_key'], uri))


    url = u'%s%s' % (BASE_URL, uri)
    oauth_sig = OAuth1(key['client_key'], client_secret= key['client_secret'],   
                    resource_owner_key= key['resource_owner_key'], 
                    resource_owner_secret= key['resource_owner_secret'],
                    signature_type='auth_header')

    print "Twitter API req: %s" % url

    r = requests.get(url, auth= oauth_sig, params= params, timeout= 10)
    # @TODO Error handling!
    # see https://dev.twitter.com/docs/error-codes-responses
    if r.status_code in (200, 304):
        remaining = int(r.headers['x-rate-limit-remaining'])
    # Lock this key/method when it reached the rate limit
        if remaining == 0:
            #release = #int(time.time()) + timeleft
            release = int(r.headers['x-rate-limit-reset'])
            cursor.execute("INSERT INTO locks VALUES (?,?,?)", (key['client_key'], uri, release))

    elif r.status_code in (400, 401, 403, 404, 406, 420, 422, 429, 500, 502, 503, 504):
        raise TwitterError(r.json()['errors'][0]['message'])
    else:
        raise TwitterError("Unknown error")
        
    return r


def get_rate_limits():
    pass

def get_friends(screen_name):
    """ 
    Returns a cursored collection of user IDs for every user 
    the specified user is following (otherwise known as their "friends"). 

    Results are given in groups of 5000
    """

    uri = u'friends/ids.json'
    params = {
        'screen_name': screen_name,
    }
    return request(uri, params)


def get_followers(screen_name):
    """
    Returns a cursored collection of user IDs for every user following the specified user.
    """
    uri = u'followers/ids.json'
    params = {}
    followers = []

    # When the screen_name is an int, we assume that we're dealing 
    # with a user id instead
    try:
        params['user_id'] = int(screen_name)
    except ValueError:
        params['screen_name'] = screen_name 

    def get_list():
        followers_list = request(uri, params).json()
        followers.extend(followers_list['ids'])
        
        if followers_list['next_cursor']:
            params['cursor'] = followers_list['next_cursor']
            get_list()
        
    get_list()

    return followers


def get_timeline(screen_name, from_date=None, to_date=None):
    """
    Returns a collection of tweets for a particular user
    Max number to return is 200
    Includes retweets and tweet entities

    Following method provided here:
    https://dev.twitter.com/docs/working-with-timelines

    """
    uri = u'statuses/user_timeline.json'
    params = {
        'count': 200, 
        'include_entities': 1,
        'include_rts': 1,
    }
    tweets = []

    # When the screen_name is an int, we assume that we're dealing 
    # with a user id instead
    try:
        params['user_id'] = int(screen_name)
    except ValueError:
        params['screen_name'] = screen_name        
    
    def get_list():
        tweet_list = request(uri, params).json()
        tweets.extend(tweet_list)

        # @TODO don't move the cursor when when more dates are parsed
        # if from_date and to_date:
        #    if from_date < tweet_date_to_datetime(tweet_list[0]['created_at']) < to_date:
        #

        # When the list is max length long (200), we assume that 
        # the cursor can be moved along
        if len(tweet_list) > 1:
            params['max_id'] = min([t['id'] for t in tweets])
            get_list()
        
    get_list()
    
    return tweets    

    
def get_favorites(screen_name):
    """
    Returns the 200 most recent Tweets favorited
    """
    uri = u'favorites/list.json'
    params = {
        'screen_name': screen_name,
        'count': 200,
        'include_entities': 1,
    }
    return request(uri, params)


def tweet_date_to_datetime(datestr):
    return datetime.strptime(datestr, '%a %b %d %H:%M:%S +0000 %Y')


class TwitterTestCase(unittest.TestCase):
    def setUp(self):
        self.test_name = 'geertwilderspvv'

    def test_timeline(self):
        tweets = get_timeline(self.test_name)
        self.assertEqual(tweets[0]['user']['screen_name'], self.test_name)

    def test_friends(self):
        friends = get_friends(self.test_name)
        self.assertEqual(friends.status_code, 200)

    def test_followers(self):
        followers = get_followers(self.test_name)
        self.assertEqual(followers.status_code, 200)

    def test_favorites(self):
        favorites = get_favorites(self.test_name)
        self.assertEqual(favorites.status_code, 200)


if __name__ == "__main__":
    cursor.execute("SELECT * FROM locks")
    print cursor.fetchall()

    for i in range(1,30):
        get_friends('ekborra')
    #unittest.main()
