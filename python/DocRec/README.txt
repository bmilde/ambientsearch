KEYWORD EXTRACTION AND DOCUMENT RECOMMENDATION IN CONVERSATIONS (DocRec)

Software from the PhD thesis of Maryam Habibi (EPFL n. 6760)

Maryam Habibi, Idiap Research Institute, October 2015

M1habiby@gmail.com
apbelis@idiap.ch (advisor)


Table of Contents
-------------------
1. Introduction
2. Main components
3. Requirements
4. References


1. Introduction
-------------------
The package contains several pieces of Matlab code.  Taken together, they extract keywords
from a conversation, then use them to build implicit queries, and then consolidate the
sets of retrieved documents to recommend to the conversation participants.

First a list of keywords is extracted from the conversation transcript. Then, the keywords
from the list are topically clustered into several topically-independent subsets. Each
subset represents an implicit query, which is submitted to the Lucene search engine
(available from lucene.apache.org) to retrieve documents from Wikipedia (using a dump of
the pages available from dumps.wikimedia.org) or any other local repository indexed by
Lucene.

Finally the lists of results from each separate query are merged using a merging method
that favors diversity of topics among the recommended documents.


2. Main components
-------------------
1. TestMaryamTexts.m : the main Matlab source code which connects different modules 
2. readWord1.m : reads the input transcript, removes stop words and represents the transcript using topical information
3. BeamSearchKeywordExtraction.m : diverse keyword extraction
4. mainRD.m : diverse merging of lists of document results


3. Requirements
-------------------
1. Create the following folders in the main folder of the software. 

AllResults: folder in which the software writes the title, WPID (id of Wikipedia page) and scores of the documents retrieved for each implicit query in three separate files per implicit query (one for titles, one for WPIDs and one for scores).

RSL75: the software writes the final merged list of results in a file in this folder.

transcripts: the software reads the input file from this folder.

Value: the software writes the weights of implicit query in a file in this folder. Each line of the file indicates one weight and the line number indicates the query number.

W: the software writes the index of the keywords (position in the word list extracted by topic modeling) extracted by diverse keyword extraction method in the file "1" and the string corresponding to each index in the file "2" in this folder.

words: the software writes the keywords representing each implicit query in a file of this folder. For example, in the case of two implicit queries, two files will be generated with the names of "1" and "2", each representing the query number.

2. Define the absolute path of the main folder (where results of each module are read or written) in TestMaryamTexts.m and the path of the code actually performing the search (see point 5, e.g. search.jar) also in TestMaryamTexts.m.

3. Build the topic table and indicate its path in "readWord1.m".  The table is a (T+1)*N matrix which is represented by a .mat file (Matlab file, see provided example "datawiki1-100.mat"). T is the number of topics and N is the words in the dictionary. The first column of the matrix is made of words (strings). The other elements of the matrix are numbers. Each element represents the number of times a word is assigned to a topic over all trained documents. A (2+1)*3 matrix example is as follows:

word	t1	t2
------------------
flower	3	0
shoe	1	7
hand	1	4

4. Compute the probability of topic given a word in the dictionary, p(z|w)=p(w|z)p(z)/p(w).
p(z)=number of words assign to topic z/sum of elements in the table above
p(w)=sum of (p(w|z)p(z)) over all topics.  Store these numbers in a .mat file following the provided example ("twp.mat").

5. Write a piece of Java code to perform search over Wikipedia using a retrieval system such as Lucene.  The input is a set of words, e.g. "w1, w2, ...". The output should be written into the "results" folder under the main folder.


4. References
-------------------
M. Habibi. Modeling Users' Information Needs in a Document Recommender 
for Meetings.  EPFL Thesis n. 6760, Electrical Engineering Doctoral 
School (EDEE), 2015.

M. Habibi and A. Popescu-Belis. Keyword Extraction and Clustering for
Document Recommendation in Conversations. IEEE/ACM Transactions on
Audio, Speech and Language Processing (TASLP), pp. 746-759, Volume 23,
Issue 4, 2015.

M. Habibi and A. Popescu-Belis. Enforcing Topic Diversity in a Document
Recommender for Conversations. In Proceedings of the 25th International
Conference on Computational Linguistics (Coling 2014), pp. 588-599, Dublin,
Ireland, 2014.

M. Habibi and A. Popescu-Belis. Diverse Keyword Extraction from
Conversations. In Proceedings of the 51st Annual Meeting of the Association for
Computational Linguistics (ACL 2013), pp. 651-657, Sofia, Bulgaria, 2013.

