from gensim.models import TfidfModel, Phrases
from gensim import corpora
from nltk.corpus import PlaintextCorpusReader
import os
import nltk
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

corpus_dir = os.path.join(data_directory(), 'audio_transcripts')
model_filename = os.path.join(data_directory(), 'conversation.tfidf')

stemmer = nltk.stem.PorterStemmer()
corpus = PlaintextCorpusReader(corpus_dir, '.*\.txt$')  # a memory-friendly iterator
dictionary = corpora.Dictionary()

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
