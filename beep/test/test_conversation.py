# $Id: test_conversation.py,v 1.8 2002/10/23 04:51:17 jpwarren Exp $
# $Revision: 1.8 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002 Justin Warren <daedalus@eigenmagic.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

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

class ConversationTest(unittest.TestCase):
	log = logging.Log()

	def test_clientMultiGreeting(self):
		"""Test connect from client with multiple greetings"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg("RPY 0 0 . 51 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.terminate()
		sess.close()
		while sess.isAlive():
			pass
		self.assertEqual(data, '')

	def test_clientStartChannel(self):
		"""Test start channel with unsupported profile"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass
		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="1">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')

		data = client.getmsg()
		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

		self.assertEqual(data, 'ERR 0 0 . 117 95\r\nContent-Type: application/beep+xml\n\n<error code="504">\r\n  Parameter Not Implemented\r\n</error>\r\nEND\r\n')

	def test_clientStartEvenChannel(self):
		"""Test start channel with incorrectly even number"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass
		# create and connect a client
		client = dummyclient.DummyClient()

		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="6">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
		data = client.getmsg()
		client.terminate()
		sess.close()
		while sess.isAlive():
			pass
		self.assertEqual(data, 'ERR 0 0 . 117 96\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Syntax Error In Parameters\r\n</error>\r\nEND\r\n')

	def test_clientStartAlphaChannel(self):
		"""Test start channel with invalid channel number"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass
		# create and connect a client
		client = dummyclient.DummyClient()

		# send a greeting msg
		client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="a">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
		data = client.getmsg()
		client.terminate()
		sess.close()
		while sess.isAlive():
			pass
		self.assertEqual(data, 'ERR 0 0 . 117 106\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Requested channel number is invalid.\r\n</error>\r\nEND\r\n')


if __name__ == '__main__':

	unittest.main()

