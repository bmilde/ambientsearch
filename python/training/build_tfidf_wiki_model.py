from gensim.models import TfidfModel
from gensim import corpora
from os.path import join, dirname, abspath, basename, exists
import nltk
import logging
import druid
import sys
import codecs
import time
import argparse

import wikidump2text

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = basename(sys.argv[0])
logger = logging.getLogger(program)

class TextCorpus(object):
    def __init__(self, filename, druid_dict, multiwords=True):
        self.corpus = codecs.open(filename, 'r', encoding='utf-8')
        self.druid_dict = druid_dict
        self.stemmer = nltk.stem.PorterStemmer()
        self.multiwords = multiwords

    def __iter__(self):
        # One line contains one wiki article.
        for line in self.corpus:
            if line[-1] == '\n':
                line = line[:-1]

            if self.multiwords:
                ngrams = self.druid_dict.find_ngrams(line.lower().split())
            else:
                ngrams = line.lower().split()

            yield [self.stemmer.stem(token) for token in ngrams]

class BowCorpus(object):
    def __init__(self, filename, druid_dict, tokenid_dictionary, multiwords=True):
        self.corpus = codecs.open(filename, 'r', encoding='utf-8')
        self.druid_dict = druid_dict
        self.stemmer = nltk.stem.PorterStemmer()
        self.tokenid_dictionary = tokenid_dictionary
        self.multiwords = multiwords

    def __iter__(self):
        for line in self.corpus:
            if line[-1] == '\n':
                line = line[:-1]
    
            if self.multiwords:
                ngrams = self.druid_dict.find_ngrams(line.lower().split())
            else:
                ngrams = line.lower().split()
            
            stemmed_article = [self.stemmer.stem(token) for token in ngrams]
            yield self.tokenid_dictionary.doc2bow(stemmed_article)

def build_tfidf_model(data_directory, corpus_path, wiki_text_output_path, model_output_path, multiwords=True, druid_cutoff_score=0.3):

    stemmer = nltk.stem.PorterStemmer()
    tokenid_dictionary = corpora.Dictionary()

    if not exists(wiki_text_output_path):
        logger.info('Converting ' + str(corpus_path) + ' into plain text file: ' + wiki_text_output_path)
        # Convert Wikipedia XML dump into .txt format
        wikidump2text.convert(corpus_path, wiki_text_output_path)
    else:
        logger.info('Found ', wiki_text_output_path, ' not converting from the raw bz2 file.')

    # Load Multiword Expressions as Dictionary
    stopwords_path = join(data_directory, 'stopwords_en.txt')
    
    if multiwords:
        druid_path = join(data_directory, 'druid_en.bz2')
        druid_dict = druid.DruidDictionary(druid_path, stopwords_path, cutoff_score=druid_cutoff_score)
        logger.info('Loaded Druid with cutoff' + str(druid_cutoff_score))
    else:
        druid_dict = None

    logger.info("Building tfidf model...")
    start_time = time.time()

    if multiwords:
        logger.info('Using druid_en.bz2 in  ' + data_directory + ' as multiword dictionary.')
        articles = TextCorpus(wiki_text_output_path, druid_dict, multiwords=True)  # a memory-friendly iterator
    else:
        logger.info('Using no multiword dicitionary, just single words')
        articles = TextCorpus(wiki_text_output_path, None, multiwords=False)
    
    tokenid_dictionary.add_documents(articles)


    model = TfidfModel(BowCorpus(wiki_text_output_path, druid_dict, tokenid_dictionary, multiwords=multiwords), id2word=tokenid_dictionary)
    model.save(model_output_path)

    logger.info("Finished building tfidf model. Time needed: " + str(time.time() - start_time))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', '--data-directory', dest='data_directory', help='Data directory, corpus is read from this directory and the output model is saved here', type=str, default = './data/')
    parser.add_argument('-c', '--corpus-path', dest='corpus_path', help='Input corpus comment file', type=str, default = 'simplewiki-latest-pages-articles.xml.bz2')
    parser.add_argument('-w', '--wiki-text-output-path', dest='wiki_text_output_path', help='Wiki text output path (converted from raw wikipedia xml)', type=str, default = 'simplewiki-latest-pages-articles.txt')
    parser.add_argument('-o', '--model-output-path', dest='model_output_path', help='Output model file', type=str, default = 'simple-enwiki-latest.tfidf')
    parser.add_argument('-nm', '--no-multiwords', dest='no_multiwords', help='No multiwords in model generation', action='store_true', default=False)
    parser.add_argument('-s', '--druid-cutoff-score', dest='druid_cutoff_score', help='DRUID cutoff score', type=float, default = 0.3)

    args = parser.parse_args()

    logger.info('Using data directory: ' + args.data_directory)

    corpus_path = join(args.data_directory, args.corpus_path)
    wiki_text_output_path = join(args.data_directory, args.wiki_text_output_path)
    model_output_path = join(args.data_directory, args.model_output_path)

    build_tfidf_model(args.data_directory, corpus_path, wiki_text_output_path, model_output_path, not args.no_multiwords, args.druid_cutoff_score)
