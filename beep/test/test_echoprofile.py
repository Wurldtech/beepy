# $Id: test_echoprofile.py,v 1.1 2002/08/02 00:24:41 jpwarren Exp $
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

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class EchoProfileTest(unittest.TestCase):
	log = logging.Log()
	log.debuglevel = logging.LOG_DEBUG

	def test_createEchoChannel(self):
		"""Test creation of a channel with the Echo profile"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)

		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg('RPY 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n')
		data = client.getmsg()

		# create a channel with the ECHO profile
		client.sendmsg('MSG 0 0 . 13 82\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</start>END\r\n')
		data = client.getmsg()
		client.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
		data = client.getmsg()
		self.assertEqual(data, 'RPY 1 0 . 0 8\r\nHello!\r\nEND\r\n')
		client.sendmsg('MSG 1 0 . 8 8\r\nHello!\r\nEND\r\n')
		data = client.getmsg()
		self.assertEqual(data, 'RPY 1 0 . 8 8\r\nHello!\r\nEND\r\n')
		client.terminate()
		sess.close()
		time.sleep(1)

if __name__ == '__main__':

	unittest.main()

