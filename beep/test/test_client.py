# $Id: test_client.py,v 1.1 2002/08/02 00:24:41 jpwarren Exp $
# $Revision: 1.1 $

import unittest
import sys
import time

sys.path.append('../../')
from beep.core import constants
from beep.core import logging
from beep.transports import tcpsession
from beep.profiles import profile
from beep.profiles import echoprofile

class ClientTest(unittest.TestCase):
# A sleeptime is required between shutting down one session listener
# and creating another one to prevent "address already in use" errors
# This is a feature, not a bug
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_connectClient(self):
		"""Test connect from client"""
		# create the server
		pdict1 = profile.ProfileDict()
		pdict1['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		listener = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)

		# create and connect a client
		pdict2 = profile.ProfileDict()
		pdict2['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		client = tcpsession.TCPInitiatorSession(self.log, pdict2, 'localhost', 1976)
		startProfile = [['http://www.eigenmagic.com/beep/ECHO',None,None]]
		# Wait for reception of greeting
		while not client.receivedGreeting:
			pass

		client.startChannel(startProfile)
		time.sleep(1)
		client.close()
		listener.close()

if __name__ == '__main__':

	unittest.main()

