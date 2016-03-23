#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

# By default gensim uses an online LDA implementation based on Hierarchical Bayesian modeling by Hoffman et al
# Mallet uses a parallel Gibbs sampling implementation of LDA by Newman et al
# According to http://rare-technologies.com/tutorial-on-mallet-in-python/ it is more accurate than the bayesian methods

# INSTRUCTIONS:
# 1) Download a Wikipedia XML Dump and save it in python/data
# 2) Convert the dump into a gensim-valid corpus using training/build_wiki_corpus.py
# 3) Download mallet toolkit and save it to python/data
# 4) Run this script with correct file paths => the LDA model will be saved under <filename>.lda for future use.

# Wikipedia corpus of 109666 documents with 79378353 positions
# (total 286888 articles, 80115807 positions before pruning articles shorter than 50 words)

import logging
import bz2
import os.path
from gensim import corpora, models, utils


def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Path to mallet binary file in the data directory
mallet_path = os.path.join(data_directory(), 'mallet-2.0.7/bin/mallet')
# Path to the dictionary file in the data directory
dictionary_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles_wordids.txt.bz2')
# Path to the training corpus in the data directory
corpus_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles_bow.mm')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# load id->word mapping (the dictionary), one of the results of step 2 above
id2word = corpora.Dictionary.load_from_text(bz2.BZ2File(dictionary_path))
# load corpus iterator
corpus = corpora.MmCorpus(corpus_path)
# mm = gensim.corpora.MmCorpus(bz2.BZ2File('wiki_en_tfidf.mm.bz2')) # use this if you compressed the TFIDF output

# train 100 LDA topics using MALLET (takes about 1 hour to train on 4-core machine with 8GB RAM)
# stores the mallet output under prefix
if not os.path.exists(os.path.join(data_directory(), 'mallet_output/')):
    os.makedirs(os.path.join(data_directory(), 'mallet_output/'))
model = models.wrappers.LdaMallet(mallet_path, corpus, num_topics=100, id2word=id2word,
                                  prefix=os.path.join(data_directory(), 'mallet_output/'))
model.save(os.path.join(data_directory(), 'enwiki-latest-pages-articles_mallet.lda'))

# now use the trained model to infer topics on a new document
doc = "Don't sell coffee, wheat nor sugar; trade gold, oil and gas instead."
bow = id2word.doc2bow(utils.simple_preprocess(doc))
print model[bow]  # print list of (topic id, topic weight) pairs
