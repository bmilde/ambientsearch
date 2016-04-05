import nltk
import codecs
import os

def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

manual_dir = os.path.join(data_directory(), 'manual_keywords2')
habibi_div_dir = os.path.join(data_directory(), 'habibi075')
habibi_no_div_dir = os.path.join(data_directory(), 'habibi10')
our_method_dir = os.path.join(data_directory(), 'keywords_our_method')
tfidf_dir = os.path.join(data_directory(), 'keywords_tfidf')

for file in os.listdir(manual_dir):
    if file.endswith('.txt'):
        manual_tokens = []
        habibi_div_tokens = []
        habibi_no_div_tokens = []
        our_method_tokens = []
        tfidf_tokens = []

        with codecs.open(os.path.join(ted_root_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            print 'Processing', file, ':'

            # Manual words are already separated
            manual_tokens = [line for line in in_infile]

        with codecs.open(os.path.join(habibi_div_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            # Habibis Tokens are already separated as well
            habibi_div_tokens = [line for line in in_infile]

        with codecs.open(os.path.join(habibi_no_div_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            habibi_no_div_tokens = [line for line in in_infile]

        with codecs.open(os.path.join(our_method_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            for line in in_file:
		        our_method_tokens += line.split()

        with codecs.open(os.path.join(tfidf_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            for line in in_file:
		        tfidf_tokens += line.split()

