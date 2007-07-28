# $Id: test_framing.py,v 1.17 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.17 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
# These tests test the way a BEEP Listener server functions
# with regard to basic framing

import unittest
import sys
import time

sys.path.append('../')

from beepy.core.debug import log
#from logging import DEBUG
#log.setLevel(DEBUG)
    
import dummyclient

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepServerFactory
from beepy.transports.tcp import reactor

class FramingTest(unittest.TestCase):

    def setUp(self):

        factory = BeepServerFactory()
        factory.addProfile(echoprofile)
        reactor.listenTCP(1976, factory, interface='127.0.0.1')
        self.client = dummyclient.DummyClient()
        reactor.iterate()

        # get greeting message
        data = self.client.getmsg(1)

    def tearDown(self):
        self.client.terminate()
        reactor.iterate()
        reactor.stop()
        reactor.iterate()

    def test_FR001(self):
        """Test frame with invalid header format"""

        self.client.sendmsg("test\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg(1)

        self.assertEqual( data, '' )

    def test_FR002(self):
        """Test frame with invalid type"""

        self.client.sendmsg("WIZ 0 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR003(self):
        """Test frame with negative channel number"""

        self.client.sendmsg("MSG -5 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR004(self):
        """Test frame with too large channel number"""

        self.client.sendmsg("MSG 5564748837473643 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR005(self):
        """Test frame with non-numeric channel number"""

        self.client.sendmsg("MSG fred 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR006(self):
        """Test frame with unstarted channel number"""

        self.client.sendmsg("MSG 55 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR007(self):
        """Test frame with negative message number"""

        self.client.sendmsg("MSG 0 -6 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR008(self):
        """Test frame with too large message number"""

        self.client.sendmsg("MSG 0 6575488457584834 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR009(self):
        """Test frame with non-numeric message number"""

        self.client.sendmsg("MSG 0 fred . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR010(self):
        """Test frame with invalid more type"""

        self.client.sendmsg("MSG 0 0 g 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR011(self):
        """Test frame with negative seqno"""

        self.client.sendmsg("MSG 0 0 . -84 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR012(self):
        """Test frame with too large seqno"""

        self.client.sendmsg("MSG 0 0 . 75747465674373643 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR013(self):
        """Test frame with non-numeric seqno"""

        self.client.sendmsg("MSG 0 0 . fred 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR014(self):
        """Test frame with out of sequence seqno"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()

        self.client.sendmsg("MSG 0 0 . 0 13\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

    def test_FR015(self):
        """Test frame with negative size"""

        self.client.sendmsg("MSG 0 0 . 0 -15\r\nhere's some stuff\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR016(self):
        """Test frame with too large size"""

        self.client.sendmsg("MSG 0 0 . 0 574857345839457\r\nhere's some stuff\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR017(self):
        """Test frame with non-numeric size"""

        self.client.sendmsg("MSG 0 0 . 0 fred\r\nhere's some stuff\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR018(self):
        """Test frame with incorrect size"""

        self.client.sendmsg("MSG 0 0 . 0 5\r\nhere's some stuff\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR019(self):
        """Test frame with negative ansno"""

        self.client.sendmsg("ANS 0 0 . 0 0 -65\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR020(self):
        """Test frame with too large ansno"""

        self.client.sendmsg("ANS 0 0 . 0 0 5857483575747\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR021(self):
        """Test frame with non-numeric ansno"""

        self.client.sendmsg("ANS 0 0 . 0 0 fred\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR022(self):
        """Test frame with missing ansno"""

        self.client.sendmsg("ANS 0 0 . 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR023(self):
        """Test frame ansno in non-ANS frame"""

        self.client.sendmsg("RPY 0 0 . 0 0 15\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR024(self):
        """Test frame NUL as intermediate"""

        self.client.sendmsg("NUL 0 0 * 0 0\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR025(self):
        """Test frame NUL with non-zero size"""

        self.client.sendmsg("NUL 0 0 . 0 5\r\nhi!\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()        
        data = self.client.getmsg()

        self.assertEqual( data, '' )

    def test_FR026(self):
        """Test frame response to MSG never sent"""

        self.client.sendmsg("RPY 0 0 . 0 51\r\nContent-Type: application/beep+xml\r\n\r\n<greeting/>\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()
        reactor.iterate()
        reactor.iterate()        
#        data = self.client.getmsg()
        self.client.sendmsg("RPY 0 71 . 51 8\r\nHello!\r\nEND\r\n")
        reactor.iterate()
        reactor.iterate()
        reactor.iterate()        
        reactor.iterate()        

        data = self.client.getmsg()

        self.assertEqual( data, '' )

if __name__ == '__main__':

    unittest.main()

