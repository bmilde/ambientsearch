#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import requests
import json
import redis
import re
from timer import Timer

red = redis.StrictRedis()

#Todo: refactor. This has been mved to the relevant event generator 
def idFromTitle(title):
    return re.sub(r'[^\w]', '_', title.replace(' ','_'))
    #return title.replace(' ','_').replace("'",'_').replace('(','_')

#Abstracts away the details of communicating with the ambient server
class KeywordClientHttp():

    def __init__(self,server_url):
        self.server_url = server_url
        self.request_header = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    def getSettings():
        r = requests.get(self.server_url+'getSettings')
        return r.json()
        
    def addRelevantEntry(self, type, title, text, url, score, insert_before):
        data = {'handle':'addRelevantEntry','type':type,'entry_id': idFromTitle(title),'title':title,'text':text,'url':url,'score':score, 'insert_before': insert_before}
        r = requests.post(self.server_url+'addRelevantEntry', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def delRelevantEntry(self, type, title):
        data = {'handle':'delRelevantEntry','type':type,'title': title, 'entry_id': idFromTitle(title)}
        r = requests.post(self.server_url+'delRelevantEntry', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def addUtterance(self, utterance,speaker):
        data = {'handle':'addUtterance','utterance':utterance,'speaker':speaker}
        r = requests.post(self.server_url+'addUtterance', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def replaceLastUtterance(self, old_utterance,new_utterance,speaker):
        data = {'handle':'replaceLastUtterance','old_utterance':old_utterance,'utterance':new_utterance,'speaker':speaker}
        r = requests.post(self.server_url+'replaceLastUtterance', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def completeUtterance(self, utterance, speaker):
        data = {'handle':'completeUtterance','utterance':utterance,'speaker':speaker}
        red.publish('ambient_transcript_only', json.dumps(data))

    def reset(self):
        data = {'handle':'reset'}
        red.publish('ambient_transcript_only', json.dumps(data))
        r = requests.post(self.server_url+'reset', data=json.dumps(data), headers=self.request_header)
        return r.status_code

#Do most of the message passing with redis, now standard version
class KeywordClient():

    def __init__(self,server_url=""):
        self.server_url = server_url
        self.request_header = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        self.timer_started = False
        self.timer = Timer()

    def checkTimer(self):
        if not self.timer_started:
            self.timer.start()
            self.timer_started = True

    def resetTimer(self):
        self.timer_started = False
        self.timer.start()

    def getSettings(self):
        r = requests.get(self.server_url+'getSettings')
        return r.json()
        
    def addRelevantEntry(self, type, title, text, url, score, insert_before):
        self.checkTimer()
        data = {'handle':'addRelevantEntry','type':type,'entry_id': idFromTitle(title),'title':title,'text':text,'url':url,'score':score, 'insert_before': insert_before, 'time': float(self.timer.current_secs())}
        print data
        red.publish('ambient', json.dumps(data))

    def delRelevantEntry(self, type, title):
        self.checkTimer()
        data = {'handle':'delRelevantEntry','type':type,'title': title, 'entry_id': idFromTitle(title), 'time': float(self.timer.current_secs())}
        red.publish('ambient', json.dumps(data))

    def addUtterance(self, utterance, speaker):
        self.checkTimer()
        data = {'handle':'addUtterance','utterance':utterance,'speaker':speaker, 'time': float(self.timer.current_secs())}
        red.publish('ambient', json.dumps(data))

    def replaceLastUtterance(self, old_utterance, new_utterance, speaker):
        self.checkTimer()
        data = {'handle':'replaceLastUtterance','old_utterance':old_utterance,'utterance':new_utterance,'speaker':speaker, 'time': float(self.timer.current_secs())}
        red.publish('ambient', json.dumps(data))

    def completeUtterance(self, utterance, speaker):
        self.checkTimer()
        data = {'handle':'completeUtterance','utterance':utterance,'speaker':speaker , 'time': float(self.timer.current_secs())}
        print data
        red.publish('ambient_transcript_only', json.dumps(data))

    def reset(self):
        data = {'handle':'reset'}
        red.publish('ambient_transcript_only', json.dumps(data))
        self.resetTimer()
        r = requests.post(self.server_url+'reset', data=json.dumps(data), headers=self.request_header)
        return r.status_code