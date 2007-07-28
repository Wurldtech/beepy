# $Id: test_saslanonymousprofile.py,v 1.16 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.16 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import unittest
import sys
import time
import threading

sys.path.append('../')

from beepy.core.debug import log

from beepy.transports.tcp import SASLServerProtocol
from beepy.transports.tcp import SASLServerFactory
from beepy.transports.tcp import SASLClientProtocol
from beepy.transports.tcp import SASLClientFactory

from beepy.transports.tcp import reactor

from beepy.profiles import saslanonymousprofile
from beepy.profiles import echoprofile

class SASLAnonClientProtocol(SASLClientProtocol):
    """ We subclass from the SASLClientProtocol so that
    we can define what should happen when various events
    occur.
    """
    def greetingReceived(self):

        ## Start a channel using the SASL/ANONYMOUS profile
        self.authchannel = self.newChannel(saslanonymousprofile)
        log.debug('attempting to start channel %d...' % self.authchannel)

    def channelStarted(self, channelnum, uri):
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

    def authenticationSucceeded(self):
        log.debug('overloaded authComplete')
        self.echochannel = self.newChannel(echoprofile)

class SASLAnonClientFactory(SASLClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = SASLAnonClientProtocol

class SASLAnonServerProtocol(SASLServerProtocol):

    def connectionLost(self, reason):
        reactor.stop()

class SASLAnonServerFactory(SASLServerFactory):

    protocol = SASLAnonServerProtocol

class SASLAnonymousProfileTest(unittest.TestCase):

    def setUp(self):
        factory = SASLAnonServerFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslanonymousprofile)        
        reactor.listenTCP(1976, factory, interface='127.0.0.1')

    def test_SASLClient(self):
        """Test SASL Anonymous with Initiator"""

        factory = SASLAnonClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslanonymousprofile)

        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()

        if factory.reason:
            raise Exception(factory.reason.getErrorMessage())

if __name__ == '__main__':

    unittest.main()

