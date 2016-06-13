#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Jonas Wacker, Benjamin Milde'

import nltk
import codecs
import io
import re
from topia.termextract import extract
import os.path
import os
import sys
import gensim
import time

from sklearn.cluster import KMeans, AffinityPropagation
from sklearn.metrics import pairwise
from scipy.spatial import distance
import numpy

#spacy for pos tagging
from spacy.en import English#, LOCAL_DATA_DIR
import spacy.en
import os
import json

#data_dir = os.environ.get('SPACY_DATA', LOCAL_DATA_DIR)

nlp = English(parser=False, tagger=True, entity=False)
#spacy end

from training import druid

#only used for visualization of AP clusters
#import matplotlib.pyplot as plt
from sklearn import decomposition
from itertools import cycle

import wiki_search_es

def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not find ', path, '!'
            sys.exit(-1)
    return path


def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# w2v_model_path = check_path(os.path.join(data_directory(), 'enwiki-latest-pages-articles.word2vec'))
w2v_model_path = check_path(os.path.join(data_directory(), 'simple-enwiki-latest.word2vec'))
# w2v_google_model_path = check_path(os.path.join(data_directory(), 'GoogleNews-vectors-negative300.bin.gz'))
# tfidf_model_path = check_path(os.path.join(data_directory(), 'wiki.tfidf'))
tfidf_model_path = check_path(os.path.join(data_directory(), 'simple-enwiki-latest.tfidf'))
tfidf_conversation_path = check_path(os.path.join(data_directory(), 'conversation.tfidf'))
druid_path = check_path(os.path.join(data_directory(), 'druid_en.bz2'))

def print_fine_pos(token):
    return (token.tag_)

def pos_tags(text):
    if type(text) != unicode:
        text = unicode(text, "utf-8")
    tokens = nlp(text)
    tags = []
    for tok in tokens:
        tags.append((unicode(tok),print_fine_pos(tok)))
    return tags

