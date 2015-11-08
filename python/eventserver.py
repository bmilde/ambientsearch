#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import flask
import redis
import os
import json
import bs4
import bridge
import codecs
import datetime

from werkzeug.serving import WSGIRequestHandler

base_path = os.getcwd() + '/'
print "base_path:",base_path

app = flask.Flask(__name__)
app.secret_key = 'asdf'
app._static_folder = base_path
app._static_files_root_folder_path = base_path

red = redis.StrictRedis()

long_poll_timeout = 0.5
long_poll_timeout_burst = 0.08

ambient_server_channel = 'ambient'
relevant_event_generator_channel = 'ambient_transcript_only'
return_string_ok = "ok"

kc = bridge.KeywordClient()

session_outfile = None

#Send event to the event stream
def event_stream():
    print "New connection to event_stream!"
    pubsub = red.pubsub()
    pubsub.subscribe(ambient_server_channel)
    for message in pubsub.listen():
        print 'New message:', message
        yield 'data: %s\n\n' % message['data']

#Event stream end point for the browser, connection is left open. Must be used with threaded Flask.
@app.route('/stream')
def stream():
    return flask.Response(event_stream(),
                          mimetype="text/event-stream")

#Traditional long polling. This is the fall back, if a browser does not support server side events. TODO: test and handle disconnects
@app.route('/stream_poll')
def poll():
    pubsub = red.pubsub()
    pubsub.subscribe(ambient_server_channel)
    message = pubsub.get_message(timeout=long_poll_timeout)
    while(message != None):
        yield message
        message = pubsub.get_message(timeout=long_poll_timeout_burst)

@app.route('/closed', methods=['POST'])
def closed():
    received_json = flask.request.json
    print "closed called"
    print received_json
    data = {'handle':'closed', 'entry_id':received_json['entry_id']}
    red.publish(relevant_event_generator_channel, json.dumps(data))
    session_outfile.write('closed ' + json.dumps(received_json) + '\n')
    return return_string_ok

@app.route('/starred', methods=['POST'])
def starred():
    received_json = flask.request.json
    print "starred called"
    print received_json
    session_outfile.write('starred ' + json.dumps(received_json) + '\n')
    return return_string_ok

@app.route('/unstarred', methods=['POST'])
def unstarred():
    received_json = flask.request.json
    print "unstarred called"
    print received_json
    session_outfile.write('unstarred ' + json.dumps(received_json) + '\n')
    return return_string_ok

@app.route('/viewing', methods=['POST'])
def viewing():
    received_json = flask.request.json
    print "viewing called"
    print received_json
    session_outfile.write('viewing ' + json.dumps(received_json) + '\n')
    return return_string_ok

@app.route('/viewingClosed', methods=['POST'])
def viewingClosed():
    received_json = flask.request.json
    print "viewingClosed called"
    print received_json
    session_outfile.write('viewingClosed ' + json.dumps(received_json) + '\n')
    return return_string_ok

@app.route('/reset', methods=['GET'])
def reset():
    print "Reset called from browser"
    #reset local timer in keyword client
    kc.resetTimer()
    data = {'handle':'reset'}
    red.publish(relevant_event_generator_channel, json.dumps(data))
    new_session_outfile()
    return return_string_ok

#These are now replaced by using redis and message passing. Do we still need them?
@app.route('/addUtterance', methods=['POST'])
@app.route('/replaceLastUtterance', methods=['POST'])
@app.route('/addRelevantEntry', methods=['POST'])
@app.route('/delRelevantEntry', methods=['POST'])
@app.route('/reset', methods=['POST'])
def generate_event():
    received_json = flask.request.json
    print received_json
    red.publish(ambient_server_channel, json.dumps(received_json))
    return return_string_ok

# This is for the flow player, which can send its subtitles 
# They look like this: "<p>Guten Abend</p><br/><p>aus dem Gasometer in Berlin.</p><br/>"
# We use beautiful Soup to strip all elements (see: http://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text)

@app.route('/addSubtitle', methods=['POST'])
def add_subtitle():
    received_json = flask.request.json
    print received_json
    soup = bs4.BeautifulSoup(received_json['text'])
    text = u' '.join(soup.findAll(text=True))
    kc.addUtterance(utterance='',speaker='TV')
    kc.replaceLastUtterance(new_utterance=text,old_utterance='',speaker='TV')
    kc.completeUtterance(utterance=text,speaker='TV')
    return return_string_ok

# TODO
#@app.route('/reset_topics', methods=['POST'])

#These should ideally be served with a real web server, but for developping purposes, serving static files with Flask is also ok:
#START static files
@app.route('/')
def root():
    print 'root called'
    return app.send_static_file('index.html')

@app.route('/flow_player')
def flow_player():
    print 'flow player called'
    return app.send_static_file('flow_player.html')

@app.route('/css/<path:path>')
def send_css(path):
    return flask.send_from_directory(base_path+'css', path)

@app.route('/js/<path:path>')
def send_js(path):
    return flask.send_from_directory(base_path+'js', path)
    
@app.route('/pics/<path:path>')
def send_pics(path):
    return flask.send_from_directory(base_path+'pics', path)
    
@app.route('/fonts/<path:path>')
def send_fonts(path):
    return flask.send_from_directory(base_path+'fonts', path)

@app.route('/test_videos/<path:path>')
def test_videos(path):
    print 'Sending test video:', path
    return flask.send_from_directory(base_path+'test_videos', path)
    
#END static files

def new_session_outfile():
    global session_outfile
    if session_outfile is not None:
        session_outfile.close()
    session_outfile = codecs.open('sessions/' + str(datetime.datetime.now()).replace('-',' ').replace(':','_').replace(' ','_') + '.txt','w','utf-8')
                          
if __name__ == '__main__':
    new_session_outfile()
    app.debug = True
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(threaded=True)