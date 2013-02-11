import sqlite3
import json
from itertools import cycle

conn = sqlite3.connect('locks.db')
conn.isolation_level = None
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS locks
             (key text, uri text, release integer, UNIQUE(key, uri) ON CONFLICT REPLACE)''')

RATELIMITS = {
    'get_friends': 15,
    'get_followers': 15, 
    'get_timeline': 180,
}
pools = {}
blocked = {}

with open('keys.json') as keys_json:
    _keys = json.load(keys_json)['keys']
    
keys = cycle(_keys)
key = keys.next()