# $Id: testall.py,v 1.1 2002/08/02 00:24:40 jpwarren Exp $
# $Revision: 1.1 $
#
# The top level testing class.
# This is used for testing various aspects of the beepy library
# Happily snarfed from http://diveintopython/ after seeing it
# in the code for py-beep

import sys, os, re, unittest
sys.path.append('../')

def unitTest():
	path = os.path.abspath(os.path.split(sys.argv[0])[0])
	print "path:", path
	testfiles = os.listdir(path)
	test = re.compile("test_.*.py$", re.IGNORECASE)
	files = filter(test.search, testfiles)
	filenameToModuleName = lambda f: os.path.splitext(f)[0]
	moduleNames = map(filenameToModuleName, files)
	modules = map(__import__, moduleNames)
	load = unittest.defaultTestLoader.loadTestsFromModule
	return unittest.TestSuite(map(load, modules))

if __name__ == '__main__':
	unittest.main(defaultTest='unitTest')
