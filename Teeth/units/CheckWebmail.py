import socket;
from MaltegoTransform import *
from TeethLib import *
import urllib2
from BeautifulSoup import BeautifulSoup
from async_dns import *
from socket import gethostbyname
import os

def trx_CheckWebMail(m,target):
    checks=["mail","webmail","owa","outlook","exchange","secure","gateway","vpn","activesync","connect"]
    async=[]
    for check in checks:
        lookup=check+"."+target;
        async.append(lookup)
    
    logger.debug("Async lookup on [%s] started"%target)
    ar = AsyncResolver(async)
    resolved = ar.resolve()
    logger.debug("Async lookup on [%s] done"%target)
    
    #do a normal look up for checking
    D=None
    try:
        D=socket.gethostbyname("notherewildcard."+target)
    except:
        D=""
    
    logger.debug("Control IP is:"+D)

    for host,ip in resolved.items():
        if ip == D or ip is None:
            logger.debug("[%s] does not resolve or resolves to wildcard."%host)
        else:        
            try:
                #test if open on 443
                logger.debug("Checking [%s] on port 443" %host)
                s=socket.socket()
                s.settimeout(4)
                s.connect((host,443))
                s.settimeout(None)
                entryp="https://"+host
                
                logger.debug("[%s] is open on 443, getting type.."%host)
                #get the version
                Title=getVersion("https://"+host)
                logger.debug("Title on [%s] is [%s]"%(host,Title))
                
                if Title!='EMPTY' and Title!='DENIED':
                
                 #if we don't get OWA try another path
                 if Title=='GENERIC':
                 
                     TitleEx=getVersion("https://"+host+"/exchange")
                     logger.debug("On [%s], trying with /exchange"%host)
                     entrypEx="https://"+host+"/exchange"
                    
                     if TitleEx=='GENERIC' or TitleEx=='EMPTY' or TitleEx=='DENIED':
                        logger.debug("On [%s], trying with /owa/"%host)
                        TitleEx=getVersion("https://"+host+"/owa")
                        entrypEx="https://"+host+"/owa"
                        
                        if TitleEx!='EMPTY' and TitleEx!='DENIED': 
                          TitEnt=m.addEntity("paterva.PossibleEntryPoint","")
                          TitEnt.setDisplayInformation("TYPE:"+TitleEx+"<BR> <a href="+entrypEx+">Open</a>")
                          TitEnt.setValue(host)
                          TitEnt.addAdditionalFields("entry","Entry","strict",entrypEx)
                          TitEnt.addAdditionalFields("type","Type","strict",TitleEx)
                          logger.info("Found [%s] title on [%s] - /owa"%(TitleEx,host))
                        else:
                         if Title=='GENERIC': #first title
                          TitEnt=m.addEntity("paterva.PossibleEntryPoint","")
                          TitEnt.setDisplayInformation("TYPE:"+Title+"<BR> <a href="+entryp+">Open</a>")
                          TitEnt.setValue(host)
                          TitEnt.addAdditionalFields("entry","Entry","strict",entryp)
                          TitEnt.addAdditionalFields("type","Type","strict",Title)
                          logger.info("Found [%s] title on [%s] - /owa"%(Title,host))
                     else:
                       TitEnt=m.addEntity("paterva.PossibleEntryPoint","")
                       TitEnt.setDisplayInformation("TYPE:"+TitleEx+"<BR> <a href="+entrypEx+">Open</a>")
                       TitEnt.setValue(host)
                       TitEnt.addAdditionalFields("entry","Entry","strict",entrypEx)
                       TitEnt.addAdditionalFields("type","Type","strict",TitleEx)
                       logger.info("Found [%s] title on [%s] - /exchange"%(TitleEx,host))
                 else:
                    TitEnt=m.addEntity("paterva.PossibleEntryPoint","")
                    TitEnt.setDisplayInformation("TYPE:"+Title+"<BR> <a href="+entryp+">Open</a>")
                    TitEnt.setValue(host)
                    TitEnt.addAdditionalFields("entry","Entry","strict",entryp)
                    TitEnt.addAdditionalFields("type","Type","strict",Title)
                    logger.info("Found specific title:[%s] on [%s]"%(Title,host))
                                                                                                                            
                
            except socket.error as msg:
                 logger.info("[%s] exists, but not open on 443"%host)
    
    m.returnOutput()


def compare_it(html,dirname,filename):
    test=slurp_file_plain(dirname+filename)
    compare=compare_strings(str(html),test)
    logger.debug("Compared at [%s] on [%s]"%(str(compare),filename))
    return compare


def determine_version(html):
#    logger.debug("Content is:\n>>>%s<<<\n"%html)
    searchdir='/opt/Teeth/static/OWA-Fingerprints/'
    for dirname, dirnames, filenames in os.walk(searchdir):
     for filename in filenames:
      compare=compare_it(html,searchdir,filename)
      if compare>0.70:
       return filename
        
    return "GENERIC"


def getVersion(website):
    logger.debug("GETVERSION: Looking at [%s]"%website)
    html=get_url_with_BS(website,10)
    
    if html=='401':
      return "OWA_NTLM"
    if html=='403':
      return "DENIED"
    if len(html)<5:
      return "EMPTY"
          
    return determine_version(html)    
    
    
    





m = MaltegoTransform()
m.parseArguments(sys.argv)
target=sys.argv[1]

logger.info("Checking for webmail on [%s]"%target)
trx_CheckWebMail(m,target)
    
    


