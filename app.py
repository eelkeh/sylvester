
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
            debug=True
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
                .container { color:#333; max-width:400px; margin:20px auto; }
                .method { display:none; }
            </style>
        </head>
        <body>

            
            <div class="container">
                <h2>Twitter tools</h2>
                <p class="muted">DMI</p>

                <ul class="nav nav-tabs">
                    <li>
                        <a href="#timeline">Timeline</a>
                    </li>
                    <li><a href="#followers">Followers</a></li>
                    <li><a href="#">What else?</a></li>
                </ul>

                <div class="forms">
                    <form method="post" action="/twitter/timeline" class="method" data-link="timeline" data-method="timeline">
                        <label>Timeline</label>
                        <p class="muted">Get all tweets (and retweets) from a users timeline in a certain date range.</p>

                        <textarea name="name" rows="10" placeholder="Twitter id's or screennames..."></textarea>
                        <!-- <input name="name" type="textfield" placeholder="Username..."/> -->
                        <label>From date</label>
                        <input name="start" type="text" placeholder="12-31-2012"/>
                        <label>To date</label>
                        <input name="end" type="text" placeholder="01-04-2013"/>
                        <div></div>
                        <button type="submit" class="btn">Submit</button>
                    </form>

                    <form method="post" action="/twitter/timeline" class="method" data-link="followers" data-method="followers">
                        <label>Followers</label>
                        <input type="text" name="name" placeholder="Twitter username..."></textarea>
                        <div></div>
                        <button type="submit" class="btn">Submit</button>
                    </form>

                    
                    <div class="message alert alert-block"><div class="m"></div></div>
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
        self.write_message(json.dumps({"message": "Processing tweets..."}))
        
        msg = json.loads(message)
        op = msg.get('method')

        if op == 'followers':
            fields = msg['fields']
            screen_name = fields.get('name')
            self.write_message(json.dumps({"message": "Processing <strong>%s</strong> followers..." % screen_name}))
            followers = twitter.get_followers(screen_name)

            self.write_message(json.dumps({
                "message": "Done! %s has %s followers..." % (screen_name, len(followers)),
                "results": """
                    <a style='display:block;' href='/static/download/%s'>Followers - Download tab separated file</a>
                """ % (converters.list_to_list(followers))
             }))


        elif op == 'timeline':
            fields = msg['fields']
            # Fields
            screen_names = [s.strip() for s in fields['name'].split("\n")]
            from_date = fields.get('start')
            end_date = fields.get('end')

            if from_date:   
                from_date = datetime.strptime(from_date, '%m-%d-%Y')        
            if end_date:
                end_date = datetime.strptime(end_date, '%m-%d-%Y')
            
            tweets = []
            hashtags = defaultdict(int)
            urls = defaultdict(int)

            for name in screen_names:
                self.write_message(json.dumps({"message": "Processing <strong>%s</strong> tweets..." % name}))
                
                ts = twitter.get_timeline(name)
                addthese = []
                
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

