# $Id: test_parser_creator.py,v 1.8 2004/08/22 04:15:58 jpwarren Exp $
# $Revision: 1.8 $
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
# Test cases to test the BEEP Management message parser
# This is a sanity test to check that the parser can read
# messages created by the creator

import unittest
import sys, os.path

sys.path.append('../')
from beepy.profiles import mgmtparser
from beepy.profiles import mgmtcreator

from beepy.core.debug import log

class ParserCreatorTest(unittest.TestCase):

    def setUp(self):
        self.parser = mgmtparser.Parser()
        self.creator = mgmtcreator.Creator()

    def test_parseGreeting(self):
        """Parse empty greeting"""
        msg = self.creator.createGreetingMessage()
        message = self.parser.parse(msg)
        self.assertEqual( message.type, 'greeting' )

    def test_parseGreetingSingleProfile(self):
        """Parse single profile greeting"""
        profileURIList = ['http://eigenmagic.com/beep']
        msg = self.creator.createGreetingMessage(profileURIList)
        message = self.parser.parse(msg)
        self.assertEqual( message.type, 'greeting' )

    def test_parseGreetingMultipleProfile(self):
        """Parse multiple profile greeting"""
        profileURIList = ['http://eigenmagic.com/beep', 'http://iana.org/beep/TLS', 'http://iana.org/beep/TLS/OTP']
        msg = self.creator.createGreetingMessage(profileURIList)
        message = self.parser.parse(msg)
        self.assertEqual( message.type, 'greeting' )

    def test_parseClose(self):
        """Parse close"""
        msg = self.creator.createCloseMessage('1', '220')
        message = self.parser.parse(msg)
        self.assertEqual( message.type, 'close' )

    def test_parseOK(self):
        """Parse ok"""
        msg = self.creator.createOKMessage()
        message = self.parser.parse(msg)
        self.assertEqual( message.type, 'ok' )

if __name__ == '__main__':
    unittest.main()

