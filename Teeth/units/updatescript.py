################################
#
# Script to update the 
# CSV database for nmap vuln scan
#
################################

from urlparse import urlparse
import urllib
import urllib2
import httplib
import os
import datetime


def downloadScip():
	print("\nUpdating Scip DB...")
	try:
		conn = httplib.HTTPConnection("www.scip.ch")
		conn.request("GET", "/vuldb/scipvuldb.csv")
		resp = conn.getresponse()
		newDict = resp.read().split('\n')
		t = open("Scip-"+str(datetime.date.today())+".csv", 'w')
		for i in newDict:
			t.write(i+'\n')
		t.close()
		print("Scip DB updated. Now contains {0} vulns\n".format(len(newDict)))
	except Exception, e:
		print("Could not download SCIP database: %s"%e)

def downloadCVE():
	
	try:
		print("Updating CVE DB... (Might take a while)")
		conn = httplib.HTTPConnection("cve.mitre.org")
		conn.request("GET", "/data/downloads/allitems.csv")
		resp = conn.getresponse()
		newDict = resp.read().split('\n')
		t = open("CVE-"+str(datetime.date.today())+".csv", 'w')
		for i in newDict:
			t.write(i+'\n')
		t.close()
		print("Successfully downloaded CVE vuln DB")
	except:
		print("Couldn't download CVE database")	

def downloadExploitDB():
	try:
		print("Updating Exploit DB... (Might take a while)")
		conn = httplib.HTTPConnection("www.exploit-db.com")
		conn.request("GET", "/archive.tar.bz2")
		resp = conn.getresponse()
		newDict = resp.read().split('\n')
		t = open("ExploitDB-"+str(datetime.date.today())+".tar.bz2", 'w')
		for i in newDict:
			t.write(i+'\n')
		t.close()
		subprocess.call(["tar","jxf", str("ExploitDB-"+str(datetime.date.today())+".tar.bz2")], stdout=subprocess.PIPE)
		print("Successfully downloaded CVE vuln DB")
	except:
		print("Couldn't download Exploit database")	


#downloadScip()
downloadCVE()
#downloadExploitDB()
