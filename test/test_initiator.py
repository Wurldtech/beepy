# $Id: test_initiator.py,v 1.3 2003/01/07 07:40:00 jpwarren Exp $
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

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
class TCPInitatorSessionTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.log = logging.Log()

	def test_connect(self):
		"""Test connection of Initiator to server
		"""
		pdict1 = profile.ProfileDict()
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)
		while not sess.isActive():
			pass

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.log, pdict2)
		while not clientmgr.isActive():
			pass

		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				print "Cannot connect to server."
				exit(1)
			pass

		# close all
		client.close()
		while client.isAlive():
			pass

		clientmgr.close()
		while clientmgr.isAlive():
			pass

		sess.close()
		while sess.isAlive():
			pass

	def test_startChannel(self):
		"""Test start of a channel
		"""
		pdict1 = profile.ProfileDict()
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.log, pdict2)
		while not clientmgr.isActive():
			pass

		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				print "Cannot connect to server."
				exit(1)
			pass

		profileList = [[echoprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			pass

		client.closeChannel(channelnum)
		while client.isChannelActive(channelnum):
			pass

		client.close()
		while client.isAlive():
			pass

		clientmgr.close()
		while clientmgr.isAlive():
			pass

		sess.close()
		while sess.isAlive():
			pass

if __name__ == '__main__':

	unittest.main()

