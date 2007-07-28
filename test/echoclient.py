# $Id: echoclient.py,v 1.9 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.9 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

import logging
from beepy.core import debug

log = logging.getLogger('echoclient')

## Ok, let's define our client application

class EchoClientProtocol(BeepClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        self.newChannel(echoprofile)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.sendMessage('Hello World!')
        log.debug('Sent message with id: %s' % msgno)
        msgno = channel.sendMessage('Hello World 1!')
#        msgno = channel.sendMessage('Hello World 2!')
#        msgno = channel.sendMessage('Hello World 3!')
#        msgno = channel.sendMessage('Hello World 4!')
#        msgno = channel.sendMessage('Hello World 5!')
        self.shutdown()

class EchoClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = EchoClientProtocol

    def clientConnectionLost(self, connection, reason):
        BeepClientFactory.clientConnectionLost(self, connection, reason)
        reactor.stop()

if __name__ == '__main__':
    factory = EchoClientFactory()
    factory.addProfile(echoprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

