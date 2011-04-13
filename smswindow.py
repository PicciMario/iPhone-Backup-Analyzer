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

def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    #first, last = float(first), float(last)
    #if first <= 0 and last >= 1:
    #    sbar.grid_remove()
    #else:
    #    sbar.grid()
    sbar.set(first, last)

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
	
	smswindow.grid_columnconfigure(2, weight=1)
	smswindow.grid_rowconfigure(1, weight=1)
	
	# header label
	smstitle = Label(smswindow, text = "SMS data from: " + filename, relief = RIDGE)
	smstitle.grid(column = 0, row = 0, sticky="ew", columnspan=4, padx=5, pady=5)

	# tree
	groupstree = ttk.Treeview(smswindow, columns=("address"),
	    displaycolumns=("address"), yscrollcommand=lambda f, l: autoscroll(mvsb, f, l))
	
	groupstree.heading("#0", text="ID", anchor='w')
	groupstree.heading("address", text="Address", anchor='w')
	
	groupstree.column("#0", width=30)
	groupstree.column("address", width=200)
	
	groupstree.grid(column = 0, row = 1, sticky="ns", rowspan=2)

	# upper textarea
	uppertextarea = Text(smswindow, bd=2, relief=SUNKEN, height=5)
	uppertextarea.grid(column = 2, row = 1, sticky="nsew")
	
	# textarea
	textarea = Text(smswindow, bd=2, relief=SUNKEN, yscrollcommand=lambda f, l: autoscroll(tvsb, f, l))
	textarea.grid(column = 2, row = 2, sticky="nsew")

	# scrollbars for tree
	mvsb = ttk.Scrollbar(smswindow, orient="vertical")
	mvsb.grid(column=1, row=1, sticky='ns')
	mvsb['command'] = groupstree.yview

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(smswindow, orient="vertical")
	tvsb.grid(column=3, row=2, sticky='ns')
	tvsb['command'] = textarea.yview
		
	# footer label
	footerlabel = StringVar()
	smsfooter = Label(smswindow, textvariable = footerlabel, relief = RIDGE)
	smsfooter.grid(column = 0, row = 3, sticky="ew", columnspan=4, padx=5, pady=5)
	
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
	
	# uppertextarea statistics
	def readKey(key):
		query = "SELECT value FROM _SqliteDatabaseProperties WHERE key = \"%s\""%key
		tempcur.execute(query)
		data = tempcur.fetchall()
		if (len(data) > 0):
			value = data[0][0]
		else:
			value = 0
		return value
	
	uppertextarea.insert(END, "Incoming messages (after last reset): %s\n"%(readKey("counter_in_all")))	
	uppertextarea.insert(END, "Lifetime incoming messages: %s\n"%(readKey("counter_in_lifetime")))
	uppertextarea.insert(END, "Outgoing messages (after last reset): %s\n"%(readKey("counter_out_all")))
	uppertextarea.insert(END, "Lifetime outgoing messages: %s\n"%(readKey("counter_out_lifetime")))
	uppertextarea.insert(END, "Counter last reset: %s\n"%(readKey("counter_last_reset")))
	
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