#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "YouTube Browser"
import plugins_utils

from Tkinter import *
#import sqlite3
import ttk
#from datetime import datetime
import os
from string import *
#from PIL import Image, ImageTk
import StringIO
#import getopt
import urllib
import xml.dom.minidom
import webbrowser

# GLOBALS -----------------------------------------------------------------------------------------

youtubetree = None
textarea = None
youtubewindow = None
filename = ""

bookmarksArray = None
historyArray = None
lastSearch = None	
lastViewedVideo = None

url_counter = 0

# saves references to images in textarea
# (to keep them alive after callback end)
photoImages = []

def cleanSpace(string):
	if (isinstance(string, str)): string = string.replace(' ', '\ ')
	return string
	
def printYoutubeData(code, textarea):
	
	#textarea.insert(END, "Retrieving video info from YouTube Server...\n\n")
	
	try:
		# retrieving data from youtube server
		url = "http://gdata.youtube.com/feeds/api/videos/" + code
		videodata = xml.dom.minidom.parse(urllib.urlopen(url))
		
		# entry (main element)
		entry = videodata.getElementsByTagName('entry')
		if (len(entry) <= 0): 
			print("no entry top element found in file")
			return
		entry = entry[0]
		
		# print video data
		tags_to_find = [
			['title', 'Video title'],
			['content', 'Video description'],
		]
		
		for tag in tags_to_find:
			tag_name = tag[0]
			tag_desc = tag[1]
			
			element = videodata.getElementsByTagName(tag_name)
			if (len(element) <= 0): 
				continue
			element = element[0].firstChild
			if (element != None):
				element = element.toxml()
			else:
				element = ""
			
			textarea.insert(END, "%s: %s\n"%(tag_desc, element))
			
		textarea.insert(END, "\n(Video data retrieved online from YouTube server.)")
	
	except xml.parsers.expat.ExpatError:
		textarea.insert(END, "Unable to retrieve video data from YouTube server. Probably the video has been removed from YouTube.")
	except:
		textarea.insert(END, "Unable to retrieve video data from YouTube server. Check your internet connection.")
		print "Unexpected error:", sys.exc_info()


def insert_url(url):
	global textarea
	global url_counter
	
	url_counter += 1
	tag = 'url' + str(url_counter)

	textarea.insert(END, url, ('dynamic_link', tag))
	textarea.tag_bind(tag, '<1>', lambda event: webbrowser.open(url))

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global youtubetree, textarea
	global photoImages
	global bookmarksArray, historyArray, lastSearch, lastViewedVideo
	global url_counter
	
	if (len(youtubetree.selection()) == 0): return;
	
	code = youtubetree.set(youtubetree.selection(), "code")
	
	textarea.delete(1.0, END)
	url_counter = 0
	
	if (code == "H"):
		textarea.insert(END, "YouTube History Data\n\n")
		textarea.insert(END, "%i elements found in archive."%len(historyArray))
	elif (code == "B"):
		textarea.insert(END, "YouTube Bookmarks Data\n\n")
		textarea.insert(END, "%i elements found in archive."%len(bookmarksArray))
	elif (code == "L"):
		textarea.insert(END, "YouTube Data about last use\n\n")
		textarea.insert(END, "Last search term: \"%s\"\n"%lastSearch)
		textarea.insert(END, "Last video viewed: \"%s\"\n"%lastViewedVideo)
		
		url = "http://www.youtube.com/watch?v=" + lastViewedVideo
		insert_url(url)
		
		textarea.insert(END, "\n\n")
		printYoutubeData(lastViewedVideo, textarea)
	
	else:
		textarea.insert(END, "YouTube Video Data\n\n")
		textarea.insert(END, "video code: %s\n"%code)
		
		url = "http://www.youtube.com/watch?v=" + code
		insert_url(url)
		
		textarea.insert(END, "\n\n")
		printYoutubeData(code, textarea)
		
# MAIN FUNCTION --------------------------------------------------------------------------------
	
def main(cursor, backup_path):
	global filename
	global youtubetree, textarea, youtubewindow
	global bookmarksArray, historyArray, lastSearch, lastViewedVideo
	
	filename = backup_path + plugins_utils.realFileName(cursor, filename="com.apple.youtube.dp.plist", domaintype="HomeDomain")
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for Contacts database: %s"%filename)
		return
	
	# main window
	youtubewindow = Toplevel()
	youtubewindow.title('YouTube data')
	youtubewindow.focus_set()
	
	youtubewindow.grid_columnconfigure(1, weight=1)
	youtubewindow.grid_rowconfigure(1, weight=1)
	
	# header label
	youtubetitle = Label(youtubewindow, text = "YouTube data from: " + filename, relief = RIDGE)
	youtubetitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# tree
	# Column type: G for groups, C for contacts
	youtubetree = ttk.Treeview(youtubewindow, columns=("name", "code"),
	    displaycolumns=("name"))
	
	youtubetree.heading("#0", text="", anchor='w')
	youtubetree.heading("name", text="Name", anchor='w')
	
	youtubetree.column("#0", width=20)
	youtubetree.column("name", width=200)
	
	youtubetree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(youtubewindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	textarea.tag_configure('dynamic_link',
		foreground="blue",
		underline=True)
	textarea.tag_bind('dynamic_link', '<Enter>',
		lambda event: textarea.configure(cursor='hand2'))
	textarea.tag_bind('dynamic_link', '<Leave>',
		lambda event: textarea.configure(cursor='arrow'))
	
	# footer label
	footerlabel = StringVar()
	youtubefooter = Label(youtubewindow, textvariable = footerlabel, relief = RIDGE)
	youtubefooter.grid(column = 0, row = 2, sticky="ew", columnspan=2, padx=5, pady=5)
	
	# destroy window when closed
	youtubewindow.protocol("WM_DELETE_WINDOW", youtubewindow.destroy)
	
	# reading plist
	from xml.dom.minidom import parse
	try:
		xmldata = parse(filename)
	except:
		print "Unexpected error while parsing XML data:", sys.exc_info()[1]
		return None
	
	# main dictionary (contains anything else)
	maindicts = xmldata.getElementsByTagName('dict')
	if (len(maindicts) <= 0): 
		print("no main dict found in file")
		return
	maindict = maindicts[0]
	
	# read data from main dict 
	outerDict = plugins_utils.readDict(maindict)
	bookmarksArray = plugins_utils.readArray(outerDict['Bookmarks'])
	historyArray = plugins_utils.readArray(outerDict['History'])
	lastSearch = outerDict['lastSearch'].firstChild.toxml()
	lastViewedVideo = outerDict['lastViewedVideo'].firstChild.toxml()
	
	# footer statistics
	footerlabel.set("Found %i history elements and %i bookmarks."%(len(historyArray), len(bookmarksArray)))
	
	# populating tree

	youtubetree.insert('', 'end', text="", values=("Last use data", "L"))

	# bookmarks in the main tree
	bookmarksnode = youtubetree.insert('', 'end', text="", values=("Bookmarks", "B"))
	for element in bookmarksArray:
		element_string = element.firstChild.toxml()
		youtubetree.insert(bookmarksnode, 'end', text="", 
			values=(element_string, element_string))	

	# history in the main tree
	historynode = youtubetree.insert('', 'end', text="", values=("History", "H"))
	for element in historyArray:
		element_string = element.firstChild.toxml()
		youtubetree.insert(historynode, 'end', text="", 
			values=(element_string, element_string))	
	
	youtubetree.bind("<ButtonRelease-1>", OnClick)
