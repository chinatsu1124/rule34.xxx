import os
import re
import sys
import time
import urllib
import threading
import bs4
import requests
import urllib3
from bs4 import BeautifulSoup

# 获取Respond
def getResultPage(rule34_url, keywords, page):
    if page == 1:
        search_data = {
            'page': 'post',
            's': 'list',
            'tags': keywords
        }
    else:
        search_data = {
            'page': 'post',
            's': 'list',
            'tags': keywords,
            'pid': str((page-1)*42)
        }
    try:
        r = requests.get(rule34_url, params=search_data, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r
    except:
        print("网络连接未响应")
        sys.exit(1)

# 下载页面到桌面


def downloadhtml(result_page, desktop):
    with open(desktop+"result.html", "w", encoding="utf-8") as f:
        f.write(result_page.content.decode())

# 查找最后一页


def findLastPage(soup):
    last_tag = soup.find(alt="last page")
    if last_tag:
        last_result = re.search('pid=.*', last_tag['href'])
        lastid = last_result.group(0)
        lastid = lastid[4:]
        max_page = int(int(lastid)/42+1)
    else:
        max_page = 1
    print('搜索结果总共%d页' % max_page)
    return max_page

# 将本页42个id存入id_list


def fillid_list(page, id_list, soup, lastid):
    count = 0
    thumb_list = soup.find_all(class_='thumb')
    for thumb in thumb_list:
        id = thumb['id']
        id = id[1:]
        if int(id) > int(lastid):
            id_list.append(id)
            count += 1
            print("第%d页总共%d个id已存入list" % (page, count))
        else:
            break
    if int(id) == int(lastid):
        print("新增id获取完毕")
        return 1
    else:
        return 0


# 创建下载目录
def mkdir(keywords):
    if not os.path.isdir("E:\\rule34\\"+keywords):
        os.mkdir("E:\\rule34\\"+keywords)
        print("目录不存在,将新建目录")
    else:
        print("目录已存在")
    return "E:\\rule34\\"+keywords+"\\"

# 将最新id写入lastid.txt


def writeIntotxt(id_list, path):
    if id_list:
        with open(path+"lastid.txt", "w", encoding="utf=8") as f:
            f.write(id_list[0])
        print("写入最新id完毕")
    else:
        print('当前数据已为最新')

# 检测lastid.txt


def find_lastid(search_dir):
    try:
        f = open(search_dir+"lastid.txt", "r", encoding="utf=8")
        lastid = f.read()
        return lastid
    except:
        print("lastid.text文件不存在,将下载全部图片")
        return 0


# 下载当前页面的JPG或WEBM
def downloadimage_all(id, search_dir, rule34_url):
    image_data = {
        'page': 'post',
        's': 'view',
        'id': id
    }
    for i in range(10):
        try:
            r = requests.get(rule34_url, params=image_data, timeout=60)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, 'html.parser')
            image = soup.find(property="og:image")
            image_url = image['content']
            size = 0
            response = requests.get(image_url, stream=True)
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code == 200:
                if re.search('webm', image_url):
                    Type = '.webm'
                elif re.search('gif', image_url):
                    Type = '.gif'
                else:
                    Type = '.jpg'
                #print('[id]:%s%s\n[文件大小]:%0.2f MB' %(id, Type, content_size/chunk_size/1024))
                with open(search_dir+id+Type, "wb") as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        #print('\r'+'[下载进度]:%s%.2f%%' % ('>'*int(size*50 / content_size), float(size/content_size*100)), end='')
                print('[id]:%s%s [文件大小]:%0.2f MB 下载完成!' %(id, Type, content_size/chunk_size/1024))
                break
            else:
                if i == 9:
                    print('[id]:%s下载失败' %id)
                    with open(search_dir+'download_error.txt', "a") as f:
                        f.write(id+'\n')
                else:
                    print('[id]:%s下载失败，重试中(%d/10)......' %(id,i+1))
        except:
            if i == 9:
                print('[id]:%s下载失败' %id)
                with open(search_dir+'download_error.txt', "a") as f:
                    f.write(id+'\n')
            else:
                print('[id]:%s下载失败，重试中(%d/10)......' %(id,i+1))

# threading多线程下载


class dThread (threading.Thread):
    def __init__(self, threadID, name, id_list, search_dir, rule34_url):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.id_list = id_list
        self.search_dir = search_dir
        self.rule34_url = rule34_url

    def run(self):
        for i in self.id_list:
            downloadimage_all(i, self.search_dir, self.rule34_url)
            #download_count += 1

# 主函数


def main():
    #download_count = 0
    id_list = []
    rule34_url = 'https://rule34.xxx/index.php'
    keywords = input("请输入查询关键字:")
    page = int(input("请输入起始页:"))
    search_dir = mkdir(keywords)
    result_page = getResultPage(rule34_url, keywords, page)
    soup = BeautifulSoup(result_page.text, 'html.parser')
    lastpage = findLastPage(soup)
    lastid = find_lastid(search_dir)
    #测试用
    #lastpage = 1
    value = fillid_list(page, id_list, soup, lastid)
    page += 1
    while page <= lastpage and value == 0:
        result_page = getResultPage(rule34_url, keywords, page)
        soup = BeautifulSoup(result_page.text, 'html.parser')
        value = fillid_list(page, id_list, soup, lastid)
        page += 1
    print("总共为%d页,id_list已fill完毕" % (int(page-1)))
    multi_thread = int(input('请输入下载线程数:'))
    start = time.time()
    cut = int(len(id_list)/multi_thread)
    threads = []
    i = 1
    while i <= multi_thread:
        if i == 1:
            thread = dThread(i, 'thread-'+str(i), id_list[:cut], search_dir, rule34_url)
        elif i == multi_thread:
            thread = dThread(i, 'thread-'+str(i), id_list[cut*(multi_thread-1):], search_dir, rule34_url)
        else:
            thread = dThread(i, 'thread-'+str(i), id_list[cut*(i-1):cut*i], search_dir, rule34_url)
        thread.start()
        threads.append(thread)
        i += 1
    for t in threads:
        t.join()
    #print("本次下载%d张图片" % download_count)
    stop = time.time()
    spend_time = stop - start
    print('总共%d张图片' %len(id_list))
    print('总耗时%.2f秒' %spend_time) 
    writeIntotxt(id_list, search_dir)


main()
