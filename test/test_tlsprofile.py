# $Id: test_tlsprofile.py,v 1.20 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.20 $
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

## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

import unittest
import sys

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.python.util import sibpath

import logging
#from beepy.core.debug import log
log = logging.getLogger()

from beepy.transports.tls import TLSServerProtocol
from beepy.transports.tls import TLSServerFactory
from beepy.transports.tls import TLSClientProtocol
from beepy.transports.tls import TLSClientFactory

from beepy.profiles import echoprofile
from beepy.profiles import tlsprofile

TESTIP = '127.0.0.1'
TESTPORT = 1976

## Ok, let's define our client application

class TLSEchoClientProtocol(TLSClientProtocol):
    """ We subclass from the TLSClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('tls client has greeting')
        if not self.TLS:
            ## Start a new channel asking for TLS
            self.authchannel = self.newChannel(tlsprofile)
            log.debug('attempting to start channel %d...' % self.authchannel)
        else:
            log.debug('TLS channel is on.')
            self.echochannel = self.newChannel(echoprofile)
            log.debug('attempting to start echo channel %d...' % self.echochannel)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        if not self.TLS:
            if channelnum == self.authchannel:
                log.debug('TLS channel started successfully.')
                channel = self.getChannel(channelnum)

                ## Turn on TLS
                msgno = channel.profile.sendReady()
        else:
            if channelnum == self.echochannel:
                log.debug('Echo channel started successfully.')
                channel = self.getChannel(channelnum)
                msgno = channel.sendMessage('Echo 1!')
                msgno = channel.sendMessage('Echo 2!')
                msgno = channel.sendMessage('Echo 3!')
                msgno = channel.sendMessage('Echo 4!')
                msgno = channel.sendMessage('Echo 5!')
                msgno = channel.sendMessage('Echo 6!')

    def connectionLost(self, reason):
        log.debug("client lost connection: %s" % reason)

class TLSEchoClientFactory(TLSClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = TLSEchoClientProtocol

class TestTLSServerProtocol(TLSServerProtocol):
    """
    A TLS Test Server protocol
    """
    def connectionLost(self, reason):
        #log.debug('Server connection lost: %s' % reason)
        pass

class TestTLSServerFactory(TLSServerFactory):
  
    protocol = TestTLSServerProtocol

class TLSProfileTest(unittest.TestCase):

    def setUp(self):
        ## We first have to create our test keys        
        import os
        keygen_program = sibpath(__file__, 'createTLSTestKeyCerts.py')
        os.system('python %s' % keygen_program)

        factory = TestTLSServerFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(tlsprofile)
        factory.privateKeyFileName = sibpath(__file__, 'serverKey.pem')
        factory.certificateFileName = sibpath(__file__, 'serverCert.pem')
        self.serverport = reactor.listenTCP(TESTPORT, factory, interface=TESTIP)

    def tearDown(self):
        self.serverport.loseConnection()
        
    def test_TLSClient(self):
        """
        Test connecting with TLS enabled
        """

        def isconnected(d=None):
            #print "checking connectedness"
            if d is None:
                d = defer.Deferred()
                
            if self.conn.state == 'connecting':
                #print "not yet connected."
                reactor.callLater(0.1, isconnected, d)
            elif self.conn.state == 'connected':
                #print "connected"
                d.callback(None)

            elif self.conn.state == 'disconnected':
                d.errback(ValueError("Client disconnected before we detected it connecting. Test is broken."))
                pass
            return d

        def connected(ignored):
            #print "connected! yay!"
            self.conn.disconnect()

        factory = TLSEchoClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(tlsprofile)

        self.conn = reactor.connectTCP(TESTIP, TESTPORT, factory)
        d = isconnected()
        d.addCallback(connected)
        return d

