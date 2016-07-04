import nltk
import codecs
import os
import numpy as np
from collections import defaultdict

def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

stemmer = nltk.stem.PorterStemmer()

manual_dir = os.path.join(data_directory(), 'manual_keywords_merged')
eval_dir = os.path.join(data_directory(), 'keywords_eval_dir')

methods = ['proposed/', 'proposed_nodruid/', 'tfidf/', 'tfidf_nodruid/', 'tfidf_nodruid_nofilter', 
                    'tfidf_nodruid_nofilter_nostopwords', 'habibi075', 'habibi10']

filenames = []

def remove_line_end(line):
    if line[-1] == '\n':
        line = line[:-1]
    return line

filelist = []
gold_standards = {}

for myfile in os.listdir(manual_dir):
    if myfile.endswith('gold_keywords.txt'):
        manual_tokens = []
        habibi_div_tokens = []
        habibi_no_div_tokens = []
        our_method_tokens = []
        tfidf_tokens = []

        with codecs.open(os.path.join(manual_dir, myfile), 'r', encoding='utf-8', errors='replace') as in_file:
            print 'Processing', myfile, ':'

            # Manual words are already separated
            gold_standard = [remove_line_end(line).strip() for line in in_file]

        raw_file = '.'.join(myfile.split('.')[:-2])
        filelist.append(raw_file)
        gold_standards[raw_file] = gold_standard 

print 'Evaluating with these files:'
print filelist

def eval_file(method_dir, raw_file, gold_standard, tolerated):
    method_tokens = []

    method_dir = os.path.join(eval_dir, method_dir)
    print 'Opening file:',os.path.join(method_dir, raw_file)
    with codecs.open(os.path.join(method_dir, raw_file), 'r', encoding='utf-8', errors='replace') as in_file:
        for line in in_file:
            method_tokens += remove_line_end(line).split()

        method_tokens_stemmed = [stemmer.stem(token) for token in method_tokens] 
        gold_standard_stemmed = [stemmer.stem(token) for token in gold_standard]
        tolerated_stemmed = [stemmer.stem(token) for token in tolerated]

        print '==========' + method_dir + '=========='
        print 'tokens:', method_tokens, method_tokens_stemmed
        print 'gold:', gold_standard, gold_standard_stemmed
        print 'tolerated:', tolerated, tolerated_stemmed
        
        recall = len(list(set(method_tokens_stemmed) & set(gold_standard_stemmed))) / float(len(gold_standard_stemmed))
        precision = len(list(set(method_tokens_stemmed) & set(gold_standard_stemmed))) / float(len(method_tokens_stemmed))
        hrr = len(list(set(method_tokens_stemmed) - set(gold_standard_stemmed) - set(tolerated_stemmed))) / float(len(method_tokens_stemmed))

        print 'Recall:', len(list(set(method_tokens_stemmed) & set(gold_standard_stemmed))), '/', len(gold_standard_stemmed), '=', recall
        print 'HRR:', len(list(set(method_tokens_stemmed) - set(gold_standard_stemmed) - set(tolerated_stemmed))), '/', len(method_tokens_stemmed), '=', hrr

        return recall,precision,hrr

recalls = defaultdict(list)
precs = defaultdict(list)
hrrs = defaultdict(list)

for myfile in filelist:
    tolerated_file = myfile + '.tolerated.txt'

    with codecs.open(os.path.join(manual_dir, tolerated_file), 'r', encoding='utf-8', errors='replace') as in_file:
        print 'Processing', tolerated_file, ':'

        # Manual words are already separated
        tolerated = [remove_line_end(line).strip() for line in in_file]

    for method in methods:
        recall,precision,hrr = eval_file(method, myfile, gold_standards[myfile], tolerated)
        recalls[method].append(recall)
        precs[method].append(precision)
        hrrs[method].append(hrr)

for key in sorted(recalls.keys()):
    print "-----------------Final Scores-----------------"
    print "Method:", "Avg. Recall (Std. Dev.),", "Avg. Precision (Std. Dev.)," , "Avg. HRR (Std. Dev.),", "Avg. Recall - Avg. HRR"
    recall = sum(recalls[key]) / len(recalls[key])
    recall_std = np.std(recalls[key])

    precision = sum(precs[key]) / len(precs[key])
    precision_std = np.std(precs[key])

    hrr = sum(hrrs[key]) / len(hrrs[key])
    hrr_std = np.std(hrrs[key])
    difference = recall - hrr
    print key, recall, "(", recall_std, "), ", precision, "(", precision_std, "), ", hrr, "(", hrr_std, "), ", difference
