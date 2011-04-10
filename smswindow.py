#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

 smswindow.py provides the code to show a TK window to browse through
 the SQLite file which holds the SMS data in the iPhone Backup.

'''

# IMPORTS -----------------------------------------------------------------------------------------

from Tkinter import *
import sqlite3
import ttk
from datetime import datetime
import os

# GLOBALS -----------------------------------------------------------------------------------------

groupstree = None
textarea = None
filename = ""

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global groupstree, textarea
	if (len(groupstree.selection()) == 0): return;
	msg_group = int(groupstree.item(groupstree.selection(), "text"))
	
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
	
def sms_window(filenamenew):
	global filename
	global groupstree, textarea
	filename = filenamenew
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for SMS database")
		return	
	
	# main window
	smswindow = Toplevel()
	smswindow.title('SMS data')
	smswindow.focus_set()
	
	# header label
	smstitle = Label(smswindow, text = "SMS data from: " + filename, relief = RIDGE)
	smstitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# tree
	groupstree = ttk.Treeview(smswindow, columns=("address"),
	    displaycolumns=("address"))
	
	groupstree.heading("#0", text="ID", anchor='w')
	groupstree.heading("address", text="Address", anchor='w')
	
	groupstree.column("#0", width=30)
	groupstree.column("address", width=200)
	
	groupstree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(smswindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	# footer label
	footerlabel = StringVar()
	smsfooter = Label(smswindow, textvariable = footerlabel, relief = RIDGE)
	smsfooter.grid(column = 0, row = 2, sticky="ew", columnspan=2, padx=5, pady=5)
	
	# destroy window when closed
	smswindow.protocol("WM_DELETE_WINDOW", smswindow.destroy)
	
	# opening database
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	
	# footer statistics
	query = "SELECT count(ROWID) FROM msg_group"
	tempcur.execute(query)
	groupsnumber = tempcur.fetchall()[0][0]
	query = "SELECT count(ROWID) FROM message"
	tempcur.execute(query)
	smsnumber = tempcur.fetchall()[0][0]
	footerlabel.set("Found %s messages in %s groups."%(smsnumber, groupsnumber))

	# populating tree with SMS groups
	query = "SELECT DISTINCT(msg_group.rowid), address FROM msg_group INNER JOIN group_member ON msg_group.rowid = group_member.group_id"
	tempcur.execute(query)
	groups = tempcur.fetchall()
	tempdb.close()
	
	for group in groups:
		groupid = group[0]
		address = group[1].replace(' ', '')
		groupstree.insert('', 'end', text=groupid, values=(address))
		
	groupstree.bind("<ButtonRelease-1>", OnClick)