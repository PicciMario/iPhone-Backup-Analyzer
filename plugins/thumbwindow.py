#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "Thumbnails browser"
import plugins_utils

from Tkinter import *
import ttk
from datetime import datetime
import os
import sqlite3
from PIL import Image, ImageTk

# GLOBALS -----------------------------------------------------------------------------------------

thumbstree = None
textarea = None
prevarea = None
filename = ""
photoImages = []
photoImagesList = []

def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    #first, last = float(first), float(last)
    #if first <= 0 and last >= 1:
    #    sbar.grid_remove()
    #else:
    #    sbar.grid()
    sbar.set(first, last)

def dump(src, length=8, limit=10000):
	FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
	N=0; result=''
	while src:
		s,src = src[:length],src[length:]
		hexa = ' '.join(["%02X"%ord(x) for x in s])
		s = s.translate(FILTER)
		result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
		N+=length
		if (len(result) > limit):
			src = "";
			result += "(analysis limit reached after %i bytes)"%limit
	return result

# Called when the user clicks on the main tree list -----------------------------------------------

def OnClick(event):
	global filename
	global thumbstree, textarea, prevarea
	global photoImages
	
	if (len(thumbstree.selection()) == 0): return;
	index = int(thumbstree.item(thumbstree.selection(), "text"))

	textarea.delete(1.0, END)
	
	f = open(filename, 'r')
	string = f.read()
	f.close()

	framelen_image = 120*120*2
	framelen_padding = 28
	framelen = framelen_image + framelen_padding
		
	string = string[framelen*index:framelen*(index+1)-1]
	padding = string[framelen_image + 1:]
	im = Image.frombuffer('RGB', (120, 120), string, 'raw', 'BGR;15', 0, 1)
	
	textarea.insert(END, "Extracted thumbnail\n\n")
	textarea.insert(END, "Thumbnail number %s\n"%index)
	textarea.insert(END, "Found into bytes %i - %i of the source file.\n"%(framelen*index, framelen*(index+1)-1))
	textarea.insert(END, "Length: %i bytes image + %i bytes padding\n"%(framelen_image, framelen_padding))
	textarea.insert(END, "\n")
	textarea.insert(END, "Padding data:\n")
	textarea.insert(END, "%s\n"%dump(padding))
	textarea.insert(END, "Real size image:\n")	
	textarea.insert(END, "\n")
	
	del photoImages[:]
	tkim = ImageTk.PhotoImage(im)
	photoImages.append(tkim)
	textarea.image_create(END, image=tkim)
	
	# scaled image in preview area
	prevarea.delete(1.0, END)
	im = im.resize((300,300), Image.ANTIALIAS)
	tkim2 = ImageTk.PhotoImage(im)
	photoImages.append(tkim2)
	prevarea.insert(END, "Preview:\n")	
	prevarea.insert(END, "\n")
	prevarea.image_create(END, image=tkim2)

# MAIN FUNCTION --------------------------------------------------------------------------------

def main(cursor, backup_path):
	global filename
	global thumbstree, textarea, prevarea
	global photoImagesList
	
	filename = backup_path + plugins_utils.realFileName(cursor, filename="120x120.ithmb")
	
	if (not os.path.isfile(filename)):
		print("Invalid file name for thumbnails file")
		return	
	
	# main window
	thumbswindow = Toplevel()
	thumbswindow.title('Thumbnails')
	thumbswindow.focus_set()
	
	thumbswindow.grid_columnconfigure(2, weight=1)
	thumbswindow.grid_rowconfigure(1, weight=1)
	
	# header label
	thumbstitle = Label(thumbswindow, text = "Thumbnails data from: " + filename, relief = RIDGE, width=100, height=2, wraplength=800, justify=LEFT)
	thumbstitle.grid(column = 0, row = 0, sticky="ew", columnspan=6, padx=5, pady=5)

	# tree
	thumbstree = ttk.Treeview(thumbswindow, columns=(),
	    displaycolumns=(), yscrollcommand=lambda f, l: autoscroll(mvsb, f, l))
	
	thumbstree.heading("#0", text="ID", anchor='w')
	#thumbstree.heading("pos", text="Address", anchor='w')
	
	thumbstree.column("#0", width=130)
	#thumbstree.column("pos", width=200)
	
	thumbstree.grid(column = 0, row = 1, sticky="ns", rowspan=2)

	# upper textarea
	#uppertextarea = Text(thumbswindow, bd=2, relief=SUNKEN, height=5)
	#uppertextarea.grid(column = 2, row = 1, sticky="nsew")
	
	# textarea
	textarea = Text(thumbswindow, bd=2, relief=SUNKEN, yscrollcommand=lambda f, l: autoscroll(tvsb, f, l), width=50)
	textarea.grid(column = 2, row = 1, rowspan=2, sticky="nsew")

	# preview area
	prevarea = Text(thumbswindow, bd=2, relief=SUNKEN, width=50)
	prevarea.grid(column = 5, row = 1, rowspan=2, sticky="nsew")
	
	# scrollbars for tree
	mvsb = ttk.Scrollbar(thumbswindow, orient="vertical")
	mvsb.grid(column=1, row=1, sticky='ns', rowspan=2)
	mvsb['command'] = thumbstree.yview

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(thumbswindow, orient="vertical")
	tvsb.grid(column=3, row=2, sticky='ns')
	tvsb['command'] = textarea.yview
		
	# footer label
	footerlabel = StringVar()
	thumbsfooter = Label(thumbswindow, textvariable = footerlabel, relief = RIDGE)
	thumbsfooter.grid(column = 0, row = 3, sticky="ew", columnspan=6, padx=5, pady=5)
	
	# destroy window when closed
	thumbswindow.protocol("WM_DELETE_WINDOW", thumbswindow.destroy)
	
	# populating list
	f = open(filename, 'r')
	wholefile = f.read()
	f.close()
	
	framelen = 120*120*2 + 28
	numframes = len(wholefile) / framelen
	print("Number of frames found: ", numframes)
	
	framelen_image = 120*120*2
	framelen_padding = 28
	framelen = framelen_image + framelen_padding
	
	del photoImagesList[:]
	
	for i in range(numframes) :
			
		string = wholefile[framelen*i:framelen*(i+1)-1]
		im = Image.frombuffer('RGB', (120, 120), string, 'raw', 'BGR;15', 0, 1)
		im = im.resize((15,15), Image.ANTIALIAS)
		tkim = ImageTk.PhotoImage(im)
		photoImagesList.append(tkim)
		thumbstree.insert('', 'end', text=i, image=tkim)
		
		
	thumbstree.bind("<ButtonRelease-1>", OnClick)