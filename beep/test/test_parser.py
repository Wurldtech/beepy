# $Id: test_parser.py,v 1.2 2002/08/02 03:36:41 jpwarren Exp $
# $Revision: 1.2 $
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
# Test xml files are located in this directory as *.xml

import unittest
import sys, os.path
sys.path.append('../../')

from beep.core import mgmtparser
from beep.core import logging

class ParserTest(unittest.TestCase):

	log = logging.Log()
#	log.debuglevel = 0

	def test_parseMalformedCdataBeforeFirstTag(self):
		"""Parse Malformed XML Document: cdata before first tag"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_cdata_before_firsttag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterGreeting(self):
		"""Parse Malformed XML Document: cdata after greeting tag"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_cdata_after_greetingtag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterOK(self):
		"""Parse Malformed XML Document: cdata after ok tag"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_cdata_after_oktag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterStart(self):
		"""Parse Malformed XML Document: cdata after start tag"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_cdata_after_starttag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedOKWithAttrs(self):
		"""Parse Malformed XML Document: ok tag with attrs"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_ok_with_attrs.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedOKWithChildren(self):
		"""Parse Malformed XML Document: ok tag with children"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_ok_with_children.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedStartWithoutProfile(self):
		"""Parse Malformed XML Document: start tag without profile"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_malformed_start_without_profile.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseGreeting(self):
		"""Parse empty greeting"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_greeting.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )
		self.assert_( message.isGreeting() )

	def test_parseGreetingSingleProfile(self):
		"""Parse single profile greeting"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_greeting_with_single_profile.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_parseGreetingMultipleProfile(self):
		"""Parse multiple profile greeting"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_greeting_with_multiple_profiles.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_parseOK(self):
		"""Parse ok"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_ok.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'ok' )

	def test_parseClose(self):
		"""Parse close"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_close.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_parseStartSingleProfile(self):
		"""Parse start with single profile"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_start_with_single_profile.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_parseStartReadyCDATA(self):
		"""Parse start with profile ready CDATA section"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_start_with_ready_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_parseStartProceedCDATA(self):
		"""Parse start with profile proceed CDATA section"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_start_with_proceed_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'profile' )

	def test_parseStartBlobCDATA(self):
		"""Parse start with profile <blob> CDATA section"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_start_with_blob_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_parseError(self):
		"""Parse error"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_error.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

	def test_parseErrorWithText(self):
		"""Parse error with text"""
		parser = mgmtparser.Parser(self.log)
		file = open('beep_error_with_text.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

if __name__ == '__main__':
	unittest.main()

