# $Id: test_initiator.py,v 1.8 2004/01/06 04:18:08 jpwarren Exp $
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

import unittest
import sys
import time

import threading

sys.path.append('../')

from beepy.transports.twistedsession import BeepServerFactory
from beepy.transports.twistedsession import BeepClientProtocol, BeepClientFactory
from twisted.internet import reactor

import logging
from beepy.core import debug

log = logging.getLogger('test_initiator')

class InitiatorTestProtocol(BeepClientProtocol):

    def greetingReceived(self):
        log.info('Greeting received in client')
        self.shutdown()

class InitiatorTestFactory(BeepClientFactory):
    protocol = InitiatorTestProtocol

class TCPInitatorSessionTest(unittest.TestCase):

    def setUp(self):
        factory = BeepServerFactory()
#        factory.addProfile(echoprofile)
        reactor.listenTCP(1976, factory, interface='127.0.0.1')
        reactor.iterate()

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

