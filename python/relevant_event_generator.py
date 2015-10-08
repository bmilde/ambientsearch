#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

import redis

import keyword_extract
import wiki_search
import argparse
import json
import bisect
from datetime import datetime

from bridge import KeywordClient

red = redis.StrictRedis()

#redis channel with relevant messages for this python module
my_redis_channel = 'ambient_transcript_only'

# Helper function :  Find an entry in a list of dictionaries 
# http://stackoverflow.com/questions/4391697/find-the-index-of-a-dict-within-a-list-by-matching-the-dicts-value
def find_entry_pos_in_list(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

# This event generator listens for incoming complete utterance redis events
# and starts the process of finding relevant information after each utterance with the keyword_extract module
# (relevant text and pictures are downloaded in a blocking manner using wiki_search)
class EventGenerator:

    def __init__(self,keyword_server_url, keyword_extrator):
        self.complete_transcript = []

        #dict with all relevant entries
        self.relevant_entries = {}
        #sorted list of displayed entries
        self.displayed_entries = []
        self.keyword_client = KeywordClient(keyword_server_url)
        self.ke = keyword_extrator

    #Listen loop (redis)
    #Todo: for other languages than English, utf8 de and encoding will be needed
    def start_listen(self):
        pubsub = red.pubsub()
        pubsub.subscribe(my_redis_channel)
        for message in pubsub.listen():
            print 'New message:', message, type(message["data"])
            if type(message["data"]) == str:
                json_message = json.loads(message["data"])
                if "handle" in json_message:
                    print json_message
                    if json_message["handle"] == "completeUtterance":
                        self.complete_transcript.append(json_message["utterance"])
                        self.send_relevant_entry_updates()
                    elif json_message["handle"] == "reset":
                        print 'reset all'
                        self.complete_transcript = []
                        self.relevant_entries = {}
                        self.displayed_entries = []

    # Add a relevant entry to the display, specify how many entries should be allowed maximally 
    def addDisplayEntry(entry,max_entries=4):
        insert_pos = bisect.bisect(self.displayed_entries, float(entry["score"]))
        
        #Only add entry if we want to insert it into the max_entries best entries
        if insert_pos < max_entries:
            #Determine position by its score
            bisect.insort(self.displayed_entries, float(entry["score"]))
            
            len_displayed_entries = len(displayed_entries)

            #In this case, one of the previous best entries needs to be deleted:
            if(len_displayed_entries > max_entries):
                #Send delete entry events to entries those score is below the four best showed entries
                for entry in self.displayed_entries[max_entries:]:
                    self.delDisplayEntry(entry_type,title)

                self.displayed_entries = self.displayed_entries[:max_entries]
                len_displayed_entries = len(displayed_entries)

            if insert_pos == len_displayed_entries -1:
                insert_before = '#end#'
            else:
                insert_before = self.displayed_entries[insert_before+1]["title"]

            self.keyword_client.addRelevantEntry("wiki", entry["title"], entry["text"], entry["url"], entry["score"], insert_before)

    # Delete a relevant entry from the display
    def delDisplayEntry(entry_type,title):
        self.keyword_client.delRelevantEntry(entry_type, title)

    # Send relevant entry updates to the display, given a new full utterance. 
    # Also specify how many entries we want (max_entries) and how existing keywords should decay their score.
    def send_relevant_entry_updates(self,max_entries=4, decay=.9):

        #Do the decay for the displayed entries:
        #TODO: handle duplicate keywords and updated scores

        for entry in self.displayed_entries:
            entry["score"] *= decay

        print 'send_relevant_entry_updates called'
        keywords = self.ke.getKeywordsDruid('\n'.join([sentence[:-1] for sentence in self.complete_transcript]))
        new_relevant_entries = wiki_search.getSummariesSingleKeyword(keywords,max_entries,lang='en',pics_folder='pics/')
        print new_relevant_entries

        #generate del relevant entries
        for key in set(self.relevant_entries) - set(new_relevant_entries):
            entry = self.relevant_entries[key]
            self.keyword_client.delRelevantEntry("wiki", entry["title"])
            print 'del',key
        #generate add relevant entries
        for key in set(new_relevant_entries) - set(self.relevant_entries):
            entry = new_relevant_entries[key]
            self.keyword_client.addRelevantEntry("wiki", entry["title"], entry["text"], entry["url"], entry["score"])
            print 'add',key

        #TODO: Update scores of existing entries in self.displayed_entries (?)

        self.relevant_entries = new_relevant_entries

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line client for kaldigstserver and the ambient visualization server')
    parser.add_argument('-a', '--ambient-uri', type=str, default='http://localhost:5000/', dest='ambient_uri', help='Ambient server websocket URI')
    parser.add_argument('-c', '--cutoff-druid-score', type=float, default=0.1, dest='cutoff_druid_score', help='Cutoff score for the druid algorithm, '
        'lower value will find more keywords, but takes longer to load and needs more memory')

    args = parser.parse_args()
    ke = keyword_extract.KeywordExtract()
    ke.buildDruidCache(cutoff_druid_score=args.cutoff_druid_score)

    event_gen = EventGenerator(args.ambient_uri, ke)
    event_gen.start_listen()
