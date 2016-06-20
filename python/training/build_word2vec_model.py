#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker'

from gensim.models import Word2Vec
from os.path import join, dirname, abspath, basename, exists
import logging
import sys
import time
import multiprocessing
import wikidump2text
import druid
import nltk
import codecs
import argparse

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = basename(sys.argv[0])
logger = logging.getLogger(program)

class MySentences(object):
    def __init__(self, filename, druid_dict, multiwords=True):
        self.filename = filename
        self.stemmer = nltk.stem.PorterStemmer()
        self.druid_dict = druid_dict
        self.multiwords = multiwords

    def __iter__(self):
        # One line contains one wiki article.
        self.corpus = codecs.open(self.filename, 'r', encoding='utf-8')
        for line in self.corpus:
            if line[-1] == '\n':
                line = line[:-1]
            if self.multiwords:
                ngrams = self.druid_dict.find_ngrams(line.lower().split())
            else:
                # actually just unigrams in this case
                ngrams = line.lower().split()
            yield [self.stemmer.stem(token) for token in ngrams]

def train_w2v(data_directory, corpus_path, wiki_text_output_path, word2vec_output_path, w2v_dim, multiwords=True):
    start_time = time.time()
    
    # Convert Wikipedia XML dump into .txt format
    if not exists(wiki_text_output_path):
        logger.info('Converting ' + str(corpus_path) + ' into plain text file: ' + wiki_text_output_path) 
        wikidump2text.convert(corpus_path, wiki_text_output_path)

    # Load Multiword Expressions as Dictionary
    stopwords_path = join(data_directory, 'stopwords_en.txt')

    if multiwords:
        logger.info('Using druid_en.bz2 in  ' + data_directory + ' as multiword dictionary.')
        druid_path = join(data_directory, 'druid_en.bz2')
        druid_dict = druid.DruidDictionary(druid_path, stopwords_path, cutoff_score=0.2)

        # Train the word2vec model, also use DRUID multiwords
        sentences = MySentences(wiki_text_output_path, druid_dict, multiwords=True)  # a memory-friendly iterator
    else:
        logger.info('Using no multiword dicitionary, just single words')
        sentences = MySentences(wiki_text_output_path, None, multiwords=False)

    # bigram_transformer = Phrases(sentences)
    # logger.info("Finished transforming bigrams. Time needed: " + str(time.time() - start_time))
    
    logger.info("Starting model training, will save to: " + word2vec_output_path)
    model = Word2Vec(sentences, size=w2v_dim, window=5, min_count=5, workers=multiprocessing.cpu_count())

    # trim unneeded model memory = use(much) less RAM
    model.init_sims(replace=True)
    
    logger.info("Saving to the following path: " + word2vec_output_path)
    model.save(word2vec_output_path, ignore=[])

    logger.info("Finished building Word2Vec model. Time needed: " + str(time.time() - start_time))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', '--data-directory', dest='data_directory', help='Data directory, corpus is read from this directory and the output model is saved here', type=str, default = './data/')
    parser.add_argument('-c', '--corpus-path', dest='corpus_path', help='Input corpus comment file', type=str, default = 'simplewiki-latest-pages-articles.xml.bz2')
    parser.add_argument('-w', '--wiki-text-output-path', dest='wiki_text_output_path', help='Wiki text output path (converted from raw wikipedia xml)', type=str, default = 'simplewiki-latest-pages-articles.txt')
    parser.add_argument('-o', '--word2vec-output-path', dest='word2vec_output_path', help='Output model file', type=str, default = 'simple-enwiki-latest.word2vec')
    parser.add_argument('-v', '--w2v-dim',  dest='w2v_dim', help='The dimensionality of the word2vec vectors', default=100)
    parser.add_argument('-nm', '--no-multiwords', dest='no_multiwords', help='No multiwords in model generation', action='store_true', default=False)

    args = parser.parse_args()

    logger.info('Using data directory: ' + args.data_directory)

    corpus_path = join(args.data_directory, args.corpus_path)
    wiki_text_output_path = join(args.data_directory, args.wiki_text_output_path)
    word2vec_output_path = join(args.data_directory, args.word2vec_output_path)

    train_w2v(args.data_directory, corpus_path, wiki_text_output_path, word2vec_output_path, args.w2v_dim, not args.no_multiwords)

