import threading
import time
from TeethLib import *
from MaltegoTransform import *



me = MaltegoTransform()
me.parseArguments(sys.argv)

if (len(sys.argv[1])<=0):
 logger.debug("Not mining in the root..again! :)")
 me.returnOutput()
 quit()

origin = me.getVar("origin")
if origin is None:
 target="http://"+sys.argv[1]
else:
 target=origin
              


urls_received = 0
stack=[]
tcount=0

def compare_url(dir, nothere,timeout_T):
  global tcount
  tcount +=1;

  compare = get_url_with_BS(target+dir,timeout_T).replace(dir,'').lower()
  if (len(compare)>0):
    
   if compare.find('directory listing of')>=0 or compare.find('index of')>=0:
    logger.info("Found indexable directory on: ["+target+dir+"]")
    dir=dir+"!"

   c_ratio = compare_strings(snippet(compare),snippet(nothere))
   logger.debug("Compare on ["+target+dir+"] is "+str(c_ratio))

   if c_ratio < 0.7 and len(compare)>0 and compare != '500':
      logger.info("Found directory: "+dir+" on "+target+" ratio is:"+str(c_ratio))
      logger.debug("Compared:\n---------------\n>>%s<<\n============\n>>>%s<<<\n"%(snippet(compare),snippet(nothere)))
      stack.append(dir)

  global urls_received
  urls_received +=1
  tcount -=1


##main

logger.info("Starting directory scan on:"+target)
dirs=read_config_file('DirectoryMiner',read_config_file('DirectoryMiner','DirectoryListInUse')).split(',')
timeout_T=int(read_config_file('DirectoryMiner','timeout'))
no_threads=int(read_config_file('DirectoryMiner','threads')) 

if read_config_file('DirectoryMiner','AlwaysShowRoot').lower()=='true' and origin is None:
 stack.append('/')

randomstring=id_generator()
randomstring2=id_generator()
nothere=get_url_with_BS(target+'/'+randomstring+'/',timeout_T).replace('/'+randomstring+'/','').lower()
nothere2=get_url_with_BS(target+'/'+randomstring2+'/',timeout_T).replace('/'+randomstring2+'/','').lower()

if len(nothere)<=0 or len(nothere2)<=0:
 logger.warn("Could not get a response for baseline on [%s] - bailing!"%target)
 me.returnOutput()
 
if compare_strings(snippet(nothere),snippet(nothere2))<0.7: 
 logger.warn("Baseline responses not different enough on [%s] - bailing"%target)
 me.returnOutput()

 
for u in dirs :
   logger.debug("Testing directory ["+u+"] on ["+target+"]")
   while tcount>no_threads:
    time.sleep(2)
    
   t = threading.Thread(target=compare_url, args = (u+'/',nothere,timeout_T))
   t.start()

##wait for threads to end
while urls_received < len(dirs) and tcount>0:
  time.sleep(1)

for f in stack:
 logger.info("Found directory ["+f+"]")
 dirEnt=me.addEntity("maltego.WebDir","")
 if f[-1:]=='!':
  dirEnt.setDisplayInformation("Indexable!!<BR>")
  f=f[0:-1]

 dirEnt.setDisplayInformation("Click <a href='"+target+f+"'>here</a> to open")
 f=f[:-1]
 dirEnt.setValue(f)

 dirEnt.addAdditionalFields('origin','origin','strict',target+f)

logger.info("Directory scan for "+target+" is complete")
me.returnOutput()