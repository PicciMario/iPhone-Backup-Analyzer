#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "Network Identification"
import plugins_utils

from Tkinter import *
import ttk
import os
#from string import *
#import StringIO
#import urllib
import xml.dom.minidom
#import webbrowser
#import cStringIO
#from PIL import Image as PILImage
#import ImageTk
import plistutils
import datetime

# GLOBALS -----------------------------------------------------------------------------------------

netidenttree = None
textarea = None
netidentwindow = None
filename = ""
dict_nodes = []

def parseipv4(id_string):
	identifiers = id_string.split(';')
	ip = ""
	mac = ""
	for identifier in identifiers:
		parts = identifier.split("=")
		if (str(parts[0]) == "IPv4.Router"):
			ip = parts[1]
		elif (str(parts[0]) == "IPv4.RouterHardwareAddress"):
			mac = parts[1]
	return [ip, mac]

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global netidenttree, textarea
	global dict_nodes
	
	if (len(netidenttree.selection()) == 0): return;
	
	dict_node_id = netidenttree.item(netidenttree.selection(), "text")
	sig_dict = None
	
	for dict_node in dict_nodes:
		number = dict_node[0]
		if (number == dict_node_id):
			sig_dict = dict_node[1]
			break
	
	if (sig_dict == None):
		print("Error while retrieving data for selected network")
		return
	
	textarea.delete(1.0, END)
	
	id_string = sig_dict['Identifier'].firstChild.toxml()
	
	textarea.insert(END, "Network data\n")
	textarea.insert(END, "\n")	
	
	#2011-12-27T17:35:53.290510Z
	timestamp_string = sig_dict['Timestamp'].firstChild.toxml()
	if ("." in timestamp_string):
		timestamp_string = timestamp_string.split(".")[0] 
	timestamp = datetime.datetime.strptime(
		timestamp_string,
		"%Y-%m-%dT%H:%M:%S"
	)
	textarea.insert(END, "Network last seen in date: %s\n"%timestamp)	
	
	# parse identification for IPv4 routers
	if (id_string.startswith('IPv4')):
		[ip, mac] = parseipv4(id_string)
		textarea.insert(END, "IP Address: %s\n"%ip)	
		textarea.insert(END, "MAC Address: %s\n"%mac)	
	else:	
		textarea.insert(END, "Network identifier: %s\n"%id_string)	

	# parse services dict
	services = plistutils.readArray(sig_dict['Services'])
	for service in services:
		textarea.insert(END, "\n")
		textarea.insert(END, "****** Service\n")
		
		service_dict = plistutils.readDict(service)
		textarea.insert(END, "Service ID: %s\n"%service_dict['ServiceID'].firstChild.toxml())
		
		for key in service_dict.keys():
		
			if (service_dict[key].nodeName != 'dict'):
				continue
		
			textarea.insert(END, "%s data\n"%key)
			single_service = plistutils.readDict(service_dict[key])
			
			for element_key in single_service.keys():
				element = single_service[element_key]
				
				if (element.nodeName == 'string'):
					textarea.insert(END, "- %s: %s\n"%(element_key, element.firstChild.toxml()))
				elif (element.nodeName == 'array'):
					textarea.insert(END, "- %s\n"%(element_key))
					element_array = plistutils.readArray(element)
					for element_array_single in element_array:
						textarea.insert(END, "  - %s\n"%(element_array_single.firstChild.toxml()))
				else:
					textarea.insert(END, "- %s: %s\n"%(element_key, element))
				
# MAIN FUNCTION --------------------------------------------------------------------------------
	
def main(cursor, backup_path):
	global filename
	global netidenttree, textarea, netidentwindow
	global dict_nodes
	
	filename = backup_path + plugins_utils.realFileName(cursor, filename="com.apple.network.identification.plist", domaintype="SystemPreferencesDomain")
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for network identification data: %s"%filename)
		return
	
	# main window
	netidentwindow = Toplevel()
	netidentwindow.title('Network Identification')
	netidentwindow.focus_set()
	
	netidentwindow.grid_columnconfigure(1, weight=1)
	netidentwindow.grid_rowconfigure(1, weight=1)
	
	# header label
	netidenttitle = Label(
		netidentwindow, 
		text = "Network Identification data from: %s (%s) "%(filename, "com.apple.network.identification.plist"), 
		relief = RIDGE,
		width=100, 
		height=3, 
		wraplength=800, 
		justify=LEFT
	)
	netidenttitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# tree
	netidenttree = ttk.Treeview(netidentwindow, columns=("id", "timestamp", "node"),
	    displaycolumns=("id", "timestamp"))
	
	netidenttree.heading("#0", text="", anchor='w')
	netidenttree.heading("id", text="ID", anchor='w')
	netidenttree.heading("timestamp", text="Time", anchor='w')
	
	netidenttree.column("#0", width=40)
	netidenttree.column("id", width=250)
	netidenttree.column("timestamp", width=150)
	
	netidenttree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(netidentwindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	# footer label
	footerlabel = StringVar()
	netidentfooter = Label(netidentwindow, textvariable = footerlabel, relief = RIDGE)
	netidentfooter.grid(column = 0, row = 2, sticky="ew", columnspan=2, padx=5, pady=5)
	
	# destroy window when closed
	netidentwindow.protocol("WM_DELETE_WINDOW", netidentwindow.destroy)
	
	# convert binary plist file into plain plist file
	netidentxml = plistutils.readPlistToXml(filename)
	if (netidentxml == None):
		print("Error while parsing binary plist data")
		return
	
	# main dictionary (contains anything else)
	maindicts = netidentxml.getElementsByTagName('dict')
	if (len(maindicts) <= 0): 
		print("no main dict found in file")
		return
	maindict = maindicts[0]

	# extract Signatures array
	maindictelements = plistutils.readDict(maindict)
	try:
		signatures = maindictelements['Signatures']
	except:
		print("No Signatures array found in main dict")
		return
	signatures_array = plistutils.readArray(signatures)
	
	# footer statistics
	footerlabel.set("Found %i identified networks."%(len(signatures_array)))
	
	id_number = 0
	
	for signature in signatures_array:
		sig_dict = plistutils.readDict(signature)
		
		id_string = sig_dict['Identifier'].firstChild.toxml()
		
		#2011-12-27T17:35:53.290510Z
		timestamp_string = sig_dict['Timestamp'].firstChild.toxml()
		if ("." in timestamp_string):
			timestamp_string = timestamp_string.split(".")[0] 
		timestamp = datetime.datetime.strptime(
			timestamp_string,
			"%Y-%m-%dT%H:%M:%S"
		)
		
		elem_id = ""
		
		# parse identification for IPv4 routers
		if (id_string.startswith('IPv4')):
			[ip, mac] = parseipv4(id_string)
			elem_id = "%s (%s)"%(ip, mac)
			
		else:	
			elem_id = id_string
		
		netidenttree.insert('', 'end', text=id_number, values=(elem_id, timestamp, sig_dict))
		dict_nodes.append([id_number, sig_dict])
		id_number = id_number + 1
		
	netidenttree.bind("<ButtonRelease-1>", OnClick)
