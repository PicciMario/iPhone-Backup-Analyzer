from Tkinter import *
import sqlite3
import ttk
from datetime import datetime

groupstree = None
textarea = None
filename = ""

def OnClick(event):
	global filename
	global groupstree, textarea
	if (len(groupstree.selection()) == 0): return;
	msg_group = int(groupstree.item(groupstree.selection(), "text"))
	query = "SELECT text, date FROM message INNER JOIN msg_group ON msg_group.rowid = message.group_id WHERE msg_group.rowid = %i ORDER BY date "%msg_group
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	tempcur.execute(query)
	messages = tempcur.fetchall()
	tempdb.close()
	
	textarea.delete(1.0, END)
	for message in messages:
		text = message[0]
		date = int(message[1])
		
		#date = date + 978307200 #JAN 1 1970
		convdate = datetime.fromtimestamp(int(date))
		
		textarea.insert(END, "Date: %s\n"%convdate)
		textarea.insert(END, "%s\n"%text)
		textarea.insert(END, "----------\n")

	
def sms_window(filenamenew):
	global filename
	global groupstree, textarea
	filename = filenamenew
	
	# main window
	smswindow = Toplevel()
	smswindow.title('SMS data')
	smswindow.focus_set()
	
	# header label
	smstitle = Label(smswindow, text = "SMS data from: " + filename, relief = RIDGE)
	smstitle.grid(column = 0, row = 0, sticky="ew", columnspan=2, padx=5, pady=5)

	# tree
	groupstree = ttk.Treeview(smswindow, columns=("address"),
	    displaycolumns=("address"))
	
	groupstree.heading("#0", text="ID", anchor='w')
	groupstree.heading("address", text="Address", anchor='w')
	
	groupstree.column("#0", width=30)
	groupstree.column("address", width=200)
	
	groupstree.grid(column = 0, row = 1, sticky="ns")
	
	# textarea
	textarea = Text(smswindow, bd=2, relief=SUNKEN)
	textarea.grid(column = 1, row = 1, sticky="nsew")
	
	# destroy window when closed
	smswindow.protocol("WM_DELETE_WINDOW", smswindow.destroy)
	
	# populating tree with SMS groups
	tempdb = sqlite3.connect(filename)
	tempcur = tempdb.cursor() 
	query = "SELECT DISTINCT(msg_group.rowid), address FROM msg_group INNER JOIN group_member ON msg_group.rowid = group_member.group_id"
	tempcur.execute(query)
	groups = tempcur.fetchall()
	tempdb.close()
	
	for element in groups:
		groupid = element[0]
		address = element[1].replace(' ', '')
		groupstree.insert('', 'end', text=groupid, values=(address))
		
	groupstree.bind("<ButtonRelease-1>", OnClick)