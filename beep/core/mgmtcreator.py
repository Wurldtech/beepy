# $Id: mgmtcreator.py,v 1.2 2002/08/02 03:36:41 jpwarren Exp $
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
#
# The BEEP Management Profile XML Creator
# This implementation uses DOM
# This class creates the various BEEP messages required
# for channel management of BEEP
#

import errors

import types
import xml.dom.minidom

class Creator:
	doc = None
	log = None

	def __init__(self, log):
		self.log = log

	# Ensure we free up memory used by self.doc since Python
	# may not garbage collect it due to circular references
	def __del__(self):
		if self.doc:
			self.doc.unlink()

	def createGreetingMessage(self, profileURIList=None, features=None, localize=None):
		# This bit is for GC, since there's no guarantee python won't
		# leak memory because of circular references in DOM documents.
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		element = self.doc.createElement('greeting')

		# Set attributes, if they've been passed in
		if features:
			element.setAttribute('features', features)
		if localize:
			element.setAttribute('localize', localize)

		self.doc.appendChild(element)

		# Build a list of profiles as children to the greeting node
		if profileURIList:
			for profileURI in profileURIList:
				profile = self.doc.createElement('profile')
				profile.setAttribute('uri', profileURI)
				element.appendChild(profile)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception:
			raise CreatorException('Exception Converting to XML')

# createStartMessage takes a profileList, different from createGreetingMessage
# It is a list of profile descriptions. A profile description consists of a list thus:
#  ['profileURI', 'encoding', chardata]
# profileURI is a string of the URI for this profile. eg: http://iana.org/beep/SASL/OTP
# encoding is an optional encoding type specifying if the chardata within the
# profile element is a base64-encoded string
# chardata is up to 4k octets of initialization message given to the channel

	def createStartMessage(self, number, profileList, serverName=None):
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		# create start element
		element = self.doc.createElement('start')
		if type(number) != types.StringType:
			raise CreatorException('number is supposed to be a string, dude.')
		element.setAttribute('number', number)
		# Set the servername, if need be
		if serverName:
			element.setAttribute('serverName', serverName)

		self.doc.appendChild(element)

		# Build a list of profiles as children to the start node
		# A start message must have at least one, so we don't check
		# for the list as in createGreetingMessage() above
		for profiledesc in profileList:
			try:
				profile = self.doc.createElement('profile')
				profile.setAttribute('uri', profiledesc[0])
				if profiledesc[1]:
					profile.setAttribute('encoding', profiledesc[1])
				if profiledesc[2]:
					data = self.doc.createCDATASection(profiledesc[2])
					profile.appendChild(data)

			except IndexError, e:
				raise CreatorException('Malformed profileList')

			element.appendChild(profile)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception, e:
			raise
#			raise CreatorException('Exception Converting to XML')

	def createStartReplyMessage(self, profileURI):
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		# create profile element
		element = self.doc.createElement('profile')
#		if type(profileURI) != types.StringType:
#			raise CreatorException('profileURI is supposed to be a string, dude.')
		element.setAttribute('uri', profileURI)

		self.doc.appendChild(element)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception, e:
			raise
#			raise CreatorException('Exception Converting to XML')

	def createCloseMessage(self, number, code, xmlLang=None, text=None):
		# This bit is for GC, since there's no guarantee python won't
		# leak memory because of circular references in DOM documents.
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		element = self.doc.createElement('close')

		# Set attributes, if they've been passed in
		element.setAttribute('number', number)
		element.setAttribute('code', code)
		if xmlLang:
			element.setAttribute('xml:lang', xmlLang)
		if text:
			textNode = self.doc.createTextNode(text)
			element.appendChild(textNode)

		self.doc.appendChild(element)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception:
			raise CreatorException('Exception Converting to XML')

	def createOKMessage(self):
		# This bit is for GC, since there's no guarantee python won't
		# leak memory because of circular references in DOM documents.
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		element = self.doc.createElement('ok')

		self.doc.appendChild(element)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception:
			raise CreatorException('Exception Converting to XML')

	def createErrorMessage(self, code, text=None, xmlLang=None):
		# This bit is for GC, since there's no guarantee python won't
		# leak memory because of circular references in DOM documents.
		if self.doc:
			self.doc.unlink()
		self.doc = xml.dom.minidom.Document()
		self.doc.parentNode = self.doc
		self.doc.ownerDocument = self.doc

		element = self.doc.createElement('error')

		# Set attributes, if they've been passed in
		element.setAttribute('code', code)
		if xmlLang:
			element.setAttribute('xml:lang', xmlLang)
		if text:
			textNode = self.doc.createTextNode(text)
			element.appendChild(textNode)

		self.doc.appendChild(element)

		# write pretty printed xml, using 2 spaces for indentation
		try:
			return self.messageToString(self.doc)

		except Exception:
			raise CreatorException('Exception Converting to XML')

	# A convenience method to print messages without leading
	# <?xml version="1.0" ?> type strings in them
	def messageToString(self, DOMdocument):
		string = DOMdocument.toprettyxml('  ', '\r\n')
		return string[23:]

class CreatorException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

