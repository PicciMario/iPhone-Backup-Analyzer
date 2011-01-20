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

verbose = True
if __name__ == '__main__':
	mbdb = mbdbdecoding.process_mbdb_file(backup_path + "Manifest.mbdb")
	mbdx = mbdbdecoding.process_mbdx_file(backup_path + "Manifest.mbdx")
	
	# prepares DB
	database = sqlite3.connect('MyDatabase.db') # Create a database file
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
	
	items = 0;
	
	for offset, fileinfo in mbdb.items():
		if offset in mbdx:
			fileinfo['fileID'] = mbdx[offset]
		else:
			fileinfo['fileID'] = "<nofileID>"
			print >> sys.stderr, "No fileID found for %s" % fileinfo_str(fileinfo)
		#print fileinfo_str(fileinfo, verbose)
		
		if (fileinfo['mode'] & 0xE000) == 0xA000: type = 'l' # symlink
		elif (fileinfo['mode'] & 0xE000) == 0x8000: type = '-' # file
		elif (fileinfo['mode'] & 0xE000) == 0x4000: type = 'd' # dir
		
		#separates domain type (AppDomain, HomeDomain, ...) from domain name
		[domaintype, sep, domain] = fileinfo['domain'].partition('-');
		
		#separates file name from file path
		[filepath, sep, filename] = fileinfo['filename'].rpartition('/')
		if (type == 'd'):
			filepath = fileinfo['filename']
			filename = "";
		
		# Insert some people into the table
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
		#print query
		cursor.execute(query)
		
		items += 1;

	database.commit() # Save our changes
	
	print "new items: %i" %items
	
	root = Tkinter.Tk()
	root.geometry("%dx%d%+d%+d" % (1100, 600, 0, 0))
	
	vsb = ttk.Scrollbar(orient="vertical")
	hsb = ttk.Scrollbar(orient="horizontal")
	  
	tree = ttk.Treeview(columns=("type", "size", "id"),
	    displaycolumns=("size", "id"), yscrollcommand=lambda f, l: autoscroll(vsb, f, l),
	    xscrollcommand=lambda f, l:autoscroll(hsb, f, l))
 	 
	vsb['command'] = tree.yview
	hsb['command'] = tree.xview


	tree.heading("#0", text="Element description", anchor='w')
	tree.heading("size", text="File Size", anchor='w')
	tree.heading("id", text="File ID", anchor='w')
	tree.grid(column=0, row=0, sticky='nswe')
	
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
			
	def buttonBoxPress(event):
		print event.widget
		return "";
	
	buttonbox = Frame(root);
	w = Button(buttonbox, text="OK", width=10, default=ACTIVE)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
	w = Button(buttonbox, text="Cancel", width=10)
	w.bind("<Button-1>", buttonBoxPress)
	w.pack()
	buttonbox.grid(column = 3, row = 0, sticky="ns")
	
	textarea = Text(root, width=70)
	textarea.grid(column=2, row=0, sticky="ns")
		
	tree.grid(column=0, row=0, sticky='nswe')
	vsb.grid(column=1, row=0, sticky='ns')
	hsb.grid(column=0, row=2, sticky='ew')
	
	root.grid_columnconfigure(0, weight=1)
	root.grid_rowconfigure(0, weight=1)
	
	tree.column("#0", width=300)
	tree.column("size", width=25)
	tree.column("id", width=25)	
	
	def OnClick(event):
		if (len(tree.selection()) == 0): return;
		
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
		
		#print first 50 bytes from file
		if (os.path.exists(item_realpath)):
			fh = open(item_realpath, 'rb')
			text = fh.read(40)
			textarea.insert(INSERT, "\n\nFirst chars from file: ")
			textarea.insert(INSERT, "\n" + binascii.b2a_uu(text))
		
		#if sqlite3, print tables list
		if (os.path.exists(item_realpath)):
			tempdb = sqlite3.connect(item_realpath) 
			try:
				tempcur = tempdb.cursor() 
				tempcur.execute("SELECT name FROM sqlite_master WHERE type=\"table\"")
				tables_list = tempcur.fetchall();
				textarea.insert(INSERT, "\n\nTables in database: ")
				for i in tables_list:
					textarea.insert(INSERT, "\n- " + str(i[0]));
				
					tempcur.execute("SELECT count(*) FROM %s" % str(i[0]));
					elem_count = tempcur.fetchone()
					textarea.insert(INSERT, " (%i elements) " % int(elem_count[0]))
				
				tempdb.close()		
			except:
				tempdb.close()

	tree.bind("<ButtonRelease-1>", OnClick)
	
	root.mainloop()
	
	database.close() # Close the connection to the database
	
	