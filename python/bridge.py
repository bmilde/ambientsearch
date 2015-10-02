import requests
import json

#Abstracts away the details of communicating with the ambient server
class KeywordClient():

    def __init__(self,server_url):
	self.server_url = server_url
	self.request_header = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    def getSettings():
        r = requests.get(self.server_url+'getSettings')
        return r.json()

    #def setKeywordList(self, keyword_list):
    #    data = {'keywords':keyword_list}
    #    r = requests.post(self.server_url+'setKeywordList', data=json.dumps(data), headers=self.request_header)
    #    return r.status_code
        
    def addRelevantEntry(self, type, title, text, url, score):
        data = {'handle':'addRelevantEntry','type':type,'entry_id':title.replace(' ','_'),'title':title,'text':text,'url':url,'score':score}
        r = requests.post(self.server_url+'addRelevantEntry', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def delRelevantEntry(self, type, title):
        data = {'handle':'delRelevantEntry','type':type,'title':title}
        r = requests.post(self.server_url+'delRelevantEntry', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def addUtterance(self, utterance,speaker):
        data = {'handle':'addUtterance','utterance':utterance,'speaker':speaker}
        r = requests.post(self.server_url+'addUtterance', data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def replaceLastUtterance(self, old_utterance,new_utterance,speaker):
        data = {'handle':'replaceLastUtterance','old_utterance':old_utterance,'utterance':new_utterance,'speaker':speaker}
        r = requests.post(self.server_url+'replaceLastUtterance', data=json.dumps(data), headers=self.request_header)
        return r.status_code
        
#Abstracts away the details of communicating with the ambient server, hacky version
class KeywordClientHacky():

    def __init__(self,server_url):
        self.server_url = server_url
        #self.request_header = "{'Content-type': 'application/json', 'Accept': 'text/plain'}"
        print 'Keyword client URL:', server_url

    def getSettings(self):
             
        #r = requests.get(server_url+'getSettings')
        #return r.json()
        return ''

    def setKeywordList(self,keyword_list):
        data = {'keywords':keyword_list}
        payload = {'keyword0': json.dumps(data)}
        #print payload
        r = requests.post(self.server_url+'setKeywordList.jsp', params=payload) #data=json.dumps(data), headers=self.request_header)
        return r.status_code

    def addUtterance(self,utterance,speaker):
        #data = {'utterance':utterance,'speaker':speaker}
        #r = requests.post(server_url+'addUtterance', data=json.dumps(data), headers=self.request_header)
        return ''#r.status_code

    def replaceLastUtterance(self,old_utterance,new_utterance,speaker):
        #data = {'old_utterance':old_utterance,'new_utterance':new_utterance,'speaker':speaker}
        #r = requests.post(server_url+'replaceLastUtterance', data=json.dumps(data), headers=self.request_header)
        return ''#r.status_code