Make sure that CVE file, deepSearch.py, quickSearch.py, vulnerability.py and services.txt are in the right folder (/opt/Teeth/units)

From cmd line pass either script a banner encapsulated within quotes e.g.

python quickSearch.py "Apache 2.2.1".

OR in maltego:
	Load settings.mtz into maltego 
	run either search in maltego off of banners. 

UPDATE DB:

 to run an update on the CVE DB, simply call updatescript.py from cmd line and it will download a new DB to the current directory.
