# $Id: test_saslotpprofile.py,v 1.7 2003/01/08 07:13:38 jpwarren Exp $
# $Revision: 1.7 $
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
	from beepy.profiles import saslotpprofile
	from beepy.profiles import echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import saslotpprofile
	from beepy.profiles import echoprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class SASLOTPProfileTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.serverlog = logging.Log(prefix="server: ")
		self.clientlog = logging.Log(prefix="client: ")
		# We have to create a OTP database to use for the tests.
		generator = saslotpprofile.OTPGenerator(self.clientlog)
		self.username = 'justin'
		self.passphrase = 'This is a test.'
		self.seed = 'TeSt'
		self.algo = 'md5'
		self.sequence = 99

		passhash = generator.createOTP(self.username, self.algo, self.seed, self.passphrase, self.sequence)

	def test_createSASLOTPSession(self):
		"""Test SASL OTP with no CDATA init"""
		pdict1 = profile.ProfileDict()
		pdict1[saslotpprofile.uri] = saslotpprofile
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.serverlog, pdict1, 'localhost', 1976)

		while sess.currentState != 'ACTIVE':
			time.sleep(0.25)

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2[saslotpprofile.uri] = saslotpprofile
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.clientlog, pdict2)
		while not clientmgr.isActive():
			time.sleep(0.25)

		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				self.client.logmsg(logging.LOG_ERR, "Erk! Channel isn't active!")
				exit(1)
			time.sleep(0.25)

		# Start a channel using SASL/OTP authentication
		profileList = [[saslotpprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)

		channel = client.getActiveChannel(channelnum)
		if not channel:
			self.client.logmsg(logging.LOG_DEBUG, "Erk! Channel isn't active!")
			sys.exit()

		# Send our authentication information
		msgno = channel.profile.sendAuth(self.passphrase, self.username, self.username)
		while channel.isMessageOutstanding(msgno):
			time.sleep(0.25)

		# Check to see if authentication worked.
		while client.isAlive():
			time.sleep(0.25)

		# old client will have exited, so get the new client
		# for the same connection, as it has the same id
		client = clientmgr.getSessionById(clientid)

		while not client.isActive():
			time.sleep(0.25)

		# Create a channel on the new, authenticated, session
		# using the echo profile
		profileList = [[echoprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)
		channel = client.getActiveChannel(channelnum)

		# send a message
		msgno = channel.sendMessage('Hello!')
		while channel.isMessageOutstanding():
			time.sleep(0.25)

		client.close()
		while not client.isExited():
			time.sleep(0.25)

		clientmgr.close()
		while not clientmgr.isExited():
			time.sleep(0.25)

		sess.close()
		while not sess.isExited():
			time.sleep(0.25)


if __name__ == '__main__':

	unittest.main()

