#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

from gensim.corpora import WikiCorpus
from gensim.models import Word2Vec, Phrases
import os.path
import logging
import sys
import time
import multiprocessing
import wikidump2text
import druid
from nltk.corpus import PlaintextCorpusReader


def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

corpus_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles12.xml-p001825001p002425000.bz2')
wiki_text_output_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles12.txt')
word2vec_output_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles.word2vec')


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)

# Convert Wikipedia XML dump into .txt format
wikidump2text.convert(corpus_path, wiki_text_output_path)


start_time = time.time()

# Train the word2vec model


class MySentences(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        # One line contains one wiki article.
        for line in open(self.filename):
            yield line.split()

sentences = MySentences(wiki_text_output_path)  # a memory-friendly iterator
bigram_transformer = Phrases(sentences)
logger.info("Finished transforming bigrams. Time needed: " + str(time.time() - start_time))
start_time = time.time()
model = Word2Vec(bigram_transformer[sentences], size=100, window=5, min_count=5, workers=multiprocessing.cpu_count())

# trim unneeded model memory = use(much) less RAM
model.init_sims(replace=True)
model.save(word2vec_output_path)

logger.info("Finished building Word2Vec model. Time needed: " + str(time.time() - start_time))
