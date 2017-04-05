# -*- conding:utf-8 -*-
import urllib.request
from bs4 import BeautifulSoup as soup
import threading
import re
import sqlite3
import queue
import time
import http.cookiejar
import matplotlib.pyplot as plt
import numpy


def urlread(i,htmlqueue,countqueue):
	'''contact URL and download html data'''

	def makemyopener():
		head={'Connection':'Keep-Alive','Accept':'text/html, application/xhtml+xml, */*','Accept-Language':'en-US, en; q=0.8, zh-Hans-CN; q=0.5,zh-Hans; q=0.3','User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko'}
		cj=http.cookiejar.CookieJar()
		opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
		header=[]
		for key,value in head.items():
			elem=(key,value)
			header.append(elem)
		opener.addheaders=header
		return opener

	oper=makemyopener()
	for x in range(i):
		print("urlread")
		url=r'http://search.51job.com/jobsearch/search_result.php?fromJs=1&jobarea=000000%2C00&district=000000&funtype=0000&industrytype=00&issuedate=9&providesalary=99&keyword=*&keywordtype=2&curr_page=' + str(x) + r'&lang=c&stype=1&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&lonlat=0%2C0&radius=-1&ord_field=0&list_type=0&dibiaoid=0&confirmdate=9'
		try:
			html=oper.open(url).read()
			#print(html.decode('GBK',"ignore"))
			htmlqueue.put(html.decode('GBK',"ignore"))
		except:
			pass
		countqueue.get()



def sodata(htmlqueue,dataqueue,countqueue):

	'''transfer the html data to queue list by beautifulsoup'''
	while True:
		print("sodata")
		'''handle html data and get data list'''
		htmldata=htmlqueue.get()
		so=soup(htmldata,"lxml")
		taglist=so.find_all("div",class_="el")
		datalist=[]
		for tag in taglist:
			list1=tag.find_all("span")
			t_list=[]
			try:
				t_list.append(list1[0].a["title"])
				t_list.append(list1[1].string)
				if len((list1[2].string).split("-"))==2:
					t_list.append((list1[2].string).split("-")[0])
					t_list.append((list1[2].string).split("-")[1])
				elif len((list1[2].string).split("-"))==1:
					t_list.append(list1[2].string)
					t_list.append("None")
				else:
					t_list.append("None")
					t_list.append("None")
				try:
					sally=((list1[3].string).split("/")[0]).split("-")
					if len(sally)==2:
						t_list.append((re.search("\d+",((list1[3].string).split("/")[0]).split("-")[0])).group(0))
						t_list.append((re.search("\d+",((list1[3].string).split("/")[0]).split("-")[1])).group(0))
					else:
						t_list.append((re.search("\d+",list1[3].string)).group(0))
						t_list.append("None")
				except:
						t_list.append(list1[3].string)
						t_list.append("None")
				t_list.append(list1[4].string)
			except:
				pass
			if t_list:
				datalist.append(t_list)
			#print(datalist)
		dataqueue.put(datalist)
		if countqueue.empty():
			break


def savedata(cur,dataqueue,countqueue):
	while True:
		print("savedata")
		print('123456789')
		rawlist=dataqueue.get()
		print(type(cur))
		ls='''insert into frist (job,company,location1,location2,sallarydown,sallaryup,date) VALUES(?,?,?,?,?,?,?)'''
		for d in rawlist:
			try:
				cur.execute(ls,(d[0],d[1],d[2],d[3],d[4],d[5],d[6]))
			except:
				print(d)
		if countqueue.empty() and dataqueue.empty():
			break


def searchdata(cur):
	count=[]
	positioncount=[]
	locationlist=[]
	averagesallerydown=[]
	averagesalleryup=[]
	count1=cur.execute('''select location1,count(job),avg(sallarydown),avg(sallaryup) from frist group by location1''')
	for i in count1.fetchall():
		count.append(list(i))
	print(count)
	for j in count:
		locationlist.append(j[0])
		positioncount.append(j[1])
		averagesallerydown.append(j[2])
		averagesalleryup.append(j[3])
	plt.rcParams['font.sans-serif']=['Noto Sans CJK SC Regular']
	plt.xlabel(u'Citys')
	plt.ylabel(u'Job Counts')
	plt.xticks(tuple(range(len(positioncount))),tuple(locationlist))
	plt.bar(left=tuple(range(len(locationlist))),height=tuple(positioncount),width=0.8)
	#plt.plot(averagesallerydown)
	#plt.plot(averagesalleryup)
	#plt.plot(positioncount)
	plt.show()



def main():

	ti=time.time()

	conn=sqlite3.connect('/home/yutian/mypy/htmldata.db',timeout=20)
	cur=conn.cursor()
	try:
		cur.execute('''drop table frist''')
	except:
		pass
	cur.execute('''create table frist
			(job varchar(200),
			company varchar(200),
			location1 varchar(200),
			location2 varchar(200),
			sallarydown varchar(50),
			sallaryup varchar(50),
			date varchar(20))''')

	htmlqueue=queue.Queue()
	dataqueue=queue.Queue()
	countqueue=queue.Queue()
	i=5
	for j in range(i):
		countqueue.put(j)

	htmlthread=threading.Thread(target=urlread,args=(i,htmlqueue,countqueue,))
	soupthread=threading.Thread(target=sodata,args=(htmlqueue,dataqueue,countqueue,))

	htmlthread.start()
	soupthread.start()
	savedata(cur,dataqueue,countqueue)
	print("444444444444")
	soupthread.join()
	print("555555555")
	searchdata(cur)
	cur.close()
	conn.commit()
	conn.close()

	print(time.time()-ti)

if __name__ == '__main__':
	main()