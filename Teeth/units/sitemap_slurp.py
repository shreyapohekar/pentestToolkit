#!/usr/bin/python
from TeethLib import *
from BeautifulSoup import BeautifulSoup
import sys

try:
 target=sys.argv[1]
except:
 print "No. First and only paramter is the website name - eg. www.paterva.com\n"
 quit()
 
sitemapxml=get_url_with_BS("http://"+target+"/sitemap.xml",15)
bs=BeautifulSoup(sitemapxml)
sets=[]
try:
 sets = bs.urlset.findAll('url')
except:
 pass
 #print "SITEMAP EMPTY"

if len(sets)>0:
 print "SITEMAP\n----------------\n"

for set in sets:
 line=str(set.loc)
 line=line.replace("<loc>","").replace("</loc>","").strip() 
 print "<U> "+line


