# $Id: test_saslotpprofile.py,v 1.18 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.18 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

import sys
import time

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

from beepy.core.debug import log

from beepy.transports.tcp import SASLServerProtocol
from beepy.transports.tcp import SASLServerFactory
from beepy.transports.tcp import SASLClientProtocol
from beepy.transports.tcp import SASLClientFactory

from beepy.profiles import saslotpprofile
from beepy.profiles import echoprofile

TESTIP = '127.0.0.1'
TESTPORT = 1976

class SASLOTPClientProtocol(SASLClientProtocol):
    """ We subclass from SASLClientProtocol to define
    what we want to do when various events occur
    """
    username = 'fred'
    passphrase = 'This is a test'
    
    def greetingReceived(self):

        ## Start a channel using the SASL/OTP profile
        self.authchannel = self.newChannel(saslotpprofile)
        log.debug('attempting to start channel %d...' % self.authchannel)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        if channelnum == self.authchannel:
            log.debug('Authentication channel started successfully.')

            channel = self.getChannel(channelnum)
            msgno = channel.profile.sendAuth(self.passphrase, self.username)

        elif channelnum == self.echochannel:
            log.debug('Echo channel started successfully.')
            channel = self.getChannel(channelnum)
            msgno = channel.sendMessage('Echo 1!')
            msgno = channel.sendMessage('Echo 2!')
            msgno = channel.sendMessage('Echo 3!')
            msgno = channel.sendMessage('Echo 4!')
            msgno = channel.sendMessage('Echo 5!')
            msgno = channel.sendMessage('Echo 6!')

        else:
            log.debug('Unknown channel created: %d' % channelnum)

    def authenticationSucceeded(self):
        log.debug('overloaded authComplete')
        self.echochannel = self.newChannel(echoprofile)

class SASLOTPClientFactory(SASLClientFactory):

    protocol = SASLOTPClientProtocol

class SASLOTPServerProtocol(SASLServerProtocol):

    def connectionLost(self, reason):
        #print "server connection lost"
        pass

class SASLOTPServerFactory(SASLServerFactory):
  
    protocol = SASLOTPServerProtocol

class SASLOTPProfileTest(unittest.TestCase):

    def setUp(self):
        factory = SASLOTPServerFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslotpprofile)
        self.serverport = reactor.listenTCP(TESTPORT, factory, interface=TESTIP)

        ## We create a new testing OTP database for
        ## testing the library. This assumes the server
        ## is running in the same directory as this tester
        generator = saslotpprofile.OTPGenerator()
        username = 'fred'
        seed = 'TeSt'
        passphrase = 'This is a test'
        algo = 'md5'
        sequence = 99

        passhash = generator.createOTP(username, algo, seed, passphrase, sequence)

    def tearDown(self):
        self.serverport.loseConnection()

    def test_createSASLOTPSession(self):
        """Test SASL OTP with no CDATA init"""
        def isconnected(d=None):
            if d is None:
                d = defer.Deferred()
                
            if self.conn.state == 'connecting':
                #print "not yet connected."
                reactor.callLater(0.1, isconnected, d)
            elif self.conn.state == 'connected':
                #print "connected"
                d.callback(None)
                pass
            elif self.conn.state == 'disconnected':
                d.errback(ValueError("Client disconnected before we detected it connecting. Test is broken."))
                pass
            return d

        def connected(ignored):
            #print "connected! yay!"
            self.conn.disconnect()

        factory = SASLOTPClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslotpprofile)

        self.conn = reactor.connectTCP(TESTIP, TESTPORT, factory)
        d = isconnected()
        d.addCallback(connected)
        return d

