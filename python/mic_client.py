__author__ = 'Benjamin Milde'

import argparse
from ws4py.client.threadedclient import WebSocketClient
import time
import threading
import sys
import urllib
import Queue
import json
import time
import os
import pyaudio
import wave
import nltk
import traceback
import requests
import redis

from topia.termextract import extract

from bridge import KeywordClient,KeywordClientHacky

std_speaker = "You"

def rate_limited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rate_limited_function(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rate_limited_function
    return decorate



class KaldiClient(WebSocketClient):

    def print_devices(self):
        info = self.paudio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        #for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
        for i in range (0,numdevices):
            if self.paudio.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
                print "Input Device id ", i, " - ", self.paudio.get_device_info_by_host_api_device_index(0,i).get('name')

            if self.paudio.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')>0:
                print "Output Device id ", i, " - ", self.paudio.get_device_info_by_host_api_device_index(0,i).get('name')

    def getYamahaID(self):
        info = self.paudio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range (0,numdevices):
            if self.paudio.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
                if 'Yamaha' in self.paudio.get_device_info_by_host_api_device_index(0,i).get('name'):
                    return i
        print 'No yamaha microphone found, defaulting to first available input device...'

        for i in range (0,numdevices):
            if self.paudio.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
                return i

        print 'No input device found! Please connect a microphone or recording device'

        return -1		    

    def __init__(self, filename, url, protocols=None, extensions=None, heartbeat_freq=None, byterate=32000,
                 save_adaptation_state_filename=None, send_adaptation_state_filename=None, keyword_server_url = ''):
        super(KaldiClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.final_hyps = []
        self.fn = filename
        self.byterate = byterate
        self.final_hyp_queue = Queue.Queue()
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename

        self.paudio = pyaudio.PyAudio()
        self.print_devices()
        self.keyword_client = KeywordClient(keyword_server_url)
        self.send_to_keywordserver = not (keyword_server_url == '')

        self.keyword_extractor = extract.TermExtractor()
        self.keyword_extractor.filter = extract.permissiveFilter

        if self.send_to_keywordserver:
            self.keyword_client.addUtterance('','speaker1')
            self.last_hyp = ''

    #@rate_limited(4)
    def send_data(self, data):
        if data is not None:
            self.send(data, binary=True)

    def opened(self):
        #print "Socket opened!"
        def send_data_to_ws():
            buffer_size = 1024

            yamahaID = self.getYamahaID()
            if yamahaID == -1:
                sys.exit(-1)
            else:
                print 'Selecting device',yamahaID,'as input device'

            stream = self.paudio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, input_device_index = yamahaID) #buffer   
            #f = open(self.fn, "rb")
            if self.send_adaptation_state_filename is not None:
                print >> sys.stderr, "Sending adaptation state from %s" % self.send_adaptation_state_filename
                try:
                    adaptation_state_props = json.load(open(self.send_adaptation_state_filename, "r"))
                    self.send(json.dumps(dict(adaptation_state=adaptation_state_props)))
                except:
                    e = sys.exc_info()[0]
                    print >> sys.stderr, "Failed to send adaptation state: ",  e
            abort = False
            while not abort:
                block = stream.read(buffer_size)
                self.send_data(block)
            print >> sys.stderr, "Audio sent, now sending EOS"
            self.send("EOS")

        t = threading.Thread(target=send_data_to_ws)
        t.start()

    def getKeywords(self, currentHyp, contextWords=200, ignoreNumRecentWords=1, maxKeywords=7):

        tokens = nltk.word_tokenize(u' '.join(self.final_hyps) + u' ' + currentHyp)[-contextWords:(None if currentHyp == '' else -ignoreNumRecentWords)] 
        #tags = nltk.pos_tag(tokens)

        past_tag = None
        extracted_keywords = self.keyword_extractor(' '.join(tokens))
        extracted_keywords = sorted(extracted_keywords, key=lambda x: x[1]*x[2], reverse=True)
        #print extracted_keywords
        keywords = [keyword[0] for keyword in extracted_keywords]

        #Get keywords as a list of nouns. MWEs are heuristically choosen if two preceedings tokens share the same noun tag.
        #for touple in tags:
        #    word,tag = touple
        #    
        #    if tag in ['NN', 'NNP', 'NNPS', 'NNS']:
        #	if past_tag and past_tag in ['NN', 'NNP', 'NNPS', 'NNS']:
        #	    keywords[0] += ' ' + word   
        #	else:	
        #	    keywords = [word] + keywords		    
        #   past_tag = tag
        #
        #keywords = [touple[0] for touple in tags if touple[1] in ['NN', 'NNP', 'NNPS', 'NNS']]

        return keywords[:maxKeywords]

    def received_message(self, m):
        try:
            response = json.loads(str(m))
            #print >> sys.stderr, "RESPONSE:", response
            #print >> sys.stderr, "JSON was:", m
            if response['status'] == 0:
                if 'result' in response:
                    trans = response['result']['hypotheses'][0]['transcript']
                    if response['result']['final']:
                        if trans not in ['a.','I.','i.','the.','but.','one.','it.','she.']:
                            self.final_hyps.append(trans)
                            keyword_list = self.getKeywords('')			    

                            if self.send_to_keywordserver:
                                self.keyword_client.replaceLastUtterance(self.last_hyp, trans, std_speaker)
                                self.keyword_client.addUtterance('',std_speaker)
                                self.last_hyp = ''
                                self.keyword_client.setKeywordList(keyword_list)
                            print u'\r\033[K',trans.replace(u'\n', u'\\n'),u'        Keywords: [',u','.join(keyword_list),u']' 
                    else:
                        keyword_list = self.getKeywords(trans)
                        if self.send_to_keywordserver:
                            self.keyword_client.replaceLastUtterance(self.last_hyp, trans, std_speaker)
                            self.last_hyp = trans
                            self.keyword_client.setKeywordList(keyword_list) 
                        print_trans = trans.replace(u'\n', u'\\n')
                        print u'\r\033[K',print_trans,u'        Keywords: [',u','.join(keyword_list),u']'
                if 'adaptation_state' in response:
                    if self.save_adaptation_state_filename:
                        print u'Saving adaptation state to %s' % self.save_adaptation_state_filename
                        with open(self.save_adaptation_state_filename, 'w') as f:
                            f.write(json.dumps(response['adaptation_state']))
            else:
                print  u'Received error from server (status %d)' % response['status']
                if 'message' in response:
                    print 'Error message:',  response['message']
        except Exception:
            print 'Exception in received_message'
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                limit=10, file=sys.stdout)

    def get_full_hyp(self, timeout=60):
        return self.final_hyp_queue.get(timeout)

    def closed(self, code, reason=None):
        #print "Websocket closed() called"
        #print >> sys.stderr
        self.final_hyp_queue.put(' '.join(self.final_hyps))

