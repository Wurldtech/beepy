# $Id: saslanonymousprofile.py,v 1.5 2002/08/13 14:37:35 jpwarren Exp $
# $Revision: 1.5 $
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
from beep.core import logging
from beep.core import constants
from beep.transports import sasltcpsession

__profileClass__ = "SASLAnonymousProfile"

class SASLAnonymousProfile(saslprofile.SASLProfile):
	"""A SASLAnonymousProfile is a SASL Profile that implements
	   the ANONYMOUS mechanism for anonymous authentication.
	"""
	tuning = 0

	def __init__(self, log, session, profileInit=None):
		saslprofile.SASLProfile.__init__(self, log, session)
		self.log.logmsg(logging.LOG_DEBUG, "initstring: %s" % profileInit)
		self.tuning = 0

	def doProcessing(self):
		"""All doProcessing should do is move the session from
		   non-authenticated to authenticated.
		"""
		theframe = self.channel.recv()
		if theframe:
			status = self.parseStatus(theframe.payload)
			if status:
				# do status code processing
				raise NotImplementedError("status processing not implemented")
			else:
				authentid = self.decodeBlob(theframe.payload)
				if authentid:
					self.log.logmsg(logging.LOG_DEBUG, "authentid: %s" % authentid)

					# Ok, start setting up for a tuning reset
					# copy connection to new session object
					conn = self.session.connection
					client_address = self.session.client_address
					sessmgr = self.session.server

					# Session object should wait for this session thread to exit before
					# going to ACTIVE state.
					newsess = sasltcpsession.SASLTCPListenerSession(conn, client_address, sessmgr, self.session, authentid)
					data = '<blob status="complete">'
					self.channel.sendReply(theframe.msgno, data)
					self.log.logmsg(logging.LOG_DEBUG, "Queued success message")
					# finally, reset Session
					raise TuningReset("SASL ANONYMOUS authentication succeeded")

