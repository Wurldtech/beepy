# $Id: test_initiator.py,v 1.16 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.16 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

import sys
import time

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

from beepy.core.debug import log

from beepy.transports.tcp import BeepServerProtocol, BeepServerFactory
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

from dummyclient import DummyProtocol

TESTIP = '127.0.0.1'
TESTPORT = 1976

class InitiatorTestProtocol(BeepClientProtocol):

    def greetingReceived(self):
        #print "got greeting"
        pass

    def connectionLost(self, reason):
        #print "initiator connection lost"
        pass

class InitiatorTestFactory(BeepClientFactory):
    protocol = InitiatorTestProtocol

class InitTestServerProtocol(BeepServerProtocol):

    def connectionLost(self, reason):
        #print "listener connection lost"
        pass

class InitTestServerFactory(BeepServerFactory):

    protocol = InitTestServerProtocol

class TCPInitatorSessionTest(unittest.TestCase):

    def setUp(self):
        factory = InitTestServerFactory()
        self.serverport = reactor.listenTCP(TESTPORT, factory, interface=TESTIP)

    def tearDown(self):
        self.serverport.loseConnection()

    def test_connect(self):
        """
        Test a simple connection to a listening BEEP server
        """
        def isconnected(d=None):
            if d is None:
                d = defer.Deferred()
                
            if self.conn.state == 'connecting':
                #print "not yet connected."
                reactor.callLater(0.1, isconnected, d)
            elif self.conn.state == 'connected':
                #print "connected"
                d.callback(None)
                pass
            return d

        def connected(ignored):
            print "connected! yay!"
            self.conn.disconnect()
            
        factory = InitiatorTestFactory()
        self.conn = reactor.connectTCP(TESTIP, TESTPORT, factory)
        d = isconnected()
        d.addCallback(connected)
        return d

if __name__ == '__main__':

    unittest.main()

