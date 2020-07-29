#!/usr/bin/python
#  Python Threaded Crawler for Maltego Teeth
#  ------------------------------------------
#  Crawls Websites and returns forms/urls/visited pages/entities
#  use with -h to see options
#  
#  - Andrew MacPherson ( @AndrewMohawk )


# -*- coding: utf-8 -*-

import sys
import time
import urllib
from urllib import urlopen,quote
from bs4 import BeautifulSoup
from Queue import Queue, Empty
import threading
from threading import Thread
import urllib2
import mechanize
from mechanize import Browser
import argparse
import re
from urlparse import urljoin,parse_qs,urlparse


visited = set()
foundforms = []
foundURLs = []
foundEntities = set()

queue = Queue()
totalDepth = 0;
maxDepth = 0;
maxTime = 5;


appStartTime = 0;
appEndTime = 0;
globalThreadTime = 30;

userAgent = 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0';

class FormObject():
	
	def __init__(self,action,method):
		self.action = action
		self.method = method
		self.fromurl = ""
		self.fields = {}
		
		self.actionFields = {}
		
		#lets parse that action field
		u = urlparse(action)
		parsed = parse_qs(u.query)
		baseURL = u.scheme + "://" +  u.netloc + u.path
		
		self.action = baseURL
		
		for f in parsed:
			self.addActionField(str(f),str(parsed[f][0]))
		
		#sys.stdout.write("fields: %s\n" % parsed)
		#sys.stdout.write("baseurl: %s\n" % baseURL);
	
	def addActionField(self,fieldName,fieldValue):
		self.actionFields[fieldName] = quote(fieldValue)
		
	def addField(self,fieldName,fieldValue):
		self.fields[fieldName] = quote(fieldValue)
		
class URLObject():
	def __init__(self,full_url,base_url):
		self.base_url = base_url
		self.fullURL = full_url
		self.fromurl = ""
		self.fields = {}
	
	def addField(self,fieldName,fieldValue):
		self.fields[fieldName] = quote(fieldValue)

