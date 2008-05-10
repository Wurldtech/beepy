# $Id: test_echoprofile.py,v 1.18 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.18 $
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

import sys
import time

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

from beepy.core.debug import log
#from logging import DEBUG
#log.setLevel(DEBUG)

from beepy.transports.tcp import BeepServerFactory
from beepy.profiles import echoprofile

from dummyclient import DummyProtocol
TESTIP = '127.0.0.1'
TESTPORT = 1976

class EchoProfileTest(unittest.TestCase):

    def setUp(self):

        factory = BeepServerFactory()
        factory.addProfile(echoprofile)
        self.serverport = reactor.listenTCP(TESTPORT, factory, interface=TESTIP)

        self.client = ClientCreator(reactor, DummyProtocol)
        self.proto = None

    def tearDown(self):
        if self.proto:
            self.proto.transport.loseConnection()
            if self.proto.later_call:
                try:
                    self.proto.later_call.cancel()
                    self.proto.later_call = None
                except Exception, e:
                    print "exception: e"
                    raise
                
        self.serverport.loseConnection()

    def test_createEchoChannel(self):
        """Test creation of a channel with the Echo profile"""

        def connected(proto):
            """
            When connected, send a greeting.
            """
            self.proto = proto
            self.proto.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d

        def gotData(data):
            """
            When we get a response to our greeting, check it.
            Then, start a channel with the ECHO profile
            """
            self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )
            self.proto.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</start>END\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def gotData2(data):
            """
            Check that the channel start was successful.
            Then, send a message on the channel.
            """
            self.assertEqual( data, 'RPY 0 0 . 117 90\r\nContent-Type: application/beep+xml\n\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\nEND\r\n')
            self.proto.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData3)
            return d

        def gotData3(data):
            """
            Check that we got the right response to our message on channel 1
            Then, send another message.
            """
            self.assertEqual( data, 'RPY 1 0 . 0 8\r\nHello!\r\nEND\r\n' )
            self.proto.sendmsg('MSG 1 1 . 8 8\r\nHello!\r\nEND\r\n')            
            d = self.proto.getmsg()
            d.addCallback(gotData4)
            return d

        def gotData4(data):
            """
            Check we got the right response to our 2nd message on channel 1
            Then, close down the channel.
            """
            self.assertEqual(data, 'RPY 1 1 . 8 8\r\nHello!\r\nEND\r\n')
            self.proto.sendmsg('MSG 0 1 . 171 70\r\nContent-type: application/beep+xml\r\n\r\n<close code="200" number="1"/>\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData5)
            return d
            
        def gotData5(data):
            """
            Check the channel was closed.
            """
            self.assertEqual(data, 'RPY 0 1 . 207 43\r\nContent-Type: application/beep+xml\n\n<ok/>\r\nEND\r\n')
            
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

if __name__ == '__main__':

    unittest.main()

