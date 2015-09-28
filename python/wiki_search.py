import wikipedia

summary_cache = {}
keyword_cache = {}

def filterBrackets(test_str):
    ret = ''
    skip1c = 0
    skip2c = 0
    for i in test_str:
        if i == '[':
            skip1c += 1
        elif i == '(':
            skip2c += 1
        elif i == ']' and skip1c > 0:
            skip1c -= 1
        elif i == ')'and skip2c > 0:
            skip2c -= 1
        elif skip1c == 0 and skip2c == 0:
            ret += i
    return ret

# Input: sorted list of tuples (keyword,scores), maximal number of articles (can be more keywords, if no)
# This version does not perform clustering
def getSummariesSingleKeyword(keywords, max_articles=4, lang="en"):
	wikipedia.set_lang(lang)
	articles,summaries = [],[]

	num_results = 0

	for keyword,score in keywords:
		if num_results >= max_articles:
			break
		#check cache first
		if 	keyword in keyword_cache:
			articles.append(keyword_cache[keyword])
			num_results += 1
		else:
			result = wikipedia.search(keyword)
			if len(result) > 0:
				articles.append(result[0])
				num_results += 1
				keyword_cache[keyword] = result[0]
			else:
				keyword_cache[keyword] = ""
				
	for article in articles:
		if article != '':
			if article in summary_cache:
				summaries += [summary_cache[article]]
			else:
				summary = filterBrackets(wikipedia.summary(article, sentences=1))
				summaries += [summary]
				summary_cache[article] = summary
	return summaries