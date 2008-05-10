# $Id: test_framing.py,v 1.18 2008/05/10 03:04:12 jpwarren Exp $
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
#
# These tests test the way a BEEP Listener server functions
# with regard to basic framing

import sys
import time

from twisted.trial import unittest
from twisted.internet import reactor, defer
from twisted.internet.protocol import ClientCreator

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepServerFactory
from beepy.transports.tcp import reactor

import logging
log = logging.getLogger()
    
from dummyclient import DummyProtocol

TESTIP = '127.0.0.1'
TESTPORT = 1976

class FramingTest(unittest.TestCase):

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

    def test_FR001(self):
        """Test frame with invalid header format"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("test\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR002(self):
        """Test frame with invalid type"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR003(self):
        """Test frame with negative channel number"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG -5 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR004(self):
        """Test frame with too large channel number"""
        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 5564748837473643 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR005(self):
        """Test frame with non-numeric channel number"""
        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG fred 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR006(self):
        """Test frame with unstarted channel number"""
        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 55 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR007(self):
        """Test frame with negative message number"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 -6 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR008(self):
        """Test frame with too large message number"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 6575488457584834 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR009(self):
        """Test frame with non-numeric message number"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 fred . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR010(self):
        """Test frame with invalid more type"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 g 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR011(self):
        """Test frame with negative seqno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . -84 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR012(self):
        """Test frame with too large seqno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . 75747465674373643 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR013(self):
        """Test frame with non-numeric seqno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . fred 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR014(self):
        """Test frame with out of sequence seqno"""

        def gotData2(data):
            self.assertEqual( data, '' )

        def gotData1(data):
            self.proto.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData1)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR015(self):
        """Test frame with negative size"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . 0 -15\r\nhere's some stuff\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR016(self):
        """Test frame with too large size"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . 0 574857345839457\r\nhere's some stuff\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR017(self):
        """Test frame with non-numeric size"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . 0 fred\r\nhere's some stuff\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR018(self):
        """Test frame with incorrect size"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR019(self):
        """Test frame with negative ansno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("ANS 0 0 . 0 0 -65\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR020(self):
        """Test frame with too large ansno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("ANS 0 0 . 0 0 5857483575747\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR021(self):
        """Test frame with non-numeric ansno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("ANS 0 0 . 0 0 fred\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR022(self):
        """Test frame with missing ansno"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("ANS 0 0 . 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR023(self):
        """Test frame ansno in non-ANS frame"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("RPY 0 0 . 0 0 15\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR024(self):
        """Test frame NUL as intermediate"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("NUL 0 0 * 0 0\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR025(self):
        """Test frame NUL with non-zero size"""

        def gotData(data):
            self.assertEqual( data, '' )
            
        def connected(proto):
            self.proto = proto
            self.proto.sendmsg("NUL 0 0 . 0 5\r\nhi!\r\nEND\r\n")
            d = self.proto.getmsg()
            d.addCallback(gotData)
            return d
        
        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d

    def test_FR026(self):
        """Test frame response to MSG never sent"""

        def gotData2(data):
            self.assertEqual( data, '' )

        def gotData1(data):
            self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )
            self.proto.sendmsg("RPY 0 71 . 51 8\r\nHello!\r\nEND\r\n")
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

