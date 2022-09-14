from pathlib import Path
from typing import final
from selenium import webdriver
import time
import requests
import os
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.select import Select
from sklearn import naive_bayes

def containsNews(url):
    if 'news' not in url or 'www.' not in url or 'http' in url:
        return False
    return True

def containsNewsCiti(url):
    if 'news' not in url or 'citigroup' in url or 'html' in url or 'social-media' in url or 'earnings' in url:
        return False
    return True

def containsNewsBnp(url):
    if 'news' not in url or 'mediaroom' in url:
        return False
    return True

def checkForDate(text):
    if 'January' in text:
        date = text.partition("January")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-01' + date[:3]
    if 'February' in text:
        date = text.partition("February")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-02' + date[:3]
    if 'March' in text:
        date = text.partition("March")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-03' + date[:3]    
    if 'April' in text:
        date = text.partition("April")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-04' + date[:3]
    if 'May' in text:
        date = text.partition("May")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-05' + date[:3]
    if 'June' in text:
        date = text.partition("June")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-06' + date[:3]
    if 'July' in text:
        date = text.partition("July")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-07' + date[:3]
    if 'August' in text:
        date = text.partition("August")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-08' + date[:3]
    if 'September' in text:
        date = text.partition("September")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-09' + date[:3]
    if 'October' in text:
        date = text.partition("October")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-10' + date[:3]
    if 'November' in text:
        date = text.partition("November")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-11' + date[:3]
    if 'December' in text:
        date = text.partition("December")[2]
        if len(date) != 9:
            date = date[0] + str(0) + date[1:]
        return date[5:] + '-12' + date[:3]
    return ""

def checkForDateDE(text):
    if 'Januar' in text:
        date = text.partition("Januar")[2]
        day = text.partition("Januar")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-01-' + day[:2]
    if 'Februar' in text:
        date = text.partition("Februar")[2]
        day = text.partition("Februar")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-02-' + day[:2]
    if 'März' in text:
        date = text.partition("März")[2]
        day = text.partition("März")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        #print(day)
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        #print(day)
        return date[1:] + '-03-' + day[:2]    
    if 'April' in text:
        date = text.partition("April")[2]
        day = text.partition("April")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
    
        return date[1:] + '-04-' + day[:2]
    if 'Mai' in text and 'Main' not in text:
        date = text.partition("Mai")[2]
        day = text.partition("Mai")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        return date[1:] + '-05-' + day[:2]
    if 'Juni' in text:
        date = text.partition("Juni")[2]
        day = text.partition("Juni")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-06-' + day[:2]
    if 'Juli' in text:
        date = text.partition("Juli")[2]
        day = text.partition("Juli")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        #print('07-' + day[:2] + "-" + date[1:])
        return date[1:] + '-07-' + day[:2]
    if 'August' in text:
        date = text.partition("August")[2]
        day = text.partition("August")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-08-' + day[:2]
    if 'September' in text:
        date = text.partition("September")[2]
        day = text.partition("September")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-09-' + day[:2]
    if 'Oktober' in text:
        date = text.partition("Oktober")[2]
        day = text.partition("Oktober")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-10-' + day[:2]
    if 'November' in text:
        date = text.partition("November")[2]
        day = text.partition("November")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            #day = day[0] + str(0) + day[1:]
            day = day[1:]
            #print(day + "/" + str(len(day)))
        if len(day) != 4:
            day = str(0) + day
            #print(day)
        #print('05-' + day[:2] + "-" + date[1:])
        return date[1:] + '-11-' + day[:2]
    if 'Dezember' in text:
        date = text.partition("Dezember")[2]
        day = text.partition("Dezember")[0]
        if "," in day:
            list = day.partition(",")
            day = list[2]
            day = day[1:]
        if len(day) != 4:
            day = str(0) + day
        day = day[len(day)-4:len(day)]
        return date[1:] + '-12-' + day[:2]
    return ""

def checkForDateBnp(text):
    text = text[54:64]
    return text[6:10] +"-"+ text[3:5]+"_" + text[0:2]

def dbScrape(language):
    lang = 3
    if language == "EN":
        lang = 1

    #dirname = Path(__file__).parent / "chromedriver"
    #print (dirname)
    #browser=webdriver.Chrome(dirname)

    dirname = "C:/Users/kkgaf/Desktop/chromedriver_win32/chromedriver.exe"
    #print (dirname)
    browser=webdriver.Chrome(dirname)

    url = "https://www.db.com/media/news?tags=sustainability&language_id="+ str(lang)
    browser.get(url)
    try:
       myElem = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'news-meta-type')))
    except TimeoutException:
       print( "Loading took too much time!")
    html = browser.page_source

    browser.close()

    #text_file = open("text.txt","w", encoding="utf-8")
    #n = text_file.write(html)
    #text_file.close()

    soup = BeautifulSoup(html,"html.parser")
    linklist = []
    for link in soup.find_all('a'):
         #print(type(link.get('class')))
        if link.get('class') is not None: 
         if len(link.get('class')) !=0 and link.get('class')[0] == 'wt-enabled':
            linklist.append(link.get('href'))
    filtered = filter(containsNews, linklist)

    finallist = []
    for s in filtered:
     if s[2:] not in finallist:
         finallist.append(s[2:])
         #finallist.append(s[2:len(s)-1] + "3")
    #for s in finallist:
     #   print(s)
    return finallist

