# $Id: test_listener.py,v 1.17 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.17 $
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
# These tests test the way a BEEP Listener server functions
# They test various framing format issues.

import sys
import time

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

from beepy.core import constants
from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepServerFactory

from beepy.core.debug import log
#from logging import DEBUG
#log.setLevel(DEBUG)

from dummyclient import DummyProtocol

TESTIP = '127.0.0.1'
TESTPORT = 1976

class ServerTest(unittest.TestCase):

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

    def test_2311000_validGreeting(self):
        """Test valid greeting"""

        def gotData(data):
            self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d
    
    def test_2311001_clientMultiGreeting(self):
        """Test connect from client with multiple greetings"""

        def gotData2(data):
            self.assertEqual(data, '' )
            
        def gotData1(data):
            self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )
            self.proto.sendmsg("RPY 0 0 . 51 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData1)
            return d

        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_clientStartChannel(self):
        """Test start channel with unsupported profile"""

        def gotData2(data):
            self.assertEqual(data, 'ERR 0 0 . 117 95\r\nContent-Type: application/beep+xml\n\n<error code="504">\r\n  Parameter Not Implemented\r\n</error>\r\nEND\r\n')
            
        def gotData1(data):
            self.proto.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="1">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData1)
            return d

        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_clientStartEvenChannel(self):
        """Test start channel with incorrectly even number"""

        def gotData2(data):
            self.assertEqual(data, 'ERR 0 0 . 117 96\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Syntax Error In Parameters\r\n</error>\r\nEND\r\n')

        def gotData1(data):
            self.proto.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="6">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData1)
            return d

        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_clientStartAlphaChannel(self):
        """Test start channel with alpha channel number"""

        def gotData2(data):
            self.assertEqual(data, 'ERR 0 0 . 117 106\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Requested channel number is invalid.\r\n</error>\r\nEND\r\n')
            
        def gotData1(data):
            self.proto.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="a">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d
        
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData1)
            return d

        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

if __name__ == '__main__':

    unittest.main()

