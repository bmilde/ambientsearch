#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Benjamin Milde'

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
import math

def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not ',path,'!'
            sys.exit(-1)
    return path

# Filter hypens at the beginning and/or end of a word
# E.g. "schlechteste -> schlechteste
# There are many unicode hyphen variant (which all look very similar), we also want ot filter these
def filterHyphens(word):
    if word.startswith(u'"') or word.startswith(u"'") or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"'):
        word = word[1:]

    if word.endswith(u'"') or word.endswith(u"'") or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"'):
        word = word[:-1]

    return word

class KeywordExtract:

    def __init__(self, lang='en', extra_keywords=''):
        self.lang = lang
        self.extra_keywords = extra_keywords
        self.keyword_extractor = extract.TermExtractor()
        self.keyword_extractor.filter = extract.permissiveFilter
        self.keyword_dict = {}

        self.common_words_filename = check_path('data/1-1000_'+lang+'.txt')
        self.stopwords_filename = check_path('data/stopwords_'+lang+'.txt')
        self.druid_mwe_file = check_path('data/druid_'+lang+'.bz2')

        self.common_words = {}
        with codecs.open(self.common_words_filename,'r','utf-8') as common_words_file:
            for line in common_words_file:
                self.common_words[line[:-1]] = 1

        self.stopwords = {}
        with codecs.open(self.stopwords_filename,'r','utf-8') as stop_words_file:
            for line in stop_words_file:
                self.stopwords[line[:-1]] = 1

        #compiled regex that can check if a string contains numbers
        self.RE_D = re.compile('\d')

    def getKeywordsTermLib(self, currentHyp, contextWords=200, ignoreNumRecentWords=1, maxKeywords=7):

        tokens = nltk.word_tokenize(u' '.join(self.final_hyps) + u' ' + currentHyp)[-contextWords:(None if currentHyp == '' else -ignoreNumRecentWords)] 

        past_tag = None
        extracted_keywords = self.keyword_extractor(' '.join(tokens))
        extracted_keywords = sorted(extracted_keywords, key=lambda x: x[1]*x[2], reverse=True)
        
        keywords = [keyword[0] for keyword in extracted_keywords]

        return keywords[:maxKeywords]

    #merges keywords and their scores (dict), with keywords_pos dict: index as key, value is a lit of keywords.
    def mergeKeywords(self, keywords, keywords_pos):
        for pos in keywords_pos:
            if len(keywords_pos[pos]) > 1:
                merge_group = keywords_pos[pos]
                lengths = [len(keyword) for keyword in merge_group]
                merge_to_pos = lengths.index(max(lengths))
                merge_to_keyword = merge_group[merge_to_pos]

                #merge all keywords that are not already merged to 'merge_to_keyword', add scores
                for keyword in merge_group:
                    if keyword != merge_to_keyword:
                        if keyword in keywords and merge_to_keyword in keywords:
                            keywords[merge_to_keyword] += keywords[keyword]
                            del keywords[keyword]

        return keywords

    #See http://www.wolframalpha.com/input/?i=plot+%28sigmoid%28x%29+-+0.5%29*2+from+0+to+4
    # Squishes values between 0 and 1 with a sigmoid-like function
    def normalize_keywordscore(self, x):
        if x < 0.0:
            return 0.0
        x *= 1.5
        return ((1.0 / (1.0 + math.exp(-x)))-0.5)*2.0

    #You have to call buildDruidCache, before you call this function
    #Todo: parameterize penality_factor and gram_factor
    def getKeywordsDruid(self, tokens):

        keywords = defaultdict(int)
        keywords_pos = defaultdict(list)

        if len(self.keyword_dict) == 0:
            print 'Warning, no Druid cache found. Wont be able to detect keywords.'
            return []

        #Automatically tokenize strings if nessecary
        if type(tokens) is str or type(tokens) is unicode:
            tokens = nltk.word_tokenize(tokens)

        #Unigram to fourgram
        for x in xrange(1,5):
            seq = nltk.ngrams(tokens, x)
            for i,gram in enumerate(seq):
                search_gram = u' '.join(gram).lower()
                #We score and rank keywords heuristically here and modify the druid score a bit: common words get penalized more, multiwords get a better score
                if len(search_gram) > 2 and search_gram in self.keyword_dict:
                    gram_factor = 1.0
                    if search_gram in self.common_words or search_gram[:-1] in self.common_words:
                        penality_factor = 0.1
                    else:
                        penality_factor = 1.0
                    keywords[search_gram] += self.keyword_dict[search_gram]*(x*gram_factor)*penality_factor

                    for pos in xrange(i,x+i):
                        keywords_pos[pos] += [search_gram]

        #Print keywords_pos
        keywords = self.mergeKeywords(keywords, keywords_pos)
        keywords_sorted = sorted(keywords.items(), key=operator.itemgetter(1), reverse=True)
        # Normalize scores to be in the range of 0.0 - 1.0
        keywords_sorted_normalized = [(item[0],self.normalize_keywordscore(item[1])) for item in keywords_sorted]
        print 'keywords_sorted_normalized:',keywords_sorted_normalized

        return keywords_sorted_normalized

    #Build a dictionary of DRUID keywords. Input is basically a filelist with multiwordness scores for 1-4 grams produced from the algorithm. Numbers and stopwords are filtered, the rest is taken as is.
    def buildDruidCache(self,cutoff_druid_score=0.2):
        druid_bz2 = bz2.BZ2File(self.druid_mwe_file, mode='r')
        druid_file = codecs.iterdecode(druid_bz2, 'utf-8')
        num_added_words=0

        for line in druid_file:
            split = line.split(u'\t')
            words = split[1].lower()
            druid_score = split[2]
            has_number = self.RE_D.search(words)
            #exlude any lines that have one or more numbers in them
            if not has_number:
                words_split = [filterHyphens(word) for word in words.split(u' ')]
                float_druid_score = float(druid_score)
                if float_druid_score > cutoff_druid_score:
                    if not any((word in self.stopwords) for word in words_split):
                        self.keyword_dict[words] = float_druid_score
                        num_added_words += 1
                        if num_added_words % 1000 == 0:
                            print words, self.keyword_dict[words]
                else:
                    break
        if self.extra_keywords != '':
            with codecs.open(self.extra_keywords) as infile:
                for line in infile:
                    words = line[:-1].lower()
                    print 'Loading user set keyword:',words
                    self.keyword_dict[words] = 3.0

if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = KeywordExtract(lang="en")
    ke.buildDruidCache()
    test = ke.getKeywordsDruid(u"A columbia university law professor stood in a hotel lobby one morning and noticed a sign apologizing for an elevator that was out of order. it had dropped unexpectedly three stories a few days earlier. the professor, eben moglen, tried to imagine what the world would be like if elevators were not built so that people could inspect them. mr. moglen was on his way to give a talk about the dangers of secret code, known as proprietary software, that controls more and more devices every day. proprietary software is an unsafe building material, mr. moglen had said. you can't inspect it. he then went to the golden gate bridge and jumped.")
    print test
    print wiki_search.getSummariesSingleKeyword(test)
    test = ke.getKeywordsDruid(u"So i was walking down the golden gate bridge, i had the epiphany that in order to be a good computer scientist, i need to learn and practise machine learning. Also proprietary software is the root of all evil and I should better use open source software.")
    print test
    print wiki_search.getSummariesSingleKeyword(test)
