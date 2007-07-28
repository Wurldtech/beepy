# $Id: test_reverbprofile.py,v 1.8 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.8 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import unittest
import sys
import time

sys.path.append('..')

import dummyclient

class ReverbProfileTest(unittest.TestCase):

	def setUp(self):

		self.client = dummyclient.DummyClient()

	def tearDown(self):
		self.client.terminate()

	def test_createEchoChannel(self):
		"""Test creation of a channel with the Echo profile"""

		# send a greeting msg
		self.client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
		data = self.client.getmsg(1)

		# create a channel with the ECHO profile
		self.client.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</start>END\r\n')
		data = self.client.getmsg(1)

		self.client.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
		data = self.client.getmsg(1)
		self.assertEqual(data, 'RPY 1 0 . 0 8\r\nHello!\r\nEND\r\n')

		self.client.sendmsg('MSG 1 1 . 8 8\r\nHello!\r\nEND\r\n')
		data = self.client.getmsg(1)

		self.assertEqual(data, 'RPY 1 1 . 8 8\r\nHello!\r\nEND\r\n')

if __name__ == '__main__':

	unittest.main()

