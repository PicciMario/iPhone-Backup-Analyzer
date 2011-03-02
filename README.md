# iPBD - iPhone Backup Decoder and Analyzer

(C)opyright 2010 Mario Piccinelli <mario.piccinelli@gmail.com>

Released under [MIT licence](http://en.wikipedia.org/wiki/MIT_License)

This software allows the user to browse through the content of an iPhone/iPad backup made by iTunes. The software is packed with all the routines needed to understand the content of files found.

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

Binary plist files are translated on runtime into their XML counterpart by the MacOsX plutil utility

User is presented with the list of tables in SQLite databases, and can immediately see the content of each and the structure of the fields.

# Requires:

* MacOsX utility plutil. So right now this software is Mac only, until I find an alternative to plutil.

* Python Tkinter library See [this link](http://tkinter.unpythonic.net/wiki/How_to_install_Tkinter) for details about the installation. On MacOsX the Tkinter framework is installed along with [ActiveTcl](http://www.python.org/download/mac/tcltk/).

* Python Imaging Library (PIL). Download from [here](http://www.pythonware.com/products/pil/).
