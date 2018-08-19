import requests
import urllib.request, urllib.parse, urllib.error
from requests_html import HTML
import re
import os, sys
import random
import sqlite3

def fetch(url):
    '''
    尋找不止一頁最新的資料!!
    '''
    def parse_next_link(doc):
        html = HTML(html=doc)
        controls = html.find('.action-bar a.btn.wide')
        '''我們需要上一頁資料(較舊的)，去抓controls中第二個(index為1)的href'''
        link = controls[1].attrs.get('href')
        return urllib.parse.urljoin('https://www.ptt.cc/', link)

    response = requests.get(url)
    response = requests.get(url, cookies={'over18': '1'})  # 一直向 server 回答滿 18 歲了 !
    html = HTML(html=response.text)
    post_entries = html.find('div.r-ent')      #post_entries為許多div 'class'="r-ent"樹組成的「list」
    Next_link = parse_next_link(response.text)
    return post_entries, Next_link

def fetch_image_links(url):
    response = requests.get(url)
    response = requests.get(url, cookies={'over18': '1'})
    html = HTML(html=response.text)
    content_entries = html.find('a')        #藉由print(response.text)可以發現圖片連結都在Element 'a'的樹裡，而且不屬於別的Element底下
    img_urls = []
    for content in content_entries:
        if re.match(r'^https?://(i.)?(m.)?imgur.com', content.attrs['href']):
            img_urls.append(content.attrs['href'])
    return img_urls

#resp = fetch(url)  # step-1
#print(resp.text) # result of step-1

#html = HTML(html=resp.text)  #.text才會decode成python形式資料

#post_entries = html.find('div.r-ent')
#print(type(resp),type(resp.text),type(html), type(post_entries))
'''post_entries為許多div class="r-ent"樹組成的「list」'''
#print(post_entries) # result of step-2

def parse_meta(entry):
    meta = {
        'title' : entry.find('div.title', first = True).text,
        'push' : entry.find('div.nrec', first = True).text,
        'date' : entry.find('div.date', first = True).text,
    }

    '''
    如果文章已被刪除會出現一個問題，網頁資料不會有link，所以以下程式碼會導致程式中斷，我們用try-except避免中斷
    '''
    try:
        meta['author'] = entry.find('div.author', first = True).text
        meta['link'] = entry.find('div.title > a', first = True).attrs['href']
        if meta['title'].split(' ')[0].startswith('Re:'):
            meta['title'] = meta['title'].replace('Re:', '[回文]')
        if '?' or '「' or '」' in meta['title']:
            meta['title'] = meta['title'].replace('?', '')
            meta['title'] = meta['title'].replace('「', '')
            meta['title'] = meta['title'].replace('」', '')
    except :
        if '(本文已被刪除)' in meta['title']:
            new_title = meta['title']
            find_author = new_title.split()
            theauthor = find_author[1]
            meta['author'] = theauthor[1:-1]
            meta['link'] = None
            if '?' or '「' or '」' in meta['title']:
                meta['title'] = meta['title'].replace('?', '')
                meta['title'] = meta['title'].replace('「', '')
                meta['title'] = meta['title'].replace('」', '')
        else:
            if '?' or '「' or '」' in meta['title']:
                meta['title'] = meta['title'].replace('?', '')
                meta['title'] = meta['title'].replace('「', '')
                meta['title'] = meta['title'].replace('」', '')
            new_title = meta['title']
            find_author = new_title.split()
            theauthor = find_author[1]
            meta['author'] = theauthor[1:-1]
            meta['link'] = None
    return meta

    return meta
