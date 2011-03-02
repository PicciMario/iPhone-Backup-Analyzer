from xml.dom.minidom import *

def printXmlKey(element, level = 0):
	
	text = ""
	
	tab = "";
	for i in range(level):
		tab = tab + "   "

	if (element.nodeType == Node.TEXT_NODE): return text
	
	if (element.nodeName == "key"):
		text += "\n\n" + tab + element.firstChild.toxml()
	else:
		if (element.nodeName == "false"):
			text += "\n" + tab + "- False"
			
		elif (element.nodeName == "true"):
			text += "\n" + tab + "- True"
		
		elif (element.nodeName == "date" or element.nodeName == "string"):
			text += "\n" + tab + "- " + element.firstChild.toxml()
		
		elif (element.nodeName == "integer" or element.nodeName == "real"):
			text += "\n" + tab + element.firstChild.toxml()
		
		elif (element.nodeName == "dict"):
			#print tab + "- Dictionary"
			for o in range(len(element.childNodes)):
				child = element.childNodes[o]
				newText = printXmlKey(child, level + 1)
				if (newText != None):
					if (len(newText) != 0):
						text += newText
		
		elif (element.nodeName == "array"):
			#print tab + "- Array"
			for o in range(len(element.childNodes)):
				child = element.childNodes[o]
				text += printXmlKey(child, level + 1)
		
		else:
			text += "\n" + tab + "- unknown data type (%s)" %(element.nodeName)
			
	return text

def decodeManifestPlist(filename):

	manifest = parse(filename)
	document = manifest.getElementsByTagName("plist")
	basedict = document[0].childNodes[1]
	nodes = basedict.childNodes
	
	xmlDecode = ""
	for i in range(len(nodes)):
		selectednode = nodes[i]
		xmlDecode += printXmlKey(selectednode)
	
	return xmlDecode

# returns device info from passed filename (Info.plist)

def deviceInfo(filename):

	manifest = parse(filename)
	# <plist>
	document = manifest.getElementsByTagName("plist")
	# main <dict>
	basedict = document[0].childNodes[1]
	# nodes in main <dict>
	nodes = basedict.childNodes
	
	properties = {}
	
	for i in range(len(nodes)):
		selectednode = nodes[i]
		
		keyname = ""
		keyval = ""
		
		proplist = (
			"Device Name",
			"Display Name",
			"GUID",
			"ICCID",
			"IMEI",
			"Last Backup Date",
			"Product Type",
			"Product Version",
			"Serial Number",
			"iTunes Version"		
		)
		
		if (selectednode.nodeName == "key"):
			keyname = selectednode.firstChild.toxml()
			if keyname in proplist:
				child = nodes[i+2].firstChild
				if (child == None): 
					print("no child")
					continue
				keyval = child.toxml()
				#print("%s - %s"%(keyname, keyval))
				properties[keyname] = keyval
		
	return properties
