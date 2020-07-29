from TeethLib import *
from MaltegoTransform import *

m = MaltegoTransform()
m.parseArguments(sys.argv);
hash=sys.argv[1]


#get fields
url=sillydecode(m.getVar('url'))
postdata=sillydecode(m.getVar('postdata'))
varstocheck=sillydecode(m.getVar('varstocheck'))
method=sillydecode(m.getVar('method'))

if method=='POST' and postdata is None:
 logger.info("Can't run a POST without any POSTDATA - exiting. [%s][%s][%s]"%(url,postdata,varstocheck))
 m.returnOutput()
 quit()

if varstocheck is None:
 logger.info("No variables to check - exiting. [%s][%s][%s]"%(url,postdata,varstocheck))
 m.returnOutput()
 quit()
 
if url is None:
 logger.info("No URL or URL malformed - exiting. [%s][%s][%s]"%(url,postdata,varstocheck))
 quit()
 
 
if url.find("?")<0 and method=='GET' and len(postdata)>0:
 #hmmm
 url=url+"?"+postdata
 logger.debug("Exception. Now url is %s"%url)
  
 
#for now 
db="MYSQL" 
additional=read_config_file('SQLMAP','AdditionalArguments')

if postdata is None:
 postdata=""
 
#OK ready go
if method=='POST' or len(postdata)>0:
 cmd="sqlmap %s --dbms %s -u \"%s\" --data \"%s\" -p \"%s\""%(additional,db,url,postdata,varstocheck)
else:
 cmd="sqlmap %s --dbms %s -u \"%s\" -p \"%s\""%(additional,db,url,varstocheck)

logger.debug("Running SQLMAP like so: [%s]"%cmd)
logger.info("Running SQLMAP on [%s][%s][%s]"%(url,postdata,varstocheck))
out=run_external(cmd)

logger.debug("SQLMAP output:>>>%s<<<<"%out)
logger.info("Finished testing on [%s][%s][%s]"%(url,postdata,varstocheck)) 

if out.find("identified the following injection points")>0:
 wootEnt=m.addEntity("maltego.Phrase","INJECTED!"+hash[0:7])
 wootEnt.setDisplayInformation('Click <a href="file:///opt/Teeth/cache/SQLMAP-output/'+urlparse(url).netloc+'/log">here</a> to open report')
m.returnOutput()

