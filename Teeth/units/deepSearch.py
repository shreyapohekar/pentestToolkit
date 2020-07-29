#THIS TOOL SEARCHES A LOCAL CVE VULNERABILITY DATABASE FOR VULNERABILITIES PRESENT IN SERVICES FOUND IN A BANNER. 
#IT CONSISTS OF TWO SEARCH ENGINES - ONE THAT ATTEMPTS TO PULL OUT SERVICE NAMES AND NUMBERS AND FIND DIRECT MATCHES
#AND A SECOND THAT PERFORMS A WEIGHTED SEARCH ON TERM RELEVANT WORDS FOUND IN THE BANNER IF THE RESULTS OF THE FIRST RUN ARE INADEQUATE.
#MADE POSSIBLE BY AND WITH THANKS TO
#   _____  __      ____________.__        _____                                       .__  __          
#  /     \/  \    /  \______   \__| _____/ ____\____  ______ ____   ____  __ _________|__|/  |_ ___.__.
# /  \ /  \   \/\/   /|       _/  |/    \   __\/  _ \/  ___// __ \_/ ___\|  |  \_  __ \  \   __<   |  |
#/    Y    \        / |    |   \  |   |  \  | (  <_> )___ \\  ___/\  \___|  |  /|  | \/  ||  |  \___  |
#\____|__  /\__/\  /  |____|_  /__|___|  /__|  \____/____  >\___  >\___  >____/ |__|  |__||__|  / ____|
#        \/      \/          \/        \/                \/     \/     \/                       \/    
#
#Contact the authors with comments, questions, or suggestions:
#	syncikin[at]gmail.com
#	matthewdmarx[at]gmail.com

import glob
import os
import sys
import subprocess
import vulnerability
import time
from TeethLib import *
from MaltegoTransform import *

sys.setrecursionlimit(2000)

globalVulList = []
userInput = ""
commonServices = []
#print("Target is {0}.\n".format(sys.argv[1]))
mainBanner = vulnerability.banner()
blacklistedWords = ["the", "and" ,"or", "at", "Port", "port", "ServerName", "in", "with", "when", "publicized", "re:", "does", "possibly", "related", "note:", "are", "long", "multiple", "information", "unknown", "properly", "a", "yet", "not", "of", "proposed", "(candidate", "allows", "attackers", "arbitrary", "by", "has", "that", "been", "which", "will", "this", "code"]
blacklistedChars = [')','(']
triggerWordspre = ["before", "previous", "earlier", "preceeding", "prior"]
triggerWordspost = ["after","later"]
serviceObjects = []
ID = 0
blacklistedVersionNames = ["server", "http", "os", "web"]
sys.setrecursionlimit(2000)
results = "<table>"

#####THIS FUNCTION GOES THROUGH THE CURR DIR, 
#####FINDS ALL THE CSV FILES, AND THEN TAKES EACH VUL
#####AND APPENDS IT TO THE GLOBAL DICTIONARY
def buildDictionary():
		#print("Building vuln dict")
		for infile in glob.glob( os.path.join("", '*.csv') ):#find all the files that end in csv in current directory.
			#print("\t -Found dictionary {0}".format(infile))
    			for line in open(infile, 'r').readlines():
				globalVulList.append(line)
		if len(globalVulList) == 0:
			#print("Error : No databases found in this directory. Place any databases in\
			#this directory in a .csv file in the following format:/nVuln id;Vuln Name/desciption")
			pass
		#print("Done Building vuln dict with {0} vulns\n".format(len(globalVulList)))

def isVersion(string, index):
	i = index
	temp = ""
	while i < len(string):
		if string[i] == ' ' or string[i] == '\\' or string[i] == '/' or i == len(string)-1 :			
			return temp
		if string[i] == '.' or is_number(string[i]):
			temp += string[i]
		else:
			return temp
		i+=1
	return ""

def searchDB():
	global serviceObjects, ID
	#Step 1: We need to find matches with our services file and pull out objects
	tempMain = mainBanner.originalBanner.lower()
	
	for service in commonServices:
		service = service.lower().strip() 
		flag = False
		if (service in tempMain):
			flag = True
		else:
			for word in service.split():
				if word not in mainBanner.originalBanner:
					flag = False
					break
				if word in mainBanner.originalBanner:
					flag = False
		if flag:
			so = vulnerability.serviceObj()
			ID +=1
			so.ID = ID
			so.name = service
			so.version = getVersion(tempMain, service)
			tempMain = tempMain.replace(service, '')
			serviceObjects.append(so)
	# Step 2: Go through the objects and remove things like "server 2.2.1" when we already have "Apache server 2.1.1 as well as duplicates
	count = 0
	checkedObjs = []
	for obj2 in serviceObjects:
		if obj2.name in checkedObjs:
			serviceObjects.remove(obj2)
			continue
		else:
			checkedObjs.append(obj2.name)
			
		obj2.version = obj2.version.strip()
		objNameList = obj2.name.split(' ')
		obj2.vulns = []	
		searchDBLegacy(obj2.name, obj2.version)
	
