# $Id: test_saslotpprofile.py,v 1.1 2002/10/15 01:57:45 jpwarren Exp $
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
from beep.profiles import saslotpprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class SASLOTPProfileTest(unittest.TestCase):
	log = logging.Log()

	def test_createSASLOTPSession(self):
		"""Test SASL OTP with no CDATA init"""
		pdict1 = profile.ProfileDict()
		pdict1[saslotpprofile.uri] = saslotpprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)

		while sess.currentState != 'ACTIVE':
			pass

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2[saslotpprofile.uri] = saslotpprofile
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

		# Start a channel using SASL/OTP authentication
		profileList = [[saslotpprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			pass

		channel = client.getActiveChannel(channelnum)
		if not channel:
			self.log.logmsg(logging.LOG_DEBUG, "Erk! Channel isn't active!")
			sys.exit()

		# Send our authentication information
		msgno = channel.profile.sendAuth('justin', 'justin')
		while channel.isMessageOutstanding(msgno):
			pass

		client.closeChannel(channelnum)
		while client.isChannelActive(channelnum):
			pass
		print "Channel closed."

		client.close()
		while client.isAlive():
			pass

		sess.close()
		while sess.isAlive():
			pass


if __name__ == '__main__':

	unittest.main()

