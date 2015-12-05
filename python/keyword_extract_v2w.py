#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

import nltk
import bz2
import codecs
import re
import operator
from collections import defaultdict
from topia.termextract import extract
import wiki_search
import os.path
import sys
import gensim

# compiled regex that can check if a string contains numbers
RE_D = re.compile('\d')

common_words = {}


def check_path(path):
    if not os.path.isfile(path):
        path = 'python/' + path
        if not os.path.isfile(path):
            print 'Could not load ', path, '!'
            sys.exit(-1)
    return path

def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

common_words_path = check_path(os.path.join(data_directory(), 'stop_words.txt'))
lda_model_path = check_path(os.path.join(data_directory(), 'enwiki-latest-pages-articles-mallet.lda'))
dictionary_path = check_path(os.path.join(data_directory(), 'enwiki-latest-pages-articles_wordids.txt.bz2'))

with codecs.open(common_words_path, 'r', 'utf-8') as common_words_file:
    for line in common_words_file:
        common_words[line[:-1]] = 1


class KeywordExtract:

    def __init__(self):
        self.keyword_extractor = extract.TermExtractor()
        self.keyword_extractor.filter = extract.permissiveFilter
        self.keyword_dict = {}
        print 'Loading Dictionary...'
        self.dict = gensim.corpora.Dictionary.load_from_text(bz2.BZ2File(dictionary_path))
        print 'Loading LDA model...'
        self.model = gensim.models.LdaModel.load(lda_model_path)
        self.model.load_word_topics()

    def get_keywords(self, text):
        return




if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = KeywordExtract()
    # test = ke.get_keywords_druid(u"A columbia university law professor stood in a hotel lobby one morning and"
    #                              u"noticed a sign apologizing for an elevator that was out of order."
    #                              u"it had dropped unexpectedly three stories a few days earlier."
    #                              u"the professor, eben moglen, tried to imagine what the world would be like"
    #                              u"if elevators were not built so that people could inspect them. mr. moglen"
    #                              u"was on his way to give a talk about the dangers of secret code,"
    #                              u"known as proprietary software, that controls more and more devices every day."
    #                              u"proprietary software is an unsafe building material, mr. moglen had said."
    #                              u"you can't inspect it. he then went to the golden gate bridge and jumped.")
    # print test
    # print wiki_search.get_summaries_single_keyword(test)
    # test = ke.get_keywords_druid(u"So i was walking down the golden gate bridge, i had the epiphany that in order"
    #                              u"to be a good computer scientist, i need to learn and practise machine learning."
    #                              u"Also proprietary software is the root of all evil and I should better use open"
    #                              u"source software.")
    # print test
    # print wiki_search.get_summaries_single_keyword(test)