class W2VKeywordExtract:

    def __init__(self, lang='en', extra_keywords='', cutoff_druid_score=0.2):
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
        # self.word2vec = gensim.models.Word2Vec.load_word2vec_format(w2v_google_model_path, binary=True)
        self.word2vec = gensim.models.Word2Vec.load(w2v_model_path)
        self.druid = druid.DruidDictionary(druid_path, self.stopwords_filename, cutoff_druid_score)

        print 'Time for loading models:', time.time() - self.start_time
        self.start_time = time.time()

    def preprocess_text(self, text, lemmatize=False):
        start_time = time.time()
        # Automatically tokenize strings if nessecary
        if type(text) is str or type(text) is unicode:
            #text = text.lower()
            tokens = nltk.word_tokenize(text.lower())

            #tags = nltk.pos_tag(tokens)
            #print tags

            pos_pattern = [u'NN', u'NNP', u'NNS', u'JJ']
            #tag_filtered = [tag[0] for tag in tags if tag[1] in pos_pattern]

            #print tag_filtered
            ngrams = self.druid.find_ngrams(tokens, n=3) #[term for term in self.druid.find_ngrams(tokens, n=3) if term not in self.stopwords]
            #print ngrams
            tags = pos_tags(u' '.join(ngrams))
            #print tags
            idf_filtered = []
            for token,tag in tags:
                try:
                    if token in self.stopwords:
                        continue
                    if (not '_' in token) and (tag not in pos_pattern):
                        continue

                    idf = self.tfidf_conversation.idfs[self.tfidf_conversation.id2word.token2id[self.stemmer.stem(token)]]
                    if idf > 3.67:
                        idf_filtered.append(token)
                except KeyError:
                    idf_filtered.append(token)

            if lemmatize:
                idf_filtered = [self.lemmatizer.lemmatize(token) for token in idf_filtered]
            #else:
                #base_form = [self.stemmer.stem(token) for token in ngrams]

            #print ngrams
            print 'Time for preprocessing text:', time.time() - start_time

            return idf_filtered
        return None

    def preprocess_text_old(self, text, lemmatize=True):
        # Automatically tokenize strings if nessecary
        if type(text) is str or type(text) is unicode:
            tokens = nltk.word_tokenize(text.lower())

            # Apply a POS Tagger
            tags = nltk.pos_tag(tokens)

            # Remove stopwords (words that were too frequent in the corpus)
            # Filter nouns and adjectives. Dictionary is used to translate into WordNet Tags
            pos_pattern = ['NN', 'NNP', 'NNS', 'JJ']
            tag_filtered = [tag[0] for tag in tags if tag[1] in pos_pattern]
            idf_filtered = []
            for token in tag_filtered:
                try:
                    if token in self.stopwords:
                        continue
                    idf = self.tfidf_conversation.idfs[self.tfidf_conversation.id2word.token2id[self.stemmer.stem(token)]]
                    if idf > 3.67:
                        idf_filtered.append(token)
                except KeyError:
                    idf_filtered.append(token)

            ngrams = self.druid.find_ngrams(idf_filtered, n=3)

            if lemmatize:
                base_form = [self.lemmatizer.lemmatize(token) for token in ngrams]
            else:
                base_form = [self.stemmer.stem(token) for token in ngrams]

            #print base_form
            print 'Time for preprocessing text:', time.time() - self.start_time

            return base_form
        return None

    def build_word_vector_matrix(self, words):
        numpy_arrays = []
        labels_array = []

        for token in words:
            try:
                vector = self.word2vec[self.stemmer.stem(token)]
                # vector = self.word2vec[token]
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
        center_vector = self.word2vec[self.stemmer.stem(cluster_center)]
        # center_vector = self.word2vec[cluster_center]
        # center_vector = cluster_center
        total_distance = numpy.sum([distance.euclidean(vector, center_vector) for vector in df])

        return 1 / (total_distance / num_words)

    def compute_cluster_tfidf(self, cluster, tokens):
        score = 0
        # num_words = len(cluster)

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

        return score  #/ num_words

    def get_cluster_score(self, cluster, cluster_center, tokens):
        tfidf_score = self.compute_cluster_tfidf(cluster, tokens)
        connectivity_score = self.compute_cluster_connectivity(cluster, cluster_center)

        return tfidf_score, connectivity_score

    # Assigns a score to each cluster, sorts them according to the score.
    # Returns a sorted clusters array with each cluster's corresponding score.
    def get_scored_clusters(self, clusters, cluster_centers, tokens):
        scores = [self.get_cluster_score(clusters[index], cluster_centers[index], tokens) for index in clusters]
        # note: single-worded clusters have no connectivity score => penality for their score (assumption: off-topic)
        cluster_scores = [score[0] * score[1] for score in scores]

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

    # Build word clusters using Affinity Propagation (Default clustering method)
    def get_ap_clusters(self, tokens):
        tokens = list(set(tokens))
        df, labels_array = self.build_word_vector_matrix(tokens)

        if df.shape[0] == 0:
        	return False, tokens

        af = AffinityPropagation(affinity='euclidean').fit(df)

        cluster_centers_indices = af.cluster_centers_indices_
        cluster_labels = af.labels_

        if cluster_centers_indices == None:
            return False, tokens

        # Uncomment the code below to visualise the ap clusters
        # n_clusters_ = len(cluster_centers_indices)
        # m = decomposition.RandomizedPCA(n_components=2)
        # tokens_vec = numpy.asarray(df)
        # tokens_vec_2d = m.fit_transform(tokens_vec)
        # colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
        # for k, col in zip(range(n_clusters_), colors):
        #     class_members = cluster_labels == k
        #     cluster_center = tokens_vec_2d[cluster_centers_indices[k]]
        #     plt.plot(tokens_vec_2d[class_members, 0], tokens_vec_2d[class_members, 1], col + '.')
        #     plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=14)
        #     for x in tokens_vec_2d[class_members]:
        #         plt.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)
        #
        # for index, point in enumerate(tokens_vec_2d):
        #     plt.annotate(labels_array[index], xy=(point[0], point[1]), fontsize=24)
        #
        # plt.show()

        # Dictionary: cluster_id -> center_word
        cluster_centers = dict([(index, labels_array[cluster_centers_indices[index]])
                                for index in range(0, len(cluster_centers_indices))])

        word_centroid_map = dict(zip(labels_array, cluster_labels))
        centroid_word_map = {}
        for k, v in word_centroid_map.iteritems():
            centroid_word_map[v] = centroid_word_map.get(v, [])
            centroid_word_map[v].append(k)

        return centroid_word_map, cluster_centers


    # Scores a keyphrase according to its centrality within the weighted clusters.
    def score_keyphrase(self, phrase, cluster_centers, cluster_scores, max_distance, text_tokens):
        try:
            phrase_vector = self.word2vec[self.stemmer.stem(phrase)]
            # phrase_vector = self.word2vec[phrase]
            center_vectors, labels = self.build_word_vector_matrix(cluster_centers.values())
            # center_vectors = cluster_centers
            total_distance_score = numpy.sum(
                [cluster_scores[index] * (1 - distance.euclidean(phrase_vector, center_vectors[index]) / max_distance)
                 for index in range(0, len(cluster_centers))])
        except KeyError:
            total_distance_score = 0

        tf = len([token for token in text_tokens if self.stemmer.stem(phrase) == self.stemmer.stem(token)])
        try:
            idf = self.tfidf.idfs[self.tfidf.id2word.token2id[self.stemmer.stem(phrase)]]
        except KeyError:
            idf = 1.0

        # distance_score = 1.0 / total_distance if total_distance > 0 else 0
        tfidf_score = tf * idf

        return total_distance_score, tfidf_score

    def get_sorted_keyphrases(self, text_tokens, cluster_centers, cluster_scores):
        tokens = list(set(text_tokens))

        token_vectors, token_labels = self.build_word_vector_matrix(tokens)
        center_vectors, center_labels = self.build_word_vector_matrix(cluster_centers.values())
        dist_matrix = pairwise.pairwise_distances(X=center_vectors, Y=token_vectors, metric='euclidean')
        # Maximum distance for any token to any cluster
        max_distance = numpy.max(dist_matrix)

        scores = [self.score_keyphrase(phrase, cluster_centers, cluster_scores, max_distance, text_tokens) for phrase in tokens]
        keyphrase_scores = [(score[0] * score[1]) for score in scores]
        # use the scores below to disable word2vec -> pure tf-idf (with preprocessing)
        # keyphrase_scores = [score[1] for score in scores]

        keyphrase_scores_sorted = sorted(
            zip(tokens, keyphrase_scores),
            key=lambda keyphrase: keyphrase[1],
            reverse=True)

        return keyphrase_scores_sorted

    # Method used by the rest of the application.
    # Extracts the n best scoring keyphrases along with their scores from the given text.
    def extract_best_keywords_clusters(self, text, n=9, lemmatize=True):
        tokens = self.preprocess_text(text, lemmatize)
        ap_clusters_map, cluster_centers = self.get_ap_clusters(tokens)
        # Dirty fix for bug if no clusters can be formed because Word2Vec does not recognize a single word.
        if not ap_clusters_map:
            return [(token, 1.0) for token in cluster_centers]
        scored_clusters = self.get_scored_clusters(ap_clusters_map, cluster_centers, tokens)
        cluster_scores = [cluster[1] for cluster in scored_clusters]
        sorted_keyphrases = self.get_sorted_keyphrases(tokens, cluster_centers, cluster_scores)

        return sorted_keyphrases[:n]


    def get_tf_idf(self, token, all_tokens):
        tf = len([item for item in all_tokens if self.stemmer.stem(item) == self.stemmer.stem(token)])
        try:
            idf = self.tfidf.idfs[self.tfidf.id2word.token2id[self.stemmer.stem(token)]]
        except KeyError:
            idf = 1.0

        return tf * idf

    def habibi_mimic(self, text, n=9, tfidf_only=False, lemmatize=True):
        print 'DEPRECATED, habibi_mimic will removed.'
        return extract_best_keywords(text, n=9, tfidf_only=False, lemmatize=True)

    def extract_best_keywords(self, text, n_words=9, tfidf_only=False, lemmatize=False, min_score=0.0, cutoff_mwe=False, count_words_in_keyphrase=True):
        tokens = self.preprocess_text(text,lemmatize)
        token_vectors, token_labels = self.build_word_vector_matrix(tokens)

        # Compute the weight vector
        sum_vector = numpy.sum(token_vectors, axis=0)
        weight_vector = sum_vector / len(tokens)

        # Compute Word2Vec score for each token
        score_vector = numpy.dot(token_vectors, weight_vector)
        tf_idf_vector = [self.get_tf_idf(token, token_labels) for token in token_labels]
        score_vector_two = score_vector * tf_idf_vector

        if not tfidf_only:
            token_scores = list(set(zip(token_labels, score_vector_two)))
        else:
            token_scores = list(set(zip(token_labels, tf_idf_vector)))

        collapsed_keyphrases = {}

        # We collapse items (add their scores up) if the stem is the same, e.g. fuel and fuels.
        # We then use the short keyword / keyphrase (unstemmed).
        for item in token_scores:
            stemmed_word = self.stemmer.stem(item[0])
            if stemmed_word in collapsed_keyphrases:
                keyphrase = item[0] if len(item[0]) >= len(collapsed_keyphrases[stemmed_word][0]) else collapsed_keyphrases[stemmed_word][0]
                score = item[1] + collapsed_keyphrases[stemmed_word][1]
            else:
                keyphrase,score = item
            
            collapsed_keyphrases[stemmed_word] = (keyphrase,score)
            
        sorted_keyphrases = [item for item in sorted(collapsed_keyphrases.values(), key=lambda token: token[1], reverse=True) if item[1] > min_score]

        # Extract n words (phrases count as multiple words)
        output_phrases = []
        word_counter = 0
        for phrase in sorted_keyphrases:
            phrase_length = len(phrase[0].split('_'))

            if count_words_in_keyphrase:
                word_counter += phrase_length
            else:
                word_counter += 1

            if word_counter > n_words:
                if cutoff_mwe:
                    # Too many words -> cut off mwe
                    remain = '_'.join(phrase[0].split('_')[:-(word_counter - n)])
                    output_phrases.append((remain, phrase[1]))
                else:
                    output_phrases.append((phrase[0], phrase[1]))
                break
            elif word_counter == n_words:
                output_phrases.append((phrase[0], phrase[1]))
                break
            else:
                output_phrases.append((phrase[0], phrase[1]))

        return output_phrases

