# $Id: saslanonymousprofile.py,v 1.2 2003/01/07 07:39:59 jpwarren Exp $
# $Revision: 1.2 $
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
# SASLProfile is the base SASL profile class
# It should be inherited from to implement particular
# SASL mechanisms

import saslprofile
from profile import TuningReset
from beepy.core import logging
from beepy.core import constants
from beepy.transports import sasltcpsession

__profileClass__ = "SASLAnonymousProfile"
uri = "http://iana.org/beep/SASL/ANONYMOUS"

class SASLAnonymousProfile(saslprofile.SASLProfile):
	"""A SASLAnonymousProfile is a SASL Profile that implements
	   the ANONYMOUS mechanism for anonymous authentication.
	"""

	def __init__(self, log, session, profileInit=None):
		self.authentid = None
		self.authid = None
		saslprofile.SASLProfile.__init__(self, log, session)
		self.log.logmsg(logging.LOG_DEBUG, "initstring: %s" % profileInit)

	def doProcessing(self):
		"""All doProcessing should do is move the session from
		   non-authenticated to authenticated.
		"""
		theframe = self.channel.recv()
		if theframe:
			error = self.parseError(theframe.payload)
			if error:
				self.log.logmsg(logging.LOG_NOTICE, "Error while authenticating: %s: %s" % (error[1], error[2]))
				return

			status = self.parseStatus(theframe.payload)
			if status:
				# do status code processing
				self.log.logmsg(logging.LOG_DEBUG, "status: %s" % status)
				if status == 'complete':
					# Server completed authentication, so we do a tuning reset
					sock = self.session.sock
					server_address = self.session.server_address
					sessmgr = self.session.sessmgr
					read_timeout = self.session.read_timeout

					self.log.logmsg(logging.LOG_DEBUG, "Creating new session...")
					newsess = sasltcpsession.SASLTCPInitiatorSession(sock, server_address, sessmgr, self.session, self.authentid, self.authid, read_timeout)
					self.log.logmsg(logging.LOG_DEBUG, "Raising tuning reset...")
					raise TuningReset("SASL ANONYMOUS authentication succeeded")

				elif status == 'abort':
					# other end has aborted negotiation, so we reset
					# to our initial state
					self.authentid = None
					self.authid = None

				elif status == 'continue':
					self.log.logmsg(logging.LOG_NOTICE, "continue during authentication")

			else:
				authentid = self.decodeBlob(theframe.payload)
				if authentid:
					self.log.logmsg(logging.LOG_DEBUG, "authentid: %s" % authentid)
					self.authentid = authentid
					# I've now dealt with the message sufficiently for it to
					# be marked as such, so we deallocate the msgno
					self.channel.deallocateMsgno(theframe.msgno)
					# Ok, start setting up for a tuning reset
					# copy connection to new session object
					sock = self.session.sock
					client_address = self.session.client_address
					sessmgr = self.session.sessmgr
					read_timeout = self.session.read_timeout

					# Session object should wait for this session thread to exit before
					# going to ACTIVE state.
					newsess = sasltcpsession.SASLTCPListenerSession(sock, client_address, sessmgr, self.session, self.authentid, self.authid, read_timeout)
					data = '<blob status="complete"/>'
					self.channel.sendReply(theframe.msgno, data)
					self.log.logmsg(logging.LOG_DEBUG, "Queued success message")
					# finally, reset Session
					raise TuningReset("SASL ANONYMOUS authentication succeeded")

	def sendAuth(self, authentid, authid=None):
		self.authentid = authentid
		data = self.encodeBlob(authentid)
		return self.channel.sendMessage(data)