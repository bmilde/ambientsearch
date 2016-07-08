#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker, Benjamin Milde'

from elasticsearch import Elasticsearch
import nltk
import traceback
import nltk.data

wiki_index = 'simple_en_wiki_may2016'
default_type = 'page'

sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

# Currently using a public server. Configure this to your own server.
es = Elasticsearch([
    {'host': 'wiki.machinelearning.online', 'port': 80}
], send_get_body_as='POST')

# Build a full ES query with filters (to remove redirect and special pages) 
# and matching typical wiki fields (["text", "title", "category"]), for a simple query string
# e.g. es_full_query_with_wiki_filters(query="woman~ spiritual~ 'mutual aid'~ kind~ religion~ mormon~ mormonism~ religious~")

def es_full_query_with_wiki_filters(query,minimum_should_match_percent=30):
    query = {
        "query": {
            "filtered": {
               "query": {
                   "query_string": {
                       "fields": ["text", "title", "category"],
                       "query": query,
                       "minimum_should_match": str(minimum_should_match_percent)+"%",
                       "use_dis_max": "false",
                       "phrase_slop": "0"
                   }
               },
               "filter": {
                   "bool": {
                       "must": [
                          {"term": {
                             "special": "false"
                          }},
                          {"term": {
                              "redirect": "false"
                          }}
                       ],
                       "must_not": [
                          {"query": {"match": {
                             "text": "#redirect"
                          }}}
                       ]
                   }
               }
            }
        }
    }
    return query


# Expects a set of keywords along with their scores (Tuples).
# Returns an es-compatible query string (see example query field above).
# Scores boost each keyword along with their scores, fuzziness also matches different spellings.
# Recommendation: Scores - yes, fuzziness - yes, Multiword - yes
def construct_query_string(keywords, scores=True, fuzziness=False, multiword=True):
    keyword_strings = []

    for keyword, score in keywords:
        keyword = keyword.replace('_', ' ')

        # Phrases need to be in quotation marks
        if multiword and len(keyword.split()) > 1:
            keyword = "\"" + keyword + "\""

        # Fuzziness rather causes problems (~)
        if fuzziness:
            keyword += "~"
        if scores:
            keyword += "^" + str(score)

        keyword_strings.append(keyword)

    return " ".join(keyword_strings)

#Adapted from http://stackoverflow.com/questions/14596884/remove-text-between-and-in-python
def clean_wiki_brackets(text):
  ret = ''
  skip1c = 0
  skip2c = 0
  skip3c = 0
  skip4c = 0

  for i in text:
      if i == '[':
          skip1c += 1
      elif i == '(':
          skip2c += 1
      elif i == '{':
          skip3c += 1
      elif i == '|':
          skip4c += 1    
      elif i == ']' and skip1c > 0:
          skip1c -= 1
      elif i == ')'and skip2c > 0:
          skip2c -= 1
      elif i == '}'and skip3c > 0:
          skip3c -= 1
      elif i == '|'and skip4c > 0:
          skip4c -= 1
      elif skip1c == 0 and skip2c == 0 and skip3c == 0 and skip4c == 0:
          ret += i
  return ret

# Extracts the first n words from the given text.
def get_summary_from_text(text, n=50):
    #print '-> fulltext:',text[:500]
    text = clean_wiki_brackets(text)

    # This is actually specific to stream2es, which sometimes returns broken wiki text.
    # This is an attempt to fix it.

    if ']]' in text:
        text = ''.join(text.split(']]')[1:])
    #print '-> fulltext cleaned:',text[:500]

    sents = sent_detector.tokenize(text)

    summary = ''

    i = 0
    while(len(summary) < n and i < len(sents)):
        summary += sents[i] + ' '
        i += 1

    #print 'summary:', summary

    return summary

# Expects a set of keywords along with their scores (Tuples).
# Extracts the n best scoring article results from elasticsearch. Use n=-1 if you want all articles returned.
def extract_best_articles(keywords, n=10, minimum_should_match_percent=25, min_summary_chars=50):

    simple_query_string = construct_query_string(keywords)
    print 'wiki search query:',simple_query_string
    query = es_full_query_with_wiki_filters(simple_query_string,minimum_should_match_percent)

    summary_box_infos = []

    try:
        results = es.search(index=wiki_index, doc_type=default_type, body=query)
    except Exception as ex:
        traceback.print_exc()
        summary_box_info = [{'title': 'Elasticsearch Error',
            'text': 'Unable to connect to elasticsearch server. Server running?',
            'url': 'https://www.elastic.co/',
            'categories': [],
            'score': 10}]
        return summary_box_info

    for result in results['hits']['hits']:

        title = result['_source']['title']
        full_text = result['_source']['text']
        categories = result['_source']['category']
        score = result['_score']
        summary = get_summary_from_text(full_text,min_summary_chars)
        url = 'https://simple.wikipedia.org/w/index.php?title='+title.replace(' ', '_')
        print 'wiki search: found',title,'with score',score

        summary_box_infos.append({
            'title': title,
            'text': summary,
            'url': url,
            'categories': categories,
            'score': score
        })

    summary_box_infos = sorted(summary_box_infos, key=lambda x: x['score'], reverse=True)

    if n != -1:
        summary_box_infos = summary_box_infos[:n]

    return summary_box_infos
