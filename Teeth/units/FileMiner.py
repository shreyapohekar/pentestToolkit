import threading
import time
from TeethLib import *
from MaltegoTransform import *

me = MaltegoTransform()
me.parseArguments(sys.argv);

target=me.getVar('origin')

urls_received = 0
stack=[]
tcount=0

def compare_url(dir, nothere,timeout_T):
  global tcount
  tcount +=1;

  compare = get_url_with_BS(target+dir,timeout_T).replace(dir,'').lower()
  if (len(compare)>0):  
  
   c_ratio = compare_strings(snippet(compare),snippet(nothere))
   logger.debug("Compare on ["+target+dir+"] is "+str(c_ratio))

   if c_ratio < 0.7 and len(compare)>0 and compare != '500': 
       logger.info("Found "+target+dir+"! - ratio was:"+str(c_ratio))
       logger.debug("Compared:\n---------------\n>>%s<<\n============\n>>>%s<<<\n"%(snippet(compare),snippet(nothere))) 
       stack.append(dir)

  global urls_received
  urls_received +=1
  tcount -=1


##main
logger.info("Starting file mining on:"+target)
exts=read_config_file('FileMiner',read_config_file('FileMiner','FileTypesInUse')).split(',')
files=read_config_file('FileMiner',read_config_file('FileMiner','FileListInUse')).split(',')
timeout_T=int(read_config_file('FileMiner','timeout'))
no_threads=int(read_config_file('FileMiner','threads'))

for e in exts:

 randomstring=id_generator()
 randomstring2=id_generator()
 logger.info("Testing for files on:["+target+'] with extension:['+e+']')

 nothere=get_url_with_BS(target+'/'+randomstring+'.'+e,timeout_T).replace('/'+randomstring+'.'+e,'').lower()
 nothere2=get_url_with_BS(target+'/'+randomstring2+'.'+e,timeout_T).replace('/'+randomstring2+'.'+e,'').lower()
 
 #test if different
 skip=0
 if compare_strings(snippet(nothere),snippet(nothere2)) < 0.7:
  logger.warn("Difference in baseline response between [%s] and [%s] is too similar, skipping ext [%s]"%(target+'/'+randomstring+'.'+e,target+'/'+randomstring2+'.'+e,e))
  logger.debug("Compared [%s] and [%s]"%(nothere,nothere2))
  skip=1
  

 if skip==0 and len(nothere)>0 and len(nothere2)>0 and nothere != '401':
  for u in files :
    while tcount>no_threads:
     time.sleep(2)
    
    t = threading.Thread(target=compare_url, args = ('/'+u+'.'+e,nothere,timeout_T))
    t.start()
 else:
  if (nothere=='401'):
   logger.info("Received a 401 on [%s]"%target)
  else: 
   logger.info("Test request for:"+target+'/'+randomstring+'.'+e+" failed..ignoring set")

##wait for threads to end
while urls_received < len(exts)*len(files) and tcount>0:
  time.sleep(1)

for f in stack:
 fileEnt=me.addEntity("maltego.Phrase",f)
 fileEnt.setDisplayInformation("Click <a href='"+target+f+"'>here</a> to open")
 fileEnt.addAdditionalFields("origin","origin","strict",target)
 logger.info("Found: [%s] on [%s]"%(f,target))

logger.info("File scan for [%s] is complete"%target)
me.returnOutput()
 