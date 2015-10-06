import redis

import keyword_extract
import wiki_search
import argparse
import json

from bridge import KeywordClient

red = redis.StrictRedis()

#This event generator listens for incoming complete utterance redis events
#and starts the process of finding relevant information after each utterance with the keyword_extract module
#(relevant text and pictures are downloaded in a blocking manner using wiki_search)
class EventGenerator:

    def __init__(self,keyword_server_url, keyword_extrator):
        self.complete_transcript = []
        self.last_relevant_entries = {}
        self.keyword_client = KeywordClient(keyword_server_url)
        self.ke = keyword_extrator

    #Listen loop (redis)
    #Todo: for other languages than English, utf8 de and encoding will be needed
    def start_listen(self):
        pubsub = red.pubsub()
        pubsub.subscribe('ambient_transcript_only')
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
                        self.complete_transcript = []
                        self.last_relevant_entries = []

    def send_relevant_entry_updates(self,max_entries=4):
        print 'send_relevant_entry_updates called'
        keywords = self.ke.getKeywordsDruid('\n'.join([sentence[:-1] for sentence in self.complete_transcript]))
        relevant_entries = wiki_search.getSummariesSingleKeyword(keywords,max_entries,lang='en',pics_folder='pics/')
        print relevant_entries

        #generate add relevant entries
        for key in set(relevant_entries) - set(self.last_relevant_entries):
            entry = relevant_entries[key]
            self.keyword_client.addRelevantEntry("wiki", entry["title"], entry["text"], entry["url"], entry["score"])
            print 'add',key
        #generate del relevant entries
        for key in set(self.last_relevant_entries) - set(relevant_entries):
            entry = self.last_relevant_entries[key]
            self.keyword_client.delRelevantEntry("wiki", entry["title"])
            print 'del',key

        self.last_relevant_entries = relevant_entries

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line client for kaldigstserver and the ambient visualization server')
    parser.add_argument('-a', '--ambient-uri', type=str, default='http://localhost:5000/', dest='ambient_uri', help='Ambient server websocket URI')
    parser.add_argument('-c', '--cutoff-druid-score', type=float, default=0.2, dest='cutoff_druid_score', help='Cutoff score for the druid algorithm, '
        'lower value will find more keywords, but takes longer to load and needs more memory')

    args = parser.parse_args()
    ke = keyword_extract.KeywordExtract()
    ke.buildDruidCache(cutoff_druid_score=args.cutoff_druid_score)

    event_gen = EventGenerator(args.ambient_uri, ke)
    event_gen.start_listen()
