# $Id: test_session.py,v 1.3 2002/08/04 10:07:07 jpwarren Exp $
# $Revision: 1.3 $
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

class SessionTest(unittest.TestCase):
# A sleeptime is required between shutting down one session listener
# and creating another one to prevent "address already in use" errors
# This is a feature, not a bug
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_1_createSession(self):
		"""Test create listener"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)

		sess.close()
		time.sleep(1)

	def test_2_connectClient(self):
		"""Test connect from client"""
		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.terminate()
		sess.close()
		time.sleep(1)

		self.assertEqual(data, 'RPY 0 0 . 0 81\r\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n')

	def test_invalidHeaderFormat(self):
		"""Test invalid frame header format"""
		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		self.assertEqual(sess.state, constants.SESSION_INITIALIZED)

#		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("test\r\nEND\r\n")

		client.terminate()
		sess.close()
		time.sleep(1)

	def test_invalidFrameType(self):
		"""Test invalid frame type"""
#		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		self.assertEqual(sess.state, constants.SESSION_INITIALIZED)
#
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")

		client.terminate()
		sess.close()
		time.sleep(1)

	def test_invalidFrameSize(self):
		"""Test invalid frame size"""
#		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		self.assertEqual(sess.state, constants.SESSION_INITIALIZED)
#
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")

		client.terminate()
		sess.close()
		time.sleep(1)

	def test_invalidSeqno(self):
		"""Test invalid frame size"""
#		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		self.assertEqual(sess.state, constants.SESSION_INITIALIZED)
#
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		client.sendmsg("MSG 0 0 . 0 13\r\nh<greeintg/>\r\nEND\r\n")

		client.terminate()
		sess.close()
		time.sleep(1)

	def test_validGreeting(self):
		"""Test invalid frame size"""
#		# create the server
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		self.assertEqual(sess.state, constants.SESSION_INITIALIZED)
#
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")

		client.terminate()
		sess.close()
		time.sleep(1)

#	def test_malformedXML(self):

if __name__ == '__main__':

	unittest.main()

