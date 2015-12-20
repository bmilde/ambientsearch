#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
__author__ = 'Jonas Wacker'

import nltk
import bz2
import codecs
import re
import operator
from collections import defaultdict
from topia.termextract import extract
import wiki_search
import os.path
import sys
import math
import gensim
import random
import time

from sklearn.cluster import KMeans
from sklearn import metrics
from scipy.spatial import distance
from numbers import Number
import numpy

import kmeans


def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not find ', path, '!'
            sys.exit(-1)
    return path


def read_file(path):
    ami_file_name = check_path(path)

    with codecs.open(ami_file_name, 'r', 'utf-8') as in_file:
        return in_file.read()


def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

w2v_model_path = check_path(os.path.join(data_directory(), 'enwiki-latest-pages-articles.word2vec'))
tfidf_model_path = check_path(os.path.join(data_directory(), 'conversation.tfidf'))
# dictionary_path = check_path(os.path.join(data_directory(), 'enwiki-latest-pages-articles_wordids.txt.bz2'))

# Filter hypens at the beginning and/or end of a word
# E.g. "schlechteste -> schlechteste
# There are many unicode hyphen variant (which all look very similar), we also want ot filter these
def filterHyphens(word):
    if word.startswith(u'"') or word.startswith(u"'") or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"'):
        word = word[1:]

    if word.endswith(u'"') or word.endswith(u"'") or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"'):
        word = word[:-1]

    return word


class autovivify_list(dict):
        """Pickleable class to replicate the functionality of collections.defaultdict"""
        def __missing__(self, key):
                value = self[key] = []
                return value

        def __add__(self, x):
                """Override addition for numeric types when self is empty"""
                if not self and isinstance(x, Number):
                        return x
                raise ValueError

        def __sub__(self, x):
                """Also provide subtraction method"""
                if not self and isinstance(x, Number):
                        return -1 * x
                raise ValueError


def find_word_clusters(labels_array, cluster_labels):
        """Read in the labels array and clusters label and return the set of words in each cluster"""
        cluster_to_words = autovivify_list()
        for c, i in enumerate(cluster_labels):
                cluster_to_words[i].append(labels_array[c])
        return cluster_to_words


