# $Id: test_tlsprofile.py,v 1.18 2004/11/22 05:13:51 jpwarren Exp $
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

## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

import unittest
import sys
sys.path.append('..')

from beepy.core.debug import log

from beepy.transports.tls import TLSServerProtocol
from beepy.transports.tls import TLSServerFactory
from beepy.transports.tls import TLSClientProtocol
from beepy.transports.tls import TLSClientFactory

from beepy.transports.tcp import reactor

from beepy.profiles import echoprofile
from beepy.profiles import tlsprofile

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
        reactor.stop()

class TLSEchoClientFactory(TLSClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = TLSEchoClientProtocol

class TestTLSServerProtocol(TLSServerProtocol):
    """
    A TLS Test Server protocol
    """
#    def connectionLost(self, reason):
#        log.debug('Server connection lost: %s' % reason)

class TestTLSServerFactory(TLSServerFactory):
  
    protocol = TestTLSServerProtocol

class TLSProfileTest(unittest.TestCase):

    def setUp(self):
        ## We first have to create our test keys        
        import os
        os.system('python ./createTLSTestKeyCerts.py')

        factory = TestTLSServerFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(tlsprofile)
        factory.privateKeyFileName = 'serverKey.pem'
        factory.certificateFileName = 'serverCert.pem'
        reactor.listenTCP(1976, factory, interface='127.0.0.1')
        reactor.iterate()

    def tearDown(self):
        reactor.stop()
        reactor.iterate()

    def test_TLSClient(self):
        factory = TLSEchoClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(tlsprofile)

        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()

        log.debug('Finished reactor run')

        if factory.reason:
            log.debug('oh no! normal reason!')
            raise Exception(factory.reason.getErrorMessage())

if __name__ == '__main__':

    unittest.main()


