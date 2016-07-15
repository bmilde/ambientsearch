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

methods = ['tfidf_nodruid_nofilter_nostopwords', 'tfidf_nodruid_nofilter', 'tfidf_nodruid', 'tfidf', 'tfidf_orig', 'habibi75', 'habibi75_orig', 'proposed', 'proposed_nodruid','proposed_orig']

#methods = ['habibi75', 'habibi75_orig', 'habibi75_prep', 'habibi75_orig_prep']

pretty_method_names = {
    'tfidf_nodruid_nofilter_nostopwords' : 'TF-IDF baseline, no multiwords, no filtering',
    'tfidf_nodruid_nofilter' : 'TF-IDF baseline, no multiwords, only stopword filtering',
    'tfidf_nodruid' : 'TF-IDF baseline, no multiwords, full filtering',
    'tfidf' : 'TF-IDF baseline, with DRUID multiwords, full filtering',
    'tfidf_orig' : 'TF-IDF baseline on gold transcriptions, with DRUID multiwords, full filtering',
    'habibi75' : 'Habibi and PB',
    'habibi75_orig' : 'Habibi and PB, gold transcriptions',
    'habibi75_prep' : 'Habibi and PB, our preprocessing',
    'habibi75_orig_prep' : 'Habibi and PB, our preprocessing, gold transcriptions',
    'proposed_nodruid' : 'Our proposed method, without DRUID multiwords',
    'proposed' : 'Our proposed method, with DRUID multiwords',
    'proposed_orig' : 'Our proposed method on gold transcriptions, with DRUID multiwords',
}

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

for i,key in enumerate(methods):
    #print "-----------------Final Scores-----------------"
    #print "Method:", "Avg. Recall (Std. Dev.),", "Avg. Precision (Std. Dev.)," , "Avg. HRR (Std. Dev.),", "Avg. Recall - Avg. HRR"
    recall = sum(recalls[key]) / len(recalls[key])
    recall_std = np.std(recalls[key])

    precision = sum(precs[key]) / len(precs[key])
    precision_std = np.std(precs[key])

    hrr = sum(hrrs[key]) / len(hrrs[key])
    hrr_std = np.std(hrrs[key])
    difference = recall - hrr
    #print key, '%0.4f' % recall, "(", '%0.4f' % recall_std, "), ", '%0.4f' % precision, "(", '%0.4f' % precision_std, "), ", \
            #'%0.4f' % hrr, "(", '%0.4f' % hrr_std, "), ", '%0.4f' % difference

    #print 'latex:'
    print ('(%i)'%(i+1)),pretty_method_names[key],'&',('%0.2f' % (recall*100.0))+'\\%', ' ('+ ('%0.2f' % (recall_std*100.0))+'\\%'+ ')','&', ('%0.2f' % (precision*100.0))+'\\%' , \
    '\\% ('+ ('%0.2f' % (precision_std*100.0))+'\\%'+ ')', '&', ('%0.2f' % (hrr*100.0)) + '\\%', '(' + ('%0.2f' % (hrr_std*100.0))+'\\%' + ')', '&' , ('%0.2f' % (difference*100.0))+'\\%','& (NDCG here)','\\\\ \\hline'
