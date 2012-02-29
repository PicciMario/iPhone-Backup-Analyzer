#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

 callhistory.py provides the code to show a TK window to browse through
 the SQLite file which holds the call history data in the iPhone Backup.

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "Call History"
import plugins_utils

from Tkinter import *
import sqlite3
import ttk
from datetime import datetime
import os

# GLOBALS -----------------------------------------------------------------------------------------

callstree = None
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

# MAIN FUNCTION --------------------------------------------------------------------------------
	
def main(cursor, backup_path):
	global filename
	global callstree, textarea
	
	filename = os.path.join(backup_path, plugins_utils.realFileName(cursor, filename="call_history.db", domaintype="WirelessDomain"))
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for SMS database")
		return	
	
	# main window
	callswindow = Toplevel()
	callswindow.title('Call History data')
	callswindow.focus_set()
	
	callswindow.grid_columnconfigure(2, weight=1)
	callswindow.grid_rowconfigure(1, weight=1)
	
	# header label
	callstitle = Label(callswindow, text = "Calls history data from: " + filename, relief = RIDGE)
	callstitle.grid(column = 0, row = 0, sticky="ew", columnspan=4, padx=5, pady=5)

	# tree
	callstree = ttk.Treeview(callswindow, columns=("address", "date", "duration", "flags", "id", "name", "countrycode"),
	    displaycolumns=("address", "date", "duration", "flags"), yscrollcommand=lambda f, l: autoscroll(mvsb, f, l))
	
	callstree.heading("#0", text="ID", anchor='w')
	callstree.heading("date", text="Date", anchor='w')
	callstree.heading("address", text="Address", anchor='w')
	callstree.heading("duration", text="Duration", anchor='w')
	callstree.heading("flags", text="Flags", anchor='w')
	
	callstree.column("#0", width=50)
	callstree.column("date", width=200)	
	callstree.column("address", width=150)
	callstree.column("duration", width=100)
	callstree.column("flags", width=100)
	
	callstree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(callswindow, bd=2, relief=SUNKEN, width=50, 
		yscrollcommand=lambda f, l: autoscroll(tvsb, f, l))
	textarea.grid(column = 2, row = 1, sticky="nsew")

	# scrollbars for tree
	mvsb = ttk.Scrollbar(callswindow, orient="vertical")
	mvsb.grid(column=1, row=1, sticky='ns')
	mvsb['command'] = callstree.yview

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(callswindow, orient="vertical")
	tvsb.grid(column=3, row=1, sticky='ns')
	tvsb['command'] = textarea.yview
		
	# footer label
	footerlabel = StringVar()
	callsfooter = Label(callswindow, textvariable = footerlabel, relief = RIDGE)
	callsfooter.grid(column = 0, row = 2, sticky="ew", columnspan=4, padx=5, pady=5)
	
	# destroy window when closed
	callswindow.protocol("WM_DELETE_WINDOW", callswindow.destroy)
	
	# opening database
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	
	# footer statistics
	query = "SELECT count(ROWID) FROM call"
	tempcur.execute(query)
	callsnumber = tempcur.fetchall()[0][0]
	footerlabel.set("Found %s calls."%callsnumber)
	
	def readKey(key):
		query = "SELECT value FROM _SqliteDatabaseProperties WHERE key = \"%s\""%key
		tempcur.execute(query)
		data = tempcur.fetchall()
		if (len(data) > 0):
			value = data[0][0]
		else:
			value = 0
		return value
	
	def formatTime(seconds):
		durationtot = int(seconds)
		durationmin = int(durationtot / 60)
		durationhh = int(durationmin / 60)
		durationmin = durationmin - (durationhh * 60)
		durationsec = durationtot - (durationmin * 60) - (durationhh * 3600)
		duration = "%i:%.2i:%.2i"%(durationhh, durationmin, durationsec)	
		return duration
	
	# populating textarea with data from _SqliteDatabaseProperties
	textarea.insert(END, "Call history limit: %s\n"%(readKey("call_history_limit")))
	textarea.insert(END, "Last call duration: %s\n"%(formatTime(readKey("timer_last"))))
	textarea.insert(END, "Incoming calls duration: %s\n"%(formatTime(readKey("timer_incoming"))))
	textarea.insert(END, "Outgoing calls duration: %s\n"%(formatTime(readKey("timer_outgoing"))))
	textarea.insert(END, "Total call duration: %s\n"%(formatTime(readKey("timer_all"))))
	textarea.insert(END, "Total lifetime call duration: %s\n"%(formatTime(readKey("timer_lifetime"))))

	# populating tree with calls
	query = "SELECT ROWID, address, date, duration, flags, id, name, country_code FROM call ORDER BY date"
	tempcur.execute(query)
	calls = tempcur.fetchall()
	tempdb.close()
	
	for call in calls:
		rowid = call[0]
		address = call[1]
		date = datetime.fromtimestamp(int(call[2]))
		duration = formatTime(call[3])
		
		flagval = call[4]
		if (flagval == 5): flags = "Outgoing"
		elif (flagval == 4): flags = "Incoming"
		else: flags = "Cancelled"
		
		id = call[5]
		name = call[6]
		country_code = call[7]
		callstree.insert('', 'end', text=rowid, values=(address, date, duration, flags))