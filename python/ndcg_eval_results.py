import json
import os
import io
import re
import math
import numpy as np
from collections import defaultdict

import flask
from flask import Flask

app = Flask(__name__)

ndcg_eval_dir = "data/ndcg_eval_dir"

origs = {}
needed_judgements = defaultdict(list)

# From http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def make_id_save(name):
    return re.sub(r'[^\w]', '_', name.replace(' ','_'))

def parse_ndcg_data():
    methods = os.listdir(ndcg_eval_dir)
    print methods
    for method in [elem for elem in methods]:
        method_dir = ndcg_eval_dir + '/' + method
        for json_file in [f for f in os.listdir(method_dir) if f.endswith(".json")]:
            with io.open(method_dir + '/' +json_file, 'r', encoding='utf-8') as json_in_file:
                filename_raw = json_file[:-5]
                ndcg_json = json.loads(json_in_file.read())
                top10 = ndcg_json[u"top10"]
                top5 = top10[:5]
                
                if filename_raw not in origs:
                    origs[filename_raw] = ndcg_json[u"orig"]

                for top in top5:
                    top[u'id'] = make_id_save(top[u'title'])
                    if top[u'id'] not in [judgement[u'id'] for judgement in needed_judgements[filename_raw]]:
                        needed_judgements[filename_raw].append(top)

    #print origs
    #print needed_judgements
    judgements = 0
    for key in needed_judgements:
        print key
        judgements += len(needed_judgements[key])
        print len(needed_judgements[key])
    print 'total judgements:',judgements

def calc_ndgc():

    save_dir = 'data/ndcg_save/'
    #save_dir = 'data/ndcg_save_no_minimum_match/'
    #save_dir = 'data/ndcg_save_unfair_druid/'

    judges = defaultdict(dict)
    judges_list = os.listdir(save_dir)
    for judge in judges_list:
        files_list = os.listdir(save_dir+judge)
        for json_file in files_list:
            if json_file.endswith(".json"):
                with io.open(save_dir+judge+'/'+json_file,'r',encoding='utf-8') as json_in_file:
                    #print save_dir+judge+'/'+json_file
                    json_str = json_in_file.read()
                    #print json_str
                    if 'Idea' in json_str:
                        print 'IdeaJSON',json_file
                    ndcg_json = json.loads(json_str)
                    judges[judge][json_file] = ndcg_json

    methods = os.listdir(ndcg_eval_dir)
    print methods
    NDCGs = defaultdict(list)
    DCGs = defaultdict(list)
    hits = defaultdict(list)
    for method in [elem for elem in methods]:
        method_dir = ndcg_eval_dir + '/' + method
        
        shorter_origs = {}

        #for key in origs:
        #    shorter_origs.

        for json_file in [f for f in os.listdir(method_dir) if f.endswith(".json")]:
            with io.open(method_dir + '/' +json_file, 'r', encoding='utf-8') as json_in_file:
                filename_raw = json_file[:-5]
                ndcg_json = json.loads(json_in_file.read())
                top10 = ndcg_json[u"top10"]
                top5 = top10[:5]

                judgement = defaultdict(float)
                judgement_div = defaultdict(float)
                for judge in judges:
                    if json_file in judges[judge]:
                        single_judgement = judges[judge][json_file]
                        for title in single_judgement:
                            print 'single:',single_judgement[title]
                            judgement[title] += single_judgement[title]
                            judgement_div[title] += 1.0
                    else:
                        print("Warning:", json_file, 'not in', judge)
                for title in judgement:
                    judgement[title] /= judgement_div[title]

                print judgement
                DCG = 0.0
                ranks = []
                ranks_title = []
                for i,top in enumerate(top5):
                    ranks_title.append(top["title"])
                    score = judgement[top["title"]]
                    ranks += [score]
                    if i==0:
                        DCG += float(score)
                    else:
                        DCG += (float(score)/ math.log(i+1,2))
                print(method,zip(ranks_title,ranks))

                #Now compute ideal ranks
                ranks = [judgement[key] for key in judgement]
                ranks.sort(reverse=True)
                #if len(ranks) > 10:
                ranks = ranks[:5]
                print('Ideal ranks:',method,ranks)
                IDCG = 0.0
                hit = 0
                for i,rank in enumerate(ranks):
                    if i==0:
                        IDCG += float(rank)
                    else:
                        IDCG += (float(rank)/ math.log(i+1,2))
                    if rank > 0:
                        hit += 1.0
                hits[method].append(hit)
                #print(method,"IDCG",i,IDCG)
                print(method,"DCG",DCG,"IDCG",IDCG)
                if IDCG == 0.0:
                    NDCG = 0.0
                else:
                    NDCG = DCG / IDCG
                print('NDCG for', method_dir + '/' +json_file,'is',NDCG)
                NDCGs[method].append(NDCG)
                DCGs[method].append(DCG)
    for method in NDCGs:
        print method,'mean NDCG:','%0.3f' % np.mean(NDCGs[method]),'std', '%0.3f' % np.std(NDCGs[method])
        #print method,'median NDCG:','%0.3f' % np.median(NDCGs[method]),'std', '%0.3f' % np.std(NDCGs[method])
        #print method,'mean DCG:','%0.3f' % np.mean(DCGs[method]),'std','%0.3f' % np.std(DCGs[method])
        #print method,'mean hit:','%0.3f' % np.mean(hits[method]),'std','%0.3f' % np.std(hits[method])

