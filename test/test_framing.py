# $Id: test_framing.py,v 1.2 2003/01/01 23:37:39 jpwarren Exp $
# $Revision: 1.2 $
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
# These tests test the way a BEEP Listener server functions
# with regard to basic framing

import unittest

import sys

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

class FramingTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.log = logging.Log()
#		self.log.debuglevel = logging.LOG_DEBUG
#		self.log.debuglevel = logging.LOG_INFO
#		self.log.debuglevel = -1

		# create a listener
		pdict = profile.ProfileDict()
		pdict[echoprofile.uri] = echoprofile
		self.listener = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while not self.listener.isActive():
			pass
		self.client = dummyclient.DummyClient()

	def tearDown(self):
		self.client.terminate()
		self.listener.close()
		while not self.listener.isExited():
			pass

	def test_FR001(self):
		"""Test frame with invalid header format"""

		data = self.client.getmsg(1)
		self.client.sendmsg("test\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR002(self):
		"""Test frame with invalid type"""

		data = self.client.getmsg(1)

		self.client.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR003(self):
		"""Test frame with negative channel number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG -5 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR004(self):
		"""Test frame with too large channel number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 5564748837473643 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR005(self):
		"""Test frame with non-numeric channel number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG fred 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR006(self):
		"""Test frame with unstarted channel number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 55 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR007(self):
		"""Test frame with negative message number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 0 -6 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR008(self):
		"""Test frame with too large message number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 0 6575488457584834 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR009(self):
		"""Test frame with non-numeric message number"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 0 fred . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR010(self):
		"""Test frame with invalid more type"""

		data = self.client.getmsg(1)

		self.client.sendmsg("MSG 0 0 g 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR011(self):
		"""Test frame with negative seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . -84 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR012(self):
		"""Test frame with too large seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 75747465674373643 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR013(self):
		"""Test frame with non-numeric seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . fred 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR014(self):
		"""Test frame with out of sequence seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg()

	def test_FR015(self):
		"""Test frame with negative size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 -15\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR016(self):
		"""Test frame with too large size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 574857345839457\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR017(self):
		"""Test frame with non-numeric size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 fred\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR018(self):
		"""Test frame with incorrect size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR019(self):
		"""Test frame with negative ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 -65\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR020(self):
		"""Test frame with too large ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 5857483575747\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR021(self):
		"""Test frame with non-numeric ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 fred\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR022(self):
		"""Test frame with missing ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR023(self):
		"""Test frame ansno in non-ANS frame"""

		data = self.client.getmsg()

		self.client.sendmsg("RPY 0 0 . 0 0 15\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR024(self):
		"""Test frame NUL as intermediate"""

		data = self.client.getmsg(1)

		self.client.sendmsg("NUL 0 0 * 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR025(self):
		"""Test frame NUL with non-zero size"""

		data = self.client.getmsg(1)

		self.client.sendmsg("NUL 0 0 . 0 5\r\nhi!\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_FR026(self):
		"""Test frame response to MSG never sent"""

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)

		self.client.sendmsg("RPY 0 15 . 51 8\r\nHello!\r\nEND\r\n")

		data = self.client.getmsg()

		self.assertEqual( data, None )

if __name__ == '__main__':

	unittest.main()

