#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bz2
import codecs
import re
import os
import sys
import logging
import time

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)

def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not find ', path, '!'
            sys.exit(-1)
    return path


# Filter hypens at the beginning and/or end of a word
# E.g. "schlechteste -> schlechteste
# There are many unicode hyphen variant (which all look very similar), we also want ot filter these
def filter_hyphens(word):
    if word.startswith(u'"') or word.startswith(u"'") or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"'):
        word = word[1:]

    if word.endswith(u'"') or word.endswith(u"'") or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"'):
        word = word[:-1]

    return word


class DruidDictionary:
    def __init__(self, druid_file, stopwords_file, cutoff_score=0.2):
        self.druid_mwe_file = check_path(druid_file)
        self.stopwords_filename = check_path(stopwords_file)
        self.keyword_dict = {}
        # compiled regex that can check if a string contains numbers
        self.RE_D = re.compile('\d')
        self.stopwords = {}
        with codecs.open(self.stopwords_filename, 'r', encoding='utf-8') as stop_words_file:
            for line in stop_words_file:
                self.stopwords[line[:-1]] = 1

        self.build_druid_cache(cutoff_score)

    def build_druid_cache(self, cutoff_druid_score, post_filter=False, old_format=False):
        druid_bz2 = bz2.BZ2File(self.druid_mwe_file, mode='r')
        druid_file = codecs.iterdecode(druid_bz2, 'utf-8')
        num_added_words = 0

        logger.info("Loading DRUID cache...")
        start_time = time.time()

        for line in druid_file:
            split = line.split(u'\t')

            if len(split) == 2:
                old_format=False
                post_filter=False
            else:
                print('Warning, you need to update your Druid dictionary and models.')
                old_format=True
                post_filter=True


            if old_format:
                words = split[1].lower()
            else:
                words = split[0].lower()

            if old_format:
                druid_score = split[2]
            else:
                druid_score = split[1]

            if post_filter:
                has_number = self.RE_D.search(words)
            else:
                has_number = False
            # exclude any lines that have one or more numbers in them
            if not has_number:
                words_split = [filter_hyphens(word) for word in words.split(u' ')]
                float_druid_score = float(druid_score)
                if float_druid_score < cutoff_druid_score:
                    break

                if not post_filter or not any((word in self.stopwords) for word in words_split):
                    self.keyword_dict[words] = float_druid_score
                    num_added_words += 1
                    if num_added_words % 1000 == 0:
                        print words, self.keyword_dict[words]

        logger.info("Finished loading DRUID cache. Time needed: " + str(time.time() - start_time))

    # Converts an ordered list of tokens into n-grams.
    def find_ngrams(self, tokens, n=3):
        filtered_tokens = []

        while len(tokens) > 0:
            longest_gram = tokens[0]

            for gram in range(1, n):
                # Avoid out of range error
                if gram > len(tokens) - 1:
                    break

                # Build ngram
                search_gram = u' '.join([tokens[j] for j in range(gram + 1)])
                if search_gram in self.keyword_dict:
                    longest_gram = search_gram

            # Replace spaces inside ngram with underscores.
            filtered_tokens.append('_'.join(longest_gram.split()))
            # Remove ngram from tokens list
            ngram_length = len(longest_gram.split())
            tokens = tokens[ngram_length:]

        return filtered_tokens


if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    druid_dict = DruidDictionary('data/druid_en.bz2', 'data/stopwords_en.txt', cutoff_score=0.0)

    text = u"""Climate change is real , as is global warming . A columbia university law professor stood in a hotel lobby one morning and
                    noticed a sign apologizing for an elevator that was out of order .
                    it had dropped unexpectedly three stories a few days earlier .
                    the professor , eben moglen , tried to imagine what the world would be like
                    if elevators were not built so that people could inspect them . mr. moglen
                    was on his way to give a talk about the dangers of secret code ,
                    known as proprietary software , that controls more and more devices every day .
                    proprietary software is an unsafe building material , mr. moglen had said .
                    you can't inspect it . he then went to the golden gate bridge and jumped ."""
    print druid_dict.find_ngrams(text.lower().split())

    text = u"""Remote controls are very handy electronic devices that we can use to negotiate with Barack Obama and Angela Merkel new york city is very beautiful with a lot of red blood cells"""
    print druid_dict.find_ngrams(text.lower().split())

