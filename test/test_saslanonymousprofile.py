# $Id: test_saslanonymousprofile.py,v 1.4 2003/01/08 05:38:12 jpwarren Exp $
# $Revision: 1.4 $
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
	from beepy.profiles import saslanonymousprofile
	from beepy.profiles import echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import saslanonymousprofile
	from beepy.profiles import echoprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class SASLAnonymousProfileTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.clientlog = logging.Log(prefix='client: ')
		self.serverlog = logging.Log(prefix='server: ')

	def test_SASLClient(self):
		"""Test SASL Anonymous with Initiator"""
		# Create a server
		pdict1 = profile.ProfileDict()
		pdict1[saslanonymousprofile.uri] = saslanonymousprofile
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.serverlog, pdict1, 'localhost', 1976, name="servermgr: localhost[1976]")
		while not sess.isActive():
			time.sleep(0.25)

		# create an initiator manager
		pdict2 = profile.ProfileDict()
		pdict2[saslanonymousprofile.uri] = saslanonymousprofile
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.clientlog, pdict2, name="clientmgr")
		while not clientmgr.isActive():
			time.sleep(0.25)

		# Connect a client
		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			time.sleep(0.25)

		self.clientlog.logmsg(logging.LOG_DEBUG, "Client connected.")

		# Start a channel using SASL/ANONYMOUS authentication
		profileList = [[saslanonymousprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)
		channel = client.getActiveChannel(channelnum)

		# Send our authentication information
		msgno = channel.profile.sendAuth('justin')
		while client.isAlive():
			time.sleep(0.25)

		# old client will have exited, so get the new client
		# for the same connection, as it has the same id
		self.clientlog.logmsg(logging.LOG_DEBUG, "Getting new client...")
		client = clientmgr.getSessionById(clientid)
		self.clientlog.logmsg(logging.LOG_DEBUG, "New client: %s" % client)

		while not client.isActive():
			time.sleep(0.25)
		self.clientlog.logmsg(logging.LOG_DEBUG, "Got new client...")

		# Create a channel on the new, authenticated, session
		# using the echo profile
		profileList = [[echoprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)
		channel = client.getActiveChannel(channelnum)
		self.clientlog.logmsg(logging.LOG_DEBUG, "Got active channel...")

		# send a message
		msgno = channel.sendMessage('Hello!')
		self.clientlog.logmsg(logging.LOG_DEBUG, "Sent Hello (msgno: %d)" % msgno)

		while channel.isMessageOutstanding():
			time.sleep(0.25)
		self.clientlog.logmsg(logging.LOG_DEBUG, "Got reply to Hello.")

		self.clientlog.logmsg(logging.LOG_DEBUG, "Stopping client...")

		client.stop()
		while not client.isExited():
			time.sleep(0.25)
		self.clientlog.logmsg(logging.LOG_DEBUG, "closed client...")

		clientmgr.close()
		while not clientmgr.isExited():
			time.sleep(0.25)

		sess.close()
		while not sess.isExited():
			time.sleep(0.25)

		self.clientlog.logmsg(logging.LOG_DEBUG, "Test complete.")


if __name__ == '__main__':

	unittest.main()