def delNums(string):
	temp = ""
	for char in string:
		if is_number(char) or char == '.' or char == ')' or char == '(':
			continue
		temp+=char
	return temp	

def getVersion(banner, service):# This looks to find the version number of a service in the banner
	indexofService = banner.find(service)
	vnum = ""
	i = indexofService + len(service)
	while i < len(banner)-1:
		i+=1
		if banner[i] == " " :
			return vnum
		if is_number(banner[i]):
			vnum = isVersion(banner, i)
			break
	return vnum			
				 
def removeObj(obList, ob):
	newList = []
	for obj in obList:
		if not obj == ob:
			newList.append(obj)
	return newList

def searchDBLegacy(sstring, verNum):
	global results
	results1 = []
	SStotalWeight = 0.0
	tempsstring = sstring
	sstring = weightSearchString(sstring)
	for node in sstring: 
		SStotalWeight += node[1]
	for vulnerability in globalVulList:
		#Now we are iterating through all of the vulns in all of the csv databases in the system
		ogVuln = vulnerability
		# 1. put vuln in lowercase Split the vulnerability into words
		vulnerability = vulnerability.lower()	
		vulnerability = vulnerability.split(' ')
		# 2. remove blacklisted words
		vulnerability = removeBlacklistWords(vulnerability)
		# 3. Check if each word of the banner appears in vulnerability. If so weight the vuln and put in list
		vulnTot = 0.0
		if (node[0].lower()) in vulnerability:
			for node in sstring:
				if node[0].lower() in vulnerability:
					vulnTot += node[1]
		if vulnTot/SStotalWeight > 0.7:
			newnode = tuple((ogVuln, vulnTot))
			results1.append(newnode)
	results2 = []
	if len(verNum) > 0:	
		for res in results1:#Check for version number NB****** need to add KF section here
			if inRange(verNum, res[0]):
				results2.append((res[0].split('|')[0], res[1]+SStotalWeight))
			results2.append((res[0].split('|')[0], res[1]))
	else:
		results2 = results1
	final = swapTuple(quickSort(swapTuple(results2)))
	final2 = final[:10]
	
	
	me = MaltegoTransform()
	me.parseArguments(sys.argv)


	entity = me.addEntity("maltego.Vulnerability", tempsstring)
	index = 0

	render = "<table>"	
	for service in final2:
		render+=format_(service[0])
	render += "</table>"
	entity.setDisplayInformation(render)
	#print render
	me.returnOutput()
	

	
	if len(final)>10:
		#print("*Most relevant results returned. Some poor matches filtered out")
		pass

def format_(vuln):
		results2 = ""
		string = ""
		status = ""	
		split = vuln.index(',')
		cve = vuln[:split]
		oldsplit = split
		split = vuln.replace(",","XXX",1).index(',')
		status = vuln[oldsplit+1].upper() + vuln[oldsplit+2:split-2]
		vulInfo = vuln[split].upper() + vuln[split+1:]  
		results2 += "\n<tr>" 
		try:
			results2 += "\n<td> " + cve + "</td><td>" + status + "</td><td>" + vulInfo + "</td>"
		except IndexError:
			pass
		results2 += "\n</tr>" 
		return results2

def removeBlacklistWords(listwords):
	newlist = []
	for word in listwords:
		if word in blacklistedWords:
			continue
		tempword = ""
		for char in word:
			if char not in blacklistedChars:
				tempword+=char
		newlist.append(tempword)
	return newlist