class W2VKeywordExtract:

    def __init__(self, lang='en', extra_keywords=''):
        self.lang = lang
        self.extra_keywords = extra_keywords
        self.keyword_extractor = extract.TermExtractor()
        self.keyword_extractor.filter = extract.permissiveFilter
        self.keyword_dict = {}

        self.common_words_filename = check_path('data/1-1000_en.txt')
        self.stopwords_filename = check_path('data/stopwords_en.txt')

        self.common_words = {}
        with codecs.open(self.common_words_filename, 'r', 'utf-8') as common_words_file:
            for line in common_words_file:
                self.common_words[line[:-1]] = 1

        self.stopwords = {}
        with codecs.open(self.stopwords_filename, 'r', 'utf-8') as stop_words_file:
            for line in stop_words_file:
                self.stopwords[line[:-1]] = 1

        # compiled regex that can check if a string contains numbers
        self.RE_D = re.compile('\d')

        self.start_time = time.time()

        self.stemmer = nltk.stem.PorterStemmer()
        self.lemmatizer = nltk.stem.WordNetLemmatizer()

        print 'Loading TF-IDF Model...'
        self.tfidf = gensim.models.tfidfmodel.TfidfModel.load(tfidf_model_path)
        print 'Loading Word2Vec model... (this can take some time)'
        # self.word2vec = gensim.models.Word2Vec.load_word2vec_format(w2v_model_path, binary=True)
        self.word2vec = gensim.models.Word2Vec.load(w2v_model_path)

        print 'Time for loading models:', time.time() - self.start_time
        self.start_time = time.time()

    def preprocess_text(self, text):
        # Automatically tokenize strings if nessecary
        if type(text) is str or type(text) is unicode:
            tokens = nltk.word_tokenize(text)

            # Apply a POS Tagger
            tags = nltk.pos_tag(tokens)
            # grammar = r"""RULE_1: {<JJ>+<NNP>*<NN>*}"""
            # noun phrases: (adjective)*(noun)+
            # chunker = nltk.RegexpParser(grammar)
            # chunked = chunker.parse(tags)
            # def filter(tree):
            #     return (tree.node == "RULE_1")
            # for s in chunked.subtrees(filter):
            #     print s

            # Remove stopwords (words that were too frequent in the corpus)
            # Filter nouns and adjectives. Dictionary is used to translate into WordNet Tags
            pos_pattern = {'NN': 'n', 'NNP': 'n', 'NNS': 'n'}  # , 'JJ': 'a'}
            tag_filtered = [tag for tag in tags if tag[1] in pos_pattern]
            lemmatized = [self.lemmatizer.lemmatize(token[0], pos=pos_pattern[token[1]]).lower() for token in tag_filtered]

            idf_filtered = []
            for token in lemmatized:
                try:
                    idf = self.tfidf.idfs[self.tfidf.id2word.token2id[self.stemmer.stem(token)]]
                    if idf > 3.66:
                        idf_filtered.append(token)
                except KeyError:
                    idf_filtered.append(token)

            print 'Time for preprocessing text:', time.time() - self.start_time

            return idf_filtered
        return None

    def build_word_vector_matrix(self, words):
        numpy_arrays = []
        labels_array = []

        for token in words:
            try:
                vector = self.word2vec[token]
            except KeyError:
                continue

            labels_array.append(token)
            numpy_arrays.append(vector)

        return numpy.array(numpy_arrays), labels_array

    def compute_cluster_connectivity(self, cluster, cluster_center):
        num_words = len(cluster)
        if num_words == 1:
            return 0
        df, labels_array = self.build_word_vector_matrix(cluster)
        total_distance = numpy.sum([distance.euclidean(vector, cluster_center) for vector in df])

        return 1 / (total_distance / num_words)

    def compute_cluster_tfidf(self, cluster, tokens):
        score = 0
        num_words = len(cluster)

        for word in cluster:
            tf = len([token for token in tokens if word == token])

            try:
                token_id = self.tfidf.id2word.token2id[self.stemmer.stem(word)]
                idf = self.tfidf.idfs[token_id]
            except KeyError:
                # idf score is ignored for unknown words
                # (assumption: ASR noise, disadvantage: important terms need to be part of corpus)
                idf = 1.0

            score += tf * idf

        return score / num_words

    def get_cluster_score(self, cluster, cluster_center, tokens):
        connectivity_score = self.compute_cluster_connectivity(cluster, cluster_center)
        tfidf_score = self.compute_cluster_tfidf(cluster, tokens)

        print cluster
        print tfidf_score
        print connectivity_score

        return tfidf_score, connectivity_score

    # Assigns a score to each cluster, sorts them according to the score.
    # Returns a sorted clusters array with each cluster's corresponding score.
    def get_sorted_clusters(self, clusters, cluster_centers, tokens):
        alpha = 0.6

        scores = [self.get_cluster_score(clusters[index], cluster_centers[index], tokens) for index in clusters]
        max_tfidf = max([score[0] for score in scores])
        max_connectivity = max([score[1] for score in scores])
        normalized_scores = [(score[0] / max_tfidf, score[1] / max_connectivity) for score in scores]
        # cluster_score = alpha * tfidf_norm + (1-alpha) * connectivity_norm
        # exception: one-worded clusters get a connectivity score of 0 by default => only tf-idf scores used
        cluster_scores = [(alpha * score[0] + (1-alpha) * score[1]) if score[1] > 0 else score[0]
                          for score in normalized_scores]

        cluster_scores_sorted = sorted(zip(clusters, cluster_scores), key=lambda tuple: tuple[1])

        return [(clusters[score[0]], score[1]) for score in cluster_scores_sorted]



    # Build word clusters using K-Means++
    def get_kmeans_clusters(self, tokens):
        # Remove duplicates
        tokens = list(set(tokens))

        df, labels_array  = self.build_word_vector_matrix(tokens)
        clusters_to_make  = int(numpy.ceil(len(labels_array) / 3.0))
        kmeans_model      = KMeans(init='k-means++', n_clusters=clusters_to_make, n_init=10)
        kmeans_model.fit(df)

        cluster_labels    = kmeans_model.labels_
        cluster_centers   = kmeans_model.cluster_centers_

        # Get cluster_word assignments by inverting word_cluster assignments
        # cluster_to_words  = find_word_clusters(labels_array, cluster_labels)
        word_centroid_map = dict(zip(labels_array, cluster_labels))
        centroid_word_map = {}
        for k, v in word_centroid_map.iteritems():
            centroid_word_map[v] = centroid_word_map.get(v, [])
            centroid_word_map[v].append(k)

        return centroid_word_map, cluster_centers

    # Build spherical kmeans clusters
    def get_sp_kmeans_clusters(self, tokens):
        # Remove duplicates
        tokens = list(set(tokens))

        ncluster  = int(len(tokens) / 4)
        kmsample = 5  # 0: random centres, > 0: kmeanssample
        kmdelta = .001
        kmiter = 10
        metric = "cosine"  # "chebyshev" = max, "cityblock" L1,  Lqmetric
        seed = 1

        numpy.set_printoptions( 1, threshold=200, edgeitems=5, suppress=True )
        numpy.random.seed(seed)
        random.seed(seed)

        df, labels_array  = self.build_word_vector_matrix(tokens)
            # cf scikits-learn datasets/
        if kmsample > 0:
            centres, xtoc, dist = kmeans.kmeanssample(df, ncluster, nsample=kmsample,
                delta=kmdelta, maxiter=kmiter, metric=metric, verbose=2 )
        else:
            randomcentres = kmeans.randomsample(df, ncluster )
            centres, xtoc, dist = kmeans.kmeans(df, randomcentres,
                delta=kmdelta, maxiter=kmiter, metric=metric, verbose=2 )

        cluster_labels    = xtoc
        cluster_inertia   = centres
        cluster_to_words  = find_word_clusters(labels_array, cluster_labels)

        return cluster_to_words


