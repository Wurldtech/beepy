# $Id: test_tlsprofile.py,v 1.8 2003/12/23 04:36:40 jpwarren Exp $
# $Revision: 1.8 $
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

## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

import unittest
import sys
sys.path.append('..')

from beepy.transports.twistedsession import TLSClientProtocol
from beepy.transports.twistedsession import TLSClientFactory

from twisted.internet import reactor
from twisted.application import internet, service

from beepy.profiles import echoprofile
from beepy.profiles import tlsprofile

import logging
from beepy.core import debug

log = logging.getLogger('tlsclient')

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

    def channelStarted(self, channelnum):
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

class TLSEchoClientFactory(TLSClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = TLSEchoClientProtocol

class TLSProfileTest(unittest.TestCase):

    def test_TLSClient(self):
        factory = TLSEchoClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(tlsprofile)

        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()

if __name__ == '__main__':

    unittest.main()
