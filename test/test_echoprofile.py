# $Id: test_echoprofile.py,v 1.6 2003/01/09 00:20:55 jpwarren Exp $
# $Revision: 1.6 $
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

try:
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import echoprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class EchoProfileTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.clientlog = logging.Log(prefix='client: ')
		self.serverlog = logging.Log(prefix='server: ')

		# create a listener
		pdict = profile.ProfileDict()
		pdict[echoprofile.uri] = echoprofile
		self.listener = tcpsession.TCPListenerManager(self.serverlog, pdict, 'localhost', 1976)
		# wait for it to become active
		while not self.listener.isActive():
			time.sleep(0.25)
		self.clientlog.logmsg(logging.LOG_DEBUG, "Listener is active.")
		self.client = dummyclient.DummyClient()

	def tearDown(self):
		self.client.terminate()
		self.listener.close()
		while not self.listener.isExited():
			time.sleep(0.25)

	def test_createEchoChannel(self):
		"""Test creation of a channel with the Echo profile"""

		# send a greeting msg
		self.client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
		self.clientlog.logmsg(logging.LOG_DEBUG, "Client sent greeting.")
		data = self.client.getmsg(1)

		# create a channel with the ECHO profile
		self.client.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</start>END\r\n')
		data = self.client.getmsg(1)

		self.clientlog.logmsg(logging.LOG_DEBUG, "sending echo frame...")
		self.client.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
		data = self.client.getmsg(1)
		self.assertEqual(data, 'RPY 1 0 . 0 8\r\nHello!\r\nEND\r\n')

		self.client.sendmsg('MSG 1 1 . 8 8\r\nHello!\r\nEND\r\n')
		data = self.client.getmsg(1)
		self.assertEqual(data, 'RPY 1 1 . 8 8\r\nHello!\r\nEND\r\n')

if __name__ == '__main__':

	unittest.main()

