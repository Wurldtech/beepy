# $Id: test_saslanonymousprofile.py,v 1.3 2002/10/07 05:52:04 jpwarren Exp $
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
from beep.profiles import saslanonymousprofile
from beep.profiles import echoprofile

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

#	def test_createSASLAnonymousSession(self):
#		"""Test SASL Anonymous with no CDATA init"""
#		pdict = profile.ProfileDict()
#		pdict['http://iana.org/beep/SASL/ANONYMOUS'] = saslanonymousprofile
#		sess = tcpsession.TCPSessionListener(self.log, pdict, 'localhost', 1976)
#
#		while sess.currentState != 'ACTIVE':
#			pass
#
#		# create and connect a client
#		client = dummyclient.DummyClient()
#		# send a greeting msg
#		client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
#		data = client.getmsg()
#
#		# create a channel with the SASL Anonymous profile
#		client.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://iana.org/beep/SASL/ANONYMOUS"/>\r\n</start>END\r\n')
#		data = client.getmsg()
#
#		self.assertEqual(data, 'RPY 0 0 . 117 90\r\nContent-Type: application/beep+xml\n\n<profile uri="http://iana.org/beep/SASL/ANONYMOUS"/>\r\nEND\r\n')
#
#		client.sendmsg('MSG 1 0 . 0 21\r\n<blob>aGVsbG8K</blob>END\r\n')
#		data = client.getmsg()
#		print "got reply: ", data
#
#		# time to regreet after tuning reset
#		client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
#		data = client.getmsg()
#		print "got reply: ", data
#
#		client.terminate()
#		sess.close()
#		time.sleep(1)

	def test_SASLClient(self):
		"""Test SASL Anonymous with Initiator"""
		# Create a server
		pdict1 = profile.ProfileDict()
		pdict1[saslanonymousprofile.uri] = saslanonymousprofile
		pdict1[echoprofile.uri] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)
		while not sess.isActive():
			pass

		# create an initiator manager
		pdict2 = profile.ProfileDict()
		pdict2[saslanonymousprofile.uri] = saslanonymousprofile
		pdict2[echoprofile.uri] = echoprofile
		clientmgr = tcpsession.TCPInitiatorSessionManager(self.log, pdict2)
		while not clientmgr.isActive():
			pass

		# Connect a client
		client = clientmgr.connectInitiator('localhost', 1976)
		clientid = client.ID
		print "client id: %d is: %s" % (clientid, client)
		while not client.isActive():
			pass

		# Start a channel using SASL/ANONYMOUS authentication
		profileList = [[saslanonymousprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			pass
		channel = client.getActiveChannel(channelnum)

		# Send our authentication information
		msgno = channel.profile.sendAuth('justin')
		while client.isAlive():
			pass

		# old client will have exited, so get the new client
		# for the same connection, as it has the same id
		print "getting client by id %d" % clientid
		client = clientmgr.getSessionById(clientid)
		print "Client is now id %d: %s" % (clientid, client)

		while not client.isActive():
			pass

		# Create a channel on the new, authenticated, session
		# using the echo profile
		profileList = [[echoprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			pass
		channel = client.getActiveChannel(channelnum)

		# send a message
		msgno = channel.sendMessage('Hello!')
		while channel.isMessageOutstanding():
			pass

		client.close()
		while not client.isExited():
			pass

		clientmgr.close()
		while not clientmgr.isExited():
			pass

		sess.close()
		while not sess.isExited():
			pass


if __name__ == '__main__':

	unittest.main()