@app.route("/ndcg_list/<username>")
def ndcg_list(username):
    html = u'''<!doctype html><html lang=en><head><meta charset=utf-8><title>NDCG Ambient Search Eval</title>
            </head><body>'''
    
    html += u'<h1>Hi '+username+u'</h1>'
    html += u'<ul>'
    for key in needed_judgements:
        length = str(len(needed_judgements[key]))
        html += u'<li><a href="/ndcg/'+key+u'/'+username+u'">'+key+u'</a> ('+length+u')</li>'
    html += u'</ul>'
    html += u'''
    </body>
    </html>'''
    return html

@app.route('/ndcg_save/<filename>/<username>', methods=['POST'])
def ndcg_save(filename,username):
    username_dir = 'data/ndcg_save/' + make_id_save(username) + "/"
    ensure_dir(username_dir)
    json_out = {}

    parse_errors = ''
    for key in flask.request.form:
        try:
            value = int(flask.request.form[key])
            if value >= 0 and value <= 3: 
                json_out[key] = value
                parse_error = False
            else:
                parse_error = True
        except:
            parse_error = True
        if parse_error:
            parse_errors += key + ' ' + (flask.request.form[key] if flask.request.form[key] != '' else '&lt;empty string&gt;') + '<br/>'

    json_str = json.dumps(json_out)

    print 'New json str:',json_str
    print 'Parse errors:',parse_errors

    with open(username_dir + filename + '.json','w') as filename_out:
        filename_out.write(json_str)

    html = u'''<!doctype html><html lang=en><head><meta charset=utf-8><title>NDCG Ambient Search Eval</title>
                    </head><body>'''
    if parse_errors != '':
        html += u'Could not parse: <br/>' + parse_errors + '<br/>'
    html += u'Thanks. Now go back to: <a href="/ndcg_list/'+username+'">the list</a>'
    html += u'</body></html>'
    return html

@app.route("/ndcg/<filename>/<username>")
def ndcg(filename,username):
    if filename not in origs:
        return u'Could not find: '+filename
    #if os.path.exists('data/ndcg_save/' + make_id_save(username) + "/" + filename + '.json'):
    
    html = u'''<!doctype html><html lang=en><head><meta charset=utf-8><title>NDCG Ambient Search Eval</title>
            </head><body>'''
#you give a 0 score for an irrelevant result, 1 for a partially relevant, 2 for relevant, and 3 for perfect.

    html += u'<h1>Hi '+username+u'</h1>'
    html +=u'''<p>Each document is to be judged on a scale of 0-3 with 0 meaning irrelevant, 
    1 partially relevant, 2 for relevant and 3 for very relevant / perfect.</p>'''
    html += u'<h2>' + filename + u' text is:</h2>'
    html += origs[filename]
    html += '<form action="/ndcg_save/'+filename+'/'+username+'" method="post">'
    for judgement in needed_judgements[filename]:
        html += u'<h3>On a scale from 0 to 3, how relevant is <a href="'+ judgement[u'url'] +'">'+ judgement[u'title']  +'</a></h3>'
        html += u'Wiki text: ' + judgement[u'text'] + u'<br/>'
        html += u'Wiki categories: ' + u' '.join(judgement[u'categories']) + u'<br/>'
        my_id = judgement[u'id']
        html += u'<input list="'+my_id+u'" name="'+judgement[u'title']+'"><datalist id="'+my_id+'"><option value="0">0</option><option value="1">1</option><option value="2">2</option><option value="3">3</option></datalist></input>'
    html += '<br/><input type="submit"></form>'
        #html += u'<ul>'

        #html += u'/<ul>'
    html += u'</body></html>'
    return html

if __name__ == "__main__":
    #parse_ndcg_data()
    calc_ndgc()
    #app.debug = True
    #app.run(host='0.0.0.0')
