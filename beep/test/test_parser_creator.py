# $Id: test_parser_creator.py,v 1.1 2002/08/02 00:24:40 jpwarren Exp $
# $Revision: 1.1 $
# Test cases to test the BEEP Management message parser
# This is a sanity test to check that the parser can read
# messages created by the creator

import unittest
import sys, os.path
sys.path.append('../../')

from beep.core import logging
from beep.core import mgmtparser
from beep.core import mgmtcreator

class ParserTest(unittest.TestCase):

	log = logging.Log()

	def test_parseGreeting(self):
		"""Parse empty greeting"""
		parser = mgmtparser.Parser(self.log)
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage()
		message = parser.parse(msg)
		self.assertEqual( message.type, 'greeting' )

	def test_parseGreetingSingleProfile(self):
		"""Parse single profile greeting"""
		parser = mgmtparser.Parser(self.log)
		profileURIList = ['http://eigenmagic.com/beep']
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage(profileURIList)
		message = parser.parse(msg)
		self.assertEqual( message.type, 'greeting' )

	def test_parseGreetingMultipleProfile(self):
		"""Parse multiple profile greeting"""
		parser = mgmtparser.Parser(self.log)
		profileURIList = ['http://eigenmagic.com/beep', 'http://iana.org/beep/TLS', 'http://iana.org/beep/TLS/OTP']
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createGreetingMessage(profileURIList)
		message = parser.parse(msg)
		self.assertEqual( message.type, 'greeting' )

	def test_parseClose(self):
		"""Parse close"""
		parser = mgmtparser.Parser(self.log)
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createCloseMessage('1', '220')
		message = parser.parse(msg)
		self.assertEqual( message.type, 'close' )

	def test_parseOK(self):
		"""Parse ok"""
		parser = mgmtparser.Parser(self.log)
		creator = mgmtcreator.Creator(self.log)
		msg = creator.createOKMessage()
		message = parser.parse(msg)
		self.assertEqual( message.type, 'ok' )

if __name__ == '__main__':
	unittest.main()

