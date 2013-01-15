import os
import twitter
import converters       
from pprint import pprint
from bottle import route, get, post, request, run, template, static_file

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
        </head>
        <body>
            <div class="container">
                
                <h1>Twitter tools</h1>
                
                <form method="POST" action="/twitter/timeline">
                    <label>Timeline</label>
                    <input name="name" type="text" placeholder="Username..."/>
                    <label class="checkbox">
                        <input id="timeline" type="checkbox"> Check me out
                    </label>
                    <button type="submit" class="btn">Submit</button>
                </form>
                
                <div class="results">

                </div>


            </div>
            
            <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script>
            <script src="/static/js/app.js"></script>

        </body>
        </html>
        '''

@post('/twitter/timeline')
def timeline():
    screen_name = request.forms.get('name')
    tweets = twitter.get_timeline(screen_name)
    for t in tweets:      
        del t['entities']
        del t['user']
        try:
            del t['retweeted_status']
        except:
            pass

    return { 'filepath': converters.list_to_tab(tweets) }



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    run(host='0.0.0.0', port=port, reloader=True)
