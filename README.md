# iPBD - iPhone Backup Decoder and Analyzer

(C)opyright 2010 Mario Piccinelli <mario.piccinelli@gmail.com>

Released under [MIT licence](http://en.wikipedia.org/wiki/MIT_License)

This software allows the user to browse through the content of an iPhone/iPad backup made by iTunes. The software is packed with all the routines needed to understand and show the content of files found.

For each file selected, the following informations are calculated/shown:

* Real name and name in the backup directory
* File UNIX permissions
* Data hash (as calculated by iOS)
* User and group ID
* Modify time, access time, creation time
* File type (from magic numbers)
* File MD5 hash
* First hex bytes
* First bytes as ASCII characters
* File content: HEX dump if data, text if ASCII or UTF8, tables list if SQLite
* EXIF data for JPG images

Binary plist files are translated on runtime into their XML counterpart by the MacOsX plutil utility.

User is presented with the list of tables in SQLite databases, and can immediately see the content of each and the structure of the fields.

Built a separate window to show text messages by thread. More views will be written to see contacts, calendar, notes, ....

# Requires:

* Tested on Python 2.6 on Linux and Mac Os X.

* Python Tkinter library. See [this link](http://tkinter.unpythonic.net/wiki/How_to_install_Tkinter) for details about the installation. On MacOsX the Tkinter framework is installed along with [ActiveTcl](http://www.python.org/download/mac/tcltk/). On Linux you should find by typing something like:
  sudo apt-get install python-tk
 
* Python TTK library. On Mac Os it is installed with ActiveTCL (see above), on Linux you should install [PyTTK](http://code.google.com/p/python-ttk/).

* Python Imaging Library (PIL). For Mac Os download from [here](http://www.pythonware.com/products/pil/). For Linux you should do something like:
  sudo apt-get install python-imaging python-imaging-tk
