import nltk
import codecs
import os
import numpy as np

def data_directory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

manual_dir = os.path.join(data_directory(), 'manual_keywords2')
habibi_div_dir = os.path.join(data_directory(), 'habibi075')
habibi_no_div_dir = os.path.join(data_directory(), 'habibi10')
our_method_dir = os.path.join(data_directory(), 'keywords_our_method')
tfidf_dir = os.path.join(data_directory(), 'keywords_tfidf')

lemmatizer = nltk.stem.WordNetLemmatizer()

habibi_div_recalls = []
habibi_no_div_recalls = []
our_method_recalls = []
tfidf_recalls = []

habibi_div_hrrs = []
habibi_no_div_hrrs = []
our_method_hrrs = []
tfidf_hrrs = []

filenames = []

for file in os.listdir(manual_dir):
    if file.endswith('gold_keywords.txt'):
        manual_tokens = []
        habibi_div_tokens = []
        habibi_no_div_tokens = []
        our_method_tokens = []
        tfidf_tokens = []

        with codecs.open(os.path.join(manual_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            print 'Processing', file, ':'

            # Manual words are already separated
            gold_standard = [line.strip() for line in in_file]
        
        tolerated_file = '.'.join(file.split('.')[:-2]) + '.tolerated.txt'
        with codecs.open(os.path.join(manual_dir, tolerated_file), 'r', encoding='utf-8', errors='replace') as in_file:
            print 'Processing', tolerated_file, ':'

            # Manual words are already separated
            tolerated = [line.strip() for line in in_file]

        raw_file = '.'.join(file.split('.')[:-2])
        with codecs.open(os.path.join(habibi_div_dir, raw_file), 'r', encoding='utf-8', errors='replace') as in_file:
            # Habibis Tokens are already separated as well
            habibi_div_tokens = [lemmatizer.lemmatize(line.strip()) for line in in_file]

            print '==========Habibi lam=0.75=========='
            recall = len(list(set(habibi_div_tokens) & set(gold_standard))) / float(len(gold_standard))
            habibi_div_recalls.append(recall)

            hrr = len(list(set(habibi_div_tokens) - set(gold_standard) - set(tolerated))) / float(len(habibi_div_tokens))
            habibi_div_hrrs.append(hrr)

            print 'Recall:', len(list(set(habibi_div_tokens) & set(gold_standard))), '/', len(gold_standard), '=', recall
            print 'HRR:', len(list(set(habibi_div_tokens) - set(gold_standard) - set(tolerated))), '/', len(habibi_div_tokens), '=', hrr

        with codecs.open(os.path.join(habibi_no_div_dir, raw_file), 'r', encoding='utf-8', errors='replace') as in_file:
            habibi_no_div_tokens = [lemmatizer.lemmatize(line.strip()) for line in in_file]

            print '==========Habibi lam=1.0=========='
            recall = len(list(set(habibi_no_div_tokens) & set(gold_standard))) / float(len(gold_standard))
            habibi_no_div_recalls.append(recall)

            hrr = len(list(set(habibi_no_div_tokens) - set(gold_standard) - set(tolerated))) / float(len(habibi_no_div_tokens))
            habibi_no_div_hrrs.append(hrr)

            print 'Recall:', len(list(set(habibi_no_div_tokens) & set(gold_standard))), '/', len(gold_standard), '=', recall
            print 'HRR:', len(list(set(habibi_no_div_tokens) - set(gold_standard) - set(tolerated))), '/', len(habibi_no_div_tokens), '=', hrr

        with codecs.open(os.path.join(our_method_dir, raw_file), 'r', encoding='utf-8', errors='replace') as in_file:
            for line in in_file:
		        our_method_tokens += line.split()

            print '==========Our method=========='
            recall = len(list(set(our_method_tokens) & set(gold_standard))) / float(len(gold_standard))
            our_method_recalls.append(recall)

            hrr = len(list(set(our_method_tokens) - set(gold_standard) - set(tolerated))) / float(len(our_method_tokens))
            our_method_hrrs.append(hrr)

            print 'Recall:', len(list(set(our_method_tokens) & set(gold_standard))), '/', len(gold_standard), '=', recall
            print 'HRR:', len(list(set(our_method_tokens) - set(gold_standard) - set(tolerated))), '/', len(our_method_tokens), '=', hrr

        with codecs.open(os.path.join(tfidf_dir, raw_file), 'r', encoding='utf-8', errors='replace') as in_file:
            for line in in_file:
		        tfidf_tokens += line.split()

            print '==========TF-IDF=========='
            recall = len(list(set(tfidf_tokens) & set(gold_standard))) / float(len(gold_standard))
            tfidf_recalls.append(recall)

            hrr = len(list(set(tfidf_tokens) - set(gold_standard) - set(tolerated))) / float(len(tfidf_tokens))
            tfidf_hrrs.append(hrr)


            print 'Recall:', len(list(set(tfidf_tokens) & set(gold_standard))), '/', len(gold_standard), '=', recall
            print 'HRR:', len(list(set(tfidf_tokens) - set(gold_standard) - set(tolerated))), '/', len(tfidf_tokens), '=', hrr

        filenames.append(raw_file)


print "-----------------Final Scores-----------------"
print "Method:", "Avg. Recall (Std. Dev.),", "Avg. HRR (Std. Dev.),", "Avg. Recall - Avg. HRR"
recall = sum(habibi_div_recalls) / len(habibi_div_recalls)
recall_std = np.std(habibi_div_recalls)
hrr = sum(habibi_div_hrrs) / len(habibi_div_hrrs)
hrr_std = np.std(habibi_div_hrrs)
difference = recall - hrr
print "Habibi (lam=0.75):", recall, "(", recall_std, "), ", hrr, "(", hrr_std, "), ", difference
recall = sum(habibi_no_div_recalls) / len(habibi_no_div_recalls)
recall_std = np.std(habibi_no_div_recalls)
hrr = sum(habibi_no_div_hrrs) / len(habibi_no_div_hrrs)
hrr_std = np.std(habibi_no_div_hrrs)
difference = recall - hrr
print "Habibi (lam=1.0):", recall, "(", recall_std, "), ", hrr, "(", hrr_std, "), ", difference
recall = sum(our_method_recalls) / len(our_method_recalls)
recall_std = np.std(our_method_recalls)
hrr = sum(our_method_hrrs) / len(our_method_hrrs)
hrr_std = np.std(our_method_hrrs)
difference = recall - hrr
print "Our method:", recall, "(", recall_std, "), ", hrr, "(", hrr_std, "), ", difference
recall = sum(tfidf_recalls) / len(tfidf_recalls)
recall_std = np.std(tfidf_recalls)
hrr = sum(tfidf_hrrs) / len(tfidf_hrrs)
hrr_std = np.std(tfidf_hrrs)
difference = recall - hrr
print "TF-IDF:", recall, "(", recall_std, "), ", hrr, "(", hrr_std, "), ", difference

print "Individual keyphrase relevance values:"
print sorted(zip(filenames,np.array(our_method_recalls) - np.array(our_method_hrrs)))
