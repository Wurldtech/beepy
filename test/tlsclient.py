## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

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


if __name__ == '__main__':
    factory = TLSEchoClientFactory()
    factory.addProfile(echoprofile)
    factory.addProfile(tlsprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

