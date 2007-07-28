# $Id: tlsclient.py,v 1.6 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.6 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import sys
sys.path.append('..')

from beepy.transports.tls import TLSClientProtocol
from beepy.transports.tls import TLSClientFactory
from beepy.transports.tcp import reactor

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

class TLSEchoClientFactory(TLSClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = TLSEchoClientProtocol

    def clientConnectionLost(self, connection, reason):
        TLSClientFactory.clientConnectionLost(self, connection, reason)
        reactor.stop()

if __name__ == '__main__':
    factory = TLSEchoClientFactory()
    factory.addProfile(echoprofile)
    factory.addProfile(tlsprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

