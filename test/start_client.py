# $Id: start_client.py,v 1.1 2002/12/28 06:16:08 jpwarren Exp $
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

class StartClient(unittest.TestCase):
# A sleeptime is required between shutting down one session listener
# and creating another one to prevent "address already in use" errors
# This is a feature, not a bug
	log = logging.Log()
#	log.debuglevel = logging.LOG_DEBUG

	def test_startClient(self):

		# create and connect a client
		pdict2 = profile.ProfileDict()
		client = tcpsession.TCPSession(self.log, pdict2, 0, 1, 'localhost', 1976)
		time.sleep(1)

		client.terminate()

if __name__ == '__main__':

	unittest.main()

