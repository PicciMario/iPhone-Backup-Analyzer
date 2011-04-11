#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

 safbookmark.py provides the code to show a TK window to browse through
 the SQLite file which holds the Safari Bookmarks in the iPhone Backup.

'''

# IMPORTS -----------------------------------------------------------------------------------------

from Tkinter import *
import sqlite3
import ttk
from datetime import datetime
import os
import webbrowser

# GLOBALS -----------------------------------------------------------------------------------------

bookmarkstree = None
textarea = None
filename = ""
namelabel = None
urllabel = None
url = ""

def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    #first, last = float(first), float(last)
    #if first <= 0 and last >= 1:
    #    sbar.grid_remove()
    #else:
    #    sbar.grid()
    sbar.set(first, last)
   
def openurl(event):
	global url
	if (len(url) == 0):
		return
	webbrowser.open_new(url)

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global bookmarkstree, textarea
	global namelabel, urllabel, url
	
	if (len(bookmarkstree.selection()) == 0): return;
	bookmark = int(bookmarkstree.set(bookmarkstree.selection(), "id"))
	
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	query = "SELECT type, title, url, num_children, editable, deletable, order_index, external_uuid FROM bookmarks WHERE id = \"%s\""%bookmark
	tempcur.execute(query)
	bookmarks = tempcur.fetchall()
	
	if (len(bookmarks) == 0):
		print("Invalid bookmark code..")
		return
		
	bookmark = bookmarks[0]
	type = bookmark[0]
	title = bookmark[1]
	newurl = bookmark[2]
	num_children = bookmark[3]
	editable = bookmark[4]
	deletable = bookmark[5]
	order_index = bookmark[6]
	external_uuid = bookmark[7]
	
	textarea.delete(1.0, END)
	
	textarea.insert(END, "Title: %s\n"%title)
	textarea.insert(END, "URL: %s\n"%newurl)

	# store url in global for the "GO" button to work with
	url = newurl

	# set title and url labels limiting length
	maxlen = 50
	if (len(title) > maxlen): title = title[0:maxlen] + "..."
	namelabel.set(title)
	if (len(newurl) > maxlen): newurl = newurl[0:maxlen] + "..."
	urllabel.set(newurl)
	
	if (type == 0):
		textarea.insert(END, "Type: simple URL\n")
	else:
		textarea.insert(END, "Type: folder\n")
	
	textarea.insert(END, "Number of children: %s\n"%num_children)
	textarea.insert(END, "Order index: %s\n"%order_index)
	
	if (editable == 1):
		textarea.insert(END, "Editable: YES\n")
	else:
		textarea.insert(END, "Editable: NO\n")

	if (deletable == 1):
		textarea.insert(END, "Deletable: YES\n")
	else:
		textarea.insert(END, "Deletable: NO\n")
	
	textarea.insert(END, "External UUID: %s"%external_uuid)

	tempdb.close()

# MAIN FUNCTION --------------------------------------------------------------------------------
	
def safbookmark_window(filenamenew):
	global filename
	global bookmarkstree, textarea
	global namelabel, urllabel, url
	
	filename = filenamenew
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for Safari Bookmarks database")
		return	
	
	# main window
	bookmarkswindow = Toplevel()
	bookmarkswindow.title('Bookmarks data')
	bookmarkswindow.focus_set()
	
	bookmarkswindow.grid_columnconfigure(2, weight=1)
	bookmarkswindow.grid_rowconfigure(1, weight=1)
	
	# header label
	bookmarkstitle = Label(bookmarkswindow, text = "Bookmarks data from: " + filename, relief = RIDGE)
	bookmarkstitle.grid(column = 0, row = 0, sticky="ew", columnspan=4, padx=5, pady=5)

	# tree
	bookmarkstree = ttk.Treeview(bookmarkswindow, columns=("id"),
	    displaycolumns=(), yscrollcommand=lambda f, l: autoscroll(mvsb, f, l))
	
	bookmarkstree.heading("#0", text="title", anchor='w')
	#bookmarkstree.heading("id", text="id", anchor='w')
	
	bookmarkstree.column("#0", width=250)
	#bookmarkstree.column("id", width=30)
	
	bookmarkstree.grid(column = 0, row = 1, sticky="ns")
	
	# center column
	centercolumn = Frame(bookmarkswindow, bd=2, relief=RAISED);
	centercolumn.grid(column=2, row=1, sticky="nswe")
	centercolumn.grid_columnconfigure(1, weight=1)
	centercolumn.grid_rowconfigure(2, weight=1)
	
	# Bookmark name
	bookmarknamefix = Label(centercolumn, text = "Title:", relief = RIDGE)
	bookmarknamefix.grid(column = 0, row = 0, sticky="ew")
	namelabel = StringVar()
	bookmarkname = Label(centercolumn, textvariable = namelabel, relief = RIDGE)
	bookmarkname.grid(column = 1, row = 0, sticky="ew", columnspan=2)
	
	# Bookmark URL
	bookmarkurlfix = Label(centercolumn, text = "URL:", relief = RIDGE)
	bookmarkurlfix.grid(column = 0, row = 1, sticky="ew")
	urllabel = StringVar()
	bookmarkurl = Label(centercolumn, textvariable = urllabel, relief = RIDGE)
	bookmarkurl.grid(column = 1, row = 1, sticky="ew")
	bookmarkbutton = Button(centercolumn, text="GO!", width=10, default=ACTIVE)
	bookmarkbutton.grid(column = 2, row = 1, sticky="ew")
	bookmarkbutton.bind("<Button-1>", openurl)

	# textarea
	textarea = Text(centercolumn, bd=2, relief=SUNKEN, yscrollcommand=lambda f, l: autoscroll(tvsb, f, l))
	textarea.grid(column = 0, row = 2, sticky="nsew", columnspan=3)

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(centercolumn, orient="vertical")
	tvsb.grid(column=3, row=2, sticky='ns')
	tvsb['command'] = textarea.yview
	
	# scrollbars for tree
	mvsb = ttk.Scrollbar(bookmarkswindow, orient="vertical")
	mvsb.grid(column=1, row=1, sticky='ns')
	mvsb['command'] = bookmarkstree.yview
		
	# footer label
	footerlabel = StringVar()
	bookmarksfooter = Label(bookmarkswindow, textvariable = footerlabel, relief = RIDGE)
	bookmarksfooter.grid(column = 0, row = 2, sticky="ew", columnspan=4, padx=5, pady=5)
	
	# destroy window when closed
	bookmarkswindow.protocol("WM_DELETE_WINDOW", bookmarkswindow.destroy)
	
	# opening database
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	
	# footer statistics
	query = "SELECT count(*) FROM bookmarks"
	tempcur.execute(query)
	bookmarksnumber = tempcur.fetchall()[0][0]
	footerlabel.set("Found %s bookmarks."%(bookmarksnumber))

	def insertBookmark(parent_node, parent_id):
		query = "SELECT id, title, num_children FROM bookmarks WHERE parent = \"%s\" ORDER BY order_index"%parent_id
		tempcur.execute(query)
		bookmarks = tempcur.fetchall()
		for bookmark in bookmarks:
			id = bookmark[0]
			title = bookmark[1]
			num_children = bookmark[2]
			newnode = bookmarkstree.insert(parent_node, 'end', text=title, values=(id))
			if (num_children != 0):
				insertBookmark(newnode, id)

	# populating tree with Safari Bookmarks
	insertBookmark('', 0)
		
	bookmarkstree.bind("<ButtonRelease-1>", OnClick)