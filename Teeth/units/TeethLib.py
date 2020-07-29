import threading, urllib2 
from urlparse import *
import time
import mechanize
import cookielib
from Levenshtein import *
import random
import string
import ConfigParser
import logging
import os
import subprocess
import datetime
import base64

_LOGFILE='/var/log/Teeth.log'
_CONFIGFILE='/opt/Teeth/etc/TeethConfig.txt'


logger = logging.getLogger('Teeth')
hdlr = logging.FileHandler(_LOGFILE)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
### set level here (INFO or DEBUG):
logger.setLevel(logging.DEBUG)

def b64e(i):
 return base64.b64encode(i)

def datestamp():
 return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
 
def cutter(s,token_b,token_e):
 startcut=s.find(token_b)+len(token_b)
 endcut=s.find(token_e,startcut)
 return s[startcut:endcut]

def sillydecode(inp):
 if inp is not None:
  inp=inp.replace('^','=')
  return inp
 else:
  return None 

def sillyencode(inp):
 if inp is not None:
  inp=inp.replace('=','^')
  return inp
 else:
  return None 
    



def read_config_file(section,option):
 try:
  Config = ConfigParser.ConfigParser()
  Config.read(_CONFIGFILE)
  return Config.get(section, option)
 except:
  logger.warn("Could not find the section [%s] [%s] in config file [%s]"%(section,option,_CONFIGFILE))

#tired of not getting this right - WTF
def read_from_config(section,option):
 return read_config_file(section,option)


def slurp_file(section,item):
 ret=[]
 try:
  ret=[line.strip() for line in open(read_config_file(section,item))]
  return ret
 except: 
  return ret 

def slurp_file_plain(filename):
 ret=""
 try:
  with open(filename, 'r') as content_file:
   ret = content_file.read()
  return ret
 except: 
  return ret 

def id_generator(size=12, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for x in range(size))



def snippet(s):
  if (len(s)<=2000):
    return s

  snippet=s[0:500]

  start=(len(s)/4)-250;
  end=  (len(s)/4)+250;
  snippet=snippet+s[start:end]
  
  start=(3*len(s)/4)-250;
  end=  (3*len(s)/4)+250;
  snippet=snippet+s[start:end]
  
  snippet=snippet+s[len(s)-500:len(s)]
  return snippet


def get_url_with_BS(where,timeout_T):
 # Browser
 br = mechanize.Browser()
 cj = cookielib.LWPCookieJar()
 br.set_cookiejar(cj)
 br.set_handle_equiv(True)
 br.set_handle_redirect(True)
 br.set_handle_referer(True)
 br.set_handle_robots(False)
        
 # Follows refresh 0 but not hangs on refresh > 0
 br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
          
 br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
 try:
  r = br.open(where,timeout=timeout_T)
  return r.read()
 except urllib2.HTTPError, e:
  return str(e.code)
 except:
  return ""           




def compare_strings(A,B):
  c_ratio = ratio(A,B)
  return c_ratio




def get_dirs_from_mirror(output,index,track):
 dict_url={}
 lines=output.split('\n')
 for line in lines:
  if line.find('<U>')==0:
    url=line.replace('<U> ','')
    parsed=urlparse(url)
    path=parsed.path
    if len(path)>0:
      parts=path.split('/')
      if len(parts)>index:
        if (parts[index].find('.')<0) and (parts[index-1]==track or (track=='' and index==1)):
          dict_url[parts[index].strip()]='1'

 result=[]
 for a in dict_url.keys():
  result.append(a)
 
 return result   



def get_forms_from_mirror(output):

 result=[]
 lines=output.split('\n')
 for line in lines:
  if line.find('<F>')==0:
    dict_form={}
    line=line.replace('<F>','')

    if line.find('POST')==0 and len(line.split(' '))==5:
     (act,url,duh,data,duh)=line.split(' ')
     dict_form['action']=act
     dict_form['url']=url
     dict_form['data']=data
     result.append(dict_form)

    if line.find('GET')==0:
     if (len(line.split(' '))==2):
      (act,url)=line.split(' ')
      dict_form['action']=act
      dict_form['url']=url
      dict_form['data']='' 
      result.append(dict_form)
      
      
     if (line.find('GET')==0 and len(line.split(' '))==5):
      (act,url,duh,data,duh)=line.split(' ')
      dict_form['action']=act
      dict_form['url']=url
      dict_form['data']=data 
      result.append(dict_form)
 
 return result   

def run_external(cmd):
 output=""
 try:
  output=subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT,)
 except:
  output=""
 return output  


def get_MirrorData(target,TTM):
 
 storeplace=read_config_file('MirrorGeneral','cachedir')
 storefile=storeplace+target
 cmd='./threadedcrawlerPiP.py -t '+TTM+' -sa -f '+target+' -w http://'+target+ ' >> '+storefile
 output=""

 if os.path.isfile(storefile):
  logger.debug("Found [%s] - reading from cache..."%storefile)
  output = run_external('cat '+storefile)
 else:
  logger.debug("Running [%s], no cache found"%cmd)
  run_external(cmd)
  time.sleep(1)
  if os.path.getsize(storefile)>1:
   output = run_external('cat '+storefile)
  else:
   logger.debug("Ran the mirror on [%s], but no data. Sad face."%target)
   return ''
 return output
    

def get_SitemapData(target,TTM):
 
 storeplace=read_config_file('MirrorGeneral','cachedir')
 storefile=storeplace+'sitemap-'+target
 cmd='./sitemap_slurp.py ' + target + ' > '+storefile
 output=""

 if os.path.isfile(storefile):
  logger.debug("Found [%s] - reading from cache..."%storefile)
  output = run_external('cat '+storefile)
 else:
  logger.debug("Running [%s], no cache found"%cmd)
  run_external(cmd)
  time.sleep(1)
  if os.path.getsize(storefile)>1:
   output = run_external('cat '+storefile)
  else:
   logger.debug("Ran the sitemap on [%s], but no data. Sad face."%target)
   return ''
 return output
    
