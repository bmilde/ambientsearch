#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker, Benjamin Milde'

import redis

import keyword_extract_w2v
import wiki_search_es
import argparse
import json
import bisect
import re
from timer import Timer
from datetime import datetime
from collections import defaultdict
import codecs

from bridge import KeywordClient

red = redis.StrictRedis()

#redis channel with relevant messages for this python module
my_redis_channel = 'ambient_transcript_only'

end_marker = '_end_'

# Helper class for addDisplayEntry and managing a list of displayed items with bisect:
# See: http://stackoverflow.com/questions/1344308/in-python-find-item-in-list-of-dicts-using-bisect 
class dict_list_index_get_member(object):
    def __init__(self, dict_list, member):
        self.dict_list = dict_list
        self.member = member
    def __getitem__(self, index):
        return self.dict_list[index][self.member]
    def __len__(self):
        return self.dict_list.__len__()

# Helper function for addDisplayEntry, the bisect module has unfortunafely no flag to reverse the ordering (we want bigger to lower values as sorting)
# Todo: choose more appropriate container, refactor
# See http://stackoverflow.com/questions/2247394/python-bisect-it-is-possible-to-work-with-descending-sorted-lists
def reverse_bisect(a, x, lo=0, hi=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if x > a[mid]: hi = mid
        else: lo = mid+1
    return lo

def idFromTitle(title):
    return re.sub(r'[^\w]', '_', title.replace(' ','_'))

# This event generator listens for incoming complete utterance redis events
# and starts the process of finding relevant information after each utterance with the keyword_extract module
# (relevant text and pictures are downloaded in a blocking manner using wiki_search)
class EventGenerator:

    def __init__(self,keyword_server_url, keyword_extrator, lang='en', decay=0.95, max_entries=4, blacklist_file=''):
        self.complete_transcript = []

        #dict with all relevant entries
        self.relevant_entries = {}
        #sorted list of displayed entries
        self.displayed_entries = []
        #number of times a wikipedia category has been encountered, from all added articles
        self.categories = defaultdict(int)
        self.keyword_client = KeywordClient(keyword_server_url)
        self.ke = keyword_extrator
        self.lang = lang
        self.decay = decay
        self.max_entries = max_entries

        if self.lang == 'en':
            self.wiki_category_string = u'Category:'
        elif self.lang == 'de':
            self.wiki_category_string = u''
        else:
            print 'WARNING, unknown language', self.lang
            self.wiki_category_string = ''

        self.blacklist_ids = {}
        if blacklist_file != '':
            with codecs.open(blacklist_file,'r','utf-8') as infile:
                for line in infile:
                    print 'blacklist wiki id:',line[:-1]
                    self.blacklist_ids[line[:-1]] = 1


    def topCategories(self,maxCategories=6):
        topCat = sorted(self.categories.items(), key=lambda x:x[1], reverse=True)
        topCat_json = [{'entry_id':idFromTitle(cat[0]),'title':cat[0].replace(u'Kategorie:',u''), 'url': u'https://simple.wikipedia.org/wiki/'
                    + self.wiki_category_string + cat[0].replace(' ','_'), 'score': cat[1]} for cat in topCat if cat[1] > 1 and 'Wikipedia:' not in cat[0]]
        return topCat_json[:maxCategories]

    #Listen loop (redis)
    #Todo: for other languages than English, utf8 de and encoding will be needed
    def start_listen(self):
        pubsub = red.pubsub()
        pubsub.subscribe(my_redis_channel)
        for message in pubsub.listen():
            print 'New message:', message, type(message['data'])
            if type(message['data']) == str:
                json_message = json.loads(message['data'])
                if 'handle' in json_message:
                    if json_message['handle'] == 'completeUtterance':
                        print 'handle: completeUtterance'
                        self.complete_transcript.append(json_message['utterance'])
                        self.send_relevant_entry_updates(self.max_entries,self.decay)
                    if json_message['handle'] == 'closed':
                        print 'handle: closed'
                        self.delDisplayId(json_message['entry_id'])
                        print json_message
                    elif json_message['handle'] == 'reset':
                        print 'handle: reset all'
                        self.complete_transcript = []
                        self.relevant_entries = {}
                        self.displayed_entries = []
                        self.categories = defaultdict(int)
                        self.keyword_client.resetTimer()
                    elif json_message['handle'] == 'setLanguage':
                        print 'handle: set language' #todo

    # Add a relevant entry to the display, specify how many entries should be allowed maximally 
    def addDisplayEntry(self, entry_type, entry, max_entries=4):
        print 'check to add', entry['title'], entry['score']
        
        #TODO: Refactor the entry_type diretly into entry
        if 'type' not in entry:
            entry['type'] = entry_type

        if 'entry_id' not in entry:
            entry['entry_id'] = idFromTitle(entry['title'])

        if entry['entry_id'] in self.blacklist_ids:
            return False

        #Determine position by its score
        displayed_entries_get_score = dict_list_index_get_member(self.displayed_entries,'score')
        insert_pos = reverse_bisect(displayed_entries_get_score, float(entry['score']))
        
        #Only add entry if we want to insert it into the max_entries best entries
        if insert_pos < max_entries:
            
            self.displayed_entries.insert(insert_pos, dict(entry))
            len_displayed_entries = len(self.displayed_entries)

            #In this case, one of the previous best entries needs to be deleted:
            if(len_displayed_entries > max_entries):
                #Send delete entry events to entries those score is below the four best showed entries
                for display_entry in self.displayed_entries[max_entries:]:
                    print 'del', display_entry['entry_id'], 'score fell below max_entries'
                    self.keyword_client.delRelevantEntry(display_entry['type'], display_entry['title'])

                self.displayed_entries = self.displayed_entries[:max_entries]
                len_displayed_entries = len(self.displayed_entries)

            if insert_pos == len_displayed_entries -1:
                insert_before = end_marker
                print 'Insert',entry['entry_id'],'at the end'
            else:
                insert_before = self.displayed_entries[insert_pos+1]['entry_id']
                print 'Insert',entry['entry_id'],'before',insert_before

            print 'add', entry['title'], entry['score']
            self.keyword_client.addRelevantEntry('wiki', entry['title'], entry['text'], entry['url'], entry['score'], insert_before)
            return True

        else:
            print "Insert pos is:", insert_pos, "below max_entries for",  entry["title"]
            return False

    # Delete a relevant entry from the display
    def delDisplayEntry(self, entry_type, title):
        print 'del',title
        for i,display_entry in list(enumerate(self.displayed_entries)):
            if (display_entry["title"] == title):
                print 'del', display_entry["title"]
                self.keyword_client.delRelevantEntry(entry_type, title)
                del self.displayed_entries[i]
                break

    # Delete a relevant entry from the model (without sending updates to the display)
    def delDisplayId(self, entry_id):
        print 'del id',entry_id
        for i,display_entry in list(enumerate(self.displayed_entries)):
            if (display_entry['entry_id'] == entry_id):
                print 'del', entry_id
                #self.keyword_client.delRelevantEntry(entry_type, title)
                del self.displayed_entries[i]
                break

    # Send relevant entry updates to the display, given a new full utterance. 
    # Also specify how many entries we want (max_entries) and how existing keywords should decay their score.
    def send_relevant_entry_updates(self,max_entries=4, decay=.9, context_utts=9, extract_top_n_keywords=10, min_found_keywords=3, min_transcript_utts=2):

        print 'send_relevant_entry_updates called'
        with Timer() as t:

            #Do the decay for the displayed entries:
            #TODO: handle duplicate keywords and updated scores
            for entry in self.displayed_entries:
                entry["score"] *= decay

            # keywords = self.ke.getKeywordsDruid(self.complete_transcript[-1])
            # Take last 10 utterances and combine them
            most_recent_transcript = " ".join(self.complete_transcript[-context_utts:])
            # Extract top 9 keywords
            keywords = self.ke.extract_best_keywords(most_recent_transcript, n_words=extract_top_n_keywords)
            print keywords

            #abort if we found very little keywords and haven't seen enough utterances
            if len(keywords) < min_found_keywords or len(self.complete_transcript) < min_transcript_utts:
                return

            # Extract top wiki articles
            new_relevant_entries = wiki_search_es.extract_best_articles(keywords, n=max_entries)
            print "-> Extracted top ", len(new_relevant_entries), " documents", [(entry["title"], entry["score"]) for entry in new_relevant_entries]

            new_relevant_entries = dict(zip([entry["title"] for entry in new_relevant_entries],
                                            [entry for entry in new_relevant_entries ] ) ) 


            new_relevant_entries_set = set(new_relevant_entries)
            relevant_entries_set = set(self.relevant_entries)
                
            num_added = 0

            #generate add relevant entries
            for key in new_relevant_entries_set - relevant_entries_set:
                entry = new_relevant_entries[key]
                if self.addDisplayEntry("wiki", entry):
                    num_added += 1
                    for category in entry["categories"]:
                        self.categories[category] += 1  

            #now look for changed scores (happens if a keyword got more important and gets mentioned again)   
            for key in (new_relevant_entries_set & relevant_entries_set):
                entry = new_relevant_entries[key]
                if entry["score"] > self.relevant_entries[key]["score"]:
                    print "score change for:",entry["title"], self.relevant_entries[key]["score"], "->", entry["score"]
                    found_displayed_entry = False
                    for display_entry in self.displayed_entries:
                        #already displayed, we could delete and read it, to reflect the new placement
                        if display_entry["title"] == key:
                            found_displayed_entry = True
                            #self.delDisplayEntry("wiki", entry["title"])
                            #self.addDisplayEntry("wiki", entry)
                            break

                    if not found_displayed_entry:
                        #not displayed, try to see if the higher score gets results in a document that is more important
                        self.addDisplayEntry("wiki", entry)

            for key in new_relevant_entries_set - relevant_entries_set:
                self.relevant_entries[key] = new_relevant_entries[key]

        topCategories_Event = self.topCategories()
        print topCategories_Event
        # TODO: only send something if topCategories actually changes
        self.keyword_client.sendCategories(topCategories_Event)

        print 'send_relevant_entry_updates finished. Time needed:', t.secs, 'seconds.'
        print 'Displayed entries should now be:',[entry['title'] for entry in self.displayed_entries]
        print 'Added:',num_added

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line client for kaldigstserver and the ambient visualization server')
    parser.add_argument('-a', '--ambient-uri', type=str, default='http://localhost:5000/', dest='ambient_uri', help='Ambient server websocket URI')
    parser.add_argument('-c', '--cutoff-druid-score', type=float, default=0.5, dest='cutoff_druid_score', help='Cutoff score for the druid algorithm, '
        'lower value will find more keywords, but takes longer to load and needs more memory')
    parser.add_argument('-l', '--language', type=str, default='en', dest='language', help='Select a language for the relevant evant geneartor (en,de). Defaults to en.')
    parser.add_argument('-d', '--decay', type=float, default=0.8, dest = 'decay', help='Score decay for displayed entries (so that new entries can come to replace the older ones')

    use_extra_keywords = False
    use_blacklist_file = False

# This has been used for demonstratory purporses in early stages of development. You can activate it 
#    parser.add_argument('-e', '--extra-keywords', type=str, default = '', dest = 'extra_keywords', help='Add these user defined extra keywords (filename)')
#    parser.add_argument('-b', '--blacklist-ids', type=str, default = '', dest = 'blacklist_file', help='Never show these wikipedia ids!')
#    use_extra_keywords = True
#    use_blacklist_file = True

    args = parser.parse_args()
    ke = keyword_extract_w2v.W2VKeywordExtract(
        lang=args.language, extra_keywords=(args.extra_keywords if use_extra_keywords else ''), cutoff_druid_score=args.cutoff_druid_score)

    event_gen = EventGenerator(args.ambient_uri, ke, lang=args.language, decay=args.decay, blacklist_file=(args.blacklist_file if use_extra_keywords else ''))
    event_gen.start_listen()

