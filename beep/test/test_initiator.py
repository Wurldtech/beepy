# $Id: test_initiator.py,v 1.1 2002/09/18 07:08:18 jpwarren Exp $
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
from beep.profiles import echoprofile

import dummyclient

# This class assumes a server is available.
# It tests the responses given to the client under a
# variety of situations. Check the server logs to
# see what the server was up to at the time.
# It pauses for a second before shutting down the client
# to make sure the server doesn't just dump pending messages
# on an unexpected disconnect.
class TCPInitatorSessionTest(unittest.TestCase):
	log = logging.Log()

#	def test_connect(self):
#		"""Test connection of Initiator to server
#		"""
#		pdict1 = profile.ProfileDict()
#		pdict1['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
#		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)
#		while sess.currentState != 'ACTIVE':
#			pass
#
#		# create and connect an initiator
#		client = tcpsession.TCPInitiatorSession(self.log, pdict1, 'localhost', 1976)
#		client.close()
#		sess.close()
#		while sess.isAlive():
#			pass

	def test_startChannel(self):
		"""Test start of a channel
		"""
		pdict1 = profile.ProfileDict()
		pdict1['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		sess = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)
		while sess.currentState != 'ACTIVE':
			pass

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		client = tcpsession.TCPInitiatorSession(self.log, pdict2, 'localhost', 1976)
		while client.currentState != 'ACTIVE':
			pass

		self.log.logmsg(logging.LOG_DEBUG, "client profileDict: %s" % client.profileDict )

		profileList = [['http://www.eigenmagic.com/beep/ECHO',None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			pass
		print "Channel started."

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

