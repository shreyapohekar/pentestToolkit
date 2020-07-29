from TeethLib import *
from MaltegoTransform import *
import socket


########## 
def checkCMS(raw,target,findwords,value,entry,property,TRXi):
 logger.debug("Looking on [%s] for the words [%s]"%(target,findwords))
 try:
  html = urllib2.urlopen(target,timeout=3).read()
#  logger.debug("Found [%s]"%html)
  if (html.find(findwords)>0):
   logger.info("Found [%s] on [%s]"%(findwords,target))
   TitEnt=TRXi.addEntity("paterva.PossibleEntryPoint","")
   TitEnt.setValue(value)
   TitEnt.addAdditionalFields("entry","Entry","strict",entry)
   TitEnt.addAdditionalFields("type","Type","strict",property)
   TitEnt.setDisplayInformation("Click <a href='"+target+"'>here</a> to open")
   return TRXi
 except urllib2.HTTPError, e:
  if (str(e.code)=='401' and str(e.info()).lower().find(findwords)):
   logger.info("Found [%s] on [%s] - with HTTP 401"%(findwords,target))
   TitEnt=TRXi.addEntity("paterva.PossibleEntryPoint","")
   TitEnt.setValue(value)
   TitEnt.addAdditionalFields("entry","Entry","strict",entry)
   TitEnt.addAdditionalFields("type","Type","strict",property)
   TitEnt.setDisplayInformation("Click <a href='"+target+"'>here</a> to open")
   return TRXi
 except:
   return TRXi




me = MaltegoTransform()
me.parseArguments(sys.argv);
target=sys.argv[1]

logger.info("Searching for known CMS on [%s]"%target)
#see that it resolves as urllib cannot set timeout on DNS
try:
  a=socket.gethostbyname(target)
except:
  logger.info("Could not resolve [%s] to IP address"%target)
  me.returnOutput()
  quit()

checkCMS(target,"http://"+target+"/wp-admin/","wp-content","WordPress CMS",target,"WP",me)
checkCMS(target,"http://"+target+"/administrator/index.php","Joomla","Joomla CMS",target,"JML",me)
checkCMS(target,"http://"+target+":2082/login/","cPanel","cPanel",target,"CP",me)

me.returnOutput()


