#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import time
import redis
import argparse
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
        return len(word) * 0.015

    def simulateSentence(self, sentence):
        split = sentence.split(" ")
        firstword = split[0]
        self.add_new(firstword,self.get_delay(firstword))
        for x in xrange(2,len(split)+1):
            self.update(' '.join(split[:x]),self.get_delay(split[x-1]))
        self.complete(sentence)
        self.last_hyp = ""

def simulate_en():        
    si = SimluateInput()
    si.simulateSentence("computational linguistics is a field that is primarily concerned with and natural language processing from the linguistic and computer standpoint of few it has roots in the rule based systems artificial intelligence")
    si.simulateSentence("and now i change the topic completely")
    si.simulateSentence("red blood cells are round with a flattish, indented center, like doughnuts without a hole.")
    si.simulateSentence("and now i change the topic again")
    si.simulateSentence("new york city is one of the major cities")
    si.simulateSentence("i have been to new york city")
    si.simulateSentence("to brookyln and harlem")

def simulate_de():
    si = SimluateInput()
    si.simulateSentence("Sprachwissenschaft, auch Linguistik, ist eine Wissenschaft, die in verschiedenen Herangehensweisen die menschliche Sprache untersucht.")
    si.simulateSentence("Inhalt sprachwissenschaftlicher Forschung ist die Sprache als System und im Gebrauch, ihre einzelnen Bestandteile und Einheiten sowie deren Bedeutungen.")
    si.simulateSentence("Des Weiteren beschäftigt sich die Sprachwissenschaft mit Entstehung, Herkunft und geschichtlicher Entwicklung von Sprache, mit ihrer vielseitigen Anwendung in der schriftlichen und mündlichen Kommunikation, mit dem Wahrnehmen, Erlernen und Artikulieren von Sprache sowie mit den möglicherweise damit einhergehenden Störungen.")
    si.simulateSentence("Nun wechseln wir das Thema!")
    si.simulateSentence("Wie wäre es mit der Frankfurter Rundschau")
    si.simulateSentence("und der akuellen Lage in Syrien?")

#def use_textfile(lang): todo    

if __name__ == '__main__':            
    parser = argparse.ArgumentParser(description='Command line test client - simulate ASR input.')
    parser.add_argument('-l', '--language', type=str, default='en', dest='language', help='Select a language for the relevant evant geneartor (en,de). Defaults to en.')

    args = parser.parse_args()

    if args.language == 'en':
        simulate_en()
    elif args.language == 'de':
        simulate_de()

