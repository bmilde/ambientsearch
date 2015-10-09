#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import time
import redis
from bridge import KeywordClient

class SimluateInput:
    def __init__(self):
        self.ks = KeywordClient(server_url="http://localhost:5000/")
        self.std_spk = "You"
        self.last_hyp = ""
        self.ks.reset()

    def update(self, utterance, delay):
        time.sleep(delay)
        self.ks.replaceLastUtterance(self.last_hyp,utterance, self.std_spk)
        self.last_hyp = utterance

    def add_new(self, utterance,delay):
        time.sleep(delay)
        self.ks.addUtterance(utterance, self.std_spk)

    def complete(self, utterance):
        self.ks.completeUtterance(utterance, self.std_spk)

    def get_delay(self, word):
        return len(word) * 0.03

    def simulateSentence(self, sentence):
        split = sentence.split(" ")
        firstword = split[0]
        self.add_new(firstword,self.get_delay(firstword))
        for x in xrange(2,len(split)+1):
            self.update(' '.join(split[:x]),self.get_delay(split[x-1]))
        self.complete(sentence)
        self.last_hyp = ""
        

if __name__ == '__main__':            
    si = SimluateInput()
    si.simulateSentence("computational linguistics is a field that is primarily concerned with and natural language processing from the linguistic and computer standpoint of few it has roots in the rule based systems artificial intelligence")
    si.simulateSentence("red blood cells are round with a flattish, indented center, like doughnuts without a hole.")
    si.simulateSentence("new york city is one of the major cities")
    si.simulateSentence("i have been to new york city")