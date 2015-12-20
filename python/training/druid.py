import bz2
import codecs
import re
import os
import sys
import nltk


def check_path(path):
    if not os.path.isfile(path):
        path = 'python/'+path
        if not os.path.isfile(path):
            print 'Could not find ', path, '!'
            sys.exit(-1)
    return path


# Filter hypens at the beginning and/or end of a word
# E.g. "schlechteste -> schlechteste
# There are many unicode hyphen variant (which all look very similar), we also want ot filter these
def filter_hyphens(word):
    if word.startswith(u'"') or word.startswith(u"'") or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"') or word.startswith(u'"'):
        word = word[1:]

    if word.endswith(u'"') or word.endswith(u"'") or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"') or word.endswith(u'"'):
        word = word[:-1]

    return word


class DruidDictionary:
    def __init__(self, druid_file, stopwords_file, cutoff_score=0.2):
        self.druid_mwe_file = druid_file
        self.stopwords_filename = stopwords_file
        self.keyword_dict = {}
        # compiled regex that can check if a string contains numbers
        self.RE_D = re.compile('\d')
        self.stopwords = {}
        with codecs.open(self.stopwords_filename, 'r', 'utf-8') as stop_words_file:
            for line in stop_words_file:
                self.stopwords[line[:-1]] = 1

        self.build_druid_cache(cutoff_score)

    def build_druid_cache(self, cutoff_druid_score):
        druid_bz2 = bz2.BZ2File(self.druid_mwe_file, mode='r')
        druid_file = codecs.iterdecode(druid_bz2, 'utf-8')
        num_added_words = 0

        for line in druid_file:
            split = line.split(u'\t')
            words = split[1].lower()
            druid_score = split[2]
            has_number = self.RE_D.search(words)
            # exclude any lines that have one or more numbers in them
            if not has_number:
                words_split = [filter_hyphens(word) for word in words.split(u' ')]
                float_druid_score = float(druid_score)
                if float_druid_score < cutoff_druid_score:
                    break

                if not any((word in self.stopwords) for word in words_split):
                    self.keyword_dict[words] = float_druid_score
                    num_added_words += 1
                    if num_added_words % 1000 == 0:
                        print words, self.keyword_dict[words]

    # Converts an ordered list of tokens into n-grams
    # Default: Trigrams
    def find_ngrams(self, tokens, n=3):
        # start with bigrams
        for index in range(n-1):
            filtered_tokens = []
            if (len(tokens) == 1):
                filtered_tokens.append(tokens[0])
                continue

            while len(tokens) > 1:
                search_gram = tokens[0] + u' ' + tokens[1]
                score_old = self.keyword_dict[tokens[0]] if tokens[0] in self.keyword_dict else 0
                score_new = self.keyword_dict[search_gram] if search_gram in self.keyword_dict else 0

                if score_new > score_old:
                    filtered_tokens.append(search_gram)
                    del tokens[1]
                else:
                    filtered_tokens.append(tokens[0])
                del tokens[0]

            tokens = filtered_tokens

        return filtered_tokens