def weightSearchString(banner2):
	bannerSplit = banner2.split()	
	#1. Remove Blacklisted words
	bannerSplit = removeBlacklistWords(bannerSplit)
	#2 Check through the known services and weight words accordingly
		# - a. change the listfrom a list of words into a list of tuples
		# - b. weight Words
	# Part a
	temp = []
	for word in bannerSplit:
		word = (word, 0)
		temp.append(word)
	bannerSplit = temp 
	bannerSplitNames = []
	for word in bannerSplit:
		bannerSplitNames.append(word[0].replace(' ','').replace('\n','').strip())
	#Part b
	for serviceList in commonServices:
		serviceList = serviceList.split(' ')
		for service in serviceList:
			service = service.replace('\n','')
			if service not in bannerSplitNames and service != ' ' and service != '\n' and len(service) > 0 and service != '\t':
				break #IE not all the words in the common service match the banner, try next one
			if (service+'\n' == serviceList[len(serviceList)-1]):
				
				for service in serviceList:
					service = service.replace('\n', '')
					bannerSplit = incrementVal(bannerSplit, service, len(bannerSplit))
	#Part 3 : add weighting based on position
	index = 0
	for node in bannerSplit:
		index += 1
		bannerSplit = incrementVal(bannerSplit, node[0], (len(bannerSplit)-index+1)*(len(bannerSplit)-index+1)) 	
	bannerSplit = incrementVal(bannerSplit, bannerSplit[0], (len(bannerSplit)-index+1)*(len(bannerSplit)-index+1)) 	
	#part 4 : add weighting if upperCase
	# check effect of factor var
	factor = 3
	for node in bannerSplit:
		if len(node[0])>0 and node[0][0].isupper():
			bannerSplit = incrementVal(bannerSplit, node[0], factor)
	return swapTuple(quickSort(swapTuple(bannerSplit)))
	#print("Finished weighting Search String")

def swapTuple(listD):
	retList = []
	for node in listD:
		tnode = (node[1], node[0]) 			
		retList.append(tnode)
	return retList
																																																																																																																	
def incrementVal(nodeList, nodeName, incr):#This is to increment the weighting of a tuple in a list
	returnNodeList = []
	for node in nodeList:
		if node[0] == nodeName:
			word = node[0]
			val = node[1]
			val += incr
			returnNodeList.append((word, val))
			continue
		returnNodeList.append(node)
	return returnNodeList

def quickSort(nodeList):#QuickSort
    if nodeList == []: 
        return []
    else:
        pivot = nodeList[0]
        lesser = quickSort([x for x in nodeList[1:] if x < pivot])
        greater = quickSort([x for x in nodeList[1:] if x >= pivot])
        return greater + [pivot] + lesser
	
def returnNameVersion(versionString):##Returns the aplh words in the banner		
	versionInfo = []
	versionString = versionString.split(' ')
	for word in versionString:
		flag = True
		for char in word:
			if is_number(char):
				flag = False
			if char == '.':
				word = word.split('.')[0]
				break
			if char == '\\':
				word = word.split('\\')[0]
				break
			if char == '/':
				word = word.split('/')[0]
				break
		if flag:
			mainBanner.words.append(word)
			mainBanner.name.append(word)

def returnNumVersion(banner):
	numbers = []
	split = banner.split()	
	temp = ""
	for i in split:
		formatted = ""
		if i[0].isdigit():
			for char in i:
				if char.isdigit() or char == ".":
					formatted += char
				else:
					formatted += " "
					break
			temp = formatted.split()
			numbers.append(temp)
			if len(numbers) > 0:	
				mainBanner.version=numbers[0]
				return
 	mainBanner.version=""

def is_number(s):#simple check to see if char is number
    try:
        float(s)
        return True
    except ValueError:
        return False

def sanitizeBanner():
	#remove some wierd stuff out of the banner	
	global banner
	wierdChars = [')', '(', ':', ';']
	for char in wierdChars:
		banner = banner.replace(char , '')
	for black in blacklistedWords:
		if black in banner:
			banner = banner.replace(black, "")

def prepareCommonServices():#This just prepares the DStruct that will hold all of the common banner information
	global commonServices
	servFile = open('services.txt', 'r')
	servFile2 = servFile.readlines()
	servFile.close()
	for line in servFile2:
		if (len(line)>1):
			commonServices.append(line.replace('\n', ''))
	 
	# To sort the list in place...
	commonServices.sort(key=lambda x: len(x), reverse=True)

	# To return a new list, use the sorted() built-in function...
	commonServices = sorted(commonServices, key=lambda x: len(x), reverse=True)
	
######################################
# KYLE FACTORY
#####################################

import sys
import re
from math import exp, expm1

to = ["between","to", "through"] #removed from case - too ambiguous 
pre = ["before","prior", "earlier"] #lower
post = ["after","afterwards","post","higher","later", "onwards"]

def isBetween(banner,index):
	global to
	split = banner.split()
	try: 	
		if to[0] in split[index-1]:
			if split[index+2][0].isdigit():
				return True
	except IndexError:
		pass
	try:	
		if to[1] in split[index+1]:
			if split[index+2][0].isdigit():
				return True
	except IndexError:
		pass
	try:
		if to[2] in split[index+1]:
			if split[index+2][0].isdigit():
				return True
	except IndexError:
		pass
	try:
		if to[2] in split[index+1]:
			if split[index+3][0].isdigit():
				return True
	except IndexError:
		pass
	return False
	
