# $Id: test_creator.py,v 1.7 2004/08/22 04:15:58 jpwarren Exp $
# $Revision: 1.7 $
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
# Test cases to test the BEEP Management message creator

import unittest
import sys, os.path

sys.path.append('../')
from beepy.profiles import mgmtcreator

class CreatorTest(unittest.TestCase):

    def test_createGreeting(self):
        """Create empty greeting"""
        creator = mgmtcreator.Creator()
        msg = creator.createGreetingMessage()
        self.assertEqual(msg, '<greeting/>\r\n')

    def test_createGreetingSingleProfile(self):
        """Create greeting with single profile"""
        profileURIList = ['http://eigenmagic.com/beep']
        creator = mgmtcreator.Creator()
        msg = creator.createGreetingMessage(profileURIList)
        self.assertEqual(msg, 
'<greeting>\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n</greeting>\r\n')

    def test_createGreetingMultiProfile(self):
        """Create greeting with multiple profiles"""
        profileURIList = ['http://eigenmagic.com/beep', 'http://iana.org/beep/TLS', 'http://iana.org/beep/TLS/OTP']
        creator = mgmtcreator.Creator()
        msg = creator.createGreetingMessage(profileURIList)
        self.assertEqual(msg, 
'<greeting>\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n  <profile uri="http://iana.org/beep/TLS"/>\r\n  <profile uri="http://iana.org/beep/TLS/OTP"/>\r\n</greeting>\r\n')

    def test_createStartSingleProfile(self):
        """Create start message with single profile"""
        profileList = [['http://eigenmagic.com/beep', None, None]]
        creator = mgmtcreator.Creator()
        msg = creator.createStartMessage('1', profileList)
        self.assertEqual(msg, '<start number="1">\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n</start>\r\n')

    def test_createStartMultiProfile(self):
        """Create start message with multiple profiles"""
        profileList = [['http://eigenmagic.com/beep', None, None], ['http://iana.org/beep/TLS', None, None], ['http://iana.org/beep/TLS/OTP', None, None]]
        creator = mgmtcreator.Creator()
        msg = creator.createStartMessage('1', profileList)
        self.assertEqual(msg, '<start number="1">\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n  <profile uri="http://iana.org/beep/TLS"/>\r\n  <profile uri="http://iana.org/beep/TLS/OTP"/>\r\n</start>\r\n')
    def test_createClose(self):
        """Create close message"""
        creator = mgmtcreator.Creator()
        msg = creator.createCloseMessage('1', '220')
        self.assertEqual(msg, '<close code="220" number="1"/>\r\n')

    def test_createOKMessage(self):
        """Create ok message"""
        creator = mgmtcreator.Creator()
        msg = creator.createOKMessage()
        self.assertEqual(msg, '<ok/>\r\n')

    def test_createErrorMessage(self):
        """Create error message"""
        creator = mgmtcreator.Creator()
        msg = creator.createErrorMessage('550')
        self.assertEqual(msg, '<error code="550">\r\n  Requested Action Not Taken\r\n</error>\r\n')

    def test_createErrorMessageWithText(self):
        """Create error message with text message"""
        creator = mgmtcreator.Creator()
        msg = creator.createErrorMessage('550', 'Just Testing')
        self.assertEqual(msg, '<error code="550">\r\n  Just Testing\r\n</error>\r\n')

if __name__ == '__main__':
    unittest.main()

