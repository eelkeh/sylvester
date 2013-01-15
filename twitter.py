import requests 
import json
from os import path
from requests_oauthlib import OAuth1
from pprint import pprint
import unittest 

base_url = u'https://api.twitter.com/1.1/'

with open('keys.json') as keys_json:
    keys = json.load(keys_json)

class TwitterAPI:
    def __init__(self, keys):
        pass
    
    def request(self, url, parms):
        pass

def request(uri, params= None):
    """
    Twitter REST OAuth request
    Returns the requests response object
    Use r.json() to parse the results as a dict
        
        >>> response = twitter.request('help/configuration.json')
        >>> results = response.json()
        >>> response.status_code
        200
    """
    url = u'%s%s' % (base_url, uri)
    oauth_sig = OAuth1(keys['client_key'], client_secret= keys['client_secret'],   
                    resource_owner_key= keys['resource_owner_key'], 
                    resource_owner_secret= keys['resource_owner_secret'],
                    signature_type='auth_header')

    r = requests.get(url, auth= oauth_sig, params= params, timeout= 10)
    return r


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
    params = {
        'screen_name': screen_name
    }
    followers = []

    def get_list():
        followers_list = request(uri, params).json()
        pprint(followers_list)
        followers.extend(followers_list['ids'])
        
        print len(followers)

        if followers_list['next_cursor']:
            params['cursor'] = followers_list['next_cursor']
            get_list()
        
    get_list()

    return followers


def get_timeline(screen_name):
    """
    Returns a collection of tweets for a particular user
    Max number to return is 200
    Includes retweets and tweet entities

    Following method provided here:
    https://dev.twitter.com/docs/working-with-timelines

    """
    uri = u'statuses/user_timeline.json'
    params = {
        'screen_name': screen_name, 
        'count': 200, 
        'include_entities': 1,
        'include_rts': 1,
    }
    tweets = []
    
    def get_list():
        tweet_list = request(uri, params).json()
        tweets.extend(tweet_list)
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
    unittest.main()
