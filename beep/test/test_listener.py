# $Id: test_listener.py,v 1.1 2002/10/23 04:51:17 jpwarren Exp $
# $Revision: 1.1 $
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
# They test various framing format issues.

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

class ServerTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.log = logging.Log()
#		self.log.debuglevel = logging.LOG_DEBUG
#		self.log.debuglevel = logging.LOG_INFO
		self.log.debuglevel = -1

		# create a listener
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
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

	def test_2211001_InvalidHeaderFormat(self):
		"""Test frame with invalid header format"""

		data = self.client.getmsg()
		self.client.sendmsg("test\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211002_invalidFrameType(self):
		"""Test frame with invalid type"""

		data = self.client.getmsg()

		self.client.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211003_negativeChannelNumber(self):
		"""Test frame with negative channel number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG -5 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211004_toolargeChannelNumber(self):
		"""Test frame with too large channel number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 5564748837473643 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211005_nonnumericChannelNumber(self):
		"""Test frame with non-numeric channel number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG fred 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211006_unstartedChannelNumber(self):
		"""Test frame with unstarted channel number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 55 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211007_negativeMessageNumber(self):
		"""Test frame with negative message number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 -6 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211008_toolargeMessageNumber(self):
		"""Test frame with too large message number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 6575488457584834 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211009_nonnumericMessageNumber(self):
		"""Test frame with non-numeric message number"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 fred . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211010_invalidMoreType(self):
		"""Test frame with invalid more type"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 g 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211011_negativeSeqno(self):
		"""Test frame with negative seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . -84 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211012_toolargeSeqno(self):
		"""Test frame with too large seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 75747465674373643 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211013_nonnumericSeqno(self):
		"""Test frame with non-numeric seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . fred 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211014_outofsequenceSeqno(self):
		"""Test frame with out of sequence seqno"""

		data = self.client.getmsg()

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg()

	def test_2211015_negativeFrameSize(self):
		"""Test frame with negative size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 -15\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211016_toolargeFrameSize(self):
		"""Test frame with too large size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 574857345839457\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211017_nonnumericFrameSize(self):
		"""Test frame with non-numeric size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 fred\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211018_incorrectFrameSize(self):
		"""Test frame with incorrect size"""

		data = self.client.getmsg()

		self.client.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211019_negativeAnsno(self):
		"""Test frame with negative ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 -65\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211020_toolargeAnsno(self):
		"""Test frame with too large ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 5857483575747\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211021_nonnumericAnsno(self):
		"""Test frame with non-numeric ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0 fred\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211022_missingAnsno(self):
		"""Test frame with missing ansno"""

		data = self.client.getmsg()

		self.client.sendmsg("ANS 0 0 . 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211023_nonANSFrameWithAnsno(self):
		"""Test frame ansno in non-ANS frame"""

		data = self.client.getmsg()

		self.client.sendmsg("RPY 0 0 . 0 0 15\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211024_intermediateNUL(self):
		"""Test frame NUL as intermediate"""

		data = self.client.getmsg()

		self.client.sendmsg("NUL 0 0 * 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211025_intermediateNUL(self):
		"""Test frame NUL with non-zero size"""

		data = self.client.getmsg()

		self.client.sendmsg("NUL 0 0 . 0 5\r\nhi!\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2211023_intermediateNUL(self):
		"""Test frame NUL as intermediate"""

		data = self.client.getmsg()

		self.client.sendmsg("NUL 0 0 * 0 0\r\nEND\r\n")
		data = self.client.getmsg()

		self.assertEqual( data, None )

	def test_2311000_validGreeting(self):
		"""Test valid greeting"""

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)

		self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )

	def test_2311001_clientMultiGreeting(self):
		"""Test connect from client with multiple greetings"""

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)

		self.client.sendmsg("RPY 0 0 . 51 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)

		self.assertEqual(data, '' )

	def test_clientStartChannel(self):
		"""Test start channel with unsupported profile"""

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)
		self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="1">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')

		data = self.client.getmsg(1)

		self.assertEqual(data, 'ERR 0 0 . 117 95\r\nContent-Type: application/beep+xml\n\n<error code="504">\r\n  Parameter Not Implemented\r\n</error>\r\nEND\r\n')

	def test_clientStartEvenChannel(self):
		"""Test start channel with incorrectly even number"""
		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)

		self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="6">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
		data = self.client.getmsg(1)

		self.assertEqual(data, 'ERR 0 0 . 117 96\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Syntax Error In Parameters\r\n</error>\r\nEND\r\n')

	def test_clientStartAlphaChannel(self):
		"""Test start channel with alpha channel number"""

		self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
		data = self.client.getmsg(1)
		self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="a">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
		data = self.client.getmsg(1)

		self.assertEqual(data, 'ERR 0 0 . 117 106\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Requested channel number is invalid.\r\n</error>\r\nEND\r\n')


if __name__ == '__main__':

	unittest.main()

