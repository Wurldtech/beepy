# $Id: test_parser.py,v 1.5 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.5 $
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
# Test xml files are located in this directory as *.xml
# These tests are designed to test the parser in isolation to ensure
# that the XML validation and parsing occurs correctly, as this is
# crucial for the correct operation of the management profile.

import unittest
import sys, os.path
sys.path.append('../')

from beepy.profiles import mgmtparser

import logging
from beepy.core import debug
log = logging.getLogger('ParserTest')

class ParserTest(unittest.TestCase):

# RFC 3080 Section 2.3.1.1
	def test_2311001_parseGreeting(self):
		"""Parse greeting with no attribs or profiles"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )
		self.assert_( message.isGreeting() )

	def test_2311002_parseGreetingSingleProfile(self):
		"""Parse greeting with single profile"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_single_profile.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311003_parseGreetingMultipleProfile(self):
		"""Parse greeting with multiple profiles"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_multiple_profiles.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311004_parseGreetingSingleFeature(self):
		"""Parse greeting with single feature"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_single_feature.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311005_parseGreetingMultipleFeature(self):
		"""Parse greeting with multiple features"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_multiple_feature.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311006_parseGreetingSingleLocalize(self):
		"""Parse greeting with single localize"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_single_localize.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311007_parseGreetingMultipleLocalize(self):
		"""Parse greeting with multiple localize"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_with_multiple_localize.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311008_parseGreetingSingleFeatureLocalize(self):
		"""Parse greeting with single feature+localize"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_single_feature_localize.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311009_parseGreetingMultipleFeatureLocalize(self):
		"""Parse greeting with multiple feature+localize"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_multiple_feature_localize.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

	def test_2311010_parseGreetingMultipleEverything(self):
		"""Parse greeting with multiple everything"""
		parser = mgmtparser.Parser()
		file = open('beep_greeting_multiple_everything.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'greeting' )

# Section 2.3.1.2
	def test_2312001_parseStartSingleProfile(self):
		"""Parse start with single profile"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_single_profile.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312002_parseStartNoProfile(self):
		"""Parse start without profile (malformed)"""
		parser = mgmtparser.Parser()
		file = open('beep_start_no_profile.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_2312003_parseStartNegativeChannelNumber(self):
		"""Parse start with negative channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_start_negative_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312004_parseStartTooLargeChannelNumber(self):
		"""Parse start with too large channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_start_toolarge_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312005_parseStartAlphaNumber(self):
		"""Parse start with alpha channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_start_alpha_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312006_parseStartOddNumber(self):
		"""Parse start with odd channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_start_odd_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312007_parseStartEvenNumber(self):
		"""Parse start with even channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_start_even_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312008_parseStartMultipleProfile(self):
		"""Parse start with multiple profiles"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_multiple_profile.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312009_parseStartReadyCDATA(self):
		"""Parse start with profile ready CDATA section"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_ready_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312010_parseStartProceedCDATA(self):
		"""Parse start with profile proceed CDATA section"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_proceed_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'profile' )

	def test_2312011_parseStartBlobCDATA(self):
		"""Parse start with profile <blob> CDATA section"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_blob_cdata.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312012_parseStartBlobAndEncoding(self):
		"""Parse start with encoded profile <blob> CDATA section"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_blob_encoding.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312013_parseStartNoBlobAndEncoding(self):
		"""Parse start with ecoding but no CDATA section"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_encoding_noblob.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312014_parseStartProfileContentsTooLarge(self):
		"""Parse start with profile contents over 4k octets"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_profile_contents_toolarge.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

	def test_2312015_parseStartServername(self):
		"""Parse start with serverName"""
		parser = mgmtparser.Parser()
		file = open('beep_start_with_servername.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'start' )

# Section 2.3.1.3
	def test_2313001_parseClose(self):
		"""Parse close"""
		parser = mgmtparser.Parser()
		file = open('beep_close.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313002_parseCloseWithNegativeNumber(self):
		"""Parse close with negative channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_close_negative_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313003_parseCloseWithTooLargeNumber(self):
		"""Parse close with too large channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_close_toolarge_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313004_parseCloseWithAlphaNumber(self):
		"""Parse close with alpha channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_close_alpha_number.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313005_parseCloseWithNoNumber(self):
		"""Parse close with no channel number"""
		parser = mgmtparser.Parser()
		file = open('beep_close_no_number.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_2313006_parseCloseWithAlphaCode(self):
		"""Parse close with alpha code"""
		parser = mgmtparser.Parser()
		file = open('beep_close_alpha_code.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313006_parseCloseWithNoCode(self):
		"""Parse close with no code"""
		parser = mgmtparser.Parser()
		file = open('beep_close_no_code.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_2313007_parseCloseWithXMLLang(self):
		"""Parse close with xml:lang"""
		parser = mgmtparser.Parser()
		file = open('beep_close_xmllang.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

	def test_2313008_parseCloseWithXMLLangNoText(self):
		"""Parse close with xml:lang and no text"""
		parser = mgmtparser.Parser()
		file = open('beep_close_xmllang_no_text.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'close' )

# Section 2.3.1.4
	def test_2314001_parseOK(self):
		"""Parse ok"""
		parser = mgmtparser.Parser()
		file = open('beep_ok.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'ok' )

	def test_2314002_parseOKWithAttrs(self):
		"""Parse ok with attrs (malformed)"""
		parser = mgmtparser.Parser()
		file = open('beep_ok_with_attrs.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_2314003_parseOKWithChildren(self):
		"""Parse ok with children (malformed)"""
		parser = mgmtparser.Parser()
		file = open('beep_ok_with_children.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

# Section 2.3.1.5

	def test_2315001_parseError(self):
		"""Parse error"""
		parser = mgmtparser.Parser()
		file = open('beep_error.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

	def test_2315002_parseErrorWithText(self):
		"""Parse error with text"""
		parser = mgmtparser.Parser()
		file = open('beep_error_with_text.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

	def test_2315003_parseErrorWithInvalidCode(self):
		"""Parse error with invalid code"""
		parser = mgmtparser.Parser()
		file = open('beep_error_with_invalid_code.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

	def test_2315004_parseErrorWithXMLLang(self):
		"""Parse error with xml:lang"""
		parser = mgmtparser.Parser()
		file = open('beep_error_with_xmllang.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

	def test_2315004_parseErrorWithXMLLangNoText(self):
		"""Parse error with xml:lang but no text"""
		parser = mgmtparser.Parser()
		file = open('beep_error_with_xmllang_notext.xml')
		message = parser.parse(file)
		self.assertEqual( message.type, 'error' )

# Generally syntactically bad XML
	def test_parseMalformedCdataBeforeFirstTag(self):
		"""Parse Malformed XML Document: cdata before first tag"""
		parser = mgmtparser.Parser()
		file = open('beep_malformed_cdata_before_firsttag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterGreeting(self):
		"""Parse Malformed XML Document: cdata after greeting tag"""
		parser = mgmtparser.Parser()
		file = open('beep_malformed_cdata_after_greetingtag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterOK(self):
		"""Parse Malformed XML Document: cdata after ok tag"""
		parser = mgmtparser.Parser()
		file = open('beep_malformed_cdata_after_oktag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )

	def test_parseMalformedCdataAfterStart(self):
		"""Parse Malformed XML Document: cdata after start tag"""
		parser = mgmtparser.Parser()
		file = open('beep_malformed_cdata_after_starttag.xml')
		self.assertRaises( mgmtparser.ParserException, parser.parse, file )


if __name__ == '__main__':
	unittest.main()

