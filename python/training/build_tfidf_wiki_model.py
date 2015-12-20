from gensim.models import TfidfModel, Phrases
from gensim import corpora
from nltk.corpus import PlaintextCorpusReader
import os
import nltk
import logging

import wikidump2text

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

corpus_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles12.xml-p001825001p002425000.bz2')
wiki_text_output_path = os.path.join(data_directory(), 'enwiki-latest-pages-articles12.txt')
model_output_path = os.path.join(data_directory(), 'wiki.tfidf')

stemmer = nltk.stem.PorterStemmer()
corpus = PlaintextCorpusReader(corpus_dir, '.*\.txt$')  # a memory-friendly iterator
dictionary = corpora.Dictionary()

# Convert Wikipedia XML dump into .txt format
wikidump2text.convert(corpus_path, wiki_text_output_path)

# Train bigram transformer
class TextCorpus(object):
    def __iter__(self):
        for file in corpus.fileids():
            yield [word.lower() for word in corpus.words(file)]

bigram_transformer = Phrases(TextCorpus())

for file in corpus.fileids():
    chunks = bigram_transformer[[word.lower() for word in corpus.words(file)]]
    dictionary.add_documents([[stemmer.stem(chunk) for chunk in chunks]])


class BowCorpus(object):
    def __iter__(self):
        for file in corpus.fileids():
            chunks = bigram_transformer[[word.lower() for word in corpus.words(file)]]
            yield dictionary.doc2bow([stemmer.stem(chunk) for chunk in chunks])

model = TfidfModel(BowCorpus(), id2word=dictionary)
model.save(model_filename)
