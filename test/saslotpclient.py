# $Id: saslotpclient.py,v 1.4 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
## This test client authenticates via SASL Anonymous
## before opening a channel with the echo profile

import sys
sys.path.append('..')

from beepy.transports.tcp import SASLClientProtocol
from beepy.transports.tcp import SASLClientFactory

from beepy.transports.tcp import reactor

from beepy.profiles import echoprofile
from beepy.profiles import saslotpprofile

import logging
from beepy.core import debug

log = logging.getLogger('saslanonclient')

## Ok, let's define our client application

class SASLAnonClientProtocol(SASLClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    username = 'fred'
    passphrase = 'This is a test'
    
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        ## Do anonymous authentication
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
        log.debug('Authentication Succeeded!')
        self.echochannel = self.newChannel(echoprofile)

class SASLAnonClientFactory(SASLClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = SASLAnonClientProtocol


if __name__ == '__main__':
    factory = SASLAnonClientFactory()
    factory.addProfile(echoprofile)
    factory.addProfile(saslotpprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

