import hashlib
from TeethLib import *   
from MaltegoTransform import *
from urlparse import *

##################
def checkDataHotList(data):
 nos=slurp_file('MirrorPIP','FieldsHotList')
 pairs=data.split('&')
 add=1;
 
 for pair in pairs:
  (name,value)=pair.split('=')
  for no in nos:
   if name==no:
    add=0
    break
      
 return add


#############
def checkDataForBadOnes(post,get):
 nos_fields=slurp_file('MirrorPIP','FieldsToIgnore')
 nos_values=slurp_file('MirrorPIP','ValuesToIgnore')

 checkforthese=[]

 #POST
 hack=""
 if (len(get)>0) and len(post)>0:
  hack=post+"&"+get
 if (len(get)>0) and len(post)==0: 
  hack=get
 if (len(post)>0) and len(get)==0:  
  hack=post
  
 pairs=hack.split('&')
 
 for pair in pairs:
  if pair.find('=')<0:
   continue

  (name,value)=pair.split('=')
  add=1 

  #check names  
  for no_f in nos_fields:
   if name.lower()==no_f.lower():
    add=0
   if no_f[0]=='~' and name.lower().find(no_f.lower()[1:])>=0:
    add=0 
    
  #check values  
  for no_v in nos_values:
   if value.lower()==no_v.lower():
    add=0 
   if no_v[0]=='~' and value.lower().find(no_v.lower()[1:])>=0:
    add=0   
  
  if add==1:
   checkforthese.append(name)  
#  else:
#   logger.debug("Not adding [%s]"%name) 

 return checkforthese


################
m = MaltegoTransform()
m.parseArguments(sys.argv);

target=sys.argv[1]

TTM=read_config_file('MirrorGeneral','time_to_mirror')
logger.info("Checking for Possible Injection Points on [%s]"%target)
output=get_MirrorData(target,TTM)
   
forms=get_forms_from_mirror(output) 
for form in forms:
  
  params=[]
  url=form['url']
  parse=urlparse(url)
  site=parse.netloc
  add=1;
  
  if site != target:
   add=0;
   continue

  if len(form['data'])>0:
    add=checkDataHotList(form['data'])
 
  params=checkDataForBadOnes(form['data'],urlparse(form['url']).query)


  if (add==1 and len(params)>0):
    goodparam=','.join(params)
    hashable=hashlib.md5(form['action']+form['url']+form['data']).hexdigest()
    PIPEnt=m.addEntity("paterva.PossibleInjectionPoint",hashable)
    PIPEnt.addAdditionalFields('method','method',"strict",form['action'])
    PIPEnt.addAdditionalFields('url','url',"strict",sillyencode(form['url']))
    PIPEnt.addAdditionalFields('postdata','postdata',"strict",sillyencode(form['data']))
    PIPEnt.addAdditionalFields('haschecked','haschecked',"strict",'false')
    PIPEnt.addAdditionalFields('varstocheck','varstocheck',"strict",sillyencode(goodparam))
    render = "<table><tr><td>Method</td><td>%s</td></tr> <tr><td>URL</td><td>%s</td></tr> <tr><td>POST Data</td><td>%s</td></tr> <tr><td>Checking</td><td>%s</td></tr> </table>"%(form['action'],form['url'],form['data'],goodparam)
    PIPEnt.setDisplayInformation(render)
    logger.info("ADDING [%s] [%s] [%s] -- Checking [%s]"%(form['action'],form['url'],form['data'],goodparam))
  else:
    logger.debug("NOT ADDING [%s] [%s] [%s]"%(form['action'],form['url'],form['data']))   
   
           
m.returnOutput()