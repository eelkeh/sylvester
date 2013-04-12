# Sylvester
A high-volume Twitter API client library in Python for research purposes.
When you have big jobs that can go wrong.

## Why use Sylvester?
Here's the gist:
- Use multiple application credentials to set up a client pool with multiple API endpoints, as many as you'd like.
- Makes use of generators to walk through big cursored lists, such as a users timeline.

## Example usage
Timeline requests are limited to 200 tweets per request, get a set of tweets until the timeline is exhausted.

	import sylvester
	import json

	pool = sylvester.create_client_pool_from_json()
	screen_name = "Twitter"
	for tweets in pool.get_timeline(screen_name):
		with open('tweets.json', 'a') as outfile:
			json.dump(tweets, outfile)


## keys.json
Example keys.json file

	{
		"keys":
		[
		    {
		        "client_key": 				"aaa",
		        "client_secret": 			"bbb",

		        "resource_owner_key":       "ccc",
		        "resource_owner_secret":    "ddd"
		    },
		    {
		        "client_key":               "eee",
		        "client_secret":            "fff",

		        "resource_owner_key":       "ggg",
		        "resource_owner_secret":    "hhh"
		    }
		]

	}