# From http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

if __name__ == "__main__":
    print 'Scripting directly called, I will perform some testing.'
    ke = W2VKeywordExtract(cutoff_druid_score=0.2)

    method_name = 'proposed_0.2/'

    ted_trans_root_dir = os.path.join(data_directory(), 'ted_transcripts')
    ted_orig_root_dir = os.path.join(data_directory(), 'ted_originals')
    keyword_eval_dir = os.path.join(data_directory(), 'keywords_eval_dir/'+method_name)
    ndcg_eval_dir = os.path.join(data_directory(), 'ndcg_eval_dir/'+method_name)

    ensure_dir(keyword_eval_dir)
    ensure_dir(ndcg_eval_dir) 

    # Fetching number of keywords to extract
    keyword_counts = {}
    with codecs.open('goal_goals.txt', 'r', encoding='utf-8', errors='replace') as in_file:
        for line in in_file:
            keyword_counts[line.split()[0].split('/')[-1]] = int(line.split()[-1])

    for myfile in os.listdir(ted_trans_root_dir):
        if myfile.endswith('.txt'):
            with codecs.open(os.path.join(ted_trans_root_dir, myfile), 'r', encoding='utf-8', errors='replace') as in_file, \
                    codecs.open(os.path.join(ted_orig_root_dir, myfile), 'r', encoding='utf-8', errors='replace') as orig_in_file:

                print 'Processing', in_file, ':'

                raw = in_file.read()
                orig = orig_in_file.read()

                num_tokens = keyword_counts[myfile]
                
                # tokens = ke.preprocess_text(raw)

                # print 'Text:'
                # for sentence in nltk.sent_tokenize(raw):
                    # print sentence
                # print 'Tokens:', tokens

                # ap_clusters_map, cluster_centers = ke.get_ap_clusters(tokens)
                # K-Means can be used alternatively (speeds up process, yields slightly worse results though)
                # ap_clusters_map, cluster_centers = ke.get_kmeans_clusters(tokens)
                # scored_clusters = ke.get_scored_clusters(ap_clusters_map, cluster_centers, tokens)
                # cluster_scores = [cluster[1] for cluster in scored_clusters]
                # sorted_keyphrases = ke.get_sorted_keyphrases(tokens, cluster_centers, cluster_scores)
                # print "Affinity Propagation:"
                # print ap_clusters_map
                # print cluster_centers
                # print sorted(scored_clusters, key=lambda cluster: cluster[1])
                # print "Keyphrases:"
                # print sorted_keyphrases

                print "extract_best_keywords:"
                extracted_num_tokens_like_manual = ke.extract_best_keywords(raw, n_words=num_tokens)
                print extracted_num_tokens_like_manual

                extracted_10_tokens = ke.extract_best_keywords(raw, n_words=10)
                print extracted_10_tokens

                # Extract top wiki articles
                new_relevant_entries = wiki_search_es.extract_best_articles(extracted_10_tokens, n=10, min_summary_chars=400)
                print "-> Extracted top ", len(new_relevant_entries), " documents", [(entry["title"], entry["score"]) for entry in new_relevant_entries]

                # Write extracted tokens into file
                with io.open(os.path.join(keyword_eval_dir, myfile), 'w', encoding='utf-8') as out_file:
                    out_file.write(u'\n'.join([' '.join(elem[0].split('_')) for elem in extracted_num_tokens_like_manual])+u'\n')

                with io.open(os.path.join(ndcg_eval_dir, myfile), 'w', encoding='utf-8') as out_file:
                    out_file.write(u'\n'.join([elem[0] + u' ' + str(elem[1]) for elem in extracted_10_tokens])+u'\n')

                json_out = {'filename':myfile, 'orig':orig, 'top10':new_relevant_entries}
                print json_out

                with open(os.path.join(ndcg_eval_dir, myfile[:-4]+'.json'), 'w') as outfile:
                    json.dump(json_out, outfile)
