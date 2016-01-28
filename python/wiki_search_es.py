#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

from elasticsearch import Elasticsearch
import nltk

wiki_index = 'en-simple-wiki'
default_type = 'page'

es = Elasticsearch([
    {'host': 'localhost', 'port': 9200}
], send_get_body_as='POST')

query = {
    "query": {
        "filtered": {
           "query": {
               "simple_query_string": {
                  "fields": ["text", "title", "category"],
                  "query": "woman~ spiritual~ 'mutual aid'~ kind~ religion~ mormon~ mormonism~ religious~",
                  "minimum_should_match": "30%"

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

# Expects a set of keywords along with their scores (Tuples).
# Returns an es-compatible simple query string.
def construct_simple_query_string(keywords, use_scores = True):
    if use_scores:
        query_string = " ".join(["'" + keyword.replace('_', ' ') + "'" + "~^" + str(score) for keyword, score in keywords])
    else:
        query_string = " ".join(["'" + keyword.replace('_', ' ') + "'" + "~" for keyword, score in keywords])

    return query_string

# Extracts the first n words from the given text.
def get_summary_from_text(text, n=20):
    return " ".join(nltk.word_tokenize(text)[:n])

# Expects a set of keywords along with their scores (Tuples).
# Extracts the n best scoring article results from elasticsearch.
def extract_best_articles(keywords, n=10):
    simple_query_string = construct_simple_query_string(keywords)
    query['query']['filtered']['query']['simple_query_string']['query'] = simple_query_string

    summary_box_info = {}
    articles = []

    try:
        results = es.search(index=wiki_index, doc_type=default_type, body=query)
    except Exception:
        summary_box_info['error'] = {
            'title': 'Elasticsearch Error',
            'text': 'Unable to connect to elasticsearch server. Server running?',
            'url': 'https://www.elastic.co/',
            'categories': [],
            'score': 1
        }
        return summary_box_info

    for result in results['hits']['hits']:
        title = result['_source']['title']
        full_text = result['_source']['text']
        categories = result['_source']['category']
        score = result['_score']
        summary = get_summary_from_text(full_text)
        url = 'https://simple.wikipedia.org/w/index.php?title='+title.replace(' ', '_')

        summary_box_info[title] = {
            'title': title,
            'text': summary,
            'url': url,
            'categories': categories,
            'score': score
        }

    return summary_box_info
