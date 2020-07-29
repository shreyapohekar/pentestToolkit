from TeethLib import *
from MaltegoTransform import *

##########MAIN
m = MaltegoTransform()
m.parseArguments(sys.argv);
target=sys.argv[1]
 
origin=m.getVar('origin')+"/"

if origin is None:
 logger.info("Origin on [%s] not found"%target)

logger.info("Checking indexability of [%s]"%origin) 

output=get_url_with_BS(origin,20)
if output.lower().find('index of')>=0 or output.lower().find('directory listing of')>=0:
 logger.info("[%s] found to be indexable"%origin)
 
 IndEnt=m.addEntity("maltego.Phrase","Indexable:"+origin)
 IndEnt.setDisplayInformation('Click <a href="'+origin+'">here</a> to view') 
else:
 logger.debug("[%s] not indexable"%origin)
  
m.returnOutput()



    
    
