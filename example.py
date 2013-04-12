import sylvester
import json
	
pool = sylvester.create_client_pool_from_json()
screen_name = "Twitter"
for tweets in pool.get_timeline(screen_name):
	with open('tweets.json', 'a') as outfile:
		json.dump(tweets, outfile)