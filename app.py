from gevent import monkey; monkey.patch_all()

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError

import os
import twitter
import converters       
import time
from datetime import datetime
from pprint import pprint
import bottle
from bottle import route, get, post, request, run, template, static_file, abort
from collections import defaultdict
import json
import tornado.ioloop
import tornado.web

app = bottle.Bottle()

# web: gunicorn -w 4 -b 0.0.0.0:$PORT -k gevent app:app

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

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)




@app.route('/stream')
def stream():
    yield 'START'
    time.sleep(3)
    yield 'MIDDLE'
    time.sleep(5)
    yield 'END'

@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='static')

@app.route('/download/<filename:path>')
def download(filename):
    return static_file(filename, root='results', download=filename)

@app.get('/')
def index():
    return '''
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
        '''

@app.route('/twitter/timeline')
def timeline():

    
    def process_timeline(fields):
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
            wsock.send(json.dumps({"message": "Processing <strong>%s</strong> tweets..." % name}))
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

                    if from_date and end_date:
                        created = datetime.strptime(t['created_at'],'%a %b %d %H:%M:%S +0000 %Y')
                        if from_date < created < end_date:
                            addthese.append(t)

            tweets.extend(addthese) 

        wsock.send(json.dumps({
            "message": "Done! Processed <strong>%s</strong> tweets..." % len(tweets), 
            "results": """
                <a style='display:block;' href='/download/%s'>Tweets - Download tab separated file</a>
                <a style='display:block;' href='/download/%s'>Hashtags - Download tab separated file</a>
                <a style='display:block;' href='/download/%s'>Urls - Download tab separated file</a>
            """ % (converters.list_to_tab(tweets), converters.countdict_to_tab(dict(hashtags)), 
                    converters.countdict_to_tab(dict(urls)) )

         }))

    

    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        try:
            message = wsock.receive()
            if message:
                fields = json.loads(message)
                print fields
                wsock.send(json.dumps({"message": "Processing tweets..."}))
                process_timeline(fields)

        except WebSocketError:
            break




        #return { 
        #    'tweets_filepath': converters.list_to_tab(tweets),
        #    'hashtags_filepath': converters.countdict_to_tab(dict(hashtags)),
        #    'urls_filepath': converters.countdict_to_tab(dict(urls))
        #}



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    port = 5000
    #app.run(host='0.0.0.0', port=port, reloader=True)
    server = pywsgi.WSGIServer(('127.0.0.1', port), app, handler_class=WebSocketHandler)
    server.serve_forever()

    app.listen(5000)
    tornado.ioloop.IOLoop.instance().start()

