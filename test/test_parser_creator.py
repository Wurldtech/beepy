# $Id: test_parser_creator.py,v 1.3 2003/01/07 07:40:00 jpwarren Exp $
# $Revision: 1.3 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002 Justin Warren <daedalus@eigenmagic.com>
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

try:
	from beepy.core import logging
	from beepy.core import mgmtparser
	from beepy.core import mgmtcreator
except ImportError:
	sys.path.append('../')
	from beepy.core import logging
	from beepy.core import mgmtparser
	from beepy.core import mgmtcreator

class ParserTest(unittest.TestCase):

	def setUp(self):
		# Set up logging
		self.log = logging.Log(logfile)
		self.log.loglevel = loglevel

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

