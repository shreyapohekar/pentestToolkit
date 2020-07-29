from TeethLib import *
from MaltegoTransform import *


#####
def buildPerson(me,firstname,lastname):
   Person=me.addEntity("maltego.Person",firstname.capitalize()+" "+lastname.capitalize())
   Person.addAdditionalFields("firstname","firstname","strict",firstname.capitalize())
   Person.addAdditionalFields("lastname","lastname","strict",lastname.capitalize())
   me.returnOutput()
   quit()




me = MaltegoTransform()
me.parseArguments(sys.argv);
target=sys.argv[1]


##check for nonsense
if (target.find('@')<0):
 logger.info("Could not parse email address [%s]"%target)
 me.returnOutput()
 quit()

(front,back)=target.split('@')
if len(front)<=0 or len(back)<=0:
 logger.info("Could not parse email address [%s]"%target)
 me.returnOutput()
 quit()
 

firstname=""
lastname=""
method=read_from_config("EmailToPerson","MethodInUse")
logger.info("Converting email address [%s] with method [%s]"%(target,method))

if method=='ParseSep_FL'  or method=='ParseSep_LF':
 seps=read_from_config("EmailToPerson","ParseSep").split(',')
 logger.debug("Seps are [%s] - front is [%s] and back is [%s]"%(seps,front,back))
 
 for sep in seps:
  if front.find(sep)>0:
   if method=='ParseSep_FL':
    (firstname,lastname)=front.split(sep)
   if method=='ParseSep_LF':
    (lastname,firstname)=front.split(sep)
   
   buildPerson(me,firstname,lastname) 
   
if method=='JDoe':
 firstname=front[0:1]
 lastname=front[1:]
 buildPerson(me,firstname,lastname)
 
if method=='DoeJ':
 firstname=front[-1:]
 lastname=front[0:-1]
 buildPerson(me,firstname,lastname)
  
   
me.returnOutput()