def connect_ws(args):
    content_type = args.content_type
    if content_type == '' and args.audiofile == '':
        content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)%d, format=(string)S16LE, channels=(int)1" %(args.rate/2)

    ws = KaldiClient('', args.uri + '?%s' % (urllib.urlencode([("content-type", content_type)])), byterate=args.rate,
                  save_adaptation_state_filename=args.save_adaptation_state, send_adaptation_state_filename=args.send_adaptation_state, keyword_server_url=args.ambient_uri)
    ws.connect()
    #print 'Disconnected.'
    result = ws.get_full_hyp()
    print result.encode('utf-8')

def main():

    parser = argparse.ArgumentParser(description='Command line client for kaldigstserver and the ambient visualization server')
    parser.add_argument('-u', '--uri', default='ws://engine.compress.to:8100/client/ws/speech', dest='uri', help='Kaldi server websocket URI')
    parser.add_argument('-a', '--ambient-uri', default='http://localhost:5000/', dest='ambient_uri', help='Ambient server websocket URI')
    parser.add_argument('-r', '--rate', default=32000, dest='rate', type=int, help='Rate in bytes/sec at which audio should be sent to the server. NB! For raw 16-bit audio it must be 2*samplerate!')
    parser.add_argument('--save-adaptation-state', help='Save adaptation state to file')
    parser.add_argument('--send-adaptation-state', help='Send adaptation state from file')
    parser.add_argument('--content-type', default='', help='Use the specified content type (empty by default, for raw files the default is  audio/x-raw, layout=(string)interleaved, rate=(int)<rate>, format=(string)S16LE, channels=(int)1')
    parser.add_argument('--audiofile', help='Audio file to be sent to the server', default='', type=str)
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = main()
    connect_ws(args)
