#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Radim Rehurek <radimrehurek@seznam.cz>
# Copyright (C) 2012 Lars Buitinck <larsmans@gmail.com>
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html


"""
Converts a Wikipedia XML Dump into a gensim-compatible model and saves it to python/data.

Usage: python build_wiki_corpus.py enwiki-latest-pages-articles<version>.xml.bz2 OUTPUT_PREFIX
"""


import logging
import os.path
import sys

from gensim.corpora import Dictionary, MmCorpus, WikiCorpus
from gensim.models import TfidfModel


def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Size of the dictionary (# of most frequent types are kept after removal of stop-words)
keep_words = 100000
# Lemmatization (slows down the process a lot, but uses a good lemmatizer)
# Requires python pattern package to be installed. Otherwise simple RegExp Lemmatizer is used.
lemmatize = False
# Upper limit for word occurences: words that appear in more than X% of the documents are removed (too common)
max_threshold = 0.2
# Lower threshold for word occurences: words that appear in less than N documents are removed (too uncommon)
min_threshold = 20
# Stop words filename for stop words in spoken language
stop_words_file = os.path.join(data_directory(), 'stop_words.txt')

if __name__ == '__main__':
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))

    if len(sys.argv) < 3:
        print(globals()['__doc__'] % locals())
        sys.exit(1)

    inp = sys.argv[1]
    prefix = sys.argv[2]
    outp = os.path.join(data_directory(), prefix)

    wiki = WikiCorpus(inp, lemmatize=lemmatize)
    # only keep the most frequent words
    wiki.dictionary.filter_extremes(no_below=min_threshold, no_above=max_threshold, keep_n=keep_words)

    # Remove stop words (additional removal of common words used in spoken language)
    stop_ids = []
    with open(stop_words_file, 'r') as infile:
        for line in infile:
            try:
                stop_ids.append(wiki.dictionary.token2id[line.lower().strip()])
            except KeyError:
                continue
    wiki.dictionary.filter_tokens(bad_ids=stop_ids)

    # save dictionary and bag-of-words (term-document frequency matrix)
    MmCorpus.serialize(outp + '_bow.mm', wiki, progress_cnt=10000)
    wiki.dictionary.save_as_text(outp + '_wordids.txt.bz2')
    # load back the id->word mapping directly from file
    # this seems to save more memory, compared to keeping the wiki.dictionary object from above
    dictionary = Dictionary.load_from_text(outp + '_wordids.txt.bz2')

    del wiki

    # initialize corpus reader and word->id mapping
    mm = MmCorpus(outp + '_bow.mm')

    # build tfidf
    tfidf = TfidfModel(mm, id2word=dictionary, normalize=True)
    tfidf.save(outp + '.tfidf_model')

    # save tfidf vectors in matrix market format
    MmCorpus.serialize(outp + '_tfidf.mm', tfidf[mm], progress_cnt=10000)

    logger.info("finished running %s" % program)