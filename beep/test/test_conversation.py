# $Id: test_conversation.py,v 1.1 2002/08/02 00:24:40 jpwarren Exp $
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
class ConversationTest(unittest.TestCase):
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_clientMultiGreeting(self):
		"""Test connect from client with multiple greetings"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)

		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg("RPY 0 0 . 13 13\r\n<greeting/>\r\nEND\r\n")
		client.terminate()

		sess.close()
		time.sleep(1)

	def test_clientStartChannel(self):
		"""Test greeting and start msg"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg('MSG 0 0 . 13 80\r\n<start number="1">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')

		data = client.getmsg()
		client.terminate()

		sess.close()
		time.sleep(1)

	def test_clientStartEvenChannel(self):
		"""Test create channel with incorrectly even number"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# create and connect a client
		client = dummyclient.DummyClient()

		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg('MSG 0 0 . 13 80\r\n<start number="6">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
		data = client.getmsg()
		client.terminate()
		self.assertEqual(data, 'ERR 0 0 . 93 60\r\n<error code="501">\r\n  Syntax Error In Parameters\r\n</error>\r\nEND\r\n')
		sess.close()
		time.sleep(1)


if __name__ == '__main__':

	unittest.main()

