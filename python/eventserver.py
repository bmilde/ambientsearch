#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import flask
import redis
import os
import json
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

#Send event to the event stream
def event_stream():
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

#This could also be replaced with just using redis for message passing
@app.route('/addUtterance', methods=['POST'])
@app.route('/replaceLastUtterance', methods=['POST'])
@app.route('/addRelevantEntry', methods=['POST'])
@app.route('/delRelevantEntry', methods=['POST'])
@app.route('/reset', methods=['POST'])
def generate_event():
    received_json = flask.request.json
    print received_json
    red.publish(ambient_server_channel, json.dumps(received_json))
    return "ok"

@app.route('/reset_topics', methods=['POST'])

#These should ideally be served with a real web server, but for developping purposes, serving static files with Flask is also ok:
#START static files
@app.route('/')
def root():
    print 'root called'
    return app.send_static_file('index.html')

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
    
#END static files
                          
if __name__ == '__main__':
    app.debug = True
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(threaded=True)  
 
