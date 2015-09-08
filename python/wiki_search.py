import wikipedia

def getSummariesSingleKeyword(keywords,lang="en"):
	wikipedia.set_lang(lang)
	articles = []
	for keyword in keywords:
		result = wikipedia.search(keyword)
		if len(result) > 0:
			articles.append(result[0])
	for article in articles:
		summaries = [wikipedia.summary(article, sentences=1)]
		
	return summaries