def isPre(banner,index):
	global pre
	split = banner.split()
	try: 
		if pre[0] == split[index-1]:
			return True
	except IndexError:
		pass

		if pre[1] == split[index-2]:
			return True
		if pre[2] == split[index-2]:
			return True
	except IndexError:
		pass
	try: 
		if pre[2] == split[index+2]:
			return True	 
	except IndexError:
		pass

	return False

def isPost(banner,index):
	global post
	split = banner.split()
	try: 
		if post[0] == split[index-1]:
			return True
		if post[2] == split[index-1]:
			return True
		if post[1] == split[index-2]:
			return True
		if post[3] == split[index-2]:
			return True
		if post[4] == split[index-2]:
			return True		
	except IndexError:
		pass

	try:
		if post[5] == split[index+1]:
			return True
		if post[1] == split[index+2]:
			return True
		if post[2] == split[index+2]:
			return True
		if post[3] == split[index+2]:
			return True
		if post[4] == split[index+2]:
			return True
		if post[0] == split[index+2]:
			return True
		if post[5] == split[index+2]:
			return True
	except IndexError:
		pass	 
		
	return False

def performMagic(banner,index):
	if isBetween(banner,index):
		return "#"
	if isPre(banner,index):
		return "-"
	if isPost(banner,index):
		return "+"
	return "="	

def getNumbers(banner):
	numbers = []
	numbersList = []
	app = []
	split = banner.split()
	flag = False
	temp = ""

	index = -1
	for i in split:
		up = False
		index+=1
		formatted=""
		if i[0].isdigit():			
			for char in i:
				if char.isdigit() or char == ".":
					formatted += char
				else:
					if char == "x":
						up = True
					break
			if formatted[len(formatted)-1] == ".":
				formatted = formatted[0:len(formatted)-1] + " "
				up = True
			temp = formatted.split()
			if flag:
				flag = False
				numbers.append("#" + temp[0])
				continue
			if up:
				app = "^" + temp[0]
				numbers.append(app)
				break
			app = performMagic(banner,index) + temp[0]	
			numbers.append(app)
			try: 
				if app[0] == "#": 	
					flag = True			
			except IndexError:
				pass
	return numbers

def inRange(number,banner):
	numbers = []
	numbers = getNumbers(banner)
	snum = 0.0
	for x in range(len(numbers)):
			if number == numbers[x][1:len(numbers[x])]:
				return True
			snum = int(scale(number))
			try: 
				if numbers[x][0] == "#" and numbers[x+1][0] == "#":
					lower = numbers[x][1:len(numbers[x])]
					upper = numbers[x+1][1:len(numbers[x+1])]
					if snum > scale(lower) and snum < scale(upper):
						return True
			except IndexError:
				pass
			if numbers[x][0] == "^": 
				try: 
					compare = numbers[x][1:len(numbers[x])]
					if snum > scale(compare) and snum < scaleUp(compare):
						return True
				except IndexError:
					pass

			if numbers[x][0] == "+":
				try: 
					compare = numbers[x][1:len(numbers[x])]
					if snum > scale(compare):
						return True
				except IndexError:
					pass	
			if numbers[x][0] == "-":
				try: 
					compare = numbers[x][1:len(numbers[x])]
					if snum < scale(compare):
						return True
				except IndexError:
					pass				
	return False

def scaleUp(number):
	decimals = 4 #hardcoded to scale for a max of 4 decimals
	split = number.split(".")
	total =  (int(split[0])+1)*pow(100,decimals)
	return total

def scale(number):
	decimals = 4 #hardcoded to scale for a max of 4 decimals
	split = number.split(".")
	total = 0
	for x in range(len(split)):
		total +=  int(split[x])*pow(100,decimals-x)
	return total

######################################
def main():
	global banner,results
	if len(sys.argv) < 2:
		#print("Please pass a banner as the argument")
		sys.exit()
	if not len(sys.argv[1]) > 0:
		#print("Please pass a banner as a string argument:")
		sys.exit()
	banner = sys.argv[1]+" "
	banner = banner.replace('-', ' ',100)
	banner = banner.replace('/', ' ',100)
	banner = banner.replace('\\', '',100)
	mainBanner.originalBanner = banner.lower()
	returnNumVersion(banner)
	returnNameVersion(banner)
	prepareCommonServices()
	buildDictionary()
	
	searchDB()


main()
