#!/usr/bin/env python
import sys, sqlite3, Tkinter, ttk, glob, os
from Tkinter import *
from datetime import datetime
import hashlib
import binascii

# magic.py - identify file type using magic numbers
import magic

# mbdbdecoding.py - functions to decode iPhone backup manifest files
import mbdbdecoding

# **** TODO: option to set this path from command line
backup_path = "Backup/" 

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
	
def buttonBoxPress(event):
	print event.widget
	return "";

if __name__ == '__main__':
	mbdb = mbdbdecoding.process_mbdb_file(backup_path + "Manifest.mbdb")
	mbdx = mbdbdecoding.process_mbdx_file(backup_path + "Manifest.mbdx")
	
	# prepares DB
	#database = sqlite3.connect('MyDatabase.db') # Create a database file
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
		"file_name VARCHAR(100)"
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
		query = "INSERT INTO indice(type, permissions, userid, groupid, filelen, mtime, atime, ctime, fileid, domain_type, domain, file_path, file_name) VALUES(";
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
		query += "'%s'" % filename.replace("'", " ")
		query += ");"

		cursor.execute(query)
		
		items += 1;

	database.commit() 
		
	print "new items: %i" %items
	
	# Builds user interface ----------------------------------------------------------------------------------
	
	# root window
	root = Tkinter.Tk()
	root.geometry("%dx%d%+d%+d" % (1100, 600, 0, 0))
	
	# scrollbars for main tree view
	vsb = ttk.Scrollbar(orient="vertical")
	hsb = ttk.Scrollbar(orient="horizontal")
	  
	# main tree view definition
	tree = ttk.Treeview(columns=("type", "size", "id"),
	    displaycolumns=("size", "id"), yscrollcommand=lambda f, l: autoscroll(vsb, f, l),
	    xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
 	 
	vsb['command'] = tree.yview
	hsb['command'] = tree.xview

	tree.heading("#0", text="Element description", anchor='w')
	tree.heading("size", text="File Size", anchor='w')
	tree.heading("id", text="File ID", anchor='w')
	tree.grid(column=0, row=0, sticky='nswe')
	
	tree.grid(column=0, row=0, sticky='nswe')
	vsb.grid(column=1, row=0, sticky='ns')
	hsb.grid(column=0, row=2, sticky='ew')
	
	root.grid_columnconfigure(0, weight=1)
	root.grid_rowconfigure(0, weight=1)
	
	tree.column("#0", width=300)
	tree.column("size", width=25)
	tree.column("id", width=25)	
	
	# right column
	buttonbox = Frame(root);
	w = Button(buttonbox, text="OK", width=10, default=ACTIVE)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
	w = Button(buttonbox, text="Cancel", width=10)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
	buttonbox.grid(column = 3, row = 0, sticky="ns")
	
	# tables tree (in right column)
	tablestree = ttk.Treeview(buttonbox, columns=("filename", "tablename"), displaycolumns=())			
	tablestree.heading("#0", text="table")
	tablestree.pack(fill=BOTH, expand=1)

	# main textarea
	textarea = Text(root, width=70)
	textarea.grid(column=2, row=0, sticky="ns")
	
	
	# populate the main tree frame ----------------------------------------------------------------------------
		
	cursor.execute("SELECT DISTINCT(domain_type) FROM indice");
	domain_types = cursor.fetchall()
	
	for domain_type_u in domain_types:
		domain_type = str(domain_type_u[0])
		domain_type_index = tree.insert('', 'end', text=domain_type)
		print "Domain type index: %s" %domain_type_index
		
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
					file_dim = str(file[1])
					file_id = int(file[2])
					file_type = str(file[3])
					tree.insert(path_index, 'end', text=substWith(file_name, "."), values=(file_type,str(file_dim)+" b", file_id))
			

	# called when an element is clicked in the tables tree frame ------------------------------------------------
	
	def TablesTreeClick(event):
	
		if (len(tablestree.selection()) == 0): return;
		
		seltable = tablestree.selection()[0]
		seltable_dbname = tablestree.set(seltable, "filename")
		seltable_tablename = tablestree.set(seltable, "tablename")
		
		if (os.path.exists(seltable_dbname)):
			seltabledb = sqlite3.connect(seltable_dbname) 
			try:
				seltablecur = seltabledb.cursor() 
				
				# clears main text field
				textarea.delete(1.0, END)
				
				# read selected table indexes
				seltablecur.execute("PRAGMA table_info(%s)" % seltable_tablename)
				seltable_fields = seltablecur.fetchall();
				
				# append table fields to main textares
				seltable_fieldslist = []
				textarea.insert(INSERT, "Table Fields:")
				#for seltable_field in seltable_fields:
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
					for seltable_record in seltable_cont:
						textarea.insert(INSERT, "\n- " + str(seltable_record))
						
						for i in range(len(seltable_record)):	
						
							import unicodedata
							try:
								value = str(seltable_record[i])
							except:
								#value = seltable_record[i].encode("utf-8", "replace") + " (decoded unicode)"
								value = "(wrong unicode string)"
													
							textarea.insert(END, "\n- " + seltable_fieldslist[i] + " : " 
								+ value)
						
						textarea.insert(END, "\n---------------------------------------")
				
				except:
					print "Unexpected error:", sys.exc_info()
					
				seltabledb.close()		
			except:
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
		
		textarea.delete(1.0, END)
		textarea.insert(INSERT, "Selezionato elemento: " + item_text + " (id " + str(item_id) + ")")
		
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
		
		textarea.insert(INSERT, "\n\nElement type: " + item_type)
		textarea.insert(INSERT, "\nPermissions: " + item_permissions)
		textarea.insert(INSERT, "\nUser id: " + item_userid)
		textarea.insert(INSERT, "\nGroup id: " + item_groupid)
		textarea.insert(INSERT, "\nLast modify time: " + item_mtime)
		textarea.insert(INSERT, "\nLast access Time: " + item_atime)
		textarea.insert(INSERT, "\nCreation time: " + item_ctime)
		textarea.insert(INSERT, "\nObfuscated file name: " + item_filecode)
		
		textarea.insert(INSERT, "\n\nAnalize file: ")
		
		item_realpath = backup_path + item_filecode
		
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
			text = fh.read(40)
			textarea.insert(INSERT, "\n\nFirst HEX values from file: ")
			textarea.insert(INSERT, "\n" + binascii.b2a_uu(text))
			fh.close()
			
		#print file content (if ASCII file) otherwise only first 50 chars
		if (os.path.exists(item_realpath)):
			if (magic.file(item_realpath) == "ASCII text"):
				fh = open(item_realpath, 'rb')
				textarea.insert(INSERT, "\nASCII content:\n\n")
				while 1:
					line = fh.readline()
					if not line: break;
					textarea.insert(INSERT, line)
				fh.close()	
			else:
				fh = open(item_realpath, 'rb')
				text = fh.read(40)
				textarea.insert(INSERT, "\nFirst chars from file (string): ")
				textarea.insert(INSERT, "\n" + str(text))
				fh.close()						
		
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


	tree.bind("<ButtonRelease-1>", OnClick)
	tablestree.bind("<ButtonRelease-1>", TablesTreeClick)
	
	from xml.dom.minidom import *
	manifest = parse("manifest.plist.txt")
	document = manifest.getElementsByTagName("plist")
	basedict = document[0].childNodes[1]
	nodes = basedict.childNodes
	for i in range(len(nodes)):
		node = nodes[i]
		if (node.nodeType == node.TEXT_NODE): continue
		if (node.nodeName == "key"):
			print node.firstChild.toxml()
	
	root.mainloop()
	
	database.close() # Close the connection to the database
	
	