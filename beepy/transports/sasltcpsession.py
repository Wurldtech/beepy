# $Id: sasltcpsession.py,v 1.3 2003/01/09 00:20:55 jpwarren Exp $
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

from beepy.core import constants
from beepy.core import logging
from beepy.core import frame
from beepy.core import saslsession

import tcpsession

class SASLTCPListener(tcpsession.TCPListener, saslsession.SASLSession):

	def __init__(self, sock, client_address, sessmgr, oldsession, authentid, userid=None, read_timeout=1):

		self.oldsession = oldsession
		self.sessmgr = sessmgr

		saslsession.SASLSession.__init__(self, authentid, userid)
		tcpsession.TCPListener.__init__(self, sock, client_address, sessmgr, read_timeout)

		self.sessmgr.replaceSession(oldsession.ID, self)

		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self )

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session Thread to exit: %s" % self.oldsession )
		self.oldsession.join()
		self.log.logmsg(logging.LOG_INFO, "Tuning reset: reconnected to %s[%s]." % self.client_address )
		tcpsession.TCPListener._stateINIT(self)
		self.transition('ok')

class SASLTCPInitiator(tcpsession.TCPInitiator, saslsession.SASLSession):

	def __init__(self, sock, server_address, sessmgr, oldsession, authentid, userid=None, read_timeout=1):

		self.oldsession = oldsession
		self.sessmgr = sessmgr
		self.sock = sock

		saslsession.SASLSession.__init__(self, authentid, userid)
		tcpsession.TCPInitiator.__init__(self, sessmgr.log, sessmgr.profileDict, server_address, sessmgr, read_timeout)

		self.sessmgr.replaceSession(oldsession.ID, self)

		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self )

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session Thread to exit: %s" % self.oldsession )
		self.oldsession.join()
		self.log.logmsg(logging.LOG_DEBUG, "Old Session Thread finished: %s" % self.oldsession )
		self.log.logmsg(logging.LOG_INFO, "Tuning reset: reconnected to %s[%s]." % self.server_address )

		try:
			self.startIOThreads(self.sock)

			self.createChannelZero()
			while not self.channels[0].profile.receivedGreeting:
				if self._stop.isSet():
					self.transition('close')
					return
				self.processFrames()
			self.log.logmsg(logging.LOG_DEBUG, 'initiator initialized successfully')
			self.transition('ok')
			return

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
			self.transition('error')

