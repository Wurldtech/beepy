# $Id: frame.py,v 1.1 2002/08/02 00:24:28 jpwarren Exp $
# $Revision: 1.1 $
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
	log = None
	frameType = None				# default type

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
	frameType = 'data'
	payload = None				# Payload object
	TRAILER = str('END\r\n')		# Trailer

	type = ''
	channelnum = -1
	msgno = -1
	more = ''
	seqno = -1L
	size = -1
	ansno = None

	def __init__(self, log, channelnum=None, msgno=None, more=None, seqno=None, size=None, payload=None, type='MSG', ansno=None, databuffer=None):
		Frame.__init__(self, log, self.frameType)

		# This lets us pass in a string type databuffer
		# to create a frame object
		if databuffer:
			self._bufferToFrame(databuffer)
		else:
			self._checkValues(channelnum, msgno, more, seqno, size, payload, type, ansno)
			self.type = type
			self.channelnum = channelnum
			self.msgno = msgno
			self.more = more
			self.seqno = seqno
			self.payload = payload
			self.size = size
			if ansno:
				self.ansno = ansno

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
		# First, check the data is terminated by the TRAILER
		if data[-5:] != self.TRAILER:
			raise DataFrameException('No Trailer')

		# Strip off the trailer
		data = data[:-5]

		# split the header and the payload
		framedata = string.split(data, '\r\n', 1)

		# Check for a frame of just a TRAILER
		if len(framedata) != 1 and len(framedata) != 2:
			raise DataFrameException('Empty Frame')

		# Now split the header into bits
		headerbits = string.split(framedata[0])

		# Check for valid header format
		if len(headerbits) != 6 and len(headerbits) != 7:
			raise DataFrameException('Header Format Invalid')
		self.type = headerbits[0]
#		self.log.logmsg(logging.LOG_DEBUG, "frame.py: type is: %s" % self.type )

		try:
			self.channelnum = string.atoi(headerbits[1])
			self.msgno = string.atoi(headerbits[2])
			self.more = headerbits[3]
			self.seqno = string.atol(headerbits[4])
			self.size = string.atoi(headerbits[5])
			if len(headerbits) == 7:
				self.ansno = string.atoi(headerbits[6])
			else:
				self.ansno = None

		except Exception, e:
			raise DataFrameException('unknown error in _bufferToFrame')

		self.payload = framedata[1]

		self._checkValues(self.channelnum, self.msgno, self.more, self.seqno, self.size, self.payload, self.type, self.ansno)

	# Sanity checking of frame values
	# We do heaps of bounds checking here, because I'm
	# paranoid and it seems like a neat place to put it
	# It means DataFrames are only really bounds checked
	# upon initial creation, but that makes a certain amount
	# of sense
	def _checkValues(self, channelnum, msgno, more, seqno, size, payload, type, ansno=None):
		if type not in constants.DataFrameTypes.keys():
			raise DataFrameException('Invalid DataFrame Type')

		if not constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL:
			raise DataFrameException('Channel number (%s) out of bounds' % channelnum)

		if not constants.MIN_MSGNO <= msgno <= constants.MAX_MSGNO:
			raise DataFrameException('MSGNO out of bounds')

		if not more in constants.MoreTypes.keys():
			raise DataFrameException('Invalid More Type')

		if not constants.MIN_SEQNO <= seqno <= constants.MAX_SEQNO:
			raise DataFrameException('SEQNO: %i out of bounds' % seqno)

		if ansno:
			if not constants.MIN_ANSNO <= ansno <= constants.MAX_ANSNO:
				raise DataFrameException('ANSNO out of bounds')

		mysize = len(payload)
		if mysize != size:
			raise DataFrameException('Size mismatch %i != %i' % (mysize, size))

	def __repr__(self):
		return "<%s instance at %s>" % (self.__class__, hex(id(self)))

class DataFrameException(FrameException):
	def __init__(self, args=None):
		self.args = args

class SEQFrame(Frame):
	frameType = 'seq'
	TRAILER = str('\r\n')		# Trailer
	type = 'SEQ'

	channelnum = -1
	ackno = -1L
	window = -1

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

		# If there are any exceptions to this, it's either a
		# bug in the code, or crap data being sent in
		# First, check the data is terminated by the TRAILER
		if data[-2:] != self.TRAILER:
			raise SEQFrameException('No Trailer')

		# Strip off the trailer
		data = data[:-2]

		# Check for a frame of just a TRAILER
		if len(data) != 1 and len(data) != 2:
			raise SEQFrameException('Empty Frame')

		# Now split the frame into bits
		bits = string.split(data[0])

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
			raise SEQFrameException('ACKNO: %i out of bounds' % seqno)

		if not constants.MIN_WINDOWSIZE <= window <= constants.MAX_WINDOWSIZE:
			raise SEQFrameException('windowsize out of bounds')

	def __str__(self):

		# We use this handy function to return a string representation

		framestring = "SEQ "
		framestring = "%i %i %i" % (self.channelnum, self.ackno, self.window)
		framestring += self.TRAILER
		return framestring

class SEQFrameException(FrameException):
	def __init__(self, args=None):
		self.args = args
