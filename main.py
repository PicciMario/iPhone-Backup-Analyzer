#!/usr/bin/env python

'''
 Analyzer for iPhone backup made by Apple iTunes

 (C)opyright 2010 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence
 
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

'''

# GENERIC IMPORTS --------------------------------------------------------------------------------------

# sqlite3 support library
import sqlite3
# system libraries
import sys, os
# graphic libraries
from Tkinter import *
import Tkinter, ttk
import tkFileDialog, tkMessageBox
# datetime used to convert unix timestamps
from datetime import datetime
# hashlib used to build md5s of files
import hashlib
# binascci used to try to convert binary data in ASCII
import binascii
# getopt used to parse command line options
import getopt

from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import StringIO	

# APPLICATION FILES IMPORTS -------------------------------------------------------------------------

# magic.py - identify file type using magic numbers
import magic
# mbdbdecoding.py - functions to decode iPhone backup manifest files
import mbdbdecoding
# decodeManifestPlist.py - functions to decode Manifest.plist file
import decodeManifestPlist

# GLOBALS -------------------------------------------------------------------------------------------

# set this path from command line
backup_path = "Backup2/" 

# saves references to images in textarea
# (to keep them alive after callback end)
photoImages = []

# FUNCTIONS -------------------------------------------------------------------------------------------

def substWith(text, subst = "-"):
	if (len(text) == 0):
		return subst
	else:
		return text

def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)
	
def md5(md5fileName, excludeLine="", includeLine=""):
	"""Compute md5 hash of the specified file"""
	m = hashlib.md5()
	try:
		fd = open(md5fileName,"rb")
	except IOError:
		return "<none>"
	content = fd.readlines()
	fd.close()
	for eachLine in content:
		if excludeLine and eachLine.startswith(excludeLine):
			continue
		m.update(eachLine)
	m.update(includeLine)
	return m.hexdigest()

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(src, length=8, limit=10000):
	N=0; result=''
	while src:
		s,src = src[:length],src[length:]
		hexa = ' '.join(["%02X"%ord(x) for x in s])
		s = s.translate(FILTER)
		result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
		N+=length
		if (len(result) > limit):
			src = "";
	return result

def hex2string(src, length=8):
	N=0; result=''
	while src:
		s,src = src[:length],src[length:]
		hexa = ' '.join(["%02X"%ord(x) for x in s])
		s = s.translate(FILTER)
		N+=length
		result += s
	return result	

def hex2nums(src, length=8):
    N=0; result=''
    while src:
       s,src = src[:length],src[length:]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       N+=length
       result += (hexa + " ")
    return result
    
def log(text):
	logbox.insert(END, "\n%s"%text)
	logbox.yview(END)
	
# Called when a button is clicked in the buttonbox (upper right) -----------------------------------------

# search function globals
pattern = ""
searchindex = "1.0"

def buttonBoxPress(event):		
	
	# SEARCH button
	if (event.widget['text'] == "Search"):
		
		global pattern
		global searchindex
		
		if (pattern != searchbox.get(1.0, END).strip() or searchindex == ""):
			searchindex = "1.0";
		
		pattern = searchbox.get("1.0", END).strip()
		if (len(str(pattern)) == 0): return
		
		textarea.mark_set("searchLimit", textarea.index("end"))
		
		searchindex = textarea.search("%s"%pattern, "%s+1c"%(searchindex) , "searchLimit", regexp = True, nocase = True)
		if (searchindex == ""): return
		
		textarea.tag_delete("yellow")
		textarea.tag_configure("yellow",background="#FFFF00")
		textarea.tag_add("yellow", searchindex, "%s+%sc"%(searchindex, str(len(pattern))))
		
		textarea.mark_set("current", searchindex)
		textarea.yview(searchindex)
	
	elif (event.widget['text'] == "Write txt"):
		outfile = tkFileDialog.asksaveasfile(mode='w', parent=root, initialdir='/home/', title='Select output text file')
		if (outfile):
			text = textarea.get("1.0", END)
			outfile.write(text)
			tkMessageBox.showwarning("Done", "Text saved\n")
			outfile.close()
		else:
			tkMessageBox.showwarning("Error", "Text NON saved\n")

	return ""

