# $Id: test_initiator.py,v 1.6 2003/01/30 09:24:30 jpwarren Exp $
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

import threading

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
		self.serverlog = logging.Log(prefix="server: ")
		self.clientlog = logging.Log(prefix="client: ")

		# create and start a listenermgr
		pdict1 = profile.ProfileDict()
		pdict1[echoprofile.uri] = echoprofile
		self.listenermgr = tcpsession.TCPListenerManager(self.serverlog, pdict1, ('localhost', 1976) )
		while not self.listenermgr.isActive():
			time.sleep(0.25)

		# create and connect an initiatormgr
		pdict2 = profile.ProfileDict()
		pdict2[echoprofile.uri] = echoprofile
		self.clientmgr = tcpsession.TCPInitiatorManager(self.clientlog, pdict2)
		while not self.clientmgr.isActive():
			time.sleep(0.25)

	def tearDown(self):

		self.clientmgr.close()
		while self.clientmgr.isAlive():
			time.sleep(0.25)

		self.listenermgr.close()
		while self.listenermgr.isAlive():
			time.sleep(0.25)

	def test_connect(self):
		"""Test connection of Initiator to server
		"""

		client = self.clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				print "Cannot connect to server."
				exit(1)
			time.sleep(0.25)

		# close all
		client.close()
		while client.isAlive():
			time.sleep(0.25)

	def test_startChannel(self):
		"""Test start of a channel
		"""

		client = self.clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				print "Cannot connect to server."
				exit(1)
			time.sleep(0.25)

		profileList = [[echoprofile.uri,None,None]]
		event = threading.Event()
		channelnum = client.startChannel(profileList, event)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)

		client.closeChannel(channelnum, event)
		while client.isChannelActive(channelnum):
			time.sleep(0.25)

		client.close()
		while client.isAlive():
			time.sleep(0.25)

if __name__ == '__main__':

	unittest.main()

