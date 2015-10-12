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

#This is needed for English. TODO: This is hacky. Move this out of the global scope and make it multi-language (de + en) and move word lists to static files.

#compiled regex that can check if a string contains numbers
RE_D = re.compile('\d')
stopwords_list = ["(",")",",",":","[","]",";",".","...","'","'d","&","$","i","a", "n't", "about", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "along", "already", "also","although","always","am","among", "amongst", "amoungst", "amount",  "an", "and", "another", "any","anyhow","anyone","anything","anyway", "anywhere", "are", "around", "as", "at", "back","be","became", "because","become","becomes", "becoming", "been", "before", "beforehand", "being", "below", "beside", "besides", "between", "beyond", "both", "bottom","but", "by", "call", "can", "cannot", "cant", "could", "couldnt", "cry", "do", "done", "down", "due", "during", "each", "eg", "either", "else", "elsewhere", "enough", "etc", "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few", "for", "former", "formerly", "from", "further", "get", "give", "go", "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his", "how", "however", "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me", "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely", "neither", "never", "nevertheless", "next", "no", "nobody", "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own","part", "per", "perhaps", "please", "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems", "serious", "several", "she", "should", "show", "side", "since", "sincere", "so", "some", "somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still", "such", "system", "take", "ten", "than", "that", "the", "their", "them", "themselves", "then", "thence", "there", "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "thickv", "this", "those", "though", "through", "throughout", "thru", "thus", "to", "together", "too", "top", "toward", "towards", "un", "under", "until", "up", "upon", "us", "very", "via", "was", "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves", "the"]
stopwords = dict(zip([unicode(word) for word in stopwords_list],[1]*len(stopwords_list)))

common_words = {}

def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not ',path,'!'
            sys.exit(-1)
    return path

common_words_filename = check_path('data/1-1000_en.txt')
druid_mwe_file = check_path('data/wikipedia_complete_druid_4gram_en.bz2')

with codecs.open(common_words_filename,'r','utf-8') as common_words_file:
    for line in common_words_file:
        common_words[line[:-1]] = 1

class KeywordExtract:

    def __init__(self):
        self.keyword_extractor = extract.TermExtractor()
        self.keyword_extractor.filter = extract.permissiveFilter
        self.keyword_dict = {}

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
                    if search_gram in common_words or search_gram[:-1] in common_words:
                        penality_factor = 0.1
                    else:
                        penality_factor = 1.0
                    keywords[search_gram] += self.keyword_dict[search_gram]*(x*gram_factor)*penality_factor

                    for pos in xrange(i,x+i):
                        keywords_pos[pos] += [search_gram]

        #Print keywords_pos
        keywords = self.mergeKeywords(keywords, keywords_pos)
        keywords_sorted = sorted(keywords.items(), key=operator.itemgetter(1), reverse=True)

        return keywords_sorted

    #Build a dictionary of DRUID keywords. Input is basically a filelist with multiwordness scores for 1-4 grams produced from the algorithm. Numbers and stopwords are filtered, the rest is taken as is.
    def buildDruidCache(self,cutoff_druid_score=0.2):
        druid_bz2 = bz2.BZ2File(druid_mwe_file, mode='r')
        druid_file = codecs.iterdecode(druid_bz2, 'utf-8')
        num_added_words=0

        for line in druid_file:
            split = line.split(u'\t')
            words = split[1].lower()
            druid_score = split[2]
            has_number = RE_D.search(words)
            #exlude any lines that have one or more numbers in them
            if not has_number:
                words_split = words.split(u' ')
                float_druid_score = float(druid_score)
                if float_druid_score > cutoff_druid_score:
                    if not any((word in stopwords) for word in words_split):
                        self.keyword_dict[words] = float_druid_score
                        num_added_words += 1
                        if num_added_words % 1000 == 0:
                            print words, self.keyword_dict[words]
                else:
                    break

if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = KeywordExtract()
    ke.buildDruidCache()
    test = ke.getKeywordsDruid(u"A columbia university law professor stood in a hotel lobby one morning and noticed a sign apologizing for an elevator that was out of order. it had dropped unexpectedly three stories a few days earlier. the professor, eben moglen, tried to imagine what the world would be like if elevators were not built so that people could inspect them. mr. moglen was on his way to give a talk about the dangers of secret code, known as proprietary software, that controls more and more devices every day. proprietary software is an unsafe building material, mr. moglen had said. you can't inspect it. he then went to the golden gate bridge and jumped.")
    print test
    print wiki_search.getSummariesSingleKeyword(test)
    test = ke.getKeywordsDruid(u"So i was walking down the golden gate bridge, i had the epiphany that in order to be a good computer scientist, i need to learn and practise machine learning. Also proprietary software is the root of all evil and I should better use open source software.")
    print test
    print wiki_search.getSummariesSingleKeyword(test)
