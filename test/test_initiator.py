# $Id: test_initiator.py,v 1.12 2004/08/02 09:46:08 jpwarren Exp $
# $Revision: 1.12 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

import unittest
import sys
import time

sys.path.append('../')

import logging
from beepy.core import debug
log = logging.getLogger('beepy')

from beepy.transports.tcp import BeepServerProtocol, BeepServerFactory
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

class InitiatorTestProtocol(BeepClientProtocol):

    def greetingReceived(self):
        log.info('Greeting received in client')
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

