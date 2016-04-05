from __future__ import print_function

import os
import codecs
import nltk
import numpy as np
from statsmodels.stats.inter_rater import cohens_kappa, to_table

manual_keyword_dir_one = 'data/ted_keywords_BM'
manual_keyword_dir_two = 'data/ted_keywords_JW'
manual_transcripts_dir = 'data/ted_originals'

manual_keyword_dir_one_post = '.keywords.txt'
manual_keyword_dir_two_post = ''

manual_output_dir = 'data/manual_keywords2/'

gold_standards = []
toleratedes = []
gold_goals = []

contigency_tables = np.array([[0,0],[0,0]])

tokens_one_count = 0
tokens_two_count = 0

for file in os.listdir(manual_keyword_dir_two):
	print(file)
	tokens_one = []
	with codecs.open(os.path.join(manual_keyword_dir_one, file+manual_keyword_dir_one_post), 'r', encoding='utf-8', errors='replace') as in_file:
		for line in in_file:
			if line[-1] == '\n':
				line = line[:-1]
			if line == '':
				continue
			tokens_one += [line.lower()]
			

	tokens_two = []
	with codecs.open(os.path.join(manual_keyword_dir_two, file+manual_keyword_dir_two_post), 'r', encoding='utf-8', errors='replace') as in_file:
		for line in in_file:
			if line[-1] == '\n':
				line = line[:-1]
			if line == '':
				continue
			tokens_two += [line.lower()]

	manual_transcript = []
	with codecs.open(os.path.join(manual_transcripts_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
		for line in in_file:
			if line[-1] == '\n':
				line = line[:-1]
			if line == '':
				continue
			manual_transcript += [word for word in nltk.word_tokenize(line) if word not in ['.','-','--','!','?',',',';',':','_']]

	tokens_one = set(tokens_one)
	tokens_two = set(tokens_two)
	print('t1',tokens_one)
	print('t2',tokens_two)
	gold_standard = tokens_one & tokens_two

	print(gold_standard)
	tolerated = tokens_one.symmetric_difference(tokens_two)

	print("Gold Standard (for recall)")
	print("Count:", len(gold_standard))
	print(gold_standard)
	print("Tolerated words (for HRR)")
	print("Count:", len(tolerated))
	print(tolerated)

	#goldtandard ist overlap
	contigency_table = np.array([[len(list(gold_standard)), len(list(tokens_two-gold_standard))],
									[len(list(tokens_one-gold_standard)), len(manual_transcript) - len(set(list(tokens_one)+list(tokens_two)))]])

	print(contigency_table)

	contigency_tables += contigency_table



	# Let's Transform Gold Standard and Tolerated Phrases into a set of lemmatized words.
	lemmatizer = nltk.stem.WordNetLemmatizer()
	
	gold_standard_tokens = []
	for token in gold_standard:
		gold_standard_tokens += token.split()

	gold_standard_lemmatized = [lemmatizer.lemmatize(token) for token in gold_standard_tokens]
	gold_standard_lemmatized = list(set(gold_standard_lemmatized))

	tolerated_tokens = []
	for token in tolerated:
		tolerated_tokens += token.split()

	tolerated_lemmatized = [lemmatizer.lemmatize(token) for token in tolerated_tokens]
	tolerated_lemmatized = list(set(tolerated_lemmatized))


	with codecs.open(os.path.join(manual_output_dir, file + '.gold_keywords.txt'), 'w' , encoding='utf-8') as outfile:
		outfile.write('\n'.join(list(gold_standard_lemmatized)))

	gold_goals += [(manual_output_dir + file, len(' '.join(list(gold_standard_lemmatized)).split(' ')))] #if mwe counts as multiple words
	#gold_goals += [(manual_output_dir + file, len(list(gold_standard)))]# if mwe count as one word

	with codecs.open(os.path.join(manual_output_dir, file + '.tolerated.txt'), 'w' , encoding='utf-8') as outfile:
		outfile.write('\n'.join(list(tolerated_lemmatized)))

	tokens_one_count += len(tokens_one)
	tokens_two_count += len(tokens_two)

	#with codecs.open(os.path.join(algorithm_output, file), 'r', encoding='utf-8', errors='replace') as in_file:
#		for line in in_file:
	#		tokens_extr = []
		#	tokens_extr += " ".split(line).lower()
	#		tokens_extr = set(tokens_extr)

with codecs.open(os.path.join('goal_goals.txt'), 'w' , encoding='utf-8') as outfile:
	outfile.write('\n'.join([elem[0] + ' ' + str(elem[1]) for elem in gold_goals]))

print('contigency_tables: \n',contigency_tables)

print(cohens_kappa(contigency_tables))

print('Annotator 1 keyword_count1: ', tokens_one_count)
print('Annotator 2 keyword_count2: ', tokens_two_count)

#test kappa, should be 1
#print(cohens_kappa(np.array([[10,0],[0,10]])))