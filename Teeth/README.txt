NB NB: This runs on Kali Linux
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#Make directory /opt/Teeth/
#Copy tgz to /opt/Teeth/
#Untar

Load the config file called /opt/Teeth/etc/Maltego_config.mtz file into Maltego. 
This is painless:
1) Open Maltego Tungsten (or Radium)
2) Click top left globe/sphere (Application button) 
3) Import -> Import configuration, choose /opt/Teeth/etc/Maltego_config.mtz

Notes
-----
Config file is in /opt/Teeth/etc/TeethConfig.txt
Everything can be set in the config file.

Log file is /var/log/Teeth.log, tail -f it while you running transforms for
real time logs of what's happening.

You can set DEBUG/INFO. DEBUG is useful for seeing progress - set in
/opt/Teeth/units/TeethLib.py line 26

Look in cache/ directory. Here you find caches of:
1) Nmap results
2) Mirrors
3) SQLMAP results

You need to remove cache files by hand if you no longer want them.
You can run housekeep/clear_cache.sh but it removes EVERYTHING.

The WP brute transform uses Metasploit.Start Metasploit server so:
	msfconsole -r /opt/Teeth/static/Teeth-MSF.rc 
It takes a while to start, so be patient.

In /housekeep is killswitch.sh - it's the same as killall python..:)


Enjoy,
RT
2013-07-23

Oh BTW - you might need to install some Python packages:
sudo apt-get install python-mechanize python-levenshtein python-adns msgpack-python python-metaconfig python-bs4 python-easygui