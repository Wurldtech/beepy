# $Id: test_creator.py,v 1.1 2002/08/02 00:24:39 jpwarren Exp $
# $Revision: 1.1 $
# Test cases to test the BEEP Management message creator

import unittest
import sys, os.path
sys.path.append('../../')

from beep.core import mgmtcreator
from beep.core import logging

class ParserTest(unittest.TestCase):

	log = logging.Log()

	def test_createGreeting(self):
		"""Create empty greeting"""
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage()
		self.assertEqual(msg, '<greeting/>\r\n')

	def test_createGreetingSingleProfile(self):
		"""Create greeting with single profile"""
		profileURIList = ['http://eigenmagic.com/beep']
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage(profileURIList)
		self.assertEqual(msg, 
'<greeting>\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n</greeting>\r\n')

	def test_createGreetingMultiProfile(self):
		"""Create greeting with multiple profiles"""
		profileURIList = ['http://eigenmagic.com/beep', 'http://iana.org/beep/TLS', 'http://iana.org/beep/TLS/OTP']
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage(profileURIList)
		self.assertEqual(msg, 
'<greeting>\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n  <profile uri="http://iana.org/beep/TLS"/>\r\n  <profile uri="http://iana.org/beep/TLS/OTP"/>\r\n</greeting>\r\n')

	def test_createStartSingleProfile(self):
		"""Create start message with single profile"""
		profileList = [['http://eigenmagic.com/beep', None, None]]
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createStartMessage('1', profileList)
		self.assertEqual(msg, '<start number="1">\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n</start>\r\n')

	def test_createStartMultiProfile(self):
		"""Create start message with multiple profiles"""
		profileList = [['http://eigenmagic.com/beep', None, None], ['http://iana.org/beep/TLS', None, None], ['http://iana.org/beep/TLS/OTP', None, None]]
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createStartMessage('1', profileList)
		self.assertEqual(msg, '<start number="1">\r\n  <profile uri="http://eigenmagic.com/beep"/>\r\n  <profile uri="http://iana.org/beep/TLS"/>\r\n  <profile uri="http://iana.org/beep/TLS/OTP"/>\r\n</start>\r\n')
	def test_createClose(self):
		"""Create close message"""
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createCloseMessage('1', '220')
		self.assertEqual(msg, '<close code="220" number="1"/>\r\n')

	def test_createOKMessage(self):
		"""Create ok message"""
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createOKMessage()
		self.assertEqual(msg, '<ok/>\r\n')

	def test_createErrorMessage(self):
		"""Create error message"""
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createErrorMessage('550')
		self.assertEqual(msg, '<error code="550"/>\r\n')

	def test_createErrorMessageWithText(self):
		"""Create error message with text message"""
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createErrorMessage('550', 'Just Testing')
		self.assertEqual(msg, '<error code="550">\r\n  Just Testing\r\n</error>\r\n')

if __name__ == '__main__':
	unittest.main()

