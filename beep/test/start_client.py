# $Id: start_client.py,v 1.1 2002/08/02 00:24:40 jpwarren Exp $
# $Revision: 1.1 $

import unittest
import sys
import time

sys.path.append('../../')
from beep.core import constants
from beep.core import logging
from beep.transports import tcpsession
from beep.profiles import profile

class StartClient(unittest.TestCase):
# A sleeptime is required between shutting down one session listener
# and creating another one to prevent "address already in use" errors
# This is a feature, not a bug
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_startClient(self):

		# create and connect a client
		pdict2 = profile.ProfileDict()
		client = tcpsession.TCPSession(self.log, pdict2, 0, 1, 'localhost', 1976)
		time.sleep(1)

		client.terminate()

if __name__ == '__main__':

	unittest.main()

