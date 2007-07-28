# $Id: test_listener.py,v 1.16 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.16 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
# These tests test the way a BEEP Listener server functions
# They test various framing format issues.

import unittest
import sys
import time

sys.path.append('../')
from beepy.core import constants
from beepy.profiles import profile
from beepy.profiles import echoprofile

from beepy.core.debug import log
#from logging import DEBUG
#log.setLevel(DEBUG)

import dummyclient

from beepy.transports.tcp import reactor
from beepy.transports.tcp import BeepServerFactory

class ServerTest(unittest.TestCase):

    def setUp(self):

        factory = BeepServerFactory()
        factory.addProfile(echoprofile)
        reactor.listenTCP(1976, factory, interface='127.0.0.1')
        self.client = dummyclient.DummyClient()
        reactor.iterate()
        
    def tearDown(self):
        self.client.terminate()
        reactor.iterate()
        reactor.stop()
        reactor.iterate()

    def test_2311000_validGreeting(self):
        """Test valid greeting"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()

        data = self.client.getmsg(1)

        self.assertEqual( data, 'RPY 0 0 . 0 117\r\nContent-Type: application/beep+xml\n\n<greeting>\r\n  <profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</greeting>\r\nEND\r\n' )

    def test_2311001_clientMultiGreeting(self):
        """Test connect from client with multiple greetings"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        data = self.client.getmsg(1)

        self.client.sendmsg("RPY 0 0 . 51 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()
        data = self.client.getmsg(1)

        self.assertEqual(data, '' )

    def test_clientStartChannel(self):
        """Test start channel with unsupported profile"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        
        data = self.client.getmsg(1)
        self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="1">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
        reactor.iterate()

        data = self.client.getmsg(1)

        self.assertEqual(data, 'ERR 0 0 . 117 95\r\nContent-Type: application/beep+xml\n\n<error code="504">\r\n  Parameter Not Implemented\r\n</error>\r\nEND\r\n')

    def test_clientStartEvenChannel(self):
        """Test start channel with incorrectly even number"""
        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        data = self.client.getmsg(1)

        self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="6">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')
        reactor.iterate()
        data = self.client.getmsg(1)

        self.assertEqual(data, 'ERR 0 0 . 117 96\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Syntax Error In Parameters\r\n</error>\r\nEND\r\n')

    def test_clientStartAlphaChannel(self):
        """Test start channel with alpha channel number"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        data = self.client.getmsg(1)
        self.client.sendmsg('MSG 0 0 . 51 118\r\nContent-Type: application/beep+xml\r\n\r\n<start number="a">\r\n  <profile uri="http://iana.org/beep/SASL/OTP"/>\r\n</start>\r\nEND\r\n')

        reactor.iterate()
        data = self.client.getmsg(1)
        self.assertEqual(data, 'ERR 0 0 . 117 106\r\nContent-Type: application/beep+xml\n\n<error code="501">\r\n  Requested channel number is invalid.\r\n</error>\r\nEND\r\n')

if __name__ == '__main__':

    unittest.main()

