# $Id: tlsprofile.py,v 1.4 2003/01/09 00:20:55 jpwarren Exp $
# $Revision: 1.4 $
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
# This file implements the TLS transport security profile
#

import profile
import saslprofile
from beepy.core import logging
from beepy.core import constants
from beepy.core import session
from beepy.transports import tlstcpsession

__profileClass__ = "TLSProfile"
uri = "http://iana.org/beep/TLS"

class TLSProfile(profile.Profile):
	"""A TLSProfile is a profile that implements the TLS
	   Transport Security Profile. It is used to set up a TLS
	   encrypted TCP session.
	"""

	def __init__(self, log, session, profileInit=None, keyFile='TLSServerPrivate.key', certFile='TLSServerCert.pem', passphrase='TeSt'):
		"""This generic TLS profile has no way of determining your
		   application specific key and certificate files. To do any sort
		   of funky processing (such as picking specific keyfiles or
		   certificates based on the address of the client, for example)
		   you have to subclass from this class and implement extra
		   bits and pieces to pass in the key and cert file locations.
		"""

		profile.Profile.__init__(self, log, session)
		self.log.logmsg(logging.LOG_DEBUG, "initstring: %s" % profileInit)

		self.keyFile = keyFile
		self.certFile = certFile
		self.passphrase = passphrase

		self.proceed = 1
		self.clientConfigured = 0

	def doProcessing(self):
		"""All doProcessing should do is move the session from
			insecure to secured.
		"""

		if self.proceed:

			if isinstance(self.session, session.Listener):
				# Listeners automatically start TLS negotiation

				sock = self.session.sock
				client_address = self.session.client_address
				sessmgr = self.session.sessmgr
				newsess = tlstcpsession.TLSTCPListener(sock, client_address, sessmgr, self.session, self.keyFile, self.certFile, self.passphrase)

				raise profile.TuningReset("Enabling server side TLS...")

			else:
				# Initiators need to have configured passphrases
				# etc. before proceeding.
				if self.clientConfigured:
					sock = self.session.sock
					server_address = self.session.server_address
					newsess = tlstcpsession.TLSTCPInitiator(sock, server_address, self.session.sessmgr, self.session, self.keyFile, self.certFile, self.passphrase )
					self.log.logmsg(logging.LOG_DEBUG, "Raising tuning reset...")
					raise profile.TuningReset("Enabling client side TLS...")


	def configureClient(self, keyFile, certFile, passphrase):
		self.keyFile = keyFile
		self.certFile = certFile
		self.passphrase = passphrase
		self.clientConfigured = 1

