# A basic echoclient for testing purposes

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.transports.twistedsession import BeepClientProtocol, BeepClientFactory

from twisted.internet import reactor

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

    def channelStarted(self, channelnum):
        log.debug('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.sendMessage('Hello World!')
        log.debug('Sent message with id: %s' % msgno)
        msgno = channel.sendMessage('Hello World 1!')
        msgno = channel.sendMessage('Hello World 2!')
        msgno = channel.sendMessage('Hello World 3!')
        msgno = channel.sendMessage('Hello World 4!')
        msgno = channel.sendMessage('Hello World 5!')

class EchoClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = EchoClientProtocol


if __name__ == '__main__':
    factory = EchoClientFactory()
    factory.addProfile(echoprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

