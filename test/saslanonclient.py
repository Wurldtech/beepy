## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

import sys
sys.path.append('..')

from beepy.transports.twistedsession import SASLClientProtocol
from beepy.transports.twistedsession import SASLClientFactory

from twisted.internet import reactor
from twisted.application import internet, service

from beepy.profiles import echoprofile
from beepy.profiles import saslanonymousprofile

import logging
from beepy.core import debug

log = logging.getLogger('saslanonclient')

## Ok, let's define our client application

class SASLAnonClientProtocol(SASLClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        ## Do anonymous authentication
        self.authchannel = self.newChannel(saslanonymousprofile)
        log.debug('attempting to start channel %d...' % self.authchannel)

    def channelStarted(self, channelnum):
        log.debug('started channel %d', channelnum)
        if channelnum == self.authchannel:
            log.debug('Authentication channel started successfully.')
            channel = self.getChannel(channelnum)
            msgno = channel.profile.sendAuth('hello!')

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

    def authenticationComplete(self):
        log.debug('overloaded authComplete')
        self.echochannel = self.newChannel(echoprofile)

class SASLAnonClientFactory(SASLClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = SASLAnonClientProtocol


if __name__ == '__main__':
    factory = SASLAnonClientFactory()
    factory.addProfile(echoprofile)
    factory.addProfile(saslanonymousprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

