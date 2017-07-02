# -*- coding: utf-8 -*-
import requests
import json
from HTMLParser import HTMLParser
#从网页中提取页码信息
class PageNumberParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.page=0
		self.href=''
	def handle_starttag(self, tag, attrs):
		def _attr(attrlist, attrname):
			for attr in attrlist:
				if attr[0] == attrname:
					return attr[1]
			return None
		if tag=="a" and _attr(attrs,'title')=="尾页":
			self.href=_attr(attrs,"href")
			str=self.href.split('/')[-1]
			try:
				self.page=int(str[2:-5])
			except ValueError:
				self.page=1
#从一系列网页中提取期刊信息
class MagazineParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.magazines=[]
		self.key=''
		self.number=0
		self.data=''
		self.in_li=False
		self.in_inner_li=False
		self.in_div=False
		self.in_ul=False
		self.in_span=False
		self.in_description=False
		self.in_include=False
		self.magazine={}
	def handle_starttag(self, tag, attrs):
		def _attr(attrlist, attrname):
			for attr in attrlist:
				if attr[0] == attrname:
					return attr[1]
			return None
		if tag == "li" and _attr(attrs,'class')=="box-item":
			self.in_li=True
		if self.in_li and tag=="img":
			self.magazine['图片：']=_attr(attrs,'src')
		if self.in_li and tag=="div" and _attr(attrs,'class')=="item-title":
			self.in_div=True
		if self.in_div and tag=="a":
			self.magazine['标题：']=_attr(attrs,'title')
		if self.in_li and tag=="ul":
			self.in_ul=True
		if self.in_ul and tag=="li" and _attr(attrs,'class')=="nofloat info":
			self.in_description=True
		if self.in_ul and tag=="li" and _attr(attrs,'class')=="nofloat":
			self.include=True
		if self.in_ul and tag=="span":
			self.in_span=True
		if self.in_ul and tag=="li" and not self.in_description and not self.in_include:
			self.in_inner_li=True
	def handle_data(self,data):
		if self.in_ul and self.in_span:
			self.key=data.strip()
		if self.in_inner_li and not self.in_span:
			self.data+=" "+data
			self.magazine[self.key]=self.data
		if self.in_description:
			self.magazine['简介：']=data
		if self.in_include:
			self.magazine['期刊收录：']=data
	def handle_endtag(self, tag):
		if tag == 'li' and self.in_li and not self.in_ul:
			self.in_li=False
			self.magazines.append(self.magazine)
			self.magazine={}
		if tag=="div":
			self.in_div=False
		if tag=="ul" and self.in_li:
			self.in_ul=False
			self.number=0
		if tag=="span":
			self.in_span=False
		if tag=="li" and self.in_description:
			self.in_description=False
		if tag=="li" and self.in_include:
			self.in_include=False
		if tag=='li' and self.in_ul and not self.in_description and not self.in_include:
			self.in_inner_li=False
			self.data=''
#从网页中提取url信息
class UrlParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.categories=[]
		self.category={}
		self.in_div=False
		self.in_inner_div=False
		self.in_r_div=False
		self.in_a=False
		self.title=''
		self.url=''
	def handle_starttag(self, tag, attrs):
		def _attr(attrlist, attrname):
			for attr in attrlist:
				if attr[0] == attrname:
					return attr[1]
			return None

		if tag=="div" and _attr(attrs,"class")=="box-item" and _attr(attrs,'res')=="tid":
			self.in_div=True
		if tag=="div" and _attr(attrs,'class')=='r' and self.in_div:
			self.in_r_div=True
		if tag=="div" and self.in_div and not self.in_r_div:
			self.in_inner_div=True
		if tag=="a" and self.in_r_div:
			self.in_a=True
			self.url=_attr(attrs,"href")
	def handle_data(self,data):
		if self.in_a:
			self.category[data]=self.url
	def handle_endtag(self,tag):
		if tag=="div":
			if self.in_r_div:
				self.in_r_div=False
			if self.in_inner_div:
				self.in_inner_div=False
			else:
				self.in_div=False
				self.categories.append(self.category)
				self.category={}
		if tag=="a":
			self.in_a=False
#把前一列表中的内容复制到后一列表，后一列表不允许重复
def _add(categories1,categories2):
	for category in categories1:
		if category not in categories2:
			categories2.append(category)
def get_categories(headers):
	categories=[]
	parser=UrlParser()
	url1='http://www.xueshu.com/qikan/zirankexue/'
	url2='http://www.xueshu.com/qikan/renwenkexue/'
	s = requests.get(url1, headers=headers)
	parser.feed(s.content)
	_add(parser.categories,categories)
	s = requests.get(url2, headers=headers)
	parser.feed(s.content)
	_add(parser.categories,categories)
	copy=categories[:]
	for category in copy:
		for value in category.values():
			s=requests.get(value, headers=headers)
			parser.feed(s.content)
			_add(parser.categories,categories)
	return categories
def get_magazines(categories,headers):
	number_parser=PageNumberParser()
	magazine_parser=MagazineParser()
	for category in categories:
		magazines=[]
		for key,value in category.items():
			filename=key.decode('utf-8')+".json"
			s=requests.get(value, headers=headers)
			number_parser.feed(s.content)
			page_number=number_parser.page
			for i in range(page_number):
				if i==0:
					s1=requests.get(value, headers=headers)
				else:
					s1 = requests.get(value+"p0"+str(i+1)+".html", headers=headers)
				magazine_parser.feed(s1.content)
				for magazine in magazine_parser.magazines:
					magazines.append(magazine)
			with open(filename,'w') as f_obj:
				json.dump(magazines,f_obj,ensure_ascii=False)

if __name__=="__main__":
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
							 ' Chrome/47.0.2526.73 Safari/537.36'}
	#获取分类
	categories=get_categories(headers)
	#保存期刊信息到json文件中
	get_magazines(categories,headers)