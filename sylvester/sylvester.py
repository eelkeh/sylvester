import requests 
#from requests_oauthlib import OAuth1
from requests.exceptions import ConnectionError
from itertools import cycle
import unittest 
from time import sleep
import datetime
import time
import sqlite3
import json
from pprint import pprint

BASE_URL = u'https://api.twitter.com/1.1/'
WINDOW = 15 * 60

conn = sqlite3.connect('locks.db')
conn.isolation_level = None
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS locks
         (key text, uri text, release integer, UNIQUE(key, uri) ON CONFLICT REPLACE)""")


def create_client_pool(keys):
    return Pool(keys)


def create_client_pool_from_json():
    try:
        with open('keys.json') as keys_json:
            keys = json.load(keys_json)['keys']
            return Pool(keys)
    except IOError:
        raise ConfigurationError("You seem to have no keys.json file configured\
                    in the current dir. Please refer to the documentation.")


class ConfigurationError(Exception):
    pass

class PoolExpired(Exception):
    pass

class RateLimitExceeded(Exception):
    pass

class TwitterError(Exception):
    pass

class Pool:

    def _get_bearer_token(self, key):
        """ Implements Twitters 'Application-only authentication'
        Get a 'bearer token' from a key pair to send along each request, 
        with this token it's no longer neccessary to sign each request. 

        @see https://dev.twitter.com/docs/auth/application-only-auth

        Note: There's no user context when issuing requests via this route.
        """
    
        url = 'https://api.twitter.com/oauth2/token'
        r = requests.post(url, data='grant_type=client_credentials', 
                    auth=(key['client_key'], key['client_secret']))
        if r.status_code in (200, 304):
            self.bearer_tokens.append(r.json()['access_token'])


    def _next_token(self):
        """ Fast forward to the next bearer token in the list """ 
        self.current_bearer = self.bearer_tokens.next()
        return self.current_bearer

    def __init__(self, keys):
        """ Init takes a list of keys and sets up the request pool """ 
        self.keys = keys
        self.bearer_tokens = []
        # Get bearer tokens for all keys
        for key in self.keys:
            self._get_bearer_token(key)

        self.bearer_tokens = cycle(self.bearer_tokens)
        self.current_bearer = self.bearer_tokens.next()

    def _lock_current_token(self, uri, release):
        """ Look the current bearer token """
        cursor.execute("INSERT INTO locks VALUES (?,?,?)", 
                        (self.current_bearer, uri, release))

    def _release_current_token(self, uri):
        """ Release the current bearer token """
        cursor.execute("DELETE FROM locks WHERE key = ?\
                        AND uri = ?", (self.current_bearer, uri))
   

    def request(self, uri, params):
        """
        Twitter API request

        For error codes, see https://dev.twitter.com/docs/error-codes-responses
        """
        cursor.execute("SELECT release FROM locks WHERE key = ?\
                        AND uri = ?", (self.current_bearer, uri))
        locked = cursor.fetchone()

        if locked and (locked[0] - int(time.time())) > 0:
            # @TODO Don't sleep(1) but "sleep" the key until it's released
            print "Sleeping key/method %s %s" % (self.current_bearer, uri)
            sleep(1)
            # Cycle to the next key, and reset the request
            self._next_token()
            self.request(uri, params)
        elif locked:
            self._release_current_token(uri)
        
        # Set up the request
        url = u'%s%s' % (BASE_URL, uri)
        header = {'Authorization': 'Bearer %s' % self.current_bearer}
        
        try:
            print "Twitter API request: %s" % url
            r = requests.get(url, headers=header, params= params, timeout= 10)
        except ConnectionError as e:
            print e
            raise

        # Not sure when this header returns, so check for it 
        # regardless of the REST status_code, which we'll catch later
        remaining_str = r.headers.get('x-rate-limit-remaining')
        print "%s requests remaining for %s %s" % (remaining_str, self.current_bearer, uri)
        
        if (remaining_str is not None and int(remaining_str) == 0)\
            or r.status_code == 429:
            # Rate limit has been exceeded, lock this key
            release = int(r.headers['x-rate-limit-reset'])
            self._lock_current_token(uri, release)
        
        if r.status_code in (200, 304):
            return r.json()
        elif r.status_code == 429:
            raise TwitterError(r.status_code, r.json())
        elif r.status_code in (400, 401, 403, 404, 406, 420, 
                                422, 500, 502, 503, 504):
            raise TwitterError(r.status_code, r.json())
        else:
            raise TwitterError(r.status_code, "Unknown error")
        

    def _gen_max_id_list(self, uri, params):
        """ Generator to walk through Twitter lists that require multiple requests
        and that use the max_id param to place the cursor.

        @TODO Should this check for dupes? Does that defeat the purpose of the generator?
        """
        i = 0
        results = []
        while i == 0 or len(results) > 1:
            if i > 0: 
               params['max_id'] = min([t['id'] for t in results])
            results = self.request(uri, params)
            i += 1
            yield results    


    def  _gen_cursored_list(self, uri, params):
        """
        Generator to walk through cursored lists, yields a resultset until the list is exhausted 
        when no next_cursor is returned in the response.
        """
        i = 0
        next_cursor = None

        while i == 0 or next_cursor:
            if next_cursor:
                params['cursor'] = next_cursor
            
            results = self.request(uri, params)
            if results['next_cursor']:
                next_cursor = results['next_cursor']
            else:
                next_cursor = None
            i += 1
            yield results

    def get_friends(self, screen_name):
        """ 
        Returns a cursored collection of user IDs for every user 
        the specified user is following (otherwise known as their "friends"). 

        Results are given in groups of 5000
        """

        uri = u'friends/ids.json'
        params = {}

         # When the screen_name is an int, we assume that we're dealing 
        # with a user id instead of a screen_name (str)
        try:
            params['user_id'] = int(screen_name)
        except ValueError:
            params['screen_name'] = screen_name 

        for resultset in self._gen_cursored_list(uri, params):
            yield resultset['ids']


    def get_followers(self, screen_name):
        """
        Returns a cursored collection of user IDs for every user following the specified user.
        """
        uri = u'followers/ids.json'
        params = {}

        # When the screen_name is an int, we assume that we're dealing 
        # with a user id instead of a screen_name (str)
        try:
            params['user_id'] = int(screen_name)
        except ValueError:
            params['screen_name'] = screen_name 

        for resultset in self._gen_cursored_list(uri, params):
            yield resultset['ids']


    def get_timeline(self, screen_name, from_date=None, to_date=None):
        """
        https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline

        Generator that yields collections of tweets for a particular users
        timeline. Max number to yield is 200.
        By default this includes retweets and tweet entities

        Following the method provided here:
        https://dev.twitter.com/docs/working-with-timelines

        """
        uri = u'statuses/user_timeline.json'
        params = {
            'count': 200, 
            'include_entities': 1,
            'include_rts': 1,
        }

        # When the screen_name is an int, we assume that we're dealing 
        # with a user id instead
        try:
            params['user_id'] = int(screen_name)
        except ValueError:
            params['screen_name'] = screen_name        
        
        for resultset in self._gen_max_id_list(uri, params):
            yield resultset


    def get_users_lookup(self, users, idmode):
        """
        https://dev.twitter.com/docs/api/1.1/get/users/lookup

        Generator for "fully-hydrated" user objects (Twitter handles 
        up to 100 users per request), takes a list of screen names or 
        users id's. 
        Always returns a generator object, even when less than 100 ids 
        are provided!

        Arguments:
            users -- a list of user id's or screen_names, depends on idmode
            idmode -- either scree_name or user_id
        """

        uri = u'users/lookup.json'
        params = {}

        while len(users) > 0:
            slicel = users[0: min(len(users), 100)]
            users = filter(lambda x: x not in slicel, users) 
            params[idmode] = ",".join([unicode(u) for u in slicel])
            yield self.request(uri, params)

    
    def get_favorites_list(self, screen_name):
        """
        https://dev.twitter.com/docs/api/1.1/get/favorites/list

        Returns the 20 most recent Tweets favorited by the specified user.
        """
        uri = u'favorites/list.json'
        params = {
            'screen_name': screen_name,
            'count': 200,
            'include_entities': 1,
        }

        favs = self.request(uri, params)
        return favs


    def get_lists_memberships(self, screen_name):
        """
        https://dev.twitter.com/docs/api/1.1/get/lists/memberships

        Generator for the lists the specified user has been added to.
        A single API response contains 20 lists max. 
        """

        uri = u'lists/memberships.json'
        params = {
            'screen_name': screen_name
        }
        
        for resultset in self._gen_cursored_list(uri, params):
            yield resultset
        


    def get_lists(self, screen_name):
        """
        https://dev.twitter.com/docs/api/1.1/get/lists/list

        Returns all lists the users subscribes to, including their own
        There's no cursorring, it should return *all* lists
        """
        uri = u'lists/list'
        params = {
            'screen_name': screen_name
        }

        return self.request(uri, params)


def tweet_date_to_datetime(datestr):
    return datetime.strptime(datestr, '%a %b %d %H:%M:%S +0000 %Y')


class TwitterTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.test_name = 'UvA_Amsterdam'
        #cls.test_name = 'geertwilderspvv'
        print "Creating client pool..."
        cls.pool = create_client_pool_from_json()
        print "Done creating client pool!"

    def atest_timeline(self):
        tweets = []
        for tweetset in self.pool.get_timeline(self.test_name):
            tweets.extend(tweetset)
        
        self.assertEqual(tweets[0]['user']['screen_name'], self.test_name)
    
    def atest_friends(self):
        friends = []
        for friendset in self.pool.get_friends(self.test_name):
            friends.extend(friendset)

        print len(friends)

    def atest_followers(self):
        followers = []
        for followerset in self.pool.get_followers(self.test_name):
            followers.extend(followerset)

        print len(followers)

    def atest_favorites(self):
        favs = self.pool.get_favorites_list(self.test_name)
        print favs

    def test_get_users_lookup(self):
        ids = [783214,6253282]
        for resultset in self.pool.get_users_lookup(ids, 'user_id'):
            pprint(resultset)

if __name__ == "__main__":
    unittest.main()
