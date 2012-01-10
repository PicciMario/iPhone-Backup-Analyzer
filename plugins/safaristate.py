#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "Safari State"
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

safstatetree = None
textarea = None
safstatewindow = None
filename = ""
dict_nodes = []

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
	global safstatetree, textarea
	global dict_nodes
	
	if (len(safstatetree.selection()) == 0): return;
	
	dict_node_id = safstatetree.item(safstatetree.selection(), "text")
	sig_dict = None
	
	for dict_node in dict_nodes:
		number = dict_node[0]
		if (number == dict_node_id):
			sig_dict = dict_node[1]
			break
	
	if (sig_dict == None):
		print("Error while retrieving data for selected element")
		return
	
	textarea.delete(1.0, END)
	
	textarea.insert(END, "Safari tab data\n")
	textarea.insert(END, "\n")	
	
	try:
		title_string = sig_dict['SafariStateDocumentTitle'].firstChild.toxml()
	except:
		title_string = ""
	
	textarea.insert(END, "Page title: %s\n"%title_string)

	url_string = sig_dict['SafariStateDocumentURL'].firstChild.toxml()
	textarea.insert(END, "Page url: %s\n"%url_string)
	
	timestamp_val = float(sig_dict['SafariStateDocumentLastViewedTime'].firstChild.toxml())
	timestamp_val = timestamp_val + 978307200 #JAN 1 1970
	timestamp = datetime.datetime.fromtimestamp(timestamp_val)
	timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
	textarea.insert(END, "Last viewed in date: %s\n"%timestamp)	

	# parse back forward list
	backforwardlist_info = plistutils.readDict(sig_dict['SafariStateDocumentBackForwardList'])
	
	textarea.insert(END, "\n")
	textarea.insert(END, "Back/forward list data\n")
	textarea.insert(END, "Capacity: %s\n"%(backforwardlist_info['capacity'].firstChild.toxml()))
	current = int(backforwardlist_info['current'].firstChild.toxml())
	textarea.insert(END, "Current: %i\n"%(current))
	
	backforwardlist = plistutils.readArray(backforwardlist_info['entries'])
	
	actual = 0
	for backforward in backforwardlist:
		
		actual_string = ""
		if (actual == current):
			actual_string = "(CURRENT)"
	
		textarea.insert(END, "\n")
		textarea.insert(END, "****** Back/Forward list element %i %s\n"%(actual, actual_string))
		
		backforward_dict = plistutils.readDict(backforward)
		textarea.insert(END, "Title: %s\n"%(backforward_dict['title'].firstChild.toxml()))
		textarea.insert(END, "URL: %s\n"%(backforward_dict['-'].firstChild.toxml()))
		
		actual = actual + 1
				
# MAIN FUNCTION --------------------------------------------------------------------------------
	
def main(cursor, backup_path):
	global filename
	global safstatetree, textarea, safstatewindow
	global dict_nodes
	
	filename = backup_path + plugins_utils.realFileName(cursor, filename="SuspendState.plist", domaintype="HomeDomain")
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for Safari state data: %s"%filename)
		return
	
	# main window
	safstatewindow = Toplevel()
	safstatewindow.title('Safari State')
	safstatewindow.focus_set()
	
	safstatewindow.grid_columnconfigure(1, weight=1)
	safstatewindow.grid_rowconfigure(1, weight=1)
	
	# header label
	safstatetitle = Label(
		safstatewindow, 
		text = "Safari State data from: %s (%s) "%(filename, "SuspendState.plist"), 
		relief = RIDGE,
		width=100, 
		height=3, 
		wraplength=800, 
		justify=LEFT
	)
	safstatetitle.grid(column = 0, row = 0, sticky="ew", columnspan=4, padx=5, pady=5)

	# tree
	safstatetree = ttk.Treeview(
		safstatewindow, 
		columns=("active", "title", "timestamp"),
	    displaycolumns=("active", "title", "timestamp"),
		yscrollcommand=lambda f, l: autoscroll(mvsb, f, l)
	)
	
	safstatetree.heading("#0", text="", anchor='w')
	safstatetree.heading("active", text="A", anchor='w')
	safstatetree.heading("title", text="Title", anchor='w')
	safstatetree.heading("timestamp", text="Timestamp", anchor='w')
	
	safstatetree.column("#0", width=30)
	safstatetree.column("active", width=20)
	safstatetree.column("title", width=250)
	safstatetree.column("timestamp", width=160)
	
	safstatetree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(
		safstatewindow, 
		bd=2, 
		relief=SUNKEN,
		yscrollcommand=lambda f, l: autoscroll(tvsb, f, l)
	)
	textarea.grid(column = 2, row = 1, sticky="nsew")

	# scrollbars for tree
	mvsb = ttk.Scrollbar(safstatewindow, orient="vertical")
	mvsb.grid(column=1, row=1, sticky='ns')
	mvsb['command'] = safstatetree.yview

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(safstatewindow, orient="vertical")
	tvsb.grid(column=3, row=1, sticky='ns')
	tvsb['command'] = textarea.yview
	
	# footer label
	footerlabel = StringVar()
	safstatefooter = Label(safstatewindow, textvariable = footerlabel, relief = RIDGE)
	safstatefooter.grid(column = 0, row = 2, sticky="ew", columnspan=4, padx=5, pady=5)
	
	# destroy window when closed
	safstatewindow.protocol("WM_DELETE_WINDOW", safstatewindow.destroy)
	
	# convert binary plist file into plain plist file
	safstatexml = plistutils.readPlistToXml(filename)
	if (safstatexml == None):
		print("Error while parsing binary plist data")
		return
	
	# main dictionary (contains anything else)
	maindicts = safstatexml.getElementsByTagName('dict')
	if (len(maindicts) <= 0): 
		print("no main dict found in file")
		return
	maindict = maindicts[0]

	# extract SafariStateDocuments array
	maindictelements = plistutils.readDict(maindict)
	try:
		safstatedocs = maindictelements['SafariStateDocuments']
	except:
		print("No SafariStateDocuments array found in main dict")
		return
		
	active_tab = int(maindictelements['SafariStateActiveDocumentIndex'].firstChild.toxml())
	safstatedocs_array = plistutils.readArray(safstatedocs)
	
	# footer statistics
	footerlabel.set("Found %i open tabs."%(len(safstatedocs_array)))
	
	id_number = 0
	
	for safstatedoc in safstatedocs_array:
		safstatedoc_dict = plistutils.readDict(safstatedoc)

		try:
			title = safstatedoc_dict['SafariStateDocumentTitle'].firstChild.toxml()		
		except:
			title = ""
				
		timestamp_val = float(safstatedoc_dict['SafariStateDocumentLastViewedTime'].firstChild.toxml())
		timestamp_val = timestamp_val + 978307200 #JAN 1 1970
		timestamp = datetime.datetime.fromtimestamp(timestamp_val)
		timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
		
		active_status = ""
		if (active_tab == id_number):
			active_status = "*"
		
		safstatetree.insert('', 'end', text=id_number, values=(active_status, title, timestamp))
		dict_nodes.append([id_number, safstatedoc_dict])
		id_number = id_number + 1
		
	safstatetree.bind("<ButtonRelease-1>", OnClick)
