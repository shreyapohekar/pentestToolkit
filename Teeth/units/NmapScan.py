from TeethLib import *
from MaltegoTransform import *
from lxml import etree

######
def parseNmap(filename,m,target):
  logger.debug("Parsing Nmap output. Filename is [%s] and target was [%s]"%(filename,target))
  doc = etree.parse(filename)
  for x in doc.xpath("//host[ports/port[state[@state='open']]]"):

    for open_p in x.xpath("ports/port[state[@state='open']]"):
     portnr=open_p.attrib['portid']
     porttype=open_p.attrib['protocol']

     for p in open_p.xpath("service"):
      myver=""
      version=""
      extrainfo=""
      product=""
      try:
       product=str(p.attrib['product'])
       version=str(p.attrib['version'])
       extrainfo=str(p.attrib['extrainfo'])
      except:
       pass
      myver=(product+" "+version+" "+extrainfo).strip()
      if len(myver)<=0:
       myver="Unknown"
      
      Service=m.addEntity("maltego.Service",portnr+":"+myver)
      Service.addAdditionalFields("port.number","Port","strict",portnr)
      Service.addAdditionalFields("banner.text","Service banner","strict",myver)
      Service.addAdditionalFields("origin","origin","strict",target)
      
      render=""
      for scripts in doc.xpath("//port[@portid='"+portnr+"']/script"):
       render+="<tr><td>"+scripts.attrib['id'].replace("\n","<br>")+"</td><td>"+scripts.attrib['output'].replace("\n","<br>")+"</td></tr>"
      
      if len(render)>0:
       render="<table><tr><td>Nmap results</td></tr>"+render+"</table>"
       Service.setDisplayInformation(render) 
  m.returnOutput()


#######
def nmap(target,m):

  additional=read_from_config("Nmap",read_from_config("Nmap","ScanArgsInUse"))
  addb64=b64e(additional)
  ports=read_from_config("Nmap",read_from_config("Nmap","PortsInUse"))
  
  
  #check if we HAVE the ports from Census
  # this is not really officially documented..
  if ports=='PS':
   logger.debug('Trying to get the ports from the <OpenPorts> property and just dumping them!')
   if not m.getVar('OpenPorts'):
    logger.debug('Sorry - it seems you dont have the <OpenPorts> property in your entity. You need to get IPs from the CensusTransforms for this to work!')
    m.returnOutput()
    quit()
   #assume it's there
   CensusPorts=m.getVar('OpenPorts').split(',')
   for CPort in CensusPorts:
    Service=m.addEntity("maltego.Service",CPort+":Census Result")
    Service.addAdditionalFields("origin","origin","strict",target)
   m.returnOutput()
   quit()
     

  #check if we have ports?
  
  if m.getVar('OpenPorts'):
   logger.debug("It seems we know of open ports on host [%s] - they are [%s]"%(target,m.getVar('OpenPorts')))
   ports=m.getVar('OpenPorts')
  
  scripttype=read_from_config("Nmap","ScriptType")
  scripts=""
  if (scripttype.lower() != 'none'):
   scripts="--script "+scripttype
  
  filename=read_from_config("Nmap","CacheDir")+target+"-"+scripttype+"."+addb64+".xml"
  filepart="-oX "+ filename
  
  #check if it's in the cache
  if os.path.exists(filename):
   logger.info("Reading Nmap results from cache file [%s]"%filename)
   parseNmap(filename,m,target)

  else: 
   fullcmd="nmap %s %s %s -p %s %s"%(filepart,scripts,additional,ports,target)
   logger.debug("Starting nmap like so [%s]"%fullcmd)
   nr=run_external(fullcmd)
   logger.debug("Nmap output is:\n<<<%s>>>"%nr)
  
   if nr.find("Nmap done")<0:
    logger.info("Nmap did not complete. Something horrible must have happened")
    newname=filename+"."+id_generator()+".broken"
    logger.debug("Moving XML to [%s] to preserve"%newname)
    run_external("mv %s %s"%(filename,newname))
    m.returnOutput()
    quit()
   
   logger.debug("Nmap done - now parsing XML")
   parseNmap(filename,m,target) 




m = MaltegoTransform()
m.parseArguments(sys.argv);
target=sys.argv[1]

logger.info("Nmap scan module started on [%s]"%target)
nmap(target,m)



