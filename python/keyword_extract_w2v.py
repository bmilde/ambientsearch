#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
__author__ = 'Jonas Wacker'

import nltk
import codecs
import re
from topia.termextract import extract
import wiki_search
import os.path
import sys
import gensim
import time
import operator

from sklearn.cluster import KMeans
from scipy.spatial import distance
import numpy

from training import druid


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
tfidf_model_path = check_path(os.path.join(data_directory(), 'wiki.tfidf'))
tfidf_conversation_path = check_path(os.path.join(data_directory(), 'conversation.tfidf'))
druid_path = check_path(os.path.join(data_directory(), 'druid_en.bz2'))

# Filter hypens at the beginning and/or end of a word
# E.g. "schlechteste -> schlechteste
# There are many unicode hyphen variant (which all look very similar), we also want ot filter these
def filterHyphens(word):
    if word.startswith(u'"') or word.startswith(u"'") or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"'):
        word = word[1:]

    if word.endswith(u'"') or word.endswith(u"'") or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"'):
        word = word[:-1]

    return word


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
        self.tfidf_conversation = gensim.models.tfidfmodel.TfidfModel.load(tfidf_conversation_path)
        print 'Loading Word2Vec model... (this can take some time)'
        # self.word2vec = gensim.models.Word2Vec.load_word2vec_format(w2v_model_path, binary=True)
        self.word2vec = gensim.models.Word2Vec.load(w2v_model_path)
        self.druid = druid.DruidDictionary(druid_path, self.stopwords_filename, cutoff_score=0.0)

        print 'Time for loading models:', time.time() - self.start_time
        self.start_time = time.time()

    def preprocess_text(self, text):
        # Automatically tokenize strings if nessecary
        if type(text) is str or type(text) is unicode:
            tokens = nltk.word_tokenize(text.lower())

            # Apply a POS Tagger
            tags = nltk.pos_tag(tokens)

            # Remove stopwords (words that were too frequent in the corpus)
            # Filter nouns and adjectives. Dictionary is used to translate into WordNet Tags
            pos_pattern = ['NN', 'NNP', 'NNS', 'JJ']
            tag_filtered = [tag[0] for tag in tags if tag[1] in pos_pattern]
            # stop_filtered = [token for token in tag_filtered if token not in self.stopwords]
            idf_filtered = []
            for token in tag_filtered:
                try:
                    if token in self.stopwords:
                        continue
                    idf = self.tfidf.idfs[self.tfidf.id2word.token2id[self.stemmer.stem(token)]]
                    if idf > 3.67:
                        idf_filtered.append(token)
                except KeyError:
                    idf_filtered.append(token)

            ngrams = self.druid.find_ngrams(idf_filtered, n=3)

            lemmatized = [self.lemmatizer.lemmatize(token) for token in ngrams]

            print 'Time for preprocessing text:', time.time() - self.start_time

            return lemmatized
        return None

    def build_word_vector_matrix(self, words):
        numpy_arrays = []
        labels_array = []

        for token in words:
            try:
                vector = self.word2vec[self.stemmer.stem(token)]
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
        if len(cluster) == 1:
            return 0, 0

        connectivity_score = self.compute_cluster_connectivity(cluster, cluster_center)
        tfidf_score = self.compute_cluster_tfidf(cluster, tokens)

        print cluster
        print tfidf_score
        print connectivity_score

        return tfidf_score, connectivity_score

    # Assigns a score to each cluster, sorts them according to the score.
    # Returns a sorted clusters array with each cluster's corresponding score.
    def get_scored_clusters(self, clusters, cluster_centers, tokens):
        alpha = 0.8

        scores = [self.get_cluster_score(clusters[index], cluster_centers[index], tokens) for index in clusters]
        max_tfidf = max([score[0] for score in scores])
        max_connectivity = max([score[1] for score in scores])
        normalized_scores = [(score[0] / max_tfidf, score[1] / max_connectivity) for score in scores]
        # cluster_score = alpha * tfidf_norm + (1-alpha) * connectivity_norm
        # exception: one-worded clusters get a connectivity score of 0 by default => only tf-idf scores used
        cluster_scores = [(alpha * score[0] + (1-alpha) * score[1]) if score[1] > 0 else score[0]
                          for score in normalized_scores]

        scored_clusters = zip(clusters, cluster_scores)

        return [(clusters[score[0]], score[1]) for score in scored_clusters]

    # Build word clusters using K-Means++
    def get_kmeans_clusters(self, tokens):
        # Remove duplicates
        tokens = list(set(tokens))

        df, labels_array = self.build_word_vector_matrix(tokens)
        clusters_to_make = int(numpy.ceil(len(labels_array) / 4.0))
        kmeans_model = KMeans(init='k-means++', n_clusters=clusters_to_make, n_init=10)
        kmeans_model.fit(df)

        cluster_labels = kmeans_model.labels_
        cluster_centers = kmeans_model.cluster_centers_

        # Get cluster_word assignments by inverting word_cluster assignments
        # cluster_to_words  = find_word_clusters(labels_array, cluster_labels)
        word_centroid_map = dict(zip(labels_array, cluster_labels))
        centroid_word_map = {}
        for k, v in word_centroid_map.iteritems():
            centroid_word_map[v] = centroid_word_map.get(v, [])
            centroid_word_map[v].append(k)

        return centroid_word_map, cluster_centers

    # Scores a keyphrase according to its centrality within the weighted clusters.
    #
    def score_keyphrase(self, phrase, cluster_centers, cluster_scores, text_tokens):
        try:
            phrase_vector = self.word2vec[self.stemmer.stem(phrase)]
            total_distance = numpy.sum([cluster_scores[index] * distance.euclidean(phrase_vector, cluster_centers[index])
                                        for index in range(0, len(cluster_centers))])
        except KeyError:
            total_distance = -1

        tf = len([token for token in text_tokens if phrase == token])
        try:
            idf = self.tfidf.idfs[self.tfidf.id2word.token2id[self.stemmer.stem(phrase)]]
        except KeyError:
            idf = 1.0

        distance_score = numpy.log(1.0 + 1.0 / total_distance) if total_distance > 0 else 0.01
        tfidf_score = tf * idf

        return distance_score, tfidf_score

    def get_sorted_keyphrases(self, text_tokens, cluster_centers, cluster_scores):
        alpha = 1.0

        tokens = list(set(text_tokens))
        scores = [self.score_keyphrase(phrase, cluster_centers, cluster_scores, text_tokens) for phrase in tokens]
        max_dist_score = max([score[0] for score in scores])
        max_tfidf_score = max([score[1] for score in scores])
        normalized_scores = [(score[0] / max_dist_score, score[1] / max_tfidf_score) for score in scores]
        keyphrase_scores = [(alpha * score[0] + (1-alpha) * score[1]) if score[0] > 0 else score[1]
                            for score in normalized_scores]

        keyphrase_scores_sorted = sorted(zip(tokens, keyphrase_scores), key=lambda keyphrase: keyphrase[1])
        return keyphrase_scores_sorted


    # Habibi Diversity
    def subset_cluster_distance(self, subset, cluster_center):
        df, labels_array = self.build_word_vector_matrix(subset)
        if len(labels_array) == 0:
            return 0
        else:
            # proximity_scores = [numpy.log(1.0 + 1.0 / distance.euclidean(vector, cluster_center)) for vector in df]
            proximity_scores = [1.0 / distance.euclidean(vector, cluster_center) for vector in df]
            # total_distance = numpy.sum([distance.euclidean(vector, cluster_center) for vector in df])

        # return numpy.log(1.0 + 1.0 / total_distance)
        return 10 * numpy.sum(proximity_scores)

    def score_subset(self, subset, cluster_centers, cluster_scores, text_tokens):
        beta = 1.0
        tfidf_score = self.compute_cluster_tfidf(subset, text_tokens)
        centrality_score = numpy.sum(
            [cluster_scores[index] * self.subset_cluster_distance(subset, cluster_centers[index])**beta
             for index in range(0, len(cluster_centers))])

        return centrality_score # * tfidf_score

    def find_best_subset(self, text_tokens, n, cluster_centers, cluster_scores):
        tokens = list(set(text_tokens))
        extracted_tokens = []
        extracted_scores = []

        while len(extracted_tokens) < n and len(tokens) > 0:
            scores = [self.score_subset(extracted_tokens + [token], cluster_centers, cluster_scores, text_tokens)
                      for token in tokens]
            max_index, max_value = max(enumerate(scores), key=operator.itemgetter(1))
            extracted_tokens.append(tokens[max_index])
            extracted_scores.append(max_value)
            del tokens[max_index]

        return zip(extracted_tokens, extracted_scores)



