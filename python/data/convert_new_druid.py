import io

with io.open('new_druid','r',encoding='utf-8') as in_file, io.open('new_druid_nopos','w',encoding='utf-8') as outfile:
	for line in in_file:
		split = line.split('\t')
		
		words = split[0].split(' ')
		words_nopos = [word.split('#')[0] for word in words]
		#print words_nopos,split[1]

		outfile.write(' '.join(words_nopos)+'\t'+str(split[1])+'\n')
