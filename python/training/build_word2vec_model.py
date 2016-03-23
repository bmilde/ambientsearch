#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

from gensim.models import Word2Vec
from os.path import join, dirname, abspath, basename
import logging
import sys
import time
import multiprocessing
import wikidump2text
import druid
import nltk
import codecs


def data_directory():
    return join(dirname(dirname(abspath(__file__))), 'data')

corpus_path = join(data_directory(), 'enwiki-latest-pages-articles12.xml-p001825001p002425000.bz2')
wiki_text_output_path = join(data_directory(), 'enwiki-latest-pages-articles12.txt')
word2vec_output_path = join(data_directory(), 'enwiki-latest-pages-articles.word2vec')


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = basename(sys.argv[0])
logger = logging.getLogger(program)

# Convert Wikipedia XML dump into .txt format
# wikidump2text.convert(corpus_path, wiki_text_output_path)

# Load Multiword Expressions as Dictionary
stopwords_path = join(data_directory(), 'stopwords_en.txt')
druid_path = join(data_directory(), 'druid_en.bz2')
druid_dict = druid.DruidDictionary(druid_path, stopwords_path, cutoff_score=0.0)

# Train the word2vec model


class MySentences(object):
    def __init__(self, filename):
        self.filename = filename
        self.stemmer = nltk.stem.PorterStemmer()

    def __iter__(self):
        # One line contains one wiki article.
        self.corpus = codecs.open(self.filename, 'r', encoding='utf-8')
        for line in self.corpus:
            ngrams = druid_dict.find_ngrams(line.lower().split())
            yield [self.stemmer.stem(token) for token in ngrams]

sentences = MySentences(wiki_text_output_path)  # a memory-friendly iterator
# bigram_transformer = Phrases(sentences)
# logger.info("Finished transforming bigrams. Time needed: " + str(time.time() - start_time))
start_time = time.time()
model = Word2Vec(sentences, size=100, window=5, min_count=5, workers=multiprocessing.cpu_count())

# trim unneeded model memory = use(much) less RAM
model.init_sims(replace=True)
model.save(word2vec_output_path)

logger.info("Finished building Word2Vec model. Time needed: " + str(time.time() - start_time))
