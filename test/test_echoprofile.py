# $Id: test_echoprofile.py,v 1.10 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.10 $
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

import unittest
import sys
import time

import logging
sys.path.append('..')

from beepy.core import debug

log = logging.getLogger('test_echoprofile')
log.setLevel(logging.DEBUG)

import dummyclient

from beepy.transports.tcp import BeepServerFactory
from beepy.transports.tcp import reactor
from beepy.profiles import echoprofile

class EchoProfileTest(unittest.TestCase):

    def my_callback(self, profile):
        """ This is a test of the profile callback functionality
        """
        print "I am a callback from object: %s" % profile

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

    def test_createEchoChannel(self):
        """Test creation of a channel with the Echo profile"""

        # send a greeting msg
        self.client.sendmsg('RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n')
        reactor.iterate()
        data = self.client.getmsg(1)

        # create a channel with the ECHO profile
        self.client.sendmsg('MSG 0 0 . 51 120\r\nContent-type: application/beep+xml\r\n\r\n<start number="1">\r\n<profile uri="http://www.eigenmagic.com/beep/ECHO"/>\r\n</start>END\r\n')
        reactor.iterate()
        data = self.client.getmsg(1)

        self.client.sendmsg('MSG 1 0 . 0 8\r\nHello!\r\nEND\r\n')
        reactor.iterate()
        data = self.client.getmsg(1)
        self.assertEqual(data, 'RPY 1 0 . 0 8\r\nHello!\r\nEND\r\n')

        self.client.sendmsg('MSG 1 1 . 8 8\r\nHello!\r\nEND\r\n')
        reactor.iterate()
        data = self.client.getmsg(1)
        self.assertEqual(data, 'RPY 1 1 . 8 8\r\nHello!\r\nEND\r\n')

if __name__ == '__main__':

    unittest.main()

