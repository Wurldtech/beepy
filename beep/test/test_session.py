# $Id: test_session.py,v 1.6 2002/09/18 07:07:02 jpwarren Exp $
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

sys.path.append('../../')
from beep.core import constants
from beep.core import logging
from beep.transports import tcpsession
from beep.profiles import profile
from beep.profiles import echoprofile

import dummyclient

class SessionTest(unittest.TestCase):

	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_3_invalidHeaderFormat(self):
		"""Test invalid frame header format"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("test\r\nEND\r\n")

		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

	def test_4_invalidFrameType(self):
		"""Test invalid frame type"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect a client
		client = dummyclient.DummyClient()
#		data = client.getmsg()
		client.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")
		data = client.getmsg()
		print data

		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

	def test_5_invalidFrameSize(self):
		"""Test invalid frame size"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass
		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")
		data = client.getmsg()
		print data

		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

	def test_6_invalidSeqno(self):
		"""Test invalid frame size"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
		data = client.getmsg()
		print data

		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

	def test_7_validGreeting(self):
		"""Test invalid frame size"""
		pdict = profile.ProfileDict()
		pdict['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
		# wait for it to become active
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect a client
		client = dummyclient.DummyClient()
		data = client.getmsg()
		client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")

		client.terminate()
		sess.close()
		while sess.isAlive():
			pass

if __name__ == '__main__':

	unittest.main()

	sess.close()
