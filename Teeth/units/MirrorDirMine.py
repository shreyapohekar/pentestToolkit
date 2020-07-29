from TeethLib import *   
from MaltegoTransform import *
from urlparse import *

m = MaltegoTransform()
m.parseArguments(sys.argv);

target=sys.argv[1]
level=m.getVar('level')
origin=m.getVar('origin')

TTM=read_config_file('MirrorGeneral','time_to_mirror')

if level is None and origin is None:
 logger.info("Running mirror directory mine on website [%s]"%target)
 level=1
 track=''
else:
 if level is not None and origin is not None:
  track=target.replace('/','')
  target=urlparse(origin).netloc
  level=str(int(level)+1)
  logger.info("Running mirror deeper mine on w[%s] l[%s] t[%s]"%(target,level,track))
 else:
  logger.info("[%s] Can only run subdirectory mirror mining on directories which are a result of a mirror"%target)
  m.returnOutput()
  quit()

output=get_MirrorData(target,TTM)

dirs=[] 
dirs=get_dirs_from_mirror(output,int(level),track) 
logger.debug("Found [%d] directories on [%s]"%(len(dirs),target))

for dir in dirs:
# logger.debug("Found directory [%s]"%dir)
 Ent=m.addEntity("maltego.WebDir",'/'+dir)
 Ent.addAdditionalFields("level","level","strict",str(level))
 
 if (level==1):
  Ent.addAdditionalFields('origin','origin','strict','http://'+target+"/"+dir)
  Ent.setDisplayInformation("Click <a href='http://"+target+"/"+dir+"/'>here</a> to open")
 else:
  Ent.addAdditionalFields('origin','origin','strict',origin+"/"+dir)
  Ent.setDisplayInformation("Click <a href='"+origin+"/"+dir+"/'>here</a> to open")
   
 
m.returnOutput()