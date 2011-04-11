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
from PIL import Image, ImageTk
import StringIO
import getopt

# GLOBALS -----------------------------------------------------------------------------------------

contactstree = None
textarea = None
contactswindow = None
filename = ""
thumbsfilename = ""

# saves references to images in textarea
# (to keep them alive after callback end)
photoImages = []

def cleanSpace(string):
	if (isinstance(string, str)): string = string.replace(' ', '\ ')
	return string

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename, thumbsfilename
	global contactstree, textarea
	global photoImages
	
	if (len(contactstree.selection()) == 0): return;
	
	# check whether the selection is a group or a contact
	type = contactstree.set(contactstree.selection(), "type")
	if (type == "G"): return
	
	user_id = int(contactstree.item(contactstree.selection(), "text"))
	
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
		
	# print thumbnail (if thumbnail file selected)
	if (thumbsfilename != None):
		thumbdb = sqlite3.connect(thumbsfilename)
		thumbcur = thumbdb.cursor() 
		
		query = "SELECT data FROM ABThumbnailImage WHERE record_id = %s"%user_id
		thumbcur.execute(query)
		queryresult = thumbcur.fetchall()
		
		if (len(queryresult) > 0 ):
			imagedata = queryresult[0][0]
			im = Image.open(StringIO.StringIO(imagedata))
			tkim = ImageTk.PhotoImage(im)
			del photoImages[:]
			photoImages.append(tkim)
			textarea.insert(END,"\n")
			textarea.image_create(END, image=tkim)		
		
		thumbdb.close()
	
	# free database file
	tempdb.close()

# MAIN FUNCTION --------------------------------------------------------------------------------
	
def contact_window(filenamenew, thumbsfilenamenew = None):
	global filename, thumbsfilename
	global contactstree, textarea, contactswindow
	filename = filenamenew
	thumbsfilename = thumbsfilenamenew
	
	#print("Filename: %s"%filename)
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for Contacts database: %s"%filename)
		return
	
	if (thumbsfilename != None):
		if (not os.path.isfile(thumbsfilename)):
			print("Invalid file name for Contacts Thumbnails database: %s"%thumbsfilename)
			return	
	
	# main window
	contactswindow = Toplevel()
	contactswindow.title('SMS data')
	contactswindow.focus_set()
	
	contactswindow.grid_columnconfigure(1, weight=1)
	contactswindow.grid_rowconfigure(1, weight=1)
	
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
	
	# footer label
	footerlabel = StringVar()
	contactsfooter = Label(contactswindow, textvariable = footerlabel, relief = RIDGE)
	contactsfooter.grid(column = 0, row = 2, sticky="ew", columnspan=2, padx=5, pady=5)
	
	# destroy window when closed
	contactswindow.protocol("WM_DELETE_WINDOW", contactswindow.destroy)
	
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
	allnode = contactstree.insert('', 'end', text="", values=("All Contacts", "G"))
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
				
			contactstree.insert(groupnode, 'end', text=personid, 
				values=(cleanSpace(name), "C"))

	tempdb.close()
	contactstree.bind("<ButtonRelease-1>", OnClick)

# STANDALONE FUNCTION ---------------------------------------------------------------------------

if __name__ == '__main__':
	# input parameters
	def usage():
		print("iPhone Backup Decoder - Contacts window.")
		print(" -h              : this help")
		print(" -f <filename>   : filename")

	try:
		opts, args = getopt.getopt(sys.argv[1:], "hf:")
	except getopt.GetoptError as err:
		print(str(err))
		sys.exit(2)
	
	file = ""
	
	for o, a in opts:
		if o in ("-h"):
			usage()
			sys.exit(0)
		if o in ("-f"):
			file = a
	
	if (len(file) == 0):
		usage()
		sys.exit(0)
	else:
		contact_window(file)
		contactswindow.mainloop()
