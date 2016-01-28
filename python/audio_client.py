__author__ = 'Jonas Wacker'

import argparse
from ws4py.client.threadedclient import WebSocketClient
import threading
import sys
import urllib
import Queue
import json
import time
import traceback
import os
from mutagen.mp3 import MP3

from bridge import KeywordClient

std_speaker = "You"


def rate_limited(max_per_second):
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        def rate_limited_function(*args, **kargs):
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kargs)
            last_time_called[0] = time.clock()
            return ret
        return rate_limited_function
    return decorate


# Returns an audio file's bitrate and length in seconds if file is in mp3-format.
def get_audio_meta_data(path):
    file_extension = os.path.splitext(path)[1] if (isinstance(path, str) and os.path.isfile(path)) else 'none'
    meta_data = {'bitrate': 32000 * 8, 'length': 0}

    if file_extension == '.mp3':
        audio = MP3(path)
        meta_data['bitrate'] = audio.info.bitrate
        meta_data['length'] = audio.info.length

    return meta_data


class KaldiClient(WebSocketClient):

    def __init__(self, filename, url, protocols=None, extensions=None, heartbeat_freq=None, byterate=32000,
                 save_adaptation_state_filename=None, send_adaptation_state_filename=None, keyword_server_url='',
                 max_sentences=0):
        super(KaldiClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.final_hyps = []
        self.fn = filename
        self.byterate = byterate
        self.final_hyp_queue = Queue.Queue()
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename

        self.keyword_client = KeywordClient(keyword_server_url)
        self.keyword_client.reset()
        self.send_to_keywordserver = not (keyword_server_url == '')

        if self.send_to_keywordserver:
            self.keyword_client.addUtterance('', 'You')
            self.last_hyp = ''

        self.max_sentences = max_sentences

    @rate_limited(4)
    def send_data(self, data):
        self.send(data, binary=True)

    def opened(self):
        # print "Socket opened!"
        def send_data_to_ws():
            f = open(self.fn, "rb")
            if self.send_adaptation_state_filename is not None:
                print >> sys.stderr, "Sending adaptation state from %s" % self.send_adaptation_state_filename
                try:
                    adaptation_state_props = json.load(open(self.send_adaptation_state_filename, "r"))
                    self.send(json.dumps(dict(adaptation_state=adaptation_state_props)))
                except:
                    e = sys.exc_info()[0]
                    print >> sys.stderr, "Failed to send adaptation state: ", e
            for block in iter(lambda: f.read(self.byterate / 4), ""):
                if self.maximum_sentences_reached():
                    break
                self.send_data(block)
            print >> sys.stderr, "Audio sent, now sending EOS"
            self.send("EOS")

        t = threading.Thread(target=send_data_to_ws)
        t.start()

    # received decoding message from upstream Kaldi server
    def received_message(self, m):
        if self.maximum_sentences_reached():
            return

        try:
            response = json.loads(str(m))
            # print >> sys.stderr, "RESPONSE:", response
            # print >> sys.stderr, "JSON was:", m
            if response['status'] == 0:
                if 'result' in response:
                    trans = response['result']['hypotheses'][0]['transcript']
                    if response['result']['final']:
                        if trans not in ['a.', 'I.', 'i.', 'the.', 'but.', 'one.', 'it.', 'she.']:
                            self.final_hyps.append(trans)

                            if self.send_to_keywordserver:
                                self.keyword_client.replaceLastUtterance(self.last_hyp, trans, std_speaker)
                                self.keyword_client.completeUtterance(trans, std_speaker)
                                self.keyword_client.addUtterance('', std_speaker)
                                self.last_hyp = ''

                                complete_transcript = '\n'.join(sentence[:-1] for sentence in self.final_hyps)

                            print u'\r\033[K', trans.replace(u'\n', u'\\n')
                    else:
                        if self.send_to_keywordserver:
                            self.keyword_client.replaceLastUtterance(self.last_hyp, trans, std_speaker)
                            self.last_hyp = trans
                        print_trans = trans.replace(u'\n', u'\\n')
                        print u'\r\033[K', print_trans
                if 'adaptation_state' in response:
                    if self.save_adaptation_state_filename:
                        print u'Saving adaptation state to %s' % self.save_adaptation_state_filename
                        with open(self.save_adaptation_state_filename, 'w') as f:
                            f.write(json.dumps(response['adaptation_state']))
            else:
                print u'Received error from server (status %d)' % response['status']
                if 'message' in response:
                    print 'Error message:', response['message']
        except Exception:
            print 'Exception in received_message'
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                                      limit=10, file=sys.stdout)

    def get_full_hyp(self, timeout=60):
        return self.final_hyp_queue.get(timeout)

    # Returns True if the maximum number of sentences defined by the user have been transcribed.
    def maximum_sentences_reached(self):
        return self.max_sentences != 0 and len(self.final_hyps) >= self.max_sentences

    def closed(self, code, reason=None):
        # print "Websocket closed() called"
        # print >> sys.stderr
        self.final_hyp_queue.put(" ".join(self.final_hyps))


def connect_ws(args):
    content_type = args.content_type
    if content_type == '' and args.audiofile.endswith(".raw"):
        content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)%d, format=(string)S16LE, channels=(int)1"\
                       % (args.rate / 2)

    if args.rate == 0:
        meta_data = get_audio_meta_data(args.audiofile)
        args.rate = meta_data['bitrate'] / 8
        print "No Bitrate provided. Setting Bitrate to: " + str(args.rate)

    try:
        ws = KaldiClient(args.audiofile, args.uri + '?%s' % (urllib.urlencode([("content-type", content_type)])),
                         byterate=args.rate, save_adaptation_state_filename=args.save_adaptation_state,
                         send_adaptation_state_filename=args.send_adaptation_state,
                         keyword_server_url=args.ambient_uri, max_sentences=args.count)
        ws.connect()

        while not ws.maximum_sentences_reached():
            time.sleep(3)
    except KeyboardInterrupt:
        ws.close()

    result = ws.get_full_hyp()
    print result.encode('utf-8')


def main():

    parser = argparse.ArgumentParser(description='Command line client for kaldigstserver')
    parser.add_argument('-u', '--uri', default="ws://localhost:8888/client/ws/speech", dest="uri",
                        help="Server websocket URI")
    parser.add_argument('-a', '--ambient-uri', default='http://localhost:5000/', dest='ambient_uri',
                        help='Ambient server websocket URI')
    parser.add_argument('-r', '--rate', default=0, dest="rate", type=int,
                        help="Rate in bytes/sec at which audio should be sent to the server."
                             "NB! For raw 16-bit audio it must be 2*samplerate!")
    parser.add_argument('-n', '--sentence-number', default=0, dest="count", type=int,
                        help="Maximum number of sentences to transcribe.")
    parser.add_argument('--save-adaptation-state', help="Save adaptation state to file")
    parser.add_argument('--send-adaptation-state', help="Send adaptation state from file")
    parser.add_argument('--content-type', default='',
                        help="Use the specified content type (empty by default,"
                             "for raw files the default is audio/x-raw, layout=(string)interleaved,"
                             "rate=(int)<rate>, format=(string)S16LE, channels=(int)1")
    parser.add_argument('audiofile', help="Audio file to be sent to the server")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = main()
    connect_ws(args)