# Called when the "convert from unix timestamp" button is clicked  ------------------------------------

def convertTimeStamp(event):
	timestamp = timebox.get("1.0", END)
	if (timestamp.strip() == ""): return
	
	try:
		timestamp = int(timestamp)
	except:
		timebox.config(background="IndianRed1")
		return
	
	timestamp = timestamp + 978307200 #JAN 1 1970
	convtimestamp = datetime.fromtimestamp(int(timestamp))
	timebox.delete("1.0", END)
	timebox.insert("1.0", convtimestamp)

def clearTimeBox(event):
	timebox.config(background="white")
	
# MAIN ----------------------------------------------------------------------------------------------------

if __name__ == '__main__':

	# input parameters
	def usage():
		print "iPBD - iPhone backup decoder."
		print " -h              : this help";
		print " -d <dir>        : backup dir (default: " + backup_path + ")";

	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd:")
	except getopt.GetoptError, err:
		print str(err)
		sys.exit(2)
	
	for o, a in opts:
		if o in ("-h"):
			usage()
			sys.exit(0)
		
		if o in ("-d"):
			backup_path = a;
			if (backup_path.strip()[-1] != "/"):
				backup_path = backup_path + "/"

	
	# decode Manifest files
	mbdb = mbdbdecoding.process_mbdb_file(backup_path + "Manifest.mbdb")
	mbdx = mbdbdecoding.process_mbdx_file(backup_path + "Manifest.mbdx")
	
	# prepares DB
	# database = sqlite3.connect('MyDatabase.db') # Create a database file
	database = sqlite3.connect(':memory:') # Create a database file in memory
	cursor = database.cursor() # Create a cursor
	cursor.execute(
		"CREATE TABLE indice (" + 
		"id INTEGER PRIMARY KEY AUTOINCREMENT," +
		"type VARCHAR(1)," +
		"permissions VARCHAR(9)," +
		"userid VARCHAR(8)," +
		"groupid VARCHAR(8)," +
		"filelen INT," +
		"mtime INT," +
		"atime INT," +
		"ctime INT," +
		"fileid VARCHAR(50)," +
		"domain_type VARCHAR(100)," +
		"domain VARCHAR(100)," +
		"file_path VARCHAR(100)," +
		"file_name VARCHAR(100)," + 
		"link_target VARCHAR(100)," + 
		"datahash VARCHAR(100)" + 
		");"
	)
	
	# count items parsed from Manifest file
	items = 0;
	
	# populates database by parsing manifest file
	for offset, fileinfo in mbdb.items():
		if offset in mbdx:
			fileinfo['fileID'] = mbdx[offset]
		else:
			fileinfo['fileID'] = "<nofileID>"
			print >> sys.stderr, "No fileID found for %s" % fileinfo_str(fileinfo)
		
		# decoding element type (symlink, file, directory)
		if (fileinfo['mode'] & 0xE000) == 0xA000: type = 'l' # symlink
		elif (fileinfo['mode'] & 0xE000) == 0x8000: type = '-' # file
		elif (fileinfo['mode'] & 0xE000) == 0x4000: type = 'd' # dir
		
		# separates domain type (AppDomain, HomeDomain, ...) from domain name
		[domaintype, sep, domain] = fileinfo['domain'].partition('-');
		
		# separates file name from file path
		[filepath, sep, filename] = fileinfo['filename'].rpartition('/')
		if (type == 'd'):
			filepath = fileinfo['filename']
			filename = "";

		# Insert record in database
		query = "INSERT INTO indice(type, permissions, userid, groupid, filelen, mtime, atime, ctime, fileid, domain_type, domain, file_path, file_name, link_target, datahash) VALUES(";
		query += "'%s'," % type
		query += "'%s'," % mbdbdecoding.modestr(fileinfo['mode']&0x0FFF)
		query += "'%08x'," % fileinfo['userid']
		query += "'%08x'," % fileinfo['groupid']
		query += "%i," % fileinfo['filelen']
		query += "%i," % fileinfo['mtime']
		query += "%i," % fileinfo['atime']
		query += "%i," % fileinfo['ctime']
		query += "'%s'," % fileinfo['fileID']
		query += "'%s'," % domaintype.replace("'", " ")
		query += "'%s'," % domain.replace("'", " ")
		query += "'%s'," % filepath.replace("'", " ")
		query += "'%s'," % filename.replace("'", " ")
		query += "'%s'," % fileinfo['linktarget']
		query += "'%s'" % hex2nums(fileinfo['datahash']).replace("'", "''")
		query += ");"
		
		#print(query)

		cursor.execute(query)
		
		items += 1;

	database.commit() 
		
	print "new items: %i" %items
	
	# Builds user interface ----------------------------------------------------------------------------------
	
	# root window
	root = Tkinter.Tk()
	root.geometry("%dx%d%+d%+d" % (1200, 700, 0, 0))
	
	# scrollbars for main tree view
	vsb = ttk.Scrollbar(orient="vertical")
	hsb = ttk.Scrollbar(orient="horizontal")
	  
	# main tree view definition
	tree = ttk.Treeview(columns=("type", "size", "id"),
	    displaycolumns=("size"), yscrollcommand=lambda f, l: autoscroll(vsb, f, l),
	    xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
 	 
	vsb['command'] = tree.yview
	hsb['command'] = tree.xview

	tree.heading("#0", text="Element description", anchor='w')
	tree.heading("size", text="File Size", anchor='w')
	#tree.heading("id", text="File ID", anchor='w')
	tree.grid(column=0, row=1, sticky='nswe')
	
	tree.grid(column=0, row=1, sticky='nswe')
	vsb.grid(column=1, row=1, sticky='ns')
	hsb.grid(column=0, row=3, sticky='ew')
	
	root.grid_columnconfigure(0, weight=1)
	root.grid_rowconfigure(1, weight=1)
	
	tree.column("#0", width=250)
	tree.column("size", width=40)
	
	# right column
	buttonbox = Frame(root, bd=2, relief=RAISED);
	
	searchbox = Text(buttonbox, width=20, height=1, relief="sunken", borderwidth=2)
	searchbox.pack()
	
	logbox = Text(root, relief="sunken", borderwidth=2, height=3, bg='lightgray')
	logbox.grid(row=4, columnspan=6, sticky='ew')
	
	w = Button(buttonbox, text="Search", width=10, default=ACTIVE)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
	
	timebox = Text(buttonbox, width=20, height=1, relief="sunken", borderwidth=2)
	timebox.pack()
	
	w = Button(buttonbox, text="Convert", width=10, default=ACTIVE)
	w.bind("<Button-1>", convertTimeStamp)
	w.pack()
	
	w = Button(buttonbox, text="Write txt", width=10, default=ACTIVE)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
		
	buttonbox.grid(column = 4, row = 1, sticky="ns", padx=5, pady=5)
	
	# header row
	headerbox = Frame(root, bd=2, relief=RAISED);
								
	im = Image.open("iphone_icon.png")
	photo = ImageTk.PhotoImage(im)	
	w = Label(headerbox, image=photo)
	w.photo = photo
	w.pack(side=LEFT)	
	
	im = Image.open("iphone_icon.png")
	photo = ImageTk.PhotoImage(im)	
	w = Label(headerbox, image=photo)
	w.photo = photo
	w.pack(side=RIGHT)
	
	w = Label(headerbox, text="iPBD - iPhone Backup Decoder\nMario Piccinelli <mario.piccinelli@gmail.com>")
	w.pack()
	
	headerbox.grid(column=0, row=0, sticky='ew', columnspan=6, padx=5, pady=5)
	
	# tables tree (in right column)
	tablestree = ttk.Treeview(buttonbox, columns=("filename", "tablename"), displaycolumns=())			
	tablestree.heading("#0", text="Tables")
	tablestree.pack(fill=BOTH, expand=1)

	# main textarea
	textarea = Text(root, width=90, yscrollcommand=lambda f, l: autoscroll(tvsb, f, l),
	    xscrollcommand=lambda f, l:autoscroll(thsb, f, l), bd=2, relief=SUNKEN)
	textarea.grid(column=2, row=1, sticky="ns")

	# scrollbars for main textarea
	tvsb = ttk.Scrollbar(orient="vertical")
	thsb = ttk.Scrollbar(orient="horizontal")
	tvsb.grid(column=3, row=1, sticky='ns')
	thsb.grid(column=2, row=3, sticky='ew')
	tvsb['command'] = textarea.yview
	thsb['command'] = textarea.xview
	
	
	# populate the main tree frame ----------------------------------------------------------------------------
	
	# standard files	
	base_files_index = tree.insert('', 'end', text="Standard files")
	tree.insert(base_files_index, 'end', text="Manifest.plist", values=("X", "", 0))
	tree.insert(base_files_index, 'end', text="Info.plist", values=("X", "", 0))
	tree.insert(base_files_index, 'end', text="Status.plist", values=("X", "", 0))
	
	cursor.execute("SELECT DISTINCT(domain_type) FROM indice");
	domain_types = cursor.fetchall()
	
	for domain_type_u in domain_types:
		domain_type = str(domain_type_u[0])
		domain_type_index = tree.insert('', 'end', text=domain_type)
		print "Extracting: %s" %domain_type
		
		query = "SELECT DISTINCT(domain) FROM indice WHERE domain_type = \"%s\" ORDER BY domain" % domain_type
		cursor.execute(query);
		domain_names = cursor.fetchall()
		
		for domain_name_u in domain_names:
			domain_name = str(domain_name_u[0])
			
			domain_name_index = tree.insert(domain_type_index, 'end', text=substWith(domain_name, "<no domain>"))
			
			query = "SELECT DISTINCT(file_path) FROM indice WHERE domain_type = \"%s\" AND domain = \"%s\" ORDER BY file_path" %(domain_type, domain_name)
			cursor.execute(query)
			paths = cursor.fetchall()
			
			for path_u in paths:
				path = str(path_u[0])
				path_index = tree.insert(domain_name_index, 'end', text=substWith(path, "/"))
				
				query = "SELECT file_name, filelen, id, type FROM indice WHERE domain_type = \"%s\" AND domain = \"%s\" AND file_path = \"%s\" ORDER BY file_name" %(domain_type, domain_name, path)
				cursor.execute(query)
				files = cursor.fetchall()
				
				for file in files:
					file_name = str(file[0])
					if (file[1]) < 1024:
						file_dim = str(file[1]) + " b"
					else:
						file_dim = str(file[1] / 1024) + " kb"
					file_id = int(file[2])
					file_type = str(file[3])
					tree.insert(path_index, 'end', text=substWith(file_name, "."), values=(file_type, file_dim, file_id))
			

	# called when an element is clicked in the tables tree frame ------------------------------------------------
	
	def TablesTreeClick(event):
	
		if (len(tablestree.selection()) == 0): return;
		
		seltable = tablestree.selection()[0]
		seltable_dbname = tablestree.set(seltable, "filename")
		seltable_tablename = tablestree.set(seltable, "tablename")
		
		# clears main text field
		textarea.delete(1.0, END)
		
		# table informations
		textarea.insert(INSERT, "Dumping table: %s\nFrom file: %s"%(seltable_tablename, seltable_dbname))
		
		if (os.path.exists(seltable_dbname)):
			seltabledb = sqlite3.connect(seltable_dbname)
			try:
				seltablecur = seltabledb.cursor() 
				
				# read selected table indexes
				seltablecur.execute("PRAGMA table_info(%s)" % seltable_tablename)
				seltable_fields = seltablecur.fetchall();
				
				# append table fields to main textares
				seltable_fieldslist = []
				textarea.insert(INSERT, "\n\nTable Fields:")
				for i in range(len(seltable_fields)):
					seltable_field = seltable_fields[i]
					textarea.insert(INSERT, "\n- ")
					textarea.insert(INSERT, "%i \"%s\" (%s)" %(seltable_field[0], seltable_field[1], seltable_field[2]))
					seltable_fieldslist.append(str(seltable_field[1]))
							
				# read all fields from selected table
				seltablecur.execute("SELECT * FROM %s" % seltable_tablename)
				seltable_cont = seltablecur.fetchall();
				
				try:
				
					# appends records to main text field
					textarea.insert(END, "\n\nTable Records:")
					
					del photoImages[:]
					
					for seltable_record in seltable_cont:

						textarea.insert(INSERT, "\n- " + str(seltable_record))
						
						#textarea.insert(END, "\nlen: %i" %len(seltable_record))
							
						for i in range(len(seltable_record)):	
						
							#import unicodedata
							try:
								value = str(seltable_record[i])
							except:
								value = seltable_record[i].encode("utf8", "replace") + " (decoded unicode)"

							#maybe an image?
							if (seltable_fieldslist[i] == "data"):
								dataMagic = magic.whatis(value)
								textarea.insert(END, "\n- Binary data: (%s)" %dataMagic)
								if (dataMagic.partition("/")[0] == "image"):			
								
									im = Image.open(StringIO.StringIO(value))
									tkim = ImageTk.PhotoImage(im)
									photoImages.append(tkim)
									textarea.insert(END, "\n ")
									textarea.image_create(END, image=tkim)
								else:
									dataMagic = magic.whatis(value)
									textarea.insert(END, "\n(format: " + dataMagic + ")")									
							else:
								try:
									textarea.insert(END, "\n- " + seltable_fieldslist[i] + " : " + value)
								except:
									dataMagic = magic.whatis(value)
									textarea.insert(END, "\n- " + seltable_fieldslist[i] + "  (" + dataMagic + ")")
						
						textarea.insert(END, "\n---------------------------------------")
				
				except:
					print "Unexpected error:", sys.exc_info()
					
				seltabledb.close()		
			except:
				print "Unexpected error:", sys.exc_info()
				seltabledb.close()

	# Called when an element is clicked in the main tree frame ---------------------------------------------------
	
	def OnClick(event):
	
		if (len(tree.selection()) == 0): return;
		
		# remove everything from tables tree
		for item in tablestree.get_children():
			tablestree.delete(item)
		
		item = tree.selection()[0]
		item_text = tree.item(item, "text")
		item_type = tree.set(item, "type")
		item_id = tree.set(item, "id")
		
		#skip "folders"
		if (item_type == ""): return;
		
		#clears textarea
		textarea.delete(1.0, END)
		
		# managing standard files
		if (item_type == "X"):	
			item_realpath = backup_path + item_text
			textarea.insert(INSERT, "Selected: " + item_realpath)
			log("Opening file %s"%item_realpath)		
			#print file content (if ASCII file) otherwise only first 50 chars
			if (os.path.exists(item_realpath)):
				if (magic.file(item_realpath) == "ASCII text"):
					fh = open(item_realpath, 'rb')
					textarea.insert(INSERT, "\n\nASCII content:\n\n")
					while 1:
						line = fh.readline()
						if not line: break;
						textarea.insert(INSERT, line)
					fh.close()	
				else:
					fh = open(item_realpath, 'rb')
					text = fh.read(30)
					textarea.insert(INSERT, "\n\nFirst 30 chars from file (string): ")
					textarea.insert(INSERT, "\n" + hex2string(text))
					fh.close()
			#if binary plist:
			if (os.path.exists(item_realpath)):	
				if (magic.file(item_realpath).partition("/")[2] == "binary_plist"):	
					manifest_tempfile = "temp01"
					os.system("plutil -convert xml1 -o temp01 " + item_realpath)
					
					textarea.insert(END, "\n\nDecoding binary Plist file:\n\n")
					
					fh = open(manifest_tempfile, 'rb')
					while 1:
						line = fh.readline()
						if not line: break;
						textarea.insert(INSERT, line)
					fh.close()				
					os.remove(manifest_tempfile)
			return

		textarea.insert(INSERT, "Selected: " + item_text + " (id " + str(item_id) + ")")
		
		query = "SELECT * FROM indice WHERE id = %s" % item_id
		cursor.execute(query)
		data = cursor.fetchone()
		
		if (len(data) == 0): return
		
		item_permissions = str(data[2])
		item_userid = str(data[3])
		item_groupid = str(data[4])
		item_mtime = str(datetime.fromtimestamp(int(data[6])))
		item_atime = str(datetime.fromtimestamp(int(data[7])))
		item_ctime = str(datetime.fromtimestamp(int(data[8])))
		item_filecode = str(data[9])
		item_link_target = str(data[14])
		item_datahash = str(data[15])
		
		textarea.insert(INSERT, "\n\nElement type: " + item_type)
		textarea.insert(INSERT, "\nPermissions: " + item_permissions)
		textarea.insert(INSERT, "\nData hash: ")
		textarea.insert(INSERT, "\n " + item_datahash)
		textarea.insert(INSERT, "\nUser id: " + item_userid)
		textarea.insert(INSERT, "\nGroup id: " + item_groupid)
		textarea.insert(INSERT, "\nLast modify time: " + item_mtime)
		textarea.insert(INSERT, "\nLast access Time: " + item_atime)
		textarea.insert(INSERT, "\nCreation time: " + item_ctime)
		textarea.insert(INSERT, "\nObfuscated file name: " + item_filecode)
		
		# treat sym links
		if (item_type == "l"):
			textarea.insert(INSERT, "\n\nThis item is a symbolic link to another file.")
			textarea.insert(INSERT, "\nLink Target: " + item_link_target)
			return
			
		# treat directories
		if (item_type == "d"):
			textarea.insert(INSERT, "\n\nThis item represents a directory.")
			return
			
		textarea.insert(INSERT, "\n\nAnalize file: ")
		
		item_realpath = backup_path + item_filecode
		
		log("Opening file %s (%s)"%(item_realpath, item_text))
		
		# print File type (from magic numbers)
		textarea.insert(INSERT, "\nFile tipe (from magic numbers): ")
		if (os.path.exists(item_realpath)):
			textarea.insert(INSERT, magic.file(item_realpath))
		else:
			textarea.insert(INSERT, "unable to analyze file")
		
		# print file MD5 hash
		textarea.insert(INSERT, "\nFile MD5 hash: ")
		textarea.insert(INSERT, md5(item_realpath))
		
		#print first 50 bytes from file (ASCII)
		if (os.path.exists(item_realpath)):
			fh = open(item_realpath, 'rb')
			text = fh.read(30)
			textarea.insert(INSERT, "\n\nFirst 30 hex bytes from file: ")
			textarea.insert(INSERT, "\n" + hex2nums(text))#binascii.b2a_uu(text))
			fh.close()
			
		#print file content (if ASCII file) otherwise only first 50 chars
		if (os.path.exists(item_realpath)):
			if (magic.file(item_realpath) == "ASCII text"):
				fh = open(item_realpath, 'rb')
				textarea.insert(INSERT, "\n\nASCII content:\n\n")
				while 1:
					line = fh.readline()
					if not line: break;
					textarea.insert(INSERT, line)
				fh.close()	
			else:
				fh = open(item_realpath, 'rb')
				text = fh.read(30)
				textarea.insert(INSERT, "\n\nFirst 30 chars from file (string): ")
				textarea.insert(INSERT, "\n" + hex2string(text))
				fh.close()						
		
		#if image file:
		if (os.path.exists(item_realpath)):	
			if (magic.file(item_realpath).partition("/")[0] == "image"):		
				im = Image.open(item_realpath)
					
				tkim = ImageTk.PhotoImage(im)
				photoImages.append(tkim)
				textarea.insert(END, "\n\nImage data: \n ")
				textarea.image_create(END, image=tkim)
				
				#decode EXIF (only JPG)
				if (magic.file(item_realpath).partition("/")[2] == "jpeg"):
					textarea.insert(END, "\n\nJPG EXIF tags:")
					exifs = im._getexif()
					for tag, value in exifs.items():
						decoded = TAGS.get(tag, tag)
						textarea.insert(END, "\nTag: %s, value: %s"%(decoded, value))
				
		#if binary plist:
		if (os.path.exists(item_realpath)):	
			if (magic.file(item_realpath).partition("/")[2] == "binary_plist"):	
				manifest_tempfile = "temp01"
				os.system("plutil -convert xml1 -o temp01 " + item_realpath)
				
				textarea.insert(END, "\n\nDecoding binary Plist file:\n\n")
				
				fh = open(manifest_tempfile, 'rb')
				while 1:
					line = fh.readline()
					if not line: break;
					textarea.insert(INSERT, line)
				fh.close()	
				
				#textarea.insert(END, decodeManifestPlist.decodeManifestPlist(manifest_tempfile))
	
				os.remove(manifest_tempfile)	
		
		#if sqlite3, print tables list
		if (os.path.exists(item_realpath)):
			tempdb = sqlite3.connect(item_realpath) 
			
			try:
				tempcur = tempdb.cursor() 
				tempcur.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
				tables_list = tempcur.fetchall();
				
				textarea.insert(INSERT, "\n\nTables in database: ")
				
				for i in tables_list:
					table_name = str(i[0])
					textarea.insert(INSERT, "\n- " + table_name);
				
					tempcur.execute("SELECT count(*) FROM %s" % table_name);
					elem_count = tempcur.fetchone()
					textarea.insert(INSERT, " (%i elements) " % int(elem_count[0]))
					
					# inserts table into tables tree
					tablestree.insert('', 'end', text=table_name, values=(item_realpath, table_name))	
					
				tempdb.close()		
				
			except:
				tempdb.close()
			
		# se "data", prova a fare il dump
		if (os.path.exists(item_realpath) and magic.file(item_realpath) == "data"):
			limit = 10000
			textarea.insert(INSERT, "\n\nDumping hex data (limit %i bytes):\n"%limit)
			content = ""
			fh = open(item_realpath, 'rb')
			while 1:
				line = fh.readline()
				if not line: break;
				content = content + line;
			fh.close()
			
			textarea.insert(INSERT, dump(content, 16, limit))

	# Main ---------------------------------------------------------------------------------------------------

	tree.bind("<ButtonRelease-1>", OnClick)
	tablestree.bind("<ButtonRelease-1>", TablesTreeClick)
	timebox.bind("<Key>", clearTimeBox)
	
	log("Welcome to the iPhone Backup browser by mario.piccinelli@gmail.com")
	log("Working directory: %s"%backup_path)

	textarea.insert(INSERT, "Welcome to the iPhone Backup browser by mario.piccinelli@gmail.com")
	textarea.insert(INSERT, "\nWorking directory: %s"%backup_path)
	textarea.insert(INSERT, "\nFound working backup for the device:\n")
	deviceinfo = decodeManifestPlist.deviceInfo(backup_path + "Info.plist")
	print deviceinfo
	for element in deviceinfo.keys():
		textarea.insert(INSERT, "\n%s - %s"%(element, deviceinfo[element]))

	root.mainloop()
	
	database.close() # Close the connection to the database
	
	