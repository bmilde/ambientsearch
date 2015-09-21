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

def getSummariesSingleKeyword(keywords,lang="en"):
	wikipedia.set_lang(lang)
	articles,summaries = [],[]
	for keyword in keywords:
		#check cache first
		if 	keyword in keyword_cache:
			articles.append(keyword_cache[keyword])
		else:
			result = wikipedia.search(keyword)
			if len(result) > 0:
				articles.append(result[0])
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