if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = W2VKeywordExtract()
    text = u"""A columbia university law professor stood in a hotel lobby one morning and
                noticed a sign apologizing for an elevator that was out of order.
                it had dropped unexpectedly three stories a few days earlier.
                the professor, eben moglen, tried to imagine what the world would be like
                if elevators were not built so that people could inspect them. mr. moglen
                was on his way to give a talk about the dangers of secret code,
                known as proprietary software, that controls more and more devices every day.
                proprietary software is an unsafe building material, mr. moglen had said.
                you can't inspect it. he then went to the golden gate bridge and jumped."""
    tokens = ke.preprocess_text(text)
    # print test
    # print wiki_search.get_summaries_single_keyword(test)
    # test = ke.get_keywords(u"So i was walking down the golden gate bridge, i had the epiphany that in order"
    #                        u"to be a good computer scientist, i need to learn and practise machine learning."
    #                        u"Also proprietary software is the root of all evil and I should better use open"
    #                        u"source software.")
    print tokens

    kmeans_clusters_map, cluster_centers = ke.get_kmeans_clusters(tokens)
    kmeans_clusters = ke.get_scored_clusters(kmeans_clusters_map, cluster_centers, tokens)
    cluster_scores = [cluster[1] for cluster in kmeans_clusters]
    sorted_keyphrases = ke.get_sorted_keyphrases(tokens, cluster_centers, cluster_scores)
    habibi_keyphrases = ke.find_best_subset(tokens, 10, cluster_centers, cluster_scores)



    print "K-Means Clusters:"
    print sorted(kmeans_clusters, key=lambda cluster: cluster[1])
    print "Keyphrases:"
    print sorted_keyphrases
    print "Habibi:"
    print habibi_keyphrases
    # print "Affinity-Propagation:"
    # print af_clusters

    # test2 = ke.get_tokens(u"key open door car key principle metric component phrase moment")

    # print wiki_search.get_summaries_single_keyword(test)

    ami = read_file('data/ami_transcripts/remote_control.txt')
    tokens = ke.preprocess_text(ami)
    kmeans_clusters_map, cluster_centers = ke.get_kmeans_clusters(tokens)
    kmeans_clusters = ke.get_scored_clusters(kmeans_clusters_map, cluster_centers, tokens)
    cluster_scores = [cluster[1] for cluster in kmeans_clusters]
    sorted_keyphrases = ke.get_sorted_keyphrases(tokens, cluster_centers, cluster_scores)
    habibi_keyphrases = ke.find_best_subset(tokens, 8, cluster_centers, cluster_scores)

    print "K-Means:"
    print sorted(kmeans_clusters, key=lambda cluster: cluster[1])
    print "Keyphrases:"
    print sorted_keyphrases
    print "Habibi:"
    print habibi_keyphrases
