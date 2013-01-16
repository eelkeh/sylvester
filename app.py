import os
import twitter
import converters       
from datetime import datetime
from pprint import pprint
from bottle import route, get, post, request, run, template, static_file
from collections import defaultdict

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='static')

@route('/download/<filename:path>')
def download(filename):
    return static_file(filename, root='results', download=filename)

@get('/')
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
                    
                    <div class="results"></div>
                </div>
            </div>
            
            <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>
            <script src="/static/js/app.js"></script>

        </body>
        </html>
        '''

@post('/twitter/timeline')
def timeline():

    screen_name_raw = request.forms.name

    try:
        from_date = datetime.strptime(request.forms.start, '%m-%d-%Y')
        end_date = datetime.strptime(request.forms.end, '%m-%d-%Y')
    except:
        from_date = None
        end_date = None     

    screen_names = [s.strip() for s in screen_name_raw.split("\n")]

    tweets = []
    hashtags = defaultdict(int)
    urls = defaultdict(int)

    for name in screen_names:
        print "Starting on %s..." % name
        ts = twitter.get_timeline(name)
        addthese = []
        for t in ts: 
            print t     
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

    return { 
        'tweets_filepath': converters.list_to_tab(tweets),
        'hashtags_filepath': converters.countdict_to_tab(dict(hashtags)),
        'urls_filepath': converters.countdict_to_tab(dict(urls))
    }



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    run(host='0.0.0.0', port=port, reloader=True)
