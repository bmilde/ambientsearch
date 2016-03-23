#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

from gensim.corpora import WikiCorpus
from os.path import isfile, basename
import logging
import sys
import time

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = basename(sys.argv[0])
logger = logging.getLogger(program)


def check_path(path):
    if not isfile(path):
        path = 'python/'+path
        if not isfile(path):
            print 'Could not find ', path, '!'
            sys.exit(-1)
    return path


# Converts a Wikipedia bz2-compressed XML dump to a text corpus and saves the output.
def convert(input_path, output_path):
    logger.info("Converting Wiki Corpus...")
    corpus_path = check_path(input_path)
    wiki_text_output_path = output_path

    start_time = time.time()

    space = " "
    i = 0

    wiki = WikiCorpus(corpus_path, lemmatize=False, dictionary={})

    output = open(wiki_text_output_path, 'w')

    # Convert WikiCorpus into Text output (1 article per line)
    for text in wiki.get_texts():
        output.write(space.join(text) + '\n')
        i += 1
        if i % 10000 == 0:
            logger.info("Saved " + str(i) + " articles")

    output.close()
    logger.info("Finished Saved " + str(i) + " articles. Time needed: " + str(time.time() - start_time))
