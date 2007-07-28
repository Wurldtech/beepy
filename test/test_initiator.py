# $Id: test_initiator.py,v 1.15 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.15 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import unittest
import sys
import time

sys.path.append('../')

from beepy.core.debug import log

from beepy.transports.tcp import BeepServerProtocol, BeepServerFactory
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

class InitiatorTestProtocol(BeepClientProtocol):

    def greetingReceived(self):
        self.shutdown()

    def connectionLost(self, reason):
        reactor.stop()

class InitiatorTestFactory(BeepClientFactory):
    protocol = InitiatorTestProtocol

class InitTestServerProtocol(BeepServerProtocol):

    def connectionLost(self, reason):
        reactor.stop()

class InitTestServerFactory(BeepServerFactory):

    protocol = InitTestServerProtocol

class TCPInitatorSessionTest(unittest.TestCase):

    def setUp(self):
        factory = InitTestServerFactory()
#        factory.addProfile(echoprofile)
        reactor.listenTCP(1976, factory, interface='127.0.0.1')
#        reactor.iterate()

    def tearDown(self):
        reactor.stop()
        reactor.iterate()

    def test_connect(self):
        """ Test a simple connection to a listening BEEP server
        """
        factory = InitiatorTestFactory()
        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()

if __name__ == '__main__':

    unittest.main()

