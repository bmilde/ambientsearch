import codecs

with codecs.open('1-1000_de.txt','r','utf-8') as infile:
    with codecs.open('1-1000_de2.txt','w','utf-8') as outfile:
	for line in infile:
	    outfile.write(line.split('#')[0] + '\n')
