# $Id: test_tlsprofile.py,v 1.7 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.7 $
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
import threading

import POW
import POW.pkix

try:
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import tlsprofile
	from beepy.profiles import echoprofile
except ImportError:
	sys.path.append('../')
	from beepy.core import constants
	from beepy.core import logging
	from beepy.transports import tcpsession
	from beepy.profiles import profile
	from beepy.profiles import tlsprofile
	from beepy.profiles import echoprofile

import dummyclient

class TLSProfileTest(unittest.TestCase):

	def setUp(self):

#		sys.exit()

		# Set up logging
		self.serverlog = logging.Log(prefix="server: ")
		self.clientlog = logging.Log(prefix="client: ")

		# create the keyfiles

		# First we create the server key and cert
		# We self-sign the server cert since we're using
		# the server as the certificate authority for any
		# clients that want to connect.
		serverName = ( ('C', 'AU'),
		               ('ST', 'VIC'),
		               ('O', 'eigenmagic'),
		               ('CN', 'Test Server')
		             )
		self.serverKey = POW.Asymmetric()
		self.serverCert = POW.X509()
		self.serverCert.setIssuer( serverName )
		self.serverCert.setSubject( serverName )
		self.serverCert.setSerial( 1 )
		self.serverCert.setNotBefore( POW.pkix.time2utc(time.time()) )
		self.serverCert.setNotAfter( POW.pkix.time2utc(time.time()+86400) )
		self.serverCert.setPublicKey( self.serverKey )
		self.serverCert.sign( self.serverKey )

		# Now we create a client key and certificate.
		# We sign the certificate with the server key as that
		# is the criterion the server uses to verify the
		# key by default.
		clientName = ( ('C', 'AU'),
		               ('ST', 'VIC'),
		               ('O', 'eigenmagic'),
		               ('CN', 'Test Client')
		             )
		self.clientKey = POW.Asymmetric()
		self.clientCert = POW.X509()
		self.clientCert.setIssuer( serverName )
		self.clientCert.setSubject( clientName )
		self.clientCert.setSerial( 1 )
		self.clientCert.setNotBefore( POW.pkix.time2utc(time.time()) )
		self.clientCert.setNotAfter( POW.pkix.time2utc(time.time()+86400) )
		self.clientCert.setPublicKey( self.clientKey )
		self.clientCert.sign( self.serverKey )

		pdict1 = profile.ProfileDict()
		pdict1.addProfile(tlsprofile, self.configureServerTLS)
		pdict1.addProfile(echoprofile)
		self.listenermgr = tcpsession.TCPListenerManager(self.serverlog, pdict1, ('localhost', 1976) )

		while not self.listenermgr.isActive():
			time.sleep(0.25)

		# create and connect an initiator
		pdict2 = profile.ProfileDict()
		pdict2.addProfile(tlsprofile, self.configureClientTLS)
		pdict2.addProfile(echoprofile)
		self.clientmgr = tcpsession.TCPInitiatorManager(self.clientlog, pdict2)
		while not self.clientmgr.isActive():
			time.sleep(0.25)

	def tearDown(self):
		self.clientmgr.close()
		while not self.clientmgr.isExited():
			time.sleep(0.25)

		self.listenermgr.close()
		while not self.listenermgr.isExited():
			time.sleep(0.25)

	def configureServerTLS(self, theprofile):
	    self.serverlog.logmsg(logging.LOG_DEBUG, "Configuring Server TLS Profile via callback...")
	    theprofile.cert = self.serverCert
	    theprofile.key = self.serverKey

	def configureClientTLS(self, theprofile):
	    self.serverlog.logmsg(logging.LOG_DEBUG, "Configuring Client TLS Profile via callback...")
	    theprofile.cert = self.clientCert
	    theprofile.key = self.clientKey

	def test_createTLSSession(self):
		"""Test TLS """

		client = self.clientmgr.connectInitiator( ('localhost', 1976) )
		clientid = client.ID
		while not client.isActive():
			if client.isExited():
				self.log.logmsg(logging.LOG_ERR, "Erk! Channel isn't active!")
				exit(1)
			time.sleep(0.25)

		# Start a channel using TLS
		profileList = [[tlsprofile.uri,None,None]]
		event = threading.Event()
		channelnum = client.startChannel(profileList, event)
		event.wait(30)
		channel = client.getActiveChannel(channelnum)
		if not channel:
			self.log.logmsg(logging.LOG_DEBUG, "Erk! Channel isn't active!")
			sys.exit()

		while client.isAlive():
			time.sleep(0.25)

		# old client will have exited, so get the new client
		# for the same connection, as it has the same id
		client = self.clientmgr.getSessionById(clientid)

		while not client.isActive():
			time.sleep(0.25)

		# Create a channel on the new, authenticated, session
		# using the echo profile
		profileList = [[echoprofile.uri,None,None]]
		channelnum = client.startChannel(profileList)
		while not client.isChannelActive(channelnum):
			time.sleep(0.25)
		channel = client.getActiveChannel(channelnum)

		# send a message
		msgno = channel.sendMessage('Hello!')
		while channel.isMessageOutstanding():
			time.sleep(0.25)

		client.close()
		while not client.isExited():
			time.sleep(0.25)


if __name__ == '__main__':

    import profile
	profile.run( unittest.main(), tlsprofile.pstats )

