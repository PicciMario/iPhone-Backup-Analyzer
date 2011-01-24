from xml.dom.minidom import *

def printXmlKey(element, level = 0):
	
	text = ""
	
	tab = "";
	for i in range(level):
		tab = tab + "   "

	if (element.nodeType == Node.TEXT_NODE): return text
	
	if (element.nodeName == "key"):
		text += "\n" + tab + element.firstChild.toxml()
	else:
		if (element.nodeName == "false"):
			text += "\n" + tab + "- False"
			
		elif (element.nodeName == "true"):
			text += "\n" + tab + "- True"
		
		elif (element.nodeName == "date" or element.nodeName == "string"):
			text += "\n" + tab + "- " + element.firstChild.toxml()
		
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
			text += "\n" + tab + "- unknown data type (%s)" %element.nodeName
			
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
