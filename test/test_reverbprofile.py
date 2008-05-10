# $Id: test_reverbprofile.py,v 1.9 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.9 $
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

from dummyclient import DummyProtocol
TESTIP = '127.0.0.1'
TESTPORT = 1976

from beepy.transports.tcp import BeepServerFactory
from beepy.profiles import reverbprofile

class ReverbProfileTest(unittest.TestCase):
    def setUp(self):

        factory = BeepServerFactory()
        factory.addProfile(reverbprofile)
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

    def test_createReverbChannel(self):
        """Test creation of a channel with the Reverb profile"""

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
            Then, start a channel with the REVERB profile
            """
            self.assertEqual( data, 'RPY 0 0 . 0 119\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/REVERB"/>\r\n</greeting>\r\nEND\r\n' )
            self.proto.sendmsg('MSG 0 0 . 51 122\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/REVERB"/>\r\n</start>END\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData2)
            return d

        def gotData2(data):
            self.assertEqual( data, 'RPY 0 0 . 119 92\r\nContent-Type: application/beep+xml\n\n<profile uri="http://www.eigenmagic.com/beep/REVERB"/>\r\nEND\r\n' )
            self.proto.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
            d = self.proto.getmsg()
            d.addCallback(gotData3)
            return d

        def gotData3(data):
            self.assertEqual( data, 'ERR 1 0 . 0 58\r\nPayload format incorrect\nUsage: <num> <secdelay> <content>END\r\n' )

        d = self.client.connectTCP(TESTIP, TESTPORT)
        d.addCallback(connected)
        return d
        
