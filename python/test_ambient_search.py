#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

import keyword_extract_w2v
import wiki_search_es
import os
import codecs
import nltk
import time

num_test_transcripts = 30

def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = keyword_extract_w2v.W2VKeywordExtract()
    ted_root_dir = os.path.join(data_directory(), 'ted_transcripts')
    
    # Fetching number of keywords to extract
    keyword_counts = {}
    with codecs.open('goal_goals.txt', 'r', encoding='utf-8', errors='replace') as in_file:
        for line in in_file:
            keyword_counts[line.split()[0].split('/')[-1]] = int(line.split()[-1])

    i = 0
    for file in sorted(os.listdir(ted_root_dir)):
        if file.endswith('.txt'):
            with codecs.open(os.path.join(ted_root_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
                print 'Processing', file, ':'

                raw = in_file.read()
                num_tokens = keyword_counts[file]

                start_time = time.time()

                print 'Extracting keyphrases...'
                tokens = ke.habibi_mimic(raw, n=num_tokens)
                print 'Done extracting keyphrases. Time needed:', time.time() - start_time

                print '==========Text=========='
                for sentence in nltk.sent_tokenize(raw):
                    print sentence
                print '==========Keyphrases=========='
                print tokens

                start_time = time.time()
                print 'Retrieving best articles...'
                results = wiki_search_es.extract_best_articles(tokens, n=10)
                print 'Done retrieving articles. Time needed:', time.time() - start_time

                # Convert resulting dictionary into sorted list
                sorted_results = []
                for key, value in results.iteritems():
                    sorted_results.append(value)
                sorted_results = sorted(sorted_results, key=lambda item: item['score'], reverse=True)

                for article in sorted_results:
                    print '==========Article=========='
                    print 'Title:', article['title']
                    #print 'Summary:', article['text']
                    #print 'URL:', article['url']
                    print 'Categories:', article['categories']
                    print 'Score:', article['score']

                i += 1
                if i == num_test_transcripts:
                    break
