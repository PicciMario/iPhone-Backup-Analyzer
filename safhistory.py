#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

 safhistory.py provides the code to show a TK window to browse through
 the binary PLIST file which holds the Safari history data in the iPhone Backup.

'''

# IMPORTS -----------------------------------------------------------------------------------------

from Tkinter import *
import sqlite3
import ttk
from datetime import datetime
import os
from string import *
from PIL import Image, ImageTk
import StringIO

# GLOBALS -----------------------------------------------------------------------------------------

historytree = None
textarea = None
historywindow = None
filename = ""

# saves references to images in textarea
# (to keep them alive after callback end)
photoImages = []

def cleanSpace(string):
	if (isinstance(string, str)): string = string.replace(' ', '\ ')
	return string

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global historytree, textarea
	global photoImages
	
	if (len(historytree.selection()) == 0): return;
	
	# check whether the selection is a group or a contact
	type = historytree.set(historytree.selection(), "type")
	if (type == "G"): return
	
	user_id = int(historytree.item(historytree.selection(), "text"))
	
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	query = "SELECT First, Last, Organization, Middle, Department, Note, Birthday, JobTitle, Nickname FROM ABPerson WHERE ROWID = \"%i\""%user_id
	tempcur.execute(query)
	user = tempcur.fetchall()[0]
	
	textarea.delete(1.0, END)
	
	first = user[0]
	last = user[1]
	organization = user[2]
	middle = user[3]
	department = user[4]
	note = user[5]
	birthday = user[6]
	jobtitle = user[7]
	nickname = user[8]
	
	# Print contact complete name and organization
	name = ""
	if (first != None):
		name = first
	if (middle != None):
		name = name + " " + middle
	if (last != None):
		name = name + " " + last

	if (first == None and last == None):
		name = organization
		textarea.insert(END, "%s\n"%(name))
	else:
		textarea.insert(END, "%s\n"%(name))
		if (organization != None):
			textarea.insert(END, "%s\n"%(organization))
	
	if (department != None):
		textarea.insert(END, "Dept: %s\n"%(department))
	
	textarea.insert(END, "****************************\n")
	
	# other elements from the ABPerson table
	printsep = 0
	
	if (note != None):
		textarea.insert(END, "Note: %s\n"%note)
		printsep = 1
	if (birthday != None):
		birthday = int(birthday.partition(".")[0]) + 978307200 #JAN 1 1970
		birthdaydate = datetime.fromtimestamp(int(birthday)).date()
		textarea.insert(END, "Birthday: %s\n"%birthdaydate)
		printsep = 1
	if (jobtitle != None):
		textarea.insert(END, "Job Title: %s\n"%jobtitle)
		printsep = 1
	if (nickname != None):
		textarea.insert(END, "Nickname: %s\n"%nickname)
		printsep = 1	
	
	if (printsep == 1):
		textarea.insert(END, "****************************\n")
	
	# multivalues
	query = "SELECT property, label, value, UID FROM ABMultiValue WHERE record_id = \"%s\""%user_id
	tempcur.execute(query)
	multivalues = tempcur.fetchall()
	
	# acquire multivalue labels
	query = "SELECT value FROM ABMultiValueLabel"
	tempcur.execute(query)
	multivaluelabels = tempcur.fetchall()

	# acquire multivalue labels keys
	query = "SELECT value FROM ABMultiValueEntryKey"
	tempcur.execute(query)
	multivalueentrykeys = tempcur.fetchall()

	# print multivalues
	for multivalue in multivalues:
		
		# decode multivalue type
		if (multivalue[0] == 3):	
			property = "Phone number"
		elif (multivalue[0] == 4):
			property = "EMail address"
		elif (multivalue[0] == 5):
			property = "Multivalue"
		elif (multivalue[0] == 22):
			property = "URL"
		else: 
			property = "Unknown (%s)"%multivalue[0]
		
		# decode multivalue label
		label = ""
		if (multivalue[1] != None):
			label = multivaluelabels[int(multivalue[1]) - 1][0]
			label = lstrip(label, "_!<$")
			label = rstrip(label, "_!>$")
		
		value = multivalue[2]
		
		# if multivalue is multipart (an address)...
		if (multivalue[0] == 5):
			multivalueid = multivalue[3]
			query = "SELECT KEY, value FROM ABMultiValueEntry WHERE parent_id = \"%i\" ORDER BY key"%multivalueid
			tempcur.execute(query)
			parts = tempcur.fetchall()

			textarea.insert(END, "Address (%s):\n"%(label))
			
			for part in parts:
				partkey = part[0]
				partvalue = part[1]
				label = multivalueentrykeys[int(partkey) - 1][0]
				textarea.insert(END, "- %s : %s\n"%(label, partvalue))
			
		else:
			textarea.insert(END, "%s (%s): %s\n"%(property, label, value))
	
	# free database file
	tempdb.close()

# MAIN FUNCTION --------------------------------------------------------------------------------
	
def history_window(filenamenew):
	global filename
	global historytree, textarea, historywindow
	filename = filenamenew
	
	#print("Filename: %s"%filename)
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for Safari History database: %s"%filename)
		return
	
	# main window
	historywindow = Toplevel()
	historywindow.title('Safari History data')
	historywindow.focus_set()
	
	historywindow.grid_columnconfigure(1, weight=1)
	historywindow.grid_rowconfigure(1, weight=1)
	
	# header label
	contactstitle = Label(historywindow, text = "Safari History data from: " + filename, relief = RIDGE)
	contactstitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# convert binary plist file into plain plist file
	history_tempfile = os.path.dirname(sys.argv[0]) + "/out.plist" #default name from perl script plutil.pl
	command = "perl \"" + os.path.dirname(sys.argv[0]) + "/plutil.pl\" \"%s\" "%filename
	os.system(command)
	
	# import main xml data from output file
	from xml.dom.minidom import parse
	historyxml = parse(history_tempfile)
	os.remove(history_tempfile)
	
	# main dictionary (contains anything else)
	maindicts = historyxml.getElementsByTagName('dict')
	if (len(maindicts) <= 0): 
		print("no main dict found in file")
		return
	maindict = maindicts[0]
	
	# reads a DICT node and returns a python dictionary with key-value pairs
	def readDict(dictNode):
		ritorno = {}
		
		# check if it really is a dict node
		if (dictNode.localName != "dict"):
			print("Node under test is not a dict (it is more likely a \"%s\")."%node.localName)
			return ritorno
		
		nodeKey = None
		for node in dictNode.childNodes:
			if (node.nodeType == node.TEXT_NODE): continue
			
			if (nodeKey == None):
				nodeKeyElement = node.firstChild
				if (nodeKeyElement == None):
					nodeKey = "-"
				else:
					nodeKey = node.firstChild.toxml()
			else:
				ritorno[nodeKey] = node
				nodeKey = None
		
		return ritorno

	# reads an ARRAY node and returns a python list with elements
	def readArray(arrayNode):
		ritorno = []
		
		# check if it really is a dict node
		if (arrayNode.localName != "array"):
			print("Node under test is not an array (it is more likely a \"%s\")."%node.localName)
			return ritorno
		
		for node in arrayNode.childNodes:
			if (node.nodeType == node.TEXT_NODE): continue
			ritorno.append(node)
		
		return ritorno

	outerDict = readDict(maindict)
	bookmarksArray = readArray(outerDict['WebHistoryDates'])
	
	for element in bookmarksArray:
		
		elementDict = readDict(element)
		
		elementTitle = ""
		if ('title' in elementDict.keys()):
			elementTitle = elementDict['title'].firstChild.toxml()
		
		elementUrl = ""
		if ('-' in elementDict.keys()):
			elementUrl = elementDict['-'].firstChild.toxml()
		
		print elementTitle
		print elementUrl
		print ("---")
	
	
	return
	
	# main <array> element (containing dicts for each history element)
	historyarrays = maindict.getElementsByTagName('array')
	if (len(historyarrays) <= 0): 
		print("no array found in main dict in file")
		return
	historyarray = historyarrays[0]
	
	def getCont(father):
		rc = []
		for node in father.childNodes:
			if (node.nodeType == node.TEXT_NODE):
				print("appending: %s"%getText(father))
				rc.append(getText(father))
			elif (node.tagName == "array"):
				ritorno = ""
				for element in node.childNodes:
					ritorno = ritorno + getCont(element) + " "
					print("--appending %s"%getCont(element))
				rc.append("(" + ritorno + ")")
				print("appending %s"%ritorno)
			else:
				rc.append(getText(father))
				print("Appending %s"%getText(father))
				
		return ''.join(rc)
	
	def getText(father):
	    rc = []
	    for node in father.childNodes:
	        if node.nodeType == node.TEXT_NODE:
	            rc.append(node.data)
	    return ''.join(rc)
	
	# browsing through elements in history dicts
	for dict in historyarray.childNodes:
		if (dict.nodeType == dict.TEXT_NODE): 
			continue
		print("\n\n----- New History Element:")
		for element in dict.childNodes:
			if (element.nodeType == element.TEXT_NODE):
				continue
			print("element: " + element.tagName + " -> " + getCont(element))
	
	return

	# tree
	historytree = ttk.Treeview(historywindow, columns=("name", "type"),
	    displaycolumns=("name"))
	
	historytree.heading("#0", text="ID", anchor='w')
	historytree.heading("name", text="Name", anchor='w')
	
	historytree.column("#0", width=80)
	historytree.column("name", width=250)
	
	historytree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(historywindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	# footer label
	footerlabel = StringVar()
	contactsfooter = Label(historywindow, textvariable = footerlabel, relief = RIDGE)
	contactsfooter.grid(column = 0, row = 2, sticky="ew", columnspan=2, padx=5, pady=5)
	
	# destroy window when closed
	historywindow.protocol("WM_DELETE_WINDOW", historywindow.destroy)
	
	# opening database
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 

	# footer statistics
	query = "SELECT count(ROWID) from ABPerson"
	tempcur.execute(query)
	contactsnumber = tempcur.fetchall()[0][0]
	query = "SELECT count(ROWID) from ABGroup"
	tempcur.execute(query)
	groupsnumber = tempcur.fetchall()[0][0]
	footerlabel.set("Found %s contacts in %s groups."%(contactsnumber, groupsnumber))
	
	# populating contacts tree

	# all contacts
	allnode = historytree.insert('', 'end', text="", values=("All Contacts", "G"))
	query = "SELECT ROWID, First, Last, Organization FROM ABPerson ORDER BY Last, First, Organization"
	tempcur.execute(query)
	people = tempcur.fetchall()
	for person in people:
		personid = person[0]
		
		if (person[1] != None):
			name = person[1]
		if (person[2] != None):
			name = name + " " + person[2]
		if (person[1] == None and person[2] == None):
			name = person[3]
		
		historytree.insert(allnode, 'end', text=personid, 
			values=(cleanSpace(name), "C"))	
	
	# groups contacts
	query = "SELECT ROWID, Name FROM ABGroup"
	tempcur.execute(query)
	groups = tempcur.fetchall()
	
	for group in groups:
		groupid = group[0]
		name = group[1]
		groupnode = historytree.insert('', 'end', text=groupid, values=(cleanSpace(name), "G"))

		query = "SELECT ABPerson.ROWID, First, Last, Organization FROM ABGroupMembers INNER JOIN ABPerson ON ABGroupMembers.member_id = ABPerson.ROWID WHERE ABGroupMembers.group_id = \"%s\" ORDER BY Last, First, Organization"%groupid
		tempcur.execute(query)
		people = tempcur.fetchall()
		
		for person in people:
			personid = person[0]
			
			if (person[1] != None):
				name = person[1]
			if (person[2] != None):
				name = name + " " + person[2]
			if (person[1] == None and person[2] == None):
				name = person[3]
				
			historytree.insert(groupnode, 'end', text=personid, 
				values=(cleanSpace(name), "C"))

	tempdb.close()
	historytree.bind("<ButtonRelease-1>", OnClick)
