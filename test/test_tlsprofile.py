# $Id: test_tlsprofile.py,v 1.4 2003/01/08 07:13:38 jpwarren Exp $
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
	from beepy.profiles import tlsprofile
	from beepy.profiles import echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import tlsprofile
	from beepy.profiles import echoprofile

import dummyclient

class TLSProfileTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.log = logging.Log()

		self.keyFile = 'TLSClientPrivate.key'
		self.certFile = 'TLSClientCert.pem'
		self.passphrase = 'TeSt'

		sys.exit()

	def test_createTLSSession(self):
		"""Test TLS """
		pdict1 = profile.ProfileDict()
		pdict1[tlsprofile.uri] = tlsprofile
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)

		while sess.currentState != 'ACTIVE':
			time.sleep(0.25)

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2[tlsprofile.uri] = tlsprofile
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.log, pdict2)
		while not clientmgr.isActive():
			time.sleep(0.25)

		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				self.log.logmsg(logging.LOG_ERR, "Erk! Channel isn't active!")
				exit(1)
			time.sleep(0.25)

		# Start a channel using TLS
		profileList = [[tlsprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)

		channel = client.getActiveChannel(channelnum)
		if not channel:
			self.log.logmsg(logging.LOG_DEBUG, "Erk! Channel isn't active!")
			sys.exit()

		# Now configure authentication parameters
		channel.profile.configureClient(self.keyFile, self.certFile, self.passphrase)

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

