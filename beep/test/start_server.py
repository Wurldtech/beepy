# $Id: start_server.py,v 1.1 2002/08/02 00:24:41 jpwarren Exp $
# $Revision: 1.1 $

import unittest
import sys
import time

import md5

sys.path.append('../../')
from beep.core import constants
from beep.core import logging
from beep.transports import tcpsession
from beep.profiles import profile

if __name__ == '__main__':

	log = logging.Log()
	log.debuglevel = logging.LOG_DEBUG

	# create the server
	pdict = profile.ProfileDict()
	pdict['http://www.eigenmagic.com/beep/ECHO'] = 'echoprofile'
	listener = tcpsession.TCPSessionListener(log, pdict, 'localhost', 1976)
	# run forever
	while(1):
		pass
else:
	print "This isn't a module you should import, dude."


