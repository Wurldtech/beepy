# $Id: frame.py,v 1.5 2002/10/23 07:07:03 jpwarren Exp $
# $Revision: 1.5 $
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
# BEEP Frame class

import errors
import constants
import logging

import string

# RFC3080 only really defines one kind of frame, but states that
# transport mappings may define other frames. I don't really grok
# this yet, so I've just created a template object for Frames in
# general and subclassed it to a DataFrame. This way, if other
# frames are used for some reason, they can also subclass from
# Frame. All the guts are in DataFrame, but that's what the RFC says.

class Frame:
	def __init__(self, log, frameType):
		self.log = log
		if( frameType not in constants.FrameTypes ):	# bad FrameType
			raise FrameException("Invalid Type")
		else:
			self.frameType = frameType

class FrameException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

class DataFrame( Frame ):

	# Class constants
	frameType = 'data'
	TRAILER = str('END\r\n')		# Trailer

#	payload = None				# Payload object
#	type = ''
#	channelnum = -1
#	msgno = -1
#	more = ''
#	seqno = -1L
#	size = -1
#	ansno = None

	def __init__(self, log, channelnum=None, msgno=None, more=None, seqno=None, size=None, type='MSG', ansno=None, databuffer=None):
		Frame.__init__(self, log, self.frameType)

		# This lets us pass in a string type databuffer
		# to create a frame object
		if databuffer:
			self._bufferToFrame(databuffer)
			self.payload = ''
		else:
			self._checkValues(channelnum, msgno, more, seqno, size, type, ansno)
			self.type = type
			self.channelnum = channelnum
			self.msgno = msgno
			self.more = more
			self.seqno = seqno
			self.size = size
			self.payload = ''
			self.complete = 0
			if ansno:
				self.ansno = ansno
			else:
				self.ansno = None

	def __str__(self):

		# We use this handy function to return a string
		# representation of a DataFrame as required for
		# transportation
		framestring = "%s %i %i %s %i %i" % (constants.DataFrameTypes[self.type], self.channelnum, self.msgno, self.more, self.seqno, self.size)

		if( self.ansno ):
			framestring += "%i" % self.ansno
		framestring += '\r\n'
		framestring += "%s" % self.payload
		framestring += self.TRAILER
		return framestring

	# Check to see if this is a MSG frame
	def isMSG(self):
		if self.type == 'MSG':
			return 1

	def isRPY(self):
		if self.type == 'RPY':
			return 1

	def isANS(self):
		if self.type == 'ANS':
			return 1

	def isERR(self):
		if self.type == 'ERR':
			return 1

	def isNUL(self):
		if self.type == 'NUL':
			return 1

	def _bufferToFrame(self, data):

		# If there are any exceptions to this, it's either a
		# bug in the code, or crap data being sent in

		# Split the header into bits
		headerbits = string.split(data)

		# Check for valid header format
		if len(headerbits) != 6 and len(headerbits) != 7:
			raise DataFrameException("Header Format Invalid")
		self.type = headerbits[0]
