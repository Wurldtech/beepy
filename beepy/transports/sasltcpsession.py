# $Id: sasltcpsession.py,v 1.1 2003/01/01 23:37:38 jpwarren Exp $
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
# 
# This class implements a DataStream object that communicates via TCP

from beepy.core import constants
from beepy.core import logging
from beepy.core import frame
from beepy.core import session
from beepy.core import saslsession

import tcpsession
import threading

class SASLTCPListenerSession(tcpsession.TCPListenerSession, saslsession.SASLListenerSession):

	def __init__(self, conn, client_address, sessmgr, oldsession, authentid, userid=None):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		self.request = conn
		self.connection = conn
		self.client_address = client_address
		self.sessmgr = sessmgr
		self.oldsession = oldsession

		# initialise as a TCPListenerSession
#		session.ListenerSession.__init__(self, self.sessmgr.log, self.sessmgr.profileDict)
		saslsession.SASLListenerSession.__init__(self, self.sessmgr.log, self.sessmgr.profileDict, authentid, userid)

		sessmgr.replaceSession(oldsession.ID, self)

		self.inbound = self.oldsession.inbound
		self.newframe = self.oldsession.newframe
		self.framebuffer = self.oldsession.framebuffer
		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self )
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session Thread to exit: %s" % self.oldsession )
		self.oldsession.join()
		self.log.logmsg(logging.LOG_DEBUG, "Old Session Thread finished: %s" % self.oldsession )
		self.log.logmsg(logging.LOG_INFO, "Tuning reset: reconnected to %s[%s]." % self.client_address )
		tcpsession.TCPListenerSession._stateINIT(self)
		self.transition('ok')

class SASLTCPInitiatorSession(tcpsession.TCPInitiatorSession, saslsession.SASLInitiatorSession):

	def __init__(self, conn, server_address, sessmgr, oldsession, authentid, userid=None):
		threading.Thread.__init__(self)
		self.shutdown = threading.Event()

		self.request = conn
		self.connection = conn
		self.server_address = server_address
		self.oldsession = oldsession

		# initialise as a TCPInitiatorSession
#		session.InitiatorSession.__init__(self, sessmgr.log, sessmgr.profileDict)
		saslsession.SASLInitiatorSession.__init__(self, sessmgr.log, sessmgr.profileDict, authentid, userid)

		sessmgr.replaceSession(oldsession.ID, self)

		# This is here to ensure that the message queue isn't
		# interrupted by the tuning reset. If we don't do this
		# we may lose messages sent just after the other side
		# resets but before we reset, as they will get read in
		# my the TCPCommsMixin to get the reset <ok/> message
		# as a batch.

		self.inbound = self.oldsession.inbound
		self.newframe = self.oldsession.newframe
		self.framebuffer = self.oldsession.framebuffer
		self.log.logmsg(logging.LOG_INFO, "%s: initialized" % self )
		self.start()

	def _stateINIT(self):
		self.log.logmsg(logging.LOG_DEBUG, "Waiting on old Session Thread to exit: %s" % self.oldsession )
		self.oldsession.join()
		self.log.logmsg(logging.LOG_DEBUG, "Old Session Thread finished: %s" % self.oldsession )
		self.log.logmsg(logging.LOG_INFO, "Tuning reset: reconnected to %s[%s]." % self.server_address )

		try:
			self.wfile = self.connection.makefile('wb', constants.MAX_OUTBUF)
			self.createChannelZero()
			self.queueOutboundFrames()
			self.sendPendingFrame()
			while not self.channels[0].profile.receivedGreeting:
				self.getInputFrame()
				self.processFrames()
			self.transition('ok')

		except Exception, e:
			self.log.logmsg(logging.LOG_ERR, "Connection to remote host failed: %s" % e)
			self.transition('error')

