# $Id: test_client.py,v 1.3 2002/08/05 07:04:26 jpwarren Exp $
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

class ClientTest(unittest.TestCase):
# A sleeptime is required between shutting down one session listener
# and creating another one to prevent "address already in use" errors
# This is a feature, not a bug
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_connectClient(self):
		"""Test connect from client"""
		# create the server
		pdict1 = profile.ProfileDict()
		pdict1['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		listener = tcpsession.TCPSessionListener(self.log, pdict1, 'localhost', 1976)

		# create and connect a client
		pdict2 = profile.ProfileDict()
		pdict2['http://www.eigenmagic.com/beep/ECHO'] = echoprofile
		client = tcpsession.TCPInitiatorSession(self.log, pdict2, 'localhost', 1976)
		startProfile = [['http://www.eigenmagic.com/beep/ECHO',None,None]]
		# Wait for reception of greeting
		while not client.receivedGreeting:
			pass

		client.startChannel(startProfile)
		time.sleep(1)
		client.close()
		listener.close()
		time.sleep(1)

if __name__ == '__main__':

	unittest.main()

