#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence

'''

# IMPORTS -----------------------------------------------------------------------------------------

PLUGIN_NAME = "Thumbnails browser 120x120"
import plugins_utils

from Tkinter import *
import ttk
from datetime import datetime
import os
import sqlite3
from PIL import Image, ImageTk

# GLOBALS -----------------------------------------------------------------------------------------

thumbs_filename = "120x120.ithmb"

frame_width = 120
frame_height = 120

framelen_image = frame_width * frame_height *2
framelen_padding = 28

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
	global frame_width, frame_height
	global framelen_image, framelen_padding, thumbs_filename
	global frame_width, frame_height
	
	if (len(thumbstree.selection()) == 0): return;
	index = int(thumbstree.item(thumbstree.selection(), "text"))

	textarea.delete(1.0, END)
	
	f = open(filename, 'r')
	string = f.read()
	f.close()

	framelen = framelen_image + framelen_padding
		
	string = string[framelen*index:framelen*(index+1)-1]
	padding = string[framelen_image + 1:]
	im = Image.frombuffer('RGB', (frame_width, frame_height), string, 'raw', 'BGR;15', 0, 1)
	
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
	global framelen_image, framelen_padding, thumbs_filename
	
	filename = backup_path + plugins_utils.realFileName(cursor, filename=thumbs_filename)
	
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
	thumbstitle = Label(thumbswindow, text = "Thumbnails data from: %s (%s)"%(filename, thumbs_filename), relief = RIDGE, width=100, height=2, wraplength=800, justify=LEFT)
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
	textarea = Text(thumbswindow, bd=2, relief=SUNKEN, yscrollcommand=lambda f, l: autoscroll(tvsb, f, l), width=60)
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
	
	framelen = framelen_image + framelen_padding
	
	numframes = len(wholefile) / framelen
	#print("Number of frames found: ", numframes)
	
	del photoImagesList[:]
	
	for i in range(numframes) :
			
		string = wholefile[framelen*i:framelen*(i+1)-1]
		im = Image.frombuffer('RGB', (frame_width, frame_height), string, 'raw', 'BGR;15', 0, 1)
		im = im.resize((15,15), Image.ANTIALIAS)
		tkim = ImageTk.PhotoImage(im)
		photoImagesList.append(tkim)
		thumbstree.insert('', 'end', text=i, image=tkim)

	textarea.insert(END, "Thumbnail file viewer\n")
	textarea.insert(END, "\n")
	textarea.insert(END, "Thumbnail file name: %s\n"%thumbs_filename)
	textarea.insert(END, "Thumbnail file real name: %s\n"%filename)
	textarea.insert(END, "\n")
	textarea.insert(END, "Thumbnail width: %i\n"%frame_width)
	textarea.insert(END, "Thumbnail height: %i\n"%frame_height)
	textarea.insert(END, "Thumbnail size in bytes: %i + %i padding for each\n"%(frame_width * frame_height *2
, framelen_padding))

	thumbstree.bind("<ButtonRelease-1>", OnClick)