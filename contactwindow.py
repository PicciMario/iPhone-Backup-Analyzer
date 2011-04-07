#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

 contactwindow.py provides the code to show a TK window to browse through
 the SQLite file which holds the Contacts data in the iPhone Backup.

'''

# IMPORTS -----------------------------------------------------------------------------------------

from Tkinter import *
import sqlite3
import ttk
from datetime import datetime
import os
from string import *

# GLOBALS -----------------------------------------------------------------------------------------

contactstree = None
textarea = None
filename = ""

def cleanSpace(string):
	if (isinstance(string, str)): string = string.replace(' ', '\ ')
	return string

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global contactstree, textarea
	if (len(contactstree.selection()) == 0): return;
	user_id = int(contactstree.item(contactstree.selection(), "text"))
	
	# check whether the selection is a group or a contact
	type = contactstree.set(contactstree.selection(), "type")
	if (type == "G"): return
	
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	query = "SELECT First, Last, Organization FROM ABPerson WHERE ROWID = \"%i\""%user_id
	tempcur.execute(query)
	user = tempcur.fetchall()[0]
	
	textarea.delete(1.0, END)
	
	first = user[0]
	last = user[1]
	organization = user[2]
	
	name = ""
	if (user[0] != None):
		name = user[0]
	if (user[1] != None):
		name = name + " " + user[1]
	if (user[0] == None and user[1] == None):
		name = user[2]
	else:
		if (user[2] != None):
			name = name + " (" + user[2] +")"
	
	textarea.insert(END, "%s\n"%(name))
	textarea.insert(END, "****************************\n")
	
	# multivalues
	query = "SELECT property, label, value FROM ABMultiValue WHERE record_id = \"%s\""%user_id
	tempcur.execute(query)
	multivalues = tempcur.fetchall()
	
	# acquire multivalue labels
	query = "SELECT value FROM ABMultiValueLabel"
	tempcur.execute(query)
	multivaluelabels = tempcur.fetchall()
	
	for multivalue in multivalues:
		
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
		
		label = multivaluelabels[int(multivalue[1]) - 1][0]
		label = lstrip(label, "_!<$")
		label = rstrip(label, "_!>$")
		
		value = multivalue[2]
		textarea.insert(END, "%s (%s): %s\n"%(property, label, value))
		
		
	
	tempdb.close()

# MAIN FUNCTION --------------------------------------------------------------------------------
	
def contact_window(filenamenew):
	global filename
	global contactstree, textarea
	filename = filenamenew
	
	print("Filename: %s"%filename)
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for SMS database: %s"%filename)
		return	
	
	# main window
	contactswindow = Toplevel()
	contactswindow.title('SMS data')
	contactswindow.focus_set()
	
	# header label
	contactstitle = Label(contactswindow, text = "Contacts data from: " + filename, relief = RIDGE)
	contactstitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# tree
	# Column type: G for groups, C for contacts
	contactstree = ttk.Treeview(contactswindow, columns=("name", "type"),
	    displaycolumns=("name"))
	
	contactstree.heading("#0", text="ID", anchor='w')
	contactstree.heading("name", text="Name", anchor='w')
	
	contactstree.column("#0", width=80)
	contactstree.column("name", width=250)
	
	contactstree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(contactswindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	# destroy window when closed
	contactswindow.protocol("WM_DELETE_WINDOW", contactswindow.destroy)
	
	# populating tree with Contact names
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 

	# all contacts
	allnode = contactstree.insert('', 'end', text="", values=("All Contacts", "G"))
	query = "SELECT ROWID, First, Last, Organization FROM ABPerson"
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
		
		contactstree.insert(allnode, 'end', text=personid, 
			values=(cleanSpace(name), "C"))	
	
	# groups contacts
	query = "SELECT ROWID, Name FROM ABGroup"
	tempcur.execute(query)
	groups = tempcur.fetchall()
	
	for group in groups:
		groupid = group[0]
		name = group[1]
		groupnode = contactstree.insert('', 'end', text=groupid, values=(cleanSpace(name), "G"))

		query = "SELECT ABPerson.ROWID, First, Last, Organization FROM ABGroupMembers INNER JOIN ABPerson ON ABGroupMembers.member_id = ABPerson.ROWID WHERE ABGroupMembers.group_id = \"%s\""%groupid
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
				
			contactstree.insert(groupnode, 'end', text=personid, 
				values=(cleanSpace(name), "C"))

	tempdb.close()
	contactstree.bind("<ButtonRelease-1>", OnClick)