class AndrewsThreadedBrowser(threading.Thread):
	global queue,appEndTime,letsBail,appStartTime,maxDepth,visited,foundforms,foundURLs,foundEntities,userAgent;
	def __init__(self,num,keyword):
		self.num = num
		self.keyword = keyword;
		self.br = Browser(factory=mechanize.RobustFactory( ))
		self.br.set_handle_robots(False)
		self.br.addheaders = [('User-Agent', userAgent),('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
		self.cj = mechanize.LWPCookieJar()
		self.br.set_cookiejar(self.cj)
		self.br._factory.is_html = True
		self.br.set_handle_refresh(False)
		self.idletime = 0
		threading.Thread.__init__(self)
		self.url = ""
		self.depth = 0
		self.output = ""
#		print "Started Thread " + str(self.num)

	def setCookies(self,file):
		self.cookiesFile = file
		self.cj = mechanize.LWPCookieJar()
		if (os.path.exists(file)):
			self.cj.revert(file,ignore_discard=True, ignore_expires=True)
		self.br.set_cookiejar(self.cj)
	
	def saveCookies(self):
		self.cj.save(self.cookiesFile, ignore_discard=True, ignore_expires=True)
		
	def get_base(self,URL):
		if(URL.rfind("/") > 6):
			return URL[:URL.rfind('/')]
		else:
			return URL
	
	def addLink(self,link):
		hashPos = link.rfind("#",link.rfind("/"))
		if(hashPos != -1):
			link = link[:hashPos]
		
		try:
			
			if(link[-1:] == "/"):
				#print "Stripped %s to %s" % (link,link[:-1])
				link = link[:-1]
		except:
			pass
			
		visited.add(self.url)
		#print "Does %s match %s = %s" % (link,self.keyword,link.find(self.keyword))
		if(((self.keyword != "") and (link.find(self.keyword) != -1)) or self.keyword == ""):
			#print "url: %s %s" % (link,urlparse(link).query)
			u = urlparse(link)
			parsed = parse_qs(u.query)
			baseURL = u.scheme + "://" +  u.netloc + u.path
			
			if(len(parsed) > 0):
				#print("The url is %s" % link)
				#print("Has the following fields and values: %s" % parsed)
				myURL = URLObject(link,baseURL)
				for query in parsed:
					#print "got field %s and value %s" % (str(query),str(parsed[query][0]))
					myURL.addField(str(query),str(parsed[query][0]))
				foundURLs.append(myURL)
			if link not in visited:
				if((self.depth+1) <= maxDepth):
					queue.put(link + "||||" +  str(self.depth + 1))

	def get_entities(self,passed):
		re_list=[]
		re_list.append({'output':'E','regex': re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')})
		re_list.append({'output':'P','regex': re.compile(r'(\d{3}) \W* (\d{3}) \W* (\d{4}) \W* (\d*)')}) #<--nogood.
		
		lines=passed.split('\n')
		for line in lines:
			for regSearch in re_list:
				results = regSearch['regex'].findall(line)
				for r in results:
					entityFound = "<%s> %s" % (regSearch['output'],r)
					foundEntities.add(entityFound)
					

	
	def get_redirects(self,passed,res):
		re_list=[]
		re_list.append(".*window.location\s*=\s*[\'\"]\s*(?P<loc>.*)\s*[\'\"].*")
		re_list.append(".*location.replace\s*\(\s*[\'\"]\s*(?P<loc>.*)\s*[\'\"]\s*\).*")
		re_list.append(".*location.href\s*=\s*[\'\"]\s*(?P<loc>.*)\s*[\'\"].*")
		re_list.append(".*location\s*=\s*[\'\"]\s*(?P<loc>.*)\s*[\'\"].*")
		goto=""
		lines=passed.split('\n')
		for line in lines:
			for re_item in re_list:
				myre=re.compile(re_item,re.DOTALL)
				if (myre.match(line.lower())):
					M=myre.match(line)
					goto = M.group('loc')
					if (goto.find('http')<0):
						if (goto.startswith('/') == False): 
							goto=self.get_base(res.geturl())+"/"+goto
						else:
							goto=self.get_base(res.geturl())+goto
						break
					break
		
		goto=goto.replace("\\","")
		return goto
	
	def storeOutput(self,outStr):
		self.output = self.output + outStr + "\n"
	
	def getFormInfo(self):
		#self.storeOutput("[+] FORMS")
		try:
			for form in self.br.forms():
				
				action = str(form.action)
				method = str(form.method)
				
				if (action.rfind("#") != -1):
					action = action[:action.rfind("#")]
				
				myForm = FormObject(action,method)

					
				myfields = {}
				for field in form.controls:
					if((field is not None) and (field.name is not None)):
						#print "type: '%s' value='%s' f:%s " % (field.type,field.value,action)
						fieldValue = str(field.value)

						if(field.type == "select" or field.type == "radio"):
								#field.value = str(field.items[len(field.items)-1])
								if(len(field.items) > 0):
									fieldValue = str(field.items[len(field.items)-1])
								else:
									fieldValue = ""
								#print "select options: %s" % field.items[len(field.items)-1]
						myForm.addField(field.name,fieldValue)
				
				foundforms.append(myForm)
		except:
			#Could not parse form :<
			pass
	
	def run(self):
		try:
			
				
			while True:
				if((time.time() > appEndTime)):
#					sys.stdout.write( "Thread %s ending, time is up!\n" % self.num)
					return;
				self.output = ""

				self.urlstr = queue.get_nowait()
				
				depthPos = self.urlstr.find("||||")
				
				if(depthPos != -1):
					self.depth = int(self.urlstr[depthPos+4:])
					self.url = self.urlstr[:depthPos]
					
					self.result = None
				else:
					sys.stdout.write( "DEPTHHIT!")
					return False
				
				#sys.stdout.write("[+] BROWSING: \n\t[+] " + self.url + " Thread-" + str(self.num) + "\n\r")
				res = self.br.open(self.url,timeout=3.0)
				#res = mechanize.urlopen(self.url,timeout=3)
				response=res.read()

				self.getFormInfo();
				self.get_entities(response);
				
				JscriptRedirect=self.get_redirects(response,res)
				if(JscriptRedirect not in visited):
					if((self.depth+1) <= maxDepth):
						#self.storeOutput( "\t[+] Adding jscript link %s" % (JscriptRedirect))
						self.addLink(JscriptRedirect);
						#queue.put(JscriptRedirect + "||||" +  str(self.depth + 1))
					
				
				if(self.br.viewing_html() == True):
					#self.storeOutput( '[+] LINKS')
					for link in self.br.links():
						#link.url =  #lazy
						self.addLink(link.absolute_url);
				else:
					##invalid HTML. prob jpg or tgz or whatever - aint nobody got time for that
					self.storeOutput( "[%] Page is NOT html (could be jpg, etc)")
					
				#print self.output
		except Empty:
			# no items
			idleSleep = 0.3
			time.sleep(idleSleep)
			self.idletime = self.idletime + idleSleep
			if(self.idletime > globalThreadTime):
#				print "Thread %s ending, Idled for too long!" % self.num # damn the man, save the empire.
#				print self.output
				return;
			else:
				self.run();
			pass
		except urllib2.URLError,e:
			#if(e.reason == "timed out"):
			#	self.stdout.write("Timed out on %s" % str(self.url))
			#self.storeOutput( "[1] invalid URL:" + str(self.url))
			#self.run();
			pass
		except mechanize._mechanize.BrowserStateError:
			#self.storeOutput( "[2] invalid browser URL:" + str(self.url))
			pass
		except:
			#:(
			pass


def uniqueForms(forms):
	output = []
	
	for x in forms:
		add = True
		
		for y in output:
			xForms = set(x.fields.keys())
			yForms = set(y.fields.keys())
			
			xActionFields = set(x.actionFields.keys())
			yActionFields = set(y.actionFields.keys())
			if((x.method == y.method) and (x.action == y.action)):
				if(len(xActionFields & yActionFields) == len(yActionFields)):
					if(len(xForms & yForms) == len(yForms)):
						add = False
				
		if(add == True):
			output.append(x)
	return output
	
	
def uniqueURLS(urls):
	output = []
	
	for x in urls:
		add = True
		
		for y in output:
			if(x.base_url == y.base_url):
				xForms = set(x.fields.keys())
				yForms = set(y.fields.keys())
				if(len(xForms & yForms) == len(yForms)):
					add = False
		if(add == True):
			output.append(x)
	return output
	
if __name__ == '__main__':
	sTime = time.time()
	
	
	
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-d","--depth", type=int, default=0, help="Page depth to recurse")
	parser.add_argument("-f","--filter", help="Keyword filter on for links")
	parser.add_argument("-w","--website", required=True,help="Website to spider");
	parser.add_argument("-t","--timeout", help="Timeout for spider");
	parser.add_argument("-n","--numthreads", type=int, help="Number of threads to use for spider");
	parser.add_argument("-du", action='store_true', default=False, help="Dont Unique the forms/urls");
	parser.add_argument("-sf", action='store_true', default=False, help="Show form details");
	parser.add_argument("-su", action='store_true', help="Show urls parsed");
	parser.add_argument("-sv", action='store_true', help="Show urls visited");
	parser.add_argument("-se", action='store_true', help="Show Entities extracted");
	parser.add_argument("-sa", action='store_true', help="Show urls parsed,visited,forms and entities");
	
	
	
	args = parser.parse_args()
	
	queue.put('%s||||%s' % (args.website,0))
	
	
	if(args.sa):
		args.su = True
		args.sv = True
		args.se = True
		args.sf = True
	
	maxDepth = 999
	if(args.depth):
		maxDepth = int(args.depth)
	
	filter = ""
	if(args.filter):
		filter = args.filter
	
	maxTime = 5
	if(args.timeout):
		maxTime = int(args.timeout)
#		print "maxTime is %s" % maxTime
	
	numThreads = 10
	if(args.numthreads):
		numThreads = args.numthreads
	
	
	appEndTime = time.time() + (maxTime)
	appStartTime = time.time()
	
	# Site Workers
	workers = []
	
	
	for i in range(numThreads):
		worker = AndrewsThreadedBrowser(i,filter)
		worker.start()
		workers.append(worker)
		
	
	for worker in workers:
		worker.join()
	
	
	
	
	eTime = time.time()
	tTime = eTime - sTime
#	print >> sys.stderr, "Executed in %0.2fs" % (tTime)
	
	
	if (args.sf):
		if(args.du == False):
			foundforms = uniqueForms(foundforms)
#		print "\n[+] FORMS:\n[+]--------------------------------------------------------[+]\n"
		for f in foundforms:
			sys.stdout.write('<F>')
			sys.stdout.write('%s ' % f.method)
			sys.stdout.write('%s' % f.action)
			fieldOutput = ""
			for field in f.actionFields:
				fieldOutput = fieldOutput + "%s=%s&" % (field,str(f.actionFields[field]))
			if(fieldOutput != ""):
				sys.stdout.write('?%s' % fieldOutput[:-1])
			else:
				sys.stdout.write(' ')
			fieldOutput = ""
			for field in f.fields:
				fieldOutput = fieldOutput + "%s=%s&" % (field,str(f.fields[field]))
			sys.stdout.write('[ %s ]' % fieldOutput[:-1])
			sys.stdout.write('\n')
	
	if (args.su):
#		print "\n[+] Get URLS:\n[+]--------------------------------------------------------[+]\n"
		#storedurls kthnx
		if(args.du == False):
			foundURLs = uniqueURLS(foundURLs)
		
		for f in foundURLs:
			sys.stdout.write('<F>')
			sys.stdout.write('%s ' % "GET")
			sys.stdout.write('%s?' % f.base_url)
			fieldOutput = ""
			for field in f.fields:
				fieldOutput = fieldOutput + "%s=%s&" % (field,str(f.fields[field]))
			sys.stdout.write('%s' % fieldOutput[:-1])
			sys.stdout.write('\n')
	
	if (args.sv):
#		print "\n[+] Visited URLs:\n[+]--------------------------------------------------------[+]\n"
		for u in visited:
			print "<U> %s " % u
	
	if (args.se):
#		print "\n[+] Entities:\n[+]--------------------------------------------------------[+]\n"
		for u in foundEntities:
			print "%s " % u
	