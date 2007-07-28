# $Id: test_parser_creator.py,v 1.10 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.10 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
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

