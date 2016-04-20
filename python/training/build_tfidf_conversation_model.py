from gensim.models import TfidfModel, Phrases
from gensim import corpora
from nltk.corpus import PlaintextCorpusReader
import nltk.corpus
import os
import nltk
import logging
import argparse

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Train bigram transformer
class TextCorpus(object):
    def __init__(self,corpus):
        self.corpus = corpus
    
    def __iter__(self):
        for myfile in self.corpus.fileids():
            print myfile
            try:
                yield_text = [word.lower() for word in self.corpus.words(myfile)]
            except Exception as e:
                print 'Warning error in file:', myfile
            if yield_text != None:
                yield yield_text

class BowCorpus(object):
    def __init__(self,corpus,dictionary,bigram_transformer,stemmer=None):
        self.corpus = corpus
        self.dictionary = dictionary
        self.bigram_transformer = bigram_transformer

        if stemmer is None:
            self.stemmer = nltk.stem.PorterStemmer()
        else:
            self.stemmer = stemmer

    def __iter__(self):
        for myfile in self.corpus.fileids():
            try:
                chunks = self.bigram_transformer[[word.lower() for word in self.corpus.words(myfile)]]
            except Exception as e:
                print 'Warning error in file:', myfile
            if chunks != None:
                yield self.dictionary.doc2bow([self.stemmer.stem(chunk) for chunk in chunks])

def build_tfidf(corpus_dir,model_filename):
    stemmer = nltk.stem.PorterStemmer()
    corpus = PlaintextCorpusReader(corpus_dir, '.*\.txt$')  # a memory-friendly iterator
    dictionary = corpora.Dictionary()

    bigram_transformer = Phrases(TextCorpus(corpus))

    for myfile in corpus.fileids():
        try:
            chunks = bigram_transformer[[word.lower() for word in corpus.words(myfile)]]
            dictionary.add_documents([[stemmer.stem(chunk) for chunk in chunks]])

        except Exception as e:
            print 'Warning error in file:', myfile

    model = TfidfModel(BowCorpus(corpus,dictionary,bigram_transformer), id2word=dictionary)
    model.save(model_filename)

if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('-c', '--corpus-dir', dest='corpus_dir', help='Ami root directory, corpus is read from this directory', type=str, default = './data/ami_transcripts/')
        parser.add_argument('-t', '--model_filename', dest='model_filename', help='Model output filename', type=str, default = './data/conversation.tfidf' )

        args = parser.parse_args()

        build_tfidf(args.corpus_dir,args.model_filename)
