# $Id: message.py,v 1.2 2002/08/02 03:36:41 jpwarren Exp $
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
# Messages are BEEP Management messages

import errors
import xml.dom.minidom
import string
import re

MessageTypes = ('greeting', 'start', 'close', 'ok', 'error', 'profile')

class Message:
	type = None		# The message type
	doc = None		# The DOM document of this message

	def __init__(self, type, doc):
		if type not in MessageTypes:
			raise MessageException('Invalid Message Type')
		self.type = type
		self.doc = doc
		if not self.validate():
			raise MessageInvalid('Invalid BEEP Message')

	def __del__(self):
		if self.doc:
			self.doc.unlink()

	# These validation checkers are far from complete.
	# Really need a validating parser or something for completeness
	def isGreeting(self):
		if self.type == 'greeting':
			return 1

	# Message of type profile are replies to a channel start MSG
	# that was successful
	def isProfile(self):
		if self.type == 'profile':
			return 1

	def isStart(self):
		if self.type == 'start':
			return 1

	def isError(self):
		if self.type == 'error':
			return 1

	def isOK(self):
		if self.type == 'ok':
			return 1

	def isClose(self):
		if self.type == 'close':
			return 1

	def getCloseChannelNum(self):
		if self.isClose():
			channelnum = self.doc.childNodes[0].getAttribute('number')
			return string.atoi(channelnum)

	def getStartChannelNum(self):
		if self.isStart():
			channelnum = self.doc.childNodes[0].getAttribute('number')
			return string.atoi(channelnum)

	def getProfileURI(self):
		"""getProfileURI returns the uri attribute of the first
		profile element found.
		inputs: None
		outputs: uri, string
		raises: None
		"""
		nodelist = self.doc.childNodes[0].getElementsByTagName('profile')
		uri = nodelist[0].getAttribute('uri')
		return uri

	def getProfileURIList(self):
		"""getProfileURIList() finds all the uri attributes of
		any profile elements and places them in a sequence, which
		is returned.
		inputs: None
		outputs: uriList, sequence of uri strings
		raises: None
		"""
		nodelist = self.doc.childNodes[0].getElementsByTagName('profile')
		uriList = []
		for node in nodelist:
			uriList.append(node.getAttribute('uri'))
		return uriList

	# This is a hack because I can't be bothered integrating
	# a validating XML parser into the core just yet. Maybe later.
	# All this does is validate the message against the
	# BEEP management profile DTD.
	# returns 1 if valid. If invalid, raises MessageException
	def validate(self):

		# firstly, the document should only have one child
		# node
		if len(self.doc.childNodes) != 1:
			raise MessageInvalid('More than one root tag')

		# ok, firstly, the first node of the doc must be
		# a 'greeting', 'start', 'profile', 'close' or 'ok'
		# element.

		currentNode = self.doc.childNodes[0]

		# Greeting type validation
		if currentNode.nodeName == 'greeting':
			nodelist = currentNode.getElementsByTagName('*')
			if len(nodelist) == 0:
				return 1
			for node in nodelist:
				if node.childNodes:
					raise MessageInvalid('Too many children')
				# profile is empty if in a greeting
				if node.nodeName == 'profile':
					if len(node.childNodes) != 0:
						raise MessageInvalid('profile not empty in greeting')
					if not node.hasAttribute('uri'):
						raise MessageInvalid
					return 1

				if node.nodeName != 'features' or node.nodeName == 'localize':
					return 1

		if currentNode.nodeName == 'start':
			if not currentNode.hasAttribute('number'):
				raise MessageInvalid('start tag has no number attribute')

			nodelist = currentNode.getElementsByTagName('*')
			foundProfile = 0
			for node in nodelist:
				if node.nodeName == 'profile':
					foundProfile = 1
					if not node.hasAttribute('uri'):
						raise MessageInvalid('start tag profile has no uri attribute')
				else:
					raise MessageInvalid('start tag contains non profile element')
			if not foundProfile:
				raise MessageInvalid('start tag has no profile element')
			return 1

		if currentNode.nodeName == 'close':
			nodelist = currentNode.getElementsByTagName('*')
			if len(nodelist) != 0:
				raise MessageInvalid('close message should not have children')

			if not currentNode.hasAttribute('number'):
				raise MessageInvalid('close message must have number attribute')

			if not currentNode.hasAttribute('code'):
				raise MessageInvalid('close message must have code attribute')

			return 1

		# Ok is easy to validate.
		if currentNode.nodeName == 'ok':

			# FIXME
			# This is here because minidom has no
			# convenience method for getting all
			# the attributes as a dictionary, which is poxy
			if len(currentNode._attrs.keys()) > 0:
				raise MessageInvalid("ok node shouldn't have attributes")

			if currentNode.childNodes:
				raise MessageInvalid("ok node shouldn't have children")
			else:
				return 1

		if currentNode.nodeName == 'error':
			nodelist = currentNode.getElementsByTagName('*')
			for node in nodelist:
				if node.nodeName != '#text' and node.nodeName != 'code' and node.nodeName != 'xml:lang':
					raise MessageInvalid('Invalid error subsection')
			return 1

		# positive reply to greeting with profile with init CDATA
		# This message type has a single profile with a CDATA section
		if currentNode.nodeName == 'profile':

			for node in currentNode.childNodes:
				if node.nodeName != '#text' and node.nodeName != '#cdata-section':
					raise MessageInvalid('Invalid profile content')

				# FIXME
				# minidom strips out CDATA sections and marks them as #text!
				# ARG! This is broken! doh! 

			return 1

		# If I make it this far, it's not valid
		raise MessageInvalid('Invalid BEEP Message')

class MessageException ( errors.BEEPException ):
	def __init__(self, args=None):
		self.args = args

class MessageInvalid( MessageException ):
	def __init__(self, args=None):
		self.args = args
