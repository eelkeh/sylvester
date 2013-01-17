
import os
import twitter
import converters       
import time
from datetime import datetime
from pprint import pprint
from collections import defaultdict
import json
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

# web: gunicorn -w 4 -b 0.0.0.0:$PORT -k gevent app:app

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/twitter/timeline", EchoWebSocket),
        ]
        settings = dict(
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            autoescape = None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>Sylvester</title>
            <link href="//netdna.bootstrapcdn.com/twitter-bootstrap/2.2.2/css/bootstrap-combined.min.css" rel="stylesheet">
            <style>
                .forms { color:#333; max-width:400px; margin:20px auto; }
            </style>
        </head>
        <body>
            <div class="container">
                
                <div class="forms">
                    <h2>Twitter tools</h2>
                    <p class="muted">Tornado version</p>
                    <form method="post" action="/twitter/timeline">
                        <label>Timeline</label>
                        <textarea name="name" rows="10" placeholder="Twitter usernames..."></textarea>
                        <!-- <input name="name" type="textfield" placeholder="Username..."/> -->
                        <label>From date</label>
                        <input name="start" type="text" placeholder="12-31-2012"/>
                        <label>To date</label>
                        <input name="end" type="text" placeholder="01-04-2013"/>
                        <div></div>
                        <button type="submit" class="btn">Submit</button>
                    </form>
                    
                    <div class="message"></div>
                    <div class="results"></div>
                </div>
            </div>
            
            <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>
            <script src="/static/js/app.js"></script>

        </body>
        </html>
        ''')


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"

    def on_message(self, message):
        fields = json.loads(message)
        self.write_message(json.dumps({"message": "Processing tweets..."}))

        screen_names = [s.strip() for s in fields['name'].split("\n")]
        try:
            from_date = datetime.strptime(fields['start'], '%m-%d-%Y')
            end_date = datetime.strptime(fields['end'], '%m-%d-%Y')
        except:
            from_date = None
            end_date = None     
        
        tweets = []
        hashtags = defaultdict(int)
        urls = defaultdict(int)

        for name in screen_names:
            self.write_message(json.dumps({"message": "Processing <strong>%s</strong> tweets..." % name}))
            ts = twitter.get_timeline(name)
            addthese = [    ]
            
            for t in ts: 
                if type(t) is dict:
                    t['screen_name'] = name

                    for h in t['entities']['hashtags']:
                        if h['text']:
                            hashtags[h['text']] += 1
                    
                    for u in t['entities']['urls']:
                        if u['expanded_url']:
                            urls[u['expanded_url']] += 1

                
                    # Remove nested stuff
                    del t['entities']
                    del t['user']
                    try:
                        del t['retweeted_status']
                    except:
                        pass

                    try:
                        del t['possibly_sensitive']
                    except:
                        pass


                    if from_date and end_date:
                        created = datetime.strptime(t['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
                        if from_date < created < end_date:
                            addthese.append(t)

            tweets.extend(addthese) 

        self.write_message(json.dumps({
            "message": "Done! Processed <strong>%s</strong> tweets..." % len(tweets), 
            "results": """
                <a style='display:block;' href='/static/download/%s'>Tweets - Download tab separated file</a>
                <a style='display:block;' href='/static/download/%s'>Hashtags - Download tab separated file</a>
                <a style='display:block;' href='/static/download/%s'>Urls - Download tab separated file</a>
            """ % (converters.list_to_tab(tweets), converters.countdict_to_tab(dict(hashtags)), 
                    converters.countdict_to_tab(dict(urls)) )

         }))



    def on_close(self):
        print "WebSocket closed"

if __name__ == '__main__':
    app = Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

