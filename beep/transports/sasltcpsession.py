# $Id: sasltcpsession.py,v 1.3 2002/08/22 05:03:35 jpwarren Exp $
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
# 
# This class implements a DataStream object that communicates via TCP

from beep.core import constants
from beep.core import logging
from beep.core import frame
from beep.core import session
from beep.core import saslsession

import tcpsession
import threading

class SASLTCPListenerSession(tcpsession.TCPListenerSession, saslsession.SASLListenerSession):

	def __init__(self, conn, client_address, server, oldsessionThread, authentid, userid=None):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		self.request = conn
		self.connection = conn
		self.client_address = client_address
		self.server = server
		self.oldsessionThread = oldsessionThread

		# Get the log info from the server
		self.log = self.server.log

		# initialise as a TCPListenerSession
		session.ListenerSession.__init__(self, self.server.log, self.server.profileDict)
		saslsession.SASLListenerSession.__init__(self, self.log, self.profileDict, authentid, userid)

		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self )
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session Thread to exit: %s" % self.oldsessionThread )
		self.oldsessionThread.join()
		self.log.logmsg(logging.LOG_DEBUG, "Old Session Thread finished: %s" % self.oldsessionThread )
#		while self.oldsessionThread.isAlive():
#			pass
#		self.oldsessionThread.join(['30'])
		self.log.logmsg(logging.LOG_INFO, "Tuning reset: reconnected to %s[%s]." % self.client_address )
		tcpsession.TCPListenerSession._stateINIT(self)
		self.transition('ok')

class SASLTCPInitiatorSession(tcpsession.TCPInitiatorSession, saslsession.SASLInitiatorSession):
	def __init__(self, log, profileDict, host, port, sock, authentid, userid=None):
		threading.Thread.__init__(self)
		saslsession.SASLInitiatorSession.__init__(self, log, profileDict, authentid, userid)

		# I'm already connected to the remote end, so we just update some
		# information
		self.server_address = (host, port)
		self.connection = sock

