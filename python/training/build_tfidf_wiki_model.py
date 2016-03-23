from gensim.models import TfidfModel
from gensim import corpora
from os.path import join, dirname, abspath, basename
import nltk
import logging
import druid
import sys
import codecs
import time

import wikidump2text

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = basename(sys.argv[0])
logger = logging.getLogger(program)


def data_directory():
    return join(dirname(dirname(abspath(__file__))), 'data')

corpus_path = join(data_directory(), 'enwiki-latest-pages-articles12.xml-p001825001p002425000.bz2')
wiki_text_output_path = join(data_directory(), 'enwiki-latest-pages-articles12.txt')
model_output_path = join(data_directory(), 'wiki.tfidf')

stemmer = nltk.stem.PorterStemmer()
dictionary = corpora.Dictionary()

# Convert Wikipedia XML dump into .txt format
wikidump2text.convert(corpus_path, wiki_text_output_path)

# Load Multiword Expressions as Dictionary
stopwords_path = join(data_directory(), 'stopwords_en.txt')
druid_path = join(data_directory(), 'druid_en.bz2')
druid_dict = druid.DruidDictionary(druid_path, stopwords_path, cutoff_score=0.0)


logger.info("Building tfidf model...")
start_time = time.time()


class TextCorpus(object):
    def __init__(self, filename):
        self.corpus = codecs.open(filename, 'r', encoding='utf-8')

    def __iter__(self):
        # One line contains one wiki article.
        for line in self.corpus:
            ngrams = druid_dict.find_ngrams(line.lower().split())
            yield [stemmer.stem(token) for token in ngrams]

articles = TextCorpus(wiki_text_output_path)  # a memory-friendly iterator
dictionary.add_documents(articles)


class BowCorpus(object):
    def __init__(self, filename):
        self.corpus = codecs.open(filename, 'r', encoding='utf-8')

    def __iter__(self):
        for line in self.corpus:
            ngrams = druid_dict.find_ngrams(line.lower().split())
            stemmed_article = [stemmer.stem(token) for token in ngrams]
            yield dictionary.doc2bow(stemmed_article)

model = TfidfModel(BowCorpus(wiki_text_output_path), id2word=dictionary)
model.save(model_output_path)

logger.info("Finished building tfidf model. Time needed: " + str(time.time() - start_time))
