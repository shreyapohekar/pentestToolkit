from TeethLib import *
from MaltegoTransform import *

##########MAIN
m = MaltegoTransform()
m.parseArguments(sys.argv);
target=sys.argv[1]
 
filetoappend=read_config_file('OWABrute','StorageFile')
logger.debug("Adding to file [%s]"%target)
open(filetoappend,"a").write(target+"\n") 
run_external("cat %s | sort | uniq > /tmp/assass;mv /tmp/assass %s"%(filetoappend,filetoappend)) 
m.returnOutput()



    
    