#		self.log.logmsg(logging.LOG_DEBUG, "frame.py: type is: %s" % self.type )

		try:
			self.channelnum = string.atol(headerbits[1])
			self.msgno = string.atol(headerbits[2])
			self.more = headerbits[3]
			self.seqno = string.atol(headerbits[4])
			self.size = string.atol(headerbits[5])
			if len(headerbits) == 7:
				self.ansno = string.atol(headerbits[6])
			else:
				self.ansno = None

		except ValueError, e:
			raise DataFrameException("Non-numeric value in frame header")

		except Exception, e:
			raise DataFrameException("Unhandled exception in _bufferToFrame: %s: %s" % (e.__class__, e) )

		self._checkValues(self.channelnum, self.msgno, self.more, self.seqno, self.size, self.type, self.ansno)

	# Sanity checking of frame values
	# We do heaps of bounds checking here, because I'm
	# paranoid and it seems like a neat place to put it
	# It means DataFrames are only really bounds checked
	# upon initial creation, but that makes a certain amount
	# of sense
	def _checkValues(self, channelnum, msgno, more, seqno, size, type, ansno=None):
		if type not in constants.DataFrameTypes.keys():
			raise DataFrameException("Invalid DataFrame Type")

		if not constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL:
			raise DataFrameException("Channel number (%s) out of bounds" % channelnum)

		if not constants.MIN_MSGNO <= msgno <= constants.MAX_MSGNO:
			raise DataFrameException("MSGNO (%s) out of bounds" % msgno )

		if not more in constants.MoreTypes.keys():
			raise DataFrameException("Invalid More Type")

		if not constants.MIN_SEQNO <= seqno <= constants.MAX_SEQNO:
			raise DataFrameException("SEQNO (%s) out of bounds" % seqno)

		if type == constants.DataFrameTypes['ANS'] and not ansno:
			raise DataFrameException("No ansno for ANS frame")

		if ansno:
			if not type == constants.DataFrameTypes['ANS']:
				raise DataFrameException("ANSNO in non ANS frame" % ansno)

			elif not constants.MIN_ANSNO <= ansno <= constants.MAX_ANSNO:
				raise DataFrameException("ANSNO (%s) out of bounds" % ansno)

		if type == constants.DataFrameTypes['NUL']:
			if more == constants.MoreTypes['*']:
				raise DataFrameException('NUL frame cannot be intermediate')
			elif size != 0:
				raise DataFrameException('NUL frame of non-zero size')

		if not constants.MIN_SIZE <= size <= constants.MAX_SIZE:
				raise DataFrameException("Frame size (%s) out of bounds" % size)

	def setPayload(self, payload):
		mysize = len(payload)
		if mysize != self.size:
			raise DataFrameException('Size mismatch %i != %i' % (mysize, size))
		self.payload = payload

	def __repr__(self):
		return "<%s instance at %s>" % (self.__class__, hex(id(self)))

class DataFrameException(FrameException):
	def __init__(self, args=None):
		self.args = args

#	def __len__(self):
#		print "DEBUG: DFE.args: %s" % self.args

class SEQFrame(Frame):
	# class constants
	frameType = 'seq'
	TRAILER = str('\r\n')		# Trailer
	type = 'SEQ'

#	channelnum = -1
#	ackno = -1L
#	window = -1

	def __init__(self, log, channelnum=None, ackno=None, window=None, databuffer=None):
		Frame.__init__(self, log, self.frameType)

		# This lets us pass in a string type databuffer
		# to create a frame object
		if databuffer:
			self._bufferToFrame(databuffer)
		else:
			self._checkValues(channelnum, ackno, window)
			self.channelnum = channelnum
			self.msgno = ackno
			self.window = window

	def _bufferToFrame(self, data):

		# Now split the frame into bits
		headerbits = string.split(data)

		# Check for valid format
		if len(headerbits) != 4:
			raise SEQFrameException('Format Invalid')

		try:
			self.channelnum = string.atoi(headerbits[1])
			self.ackno = string.atoi(headerbits[2])
			self.window = string.atol(headerbits[3])

		except Exception, e:
			raise SEQFrameException('unknown error in _bufferToFrame')

		self._checkValues(self.channelnum, self.ackno, self.window)

	# Sanity checking
	def _checkValues(self, channelnum, ackno, window):

		if not constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL:
			raise SEQFrameException('Channel number (%s) out of bounds' % channelnum)

		if not constants.MIN_ACKNO <= ackno <= constants.MAX_ACKNO:
			raise SEQFrameException('ACKNO (%s) out of bounds' % ackno)

		if not constants.MIN_WINDOWSIZE <= window <= constants.MAX_WINDOWSIZE:
			raise SEQFrameException('windowsize (%s) out of bounds' % window )

	def __str__(self):

		# We use this handy function to return a string representation

		framestring = "SEQ "
		framestring = "%i %i %i" % (self.channelnum, self.ackno, self.window)
		framestring += self.TRAILER
		return framestring

class SEQFrameException(FrameException):
	def __init__(self, args=None):
		self.args = args

