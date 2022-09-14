import requests
import os
from google.cloud import datastore
from scraper import getArticles
import json
        
#getArticles()

#datastore_client = datastore.Client()

url = "http://127.0.0.1:8080/api/text"
analysisUrl = "http://127.0.0.1:8080/api/analysis"

#requests.delete( "http://127.0.0.1:8080/api/clean")

script_dir = os.path.dirname(__file__)

pathLists = ["articles/db/en/","articles/db/de/","articles/citi/","articles/bnp/"]
en_path = "articles/db/en/"
de_path = "articles/db/de/"
citi_path = "articles/citi/"
bnp_path = "articles/bnp/"

enList = []
deList = []
citiList = []
bnpList = []
abs_dir = ""
for file_dir in pathLists:
    abs_dir = os.path.join(script_dir,file_dir)
    #print(abs_dir)
    if file_dir== en_path:
        for filename in os.listdir(abs_dir):
            #print(filename)
            enList.append(filename)
    elif file_dir == de_path:
        for filename in os.listdir(abs_dir):
            deList.append(filename)
    elif file_dir == citi_path:
        for filename in os.listdir(abs_dir):
            citiList.append(filename)
    elif file_dir == bnp_path:
        for filename in os.listdir(abs_dir):
            bnpList.append(filename)

#for filename in bnpList:
 #   print(filename)
"""for i in enList:
    print(i)
for i in deList:
    print(i)
for i in citiList:
    print(i)
for i in bnpList:
    print(i)
"""
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

text = ""
for article in enList:
    data = ""
    middle = os.path.join(script_dir,en_path)
    opened = os.path.join(middle,article)
    with open(opened, 'r',encoding="utf8") as file:
        one_char = file.read(1)
        if not one_char:
            continue
        data = file.read()
        data = data.strip(" ")
        data = data.strip('\n')
        data = data.strip('\t')
    msg = "?timestamp=" + article[0:10]+"&bank=dben" +"&title="+article[10:] +"&text="+data#'{"timestamp" :'+article[0:10]+', "text" :'+text+', "title":'+article[10:]+'}'
    #requests.post(url=url, headers=headers, data =json.dumps(msg))
    requests.post(url=url+msg)
    #requests.post(url=analysisUrl+msg)

for article in deList:
    data = ""
    middle = os.path.join(script_dir,de_path)
    opened = os.path.join(middle,article)
    with open(opened, 'r',encoding="utf8") as file:
        one_char = file.read(1)
        if not one_char:
            continue
        data = file.read()
        data = data.strip(" ")
        data = data.strip('\n')
        data = data.strip('\t')
    msg = "?timestamp=" + article[0:10]+"&bank=dbde" +"&title="+article[10:] +"&text="+data
    requests.post(url=url + msg)
    #requests.post(url=analysisUrl+msg)

for article in citiList:
    data = ""
    middle = os.path.join(script_dir,citi_path)
    opened = os.path.join(middle,article)
    with open(opened, 'r',encoding="utf8") as file:
        one_char = file.read(1)
        if not one_char:
            continue
        data = file.read()
        data = data.strip(" ")
        data = data.strip('\n')
        data = data.strip('\t')
    msg = "?timestamp=" + article[0:10]+"&bank=citi" +"&title="+article[10:] +"&text="+data
    requests.post(url=url+msg)
    #requests.post(url=analysisUrl+msg)

for article in bnpList:
    data = ""
    middle = os.path.join(script_dir,bnp_path)
    opened = os.path.join(middle,article)
    with open(opened, 'r',encoding="utf8") as file:
        one_char = file.read(1)
        if not one_char:
            continue
        data = file.read()
        data = data.strip(" ")
        data = data.strip('\n')
        data = data.strip('\t')
        date = article[0:10].replace("_","-")
    msg = "?timestamp=" + date+"&bank=bnp" +"&title="+article[10:] +"&text="+data
    requests.post(url=url+msg)
    #requests.post(url=analysisUrl+msg)

#requests.post(url + "?timestamp=test&bank=test&title=test&text=test")
#text = 
#headers = {
#    'accept': 'application/json',
#    'Content-Type': 'application/x-www-form-urlencoded'
#}

#print(requests.post(url=url, headers=headers, data=text))