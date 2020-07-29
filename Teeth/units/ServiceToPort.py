from TeethLib import *
from MaltegoTransform import *

me = MaltegoTransform()
me.parseArguments(sys.argv);
target=sys.argv[1]

port=""
banner=""

if (target.find(':')>0):
 (port,banner)=target.split(':')
else:
 logger.info("Could not split port and banner on ':' - we found [%s]"%target)
 me.returnOutput()
 quit()
 
PortEnt=me.addEntity("maltego.Port",port)
me.returnOutput()


