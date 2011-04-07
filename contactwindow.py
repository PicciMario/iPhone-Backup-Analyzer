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

# GLOBALS -----------------------------------------------------------------------------------------

contactstree = None
textarea = None
filename = ""

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global contactstree, textarea
	if (len(contactstree.selection()) == 0): return;
	msg_group = int(contactstree.item(contactstree.selection(), "text"))
	
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	query = "SELECT text, date, flags, message.ROWID FROM message INNER JOIN msg_group ON msg_group.rowid = message.group_id WHERE msg_group.rowid = %i ORDER BY date "%msg_group
	tempcur.execute(query)
	messages = tempcur.fetchall()
	
	textarea.delete(1.0, END)
	
	curday = 0
	curmonth = 0
	curyear = 0
	
	for message in messages:
		text = message[0]
		date = int(message[1])
		flag = int(message[2])
		messageid = int(message[3])
		
		convdate = datetime.fromtimestamp(int(date))
		newday = convdate.day
		newmonth = convdate.month
		newyear = convdate.year
		
		# checks whether the day is the same from the last message
		changeday = 0
		if (curday != newday) or (curmonth != newmonth) or (curyear != newyear): 
			changeday = 1
			curday = newday
			curmonth = newmonth
			curyear = newyear
			
		# if day changed print a separator with date	
		if (changeday == 1):
			textarea.insert(END, "\n******** %s ********\n"%convdate.date())
		else:
			textarea.insert(END, "-------\n")
		
		# tests the field "flag" whether the message was sent or received		
		if (flag == 2):
			status = "Received"
		else:
			status = "Sent"
		
		# prints message date and text
		textarea.insert(END, "%s in date: %s\n"%(status,convdate))
		textarea.insert(END, "%s\n"%text)
		
		# other message parts (from table message_id)
		query = "SELECT part_id, content_type, content_loc FROM msg_pieces "
		query = query + "WHERE message_id = %i ORDER BY part_id "%messageid
		tempcur.execute(query)
		attachments = tempcur.fetchall()
		
		# prints attachments under the message text
		for attachment in attachments:
			part_id = attachment[0]
			content_type = attachment[1]
			content_loc = attachment[2]
			textarea.insert(END, "-> %i - %s (%s)\n"%(part_id, content_type, content_loc))

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
	contactstree = ttk.Treeview(contactswindow, columns=("first", "last"),
	    displaycolumns=("first", "last"))
	
	contactstree.heading("#0", text="ID", anchor='w')
	contactstree.heading("first", text="First", anchor='w')
	contactstree.heading("last", text="Last", anchor='w')
	
	contactstree.column("#0", width=30)
	contactstree.column("first", width=150)
	contactstree.column("last", width=150)
	
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
	allnode = contactstree.insert('', 'end', text="", values=("All Contacts", ""))
	query = "SELECT ROWID, First, Last FROM ABPerson"
	tempcur.execute(query)
	people = tempcur.fetchall()
	for person in people:
		personid = person[0]
		personfirst = person[1]
		personlast = person[2]
		contactstree.insert(allnode, 'end', text=personid, values=(personfirst, personlast))	
	
	# groups contacts
	query = "SELECT ROWID, Name FROM ABGroup"
	tempcur.execute(query)
	groups = tempcur.fetchall()
	
	for group in groups:
		groupid = group[0]
		name = group[1]
		groupnode = contactstree.insert('', 'end', text=groupid, values=(name, ""))

		query = "SELECT ROWID, First, Last FROM ABGroupMembers INNER JOIN ABPerson ON ABGroupMembers.member_id = ABPerson.ROWID WHERE ABGroupMembers.group_id = \"%s\""%groupid
		tempcur.execute(query)
		people = tempcur.fetchall()
		
		for person in people:
			personid = person[0]
			personfirst = person[1]
			personlast = person[2]
			contactstree.insert(groupnode, 'end', text=personid, values=(personfirst, personlast))


	tempdb.close()
	contactstree.bind("<ButtonRelease-1>", OnClick)