if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = W2VKeywordExtract()
    tokens = ke.preprocess_text(u"A columbia university law professor stood in a hotel lobby one morning and"
                         u"noticed a sign apologizing for an elevator that was out of order."
                         u"it had dropped unexpectedly three stories a few days earlier."
                         u"the professor, eben moglen, tried to imagine what the world would be like"
                         u"if elevators were not built so that people could inspect them. mr. moglen"
                         u"was on his way to give a talk about the dangers of secret code,"
                         u"known as proprietary software, that controls more and more devices every day."
                         u"proprietary software is an unsafe building material, mr. moglen had said."
                         u"you can't inspect it. he then went to the golden gate bridge and jumped.")
    # print test
    # print wiki_search.get_summaries_single_keyword(test)
    # test = ke.get_keywords(u"So i was walking down the golden gate bridge, i had the epiphany that in order"
    #                        u"to be a good computer scientist, i need to learn and practise machine learning."
    #                        u"Also proprietary software is the root of all evil and I should better use open"
    #                        u"source software.")
    print tokens

    kmeans_clusters_map, cluster_centers = ke.get_kmeans_clusters(tokens)
    kmeans_sorted_clusters = ke.get_sorted_clusters(kmeans_clusters_map, cluster_centers, tokens)
    sphere_clusters = ke.get_sp_kmeans_clusters(tokens)



    print "K-Means:"
    print kmeans_sorted_clusters
    print "Sphere:"
    print sphere_clusters
    # print "Affinity-Propagation:"
    # print af_clusters

    # test2 = ke.get_tokens(u"key open door car key principle metric component phrase moment")

    # print wiki_search.get_summaries_single_keyword(test)

    ami = read_file('data/ami_transcripts/remote_control.txt')
    tokens = ke.preprocess_text(ami)
    kmeans_clusters_map, cluster_centers = ke.get_kmeans_clusters(tokens)
    kmeans_sorted_clusters = ke.get_sorted_clusters(kmeans_clusters_map, cluster_centers, tokens)
    sphere_clusters = ke.get_sp_kmeans_clusters(tokens)

    print "K-Means:"
    print kmeans_sorted_clusters
    print "Sphere:"
    print sphere_clusters

