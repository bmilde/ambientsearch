import bz2
import os.path
import numpy as np
import scipy.io
from gensim import corpora, models

wiki_file = 'simplewiki'

def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Path to the dictionary file in the data directory
dictionary_path = os.path.join(data_directory(), wiki_file + '_wordids.txt.bz2')
# Path to the training corpus in the data directory
corpus_path = os.path.join(data_directory(), wiki_file + '_bow.mm')
# Path to the mallet lda model in the data directory
lda_model_path = os.path.join(data_directory(), wiki_file + '_mallet.lda')
# Path at which the p(t|w) distribution should be saved
filename_twp = os.path.join(data_directory(), 'word_topic_prob_dist')
filename_dict = os.path.join(data_directory(), 'dict')


# load corpus iterator
corpus = corpora.MmCorpus(corpus_path)
# load lda model
model = models.LdaModel.load(lda_model_path)
# load id->word mapping (the dictionary), one of the results of step 2 above
id2word = model.id2word

mallet = True
beta = 0.01  # topic smoothing factor from mallet LDA output

if not mallet:
    # Infer topic probability distribution for the entire corpus

    # Create an array with num_topics 0-values
    topic_prob_dist = [0] * model.num_topics

    for index, document in enumerate(corpus):
        # infer topic distribution for each document
        for topic in model.get_document_topics(document, minimum_probability=0.0):
            topic_prob_dist[topic[0]] += topic[1]
        if index % 1000 == 0:
            print 'Document:', index

    # for index, prob in enumerate(topic_prob_dist):
    #     topic_dist_file.write(str(prob / len(corpus)) + '\n')

if mallet:
    # Infer p(topic|word) distribution for the entire corpus
    print('Inferring mallet topic-word-assignment. This can take several minutes...')
    model.load_word_topics()

    print('Inferring p(topic|word) distribution...')
    # word_topic_dist = np.zeros((model.num_terms, model.num_topics), dtype=np.float32)
    # # Transpose model.wordtopics in order to get a (words X topics)-matrix with word-topic-assignment-counts as values
    # word_topic_matrix = model.wordtopics.transpose()
    # for token_id in range(0, model.num_terms):
    #     total_word_assignments = np.sum(word_topic_matrix[token_id])
    #     if total_word_assignments == 0:
    #         continue
    #     for topic_id in range(0, model.num_topics):
    #         word_topic_dist[token_id, topic_id] = word_topic_matrix[token_id, topic_id] / total_word_assignments
    #
    # print('Saving distribution under', filename)
    # np.save(filename, word_topic_dist)  # np.load
    # print('Done.')

    print('Computing p(t)...')
    # p(t) = num_assigned_tokens(topic) / num_assigned_tokens(all_topics)
    tokens_per_topic = map(lambda topic_word_counts: np.sum(topic_word_counts), model.wordtopics)
    tokens_total = np.sum(tokens_per_topic)
    topic_dist = map(lambda topic_tokens: topic_tokens / tokens_total, tokens_per_topic)

    # p(w|t) = (num_assigned_tokens(word,topic) + beta) / (num_assigned_tokens(topic) + vocab_size * beta)
    # beta is the smoothing factor in order to avoid p(w|t)=0 for any word
    topic_word_dist = np.zeros((model.num_topics, model.num_terms), dtype=np.double)
    for topic_id, topic in enumerate(model.wordtopics):
        topic_word_dist[topic_id] = map(lambda word_count: (word_count + beta) /
                                                           (tokens_per_topic[topic_id] + beta * model.num_terms), topic)

    print('Computing p(w)...')
    # p(w) = sum_over_each_topic(p(t) * p(w|t))
    word_dist = [0] * model.num_terms
    for token_id in range(0, model.num_terms):
        word_dist[token_id] = np.sum(
            [topic_word_prob[token_id] * topic_dist[topic_id]
             for topic_id, topic_word_prob in enumerate(topic_word_dist)]
        )

    print('Computing p(t|w)...')
    # p(t|w) = p(w|t) * p(t) / p(w)
    word_topic_dist = np.zeros((model.num_terms, model.num_topics), dtype=np.double)
    for token_id in range(0, model.num_terms):
        for topic_id in range(0, model.num_topics):
            word_topic_dist[token_id, topic_id] =\
                topic_word_dist[topic_id, token_id] * topic_dist[topic_id] / word_dist[token_id]

    print('Saving files...')
    np.save(filename_twp, word_topic_dist)

    # Also save to matlab format.
    scipy.io.savemat(filename_twp, mdict={'twp': word_topic_dist})
    wordsw = np.zeros((model.num_terms, 1), dtype=np.object)
    print id2word[0],type(id2word[0])
    for token_id in range(0, model.num_terms):
        wordsw[token_id, 0] = id2word[token_id].encode("utf8")
    scipy.io.savemat(filename_dict, mdict={'wordsw': wordsw},long_field_names=True)

    print('Done.')