####
def save(img_urls, title_dictionary, article):
    def fetch_realimg_url(url):
        response = requests.get(url)
        html = HTML(html=response.text)
        manytrees = html.find('link')                #實際圖片網址藏在 Element = 'link', Attributes : rel ='imag_src'; href = 'https:!@#$%^'
        real_img_url = []                            #必須先在這裡設real_img_url變數為空串列，假如我們用real_img_url = real_img.attrs['href']，for迴圈外面看不到real_img_url這個變數
        for real_img in manytrees:
            if not real_img.attrs['rel'] == ('image_src',): continue       #.attrs['rel']抓出的是tuple 所以要把'image_src'改成('image_src',)
            real_img_url.append(real_img.attrs['href'])
        return real_img_url

    dname = title_dictionary.strip()

    if '"' in dname:
        a = dname.split('''"''')
        dname = a[0] + a[1]
        if '<' or '>' in dname:
            dname = dname.replace('''>''', '')
            dname = dname.replace('''<''', '')

    #os.makedirs(dname)
    try:
        for img_url in img_urls:
            if img_url.split('//')[1].startswith('m.'):
                img_url = img_url.replace('//m.', '//i.')
            if not img_url.split('//')[1].startswith('i.'):
                img_url = img_url.split('//')[0] + '//i.' + img_url.split('//')[1]
            if not img_url.endswith('.jpg'):
                img_url = img_url + '.jpg'
            if img_url.split('/')[-2] == 'a':  # 如果圖片往只是http://imgur.com/a/asfawg的形式必須透過重新爬此網址背後真實圖片網址才能抓下來
                img_url_list = fetch_realimg_url(img_url)
                img_url = img_url＿list[0]
            fname = article + img_url.split('/')[-1]
            urllib.request.urlretrieve(img_url, os.path.join(dname, fname))
    except Exception as e:
        print(e)
    '''
    try:
        dname = title_dictionary.strip()
        os.makedirs(dname)
    except:
        try:
            for img_url in img_urls:
                if img_url.split('//')[1].startswith('m.'):
                    img_url = img_url.replace('//m.', '//i.')
                if not img_url.split('//')[1].startswith('i.'):
                    img_url = img_url.split('//')[0] + '//i.' +img_url.split('//')[1]
                if not img_url.endswith('.jpg'):
                    img_url = img_url + '.jpg'
                if img_url.split('/')[-2] == 'a':                                       #如果圖片往只是http://imgur.com/a/asfawg的形式必須透過重新爬此網址背後真實圖片網址才能抓下來
                    img_url_list = fetch_realimg_url(img_url)
                    img_url = img_url＿list[0]
                fname = img_url.split('/')[-1]
                urllib.request.urlretrieve(img_url, os.path.join(dname, fname))
        except Exception as e:
            print(e)
    '''

        #reallink = urllib.parse.urljoin('https://www.ptt.cc/', link)
        #print(title, push, date, author, reallink)


start_url = 'https://www.ptt.cc/bbs/sex/index.html'
num_pages = int(input('How many pages U need: '))
collected_meta = []
for a in range(num_pages):
    meta_onepage, link = fetch(start_url)
    meta_data = [parse_meta(onepost) for onepost in meta_onepage]
    collected_meta += meta_data
    start_url = link
print(collected_meta)
#print(collected_meta) meta_data是每一篇的題目作者連結等等，每頁收集完成後把dict放入collected_data這個list裡
#print(len(collected_meta))

post_link = [ ]
PTT_URL = 'https://www.ptt.cc'
conn = sqlite3.connect('sexdb.sqlite')
cur = conn.cursor()
try:
    cur.execute('''
    CREATE TABLE Links (link TEXT, title TEXT)''')
# post : 每一篇文章的連結，但少了https://www.ptt.cc
except:
    for post in collected_meta:
        if post['link'] is None: continue
        page = PTT_URL + post['link']
        #爬完一篇文章把連結和標題放入SQLite，不論此篇文章有圖片連結與否
        cur.execute('SELECT title FROM Links WHERE link = ? ', (page,))
        row = cur.fetchone()
        print(row)
        if row is None:
            cur.execute('''INSERT INTO Links (link, title)
                       VALUES (?, ?)''', (page, post['title']))
        else:
            continue
        conn.commit()
        img_urls = fetch_image_links(page)             #由fetch_image_links得到單單一篇文章的所有圖片網址
        if not img_urls : continue
        #有圖片連結的文章才會存入本機硬碟，所以SQLite_table 文章數量會大於產生的資料夾數量，一般而言
        #save(img_urls, post['title'] + str(random.randrange(0,1000)))
        save(img_urls, 'Sex', post['title'])
    #print(post)

#print(post_link)
