# $Id: test_saslanonymousprofile.py,v 1.1 2002/08/13 14:39:33 jpwarren Exp $
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

import unittest
import sys
import time

sys.path.append('../../')
from beep.core import constants
from beep.core import logging
from beep.transports import tcpsession
from beep.profiles import profile
from beep.profiles import saslanonymousprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class SASLAnonymousProfileTest(unittest.TestCase):
	log = logging.Log()
	log.debuglevel = logging.LOG_DEBUG

	def test_createSASLAnonymousSession(self):
		"""Test SASL Anonymous with no CDATA init"""
		pdict = profile.ProfileDict()
		pdict['http://iana.org/beep/SASL/ANONYMOUS'] = saslanonymousprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)

		# create and connect a client
		client = dummyclient.DummyClient()
		# send a greeting msg
		client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
		data = client.getmsg()

		# create a channel with the SASL Anonymous profile
		client.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://iana.org/beep/SASL/ANONYMOUS"/>\r\n</start>END\r\n')
		data = client.getmsg()

		self.assertEqual(data, 'RPY 0 0 . 117 90\r\nContent-Type: application/beep+xml\n\n<profile uri="http://iana.org/beep/SASL/ANONYMOUS"/>\r\nEND\r\n')

		client.sendmsg('MSG 1 0 . 0 21\r\n<blob>aGVsbG8K</blob>END\r\n')
		data = client.getmsg()
		print "got reply: ", data

		# time to regreet after tuning reset
		client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
		data = client.getmsg()
		print "got reply: ", data

		client.terminate()
		sess.close()
		time.sleep(1)

if __name__ == '__main__':

	unittest.main()