def citiScrape():
    dirname = "C:/Users/kkgaf/Desktop/chromedriver_win32/chromedriver.exe"
    #print (dirname)
    browser=webdriver.Chrome(dirname)
    url = "https://www.citigroup.com/citi/news/news_list_view.html"
    browser.get(url)
    try:
       myElem = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.ID, 'press-topic')))
    except TimeoutException:
       print( "Loading took too much time!")
    time.sleep(5)
    sel = Select(browser.find_element_by_xpath("//select[@id='press-topic']"))
    #print(sel.all_selected_options)
    sel.select_by_index(3)

    html = browser.page_source

    browser.close()

    soup = BeautifulSoup(html,"html.parser")
    linklist = []
    for link in soup.find_all('a'):
        linklist.append(link.get('href'))
    filtered = filter(containsNewsCiti, linklist)

    finallist = []
    for s in filtered:
     if s not in finallist:
         finallist.append("https://www.citigroup.com" + s)
         #finallist.append(s[2:len(s)-1] + "3")
    #for s in finallist:
    #    print(s)
    return finallist

def bnpScrape():
    dirname = "C:/Users/kkgaf/Desktop/chromedriver_win32/chromedriver.exe"
    #print (dirname)
    browser=webdriver.Chrome(dirname)
    url = "https://group.bnpparibas/en/all-news/sustainable-finance"
    browser.get(url)
    try:
       myElem = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'card-link')))
    except TimeoutException:
       print( "Loading took too much time!")
    time.sleep(5)
    #sel = Select(browser.find_element_by_xpath("//select[@id='press-topic']"))
    #print(sel.all_selected_options)
    #sel.select_by_index(3)

    html = browser.page_source

    browser.close()

    soup = BeautifulSoup(html,"html.parser")
    linklist = []
    for link in soup.find_all('a'):
        if link.get('class') is not None and link.get('class')[0] == "card-link":
            linklist.append(link.get('href'))
    filtered = filter(containsNewsBnp, linklist)

    finallist = []
    for s in filtered:
     if s not in finallist:
        if 'https' not in s:
            finallist.append("https://group.bnpparibas" + s)
        else:
            finallist.append(s)
    return finallist

def getArticles():
    dbListEN = dbScrape("EN")
    dbListDE = dbScrape("DE")
    citiList = citiScrape()
    bnpList = bnpScrape()
    #print(dbListEN)
    #print(dbListDE)
    #print(citiList)
    #print(bnpList)
    for link in dbListEN:
        html = requests.get("http://" + link).text
        #print(html)
        date = ""
        soup = BeautifulSoup(html,"html.parser")
        for span in soup.find_all('span'):
            value = checkForDate(span.get_text())
            if value != "":
                date = value.replace(" ","-")
                #print(date)
                break
        title = soup.h1.string
        body = soup.get_text()
        fileTitle = title.replace(" ","_")
        script_dir = os.path.dirname(__file__)
        rel_path = "articles/db/en/" + date + "_"  + fileTitle + ".txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        text_file = open(abs_file_path,"w", encoding="utf-8")
        text_file.write(body)
        text_file.close()
    for link in dbListDE:
        html = requests.get("http://" + link).text
        #print(html)
        date = ""
        soup = BeautifulSoup(html,"html.parser")
        for span in soup.find_all('span'):
            value = checkForDateDE(span.get_text())
            if value != "":
                date = value.replace(" ","-")
                #print(date)
                break
        title = soup.h1.string
        body = soup.get_text()
        fileTitle = title.replace(" ","_")
        script_dir = os.path.dirname(__file__)
        rel_path = "articles/db/de/" + date + "_"  + fileTitle +".txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        text_file = open(abs_file_path,"w", encoding="utf-8")
        text_file.write(body)
        text_file.close()
    for link in citiList:
        html = requests.get(link).text
        #print(html)
        date = ""
        soup = BeautifulSoup(html,"html.parser")
        for span in soup.find_all('div'):
            #print(span.get_text)
            value = ""
            if(span.get('class') is not None and len(span.get('class')) > 1 and span.get('class')[1] == "press-date"):
                #print(span.text + "/" + span.text[5:len(span.text) - 5])
                value = checkForDate(span.text)
            if value != "":
                #print(value)
                #print("Here")
                date = value.replace(" ","-")
                #print(date)
                break
        title = soup.h1.string
        #print(title)
        body = soup.get_text()
        fileTitle = title.replace(" ","_")
        script_dir = os.path.dirname(__file__)
        rel_path = "articles/citi/" + date + "_"  + title + ".txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        text_file = open(abs_file_path,"w",encoding="utf-8")
        text_file.write(body)
        text_file.close()
    for link in bnpList:
        html = requests.get(link).text
        #print(html)
        date = ""
        soup = BeautifulSoup(html,"html.parser")
        for span in soup.find_all('div'):
            #print(span.get_text)
            value = ""
            if(span.get('class') is not None and span.get('class')[0] == 'article-date'):
                #print(span.text + "/" + span.text[5:len(span.text) - 5])
                value = checkForDateBnp(span.text)
            if value != "":
                #print(value)
                #print("Here")
                date = value.replace(" ","-")
                #print(date)
                break
        titleList = soup.find_all("h1")
        title = ""
        #print(titleList)
        for s in titleList:
            if s.get("class") is not None and s.get("class")[0] == "title-2":
                title = s.get_text()
                #print (title)
        #print(title)
        body = soup.get_text()
        fileTitle = title.replace(" ","_")
        fileTitle = title.replace(":","")
        script_dir = os.path.dirname(__file__)
        rel_path = "articles/bnp/" + date + "_"  + title + ".txt"
        abs_file_path = os.path.join(script_dir, rel_path)
        text_file = open(abs_file_path,"w",encoding="utf-8")
        text_file.write(body)
        text_file.close()
#getArticles()