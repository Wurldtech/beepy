# $Id: channel.py,v 1.2 2002/08/02 03:36:41 jpwarren Exp $
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
# Channel object
# It's quite possible some locking may be required here
# due to the threading of Sessions. Not sure yet.
# Have to analyse the concurrency once the code stabilises a bit

import constants
import errors
import logging
import frame

import Queue

class Channel:
	log = None
	number = -1			# Channel number
	localSeqno = -1L		# My current Sequence number
	remoteSeqno = -1L		# Remote Sequence number
	ansno = -1			# Current Answer number
	profile = None			# channel Profile
	allocatedMsgnos = []		# List of allocated msgno's
	inbound = None			# queue of incoming frames
	outbound = None			# queue of outgoing frames
	moreFrameType = None		# Frame type we're expecting more of
	moreFrameMsgno = 0		# Msgno of what we're expecting more of
	state = 0

	# Create a new channel object
	def __init__(self, log, channelnum, profile):
		self.log = log
		try:
			assert( constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL)
			self.state = constants.CHANNEL_STARTING
			self.number = channelnum
			self.allocatedMsgnos = []
			self.started = 0
			self.localSeqno = 0
			self.remoteSeqno = 0
			self.ansno = 0
			self.inbound = Queue.Queue(constants.MAX_INPUT_QUEUE_SIZE)
			self.outbound = Queue.Queue(constants.MAX_INPUT_QUEUE_SIZE)
			self.profile = profile

			# This binds the profile to this channel, readying it for operation.
			self.profile.setChannel(self)

		except AssertionError:
			raise ChannelException('Channel number out of bounds')

	# Send frame over this channel
	# Used by Profiles
	def send(self, frame):
		"""send() is the raw interface to the Channel's
		outbound frame Queue. It isn't designed to be
		used directly as that would require messing about
		inside the Channel's variables directly, which would
		be.. well.. messy. Use the convenience methods like
		sendMessage() instead.
		It raises a ChannelQueueFull exception if the
		Channel's outbound Queue is full, strangely enough.
		"""
		if self.state is constants.CHANNEL_ACTIVE:
			if not self.outbound.full():
				self.outbound.put(frame)
			else:
				raise ChannelQueueFull('Outbound queue full')
		else:
			raise ChannelStateException('Channel not active')

	# Receive frame from this channel
	# Used by Profiles
	def recv(self):
		"""recv() is used by Profiles to receive
		frames from the Channel inbound Queue for
		processing in their processMessages() method.
		It ignores a Queue.Empty condition.
		"""
		if self.state is constants.CHANNEL_ACTIVE:
			try:
				return self.inbound.get(0)
			except Queue.Empty:
				pass
		else:
			raise ChannelStateException('Channel not started')

	# interface to Session
	def push(self, theframe):
		"""push() is used by a Session when it receives a frame
		off the wire to place it into the Channel. The Channel
		can then do some quick checks on the content of the frame
		to make sure that it is contextually valid.
		This is not syntax checking, that gets handled when the
		Frame object is created.
		"""
		if self.state is not constants.CHANNEL_ACTIVE:
			raise ChannelStateException('Channel not active')
		# check sequence number
		if theframe.seqno != self.remoteSeqno:
			raise ChannelOutOfSequence("Expected seqno: %i but got %i" % (self.remoteSeqno, theframe.seqno))
		else:
			# update my seqno
			self.allocateRemoteSeqno(theframe.size)

		# check the frametype is the right one if we're expecting More frames
		if self.moreFrameType:
			if theframe.type is not self.moreFrameType:
				raise ChannelException("Frametype incorrect. Expecting more %s frames" % self.moreFrameType)
			# Then check the msgno is the right one
			if theframe.msgno is not self.moreFrameMsgno:
				raise ChannelException("Msgno incorrect. Expecting more frames for msgno: %i" % self.moreFrameMsgno)
		# if Frame has the more flag set, set our expected MoreType and Msgno
		if theframe.more is constants.MoreTypes['*']:
			self.moreFrameType = theframe.type
			self.moreFrameMsgno = theframe.msgno
		else:
			self.moreFrameType = None
			self.moreFrameMsgno = 0

		# If frametype is RPY, check the msgno is valid
		if theframe.type is constants.DataFrameTypes['RPY']:
			if theframe.msgno not in self.allocatedMsgnos:
				raise ChannelRPYMsgnoInvalid('msgno %i not valid for RPY' % theframe.msgno)
			else:
				self.deallocateMsgno(theframe.msgno)

		# Finally, allow the frame to be put on our inbound queue.
		if not self.inbound.full():
			self.inbound.put(theframe)
		else:
			raise ChannelQueueFull('Inbound queue full')

	def pull(self):
		"""pull() is used by a Session to retrive frames from
		the Channel outbound Queue destined for the wire.
		"""
		if self.state is constants.CHANNEL_ACTIVE:
			try:
				message = self.outbound.get(0)
				return message
			except Queue.Empty:
				pass
		else:
			raise ChannelStateException('Channel not active')

	# Method for allocating the next sequence number
	# seqno = last_seqno + size and wraps around constants.MAX_SEQNO
	# FIXME
	# This code may need to be mutexed. Have to analyse the
	# amount of concurrency.
	def allocateRemoteSeqno(self, msgsize):
		new_seqno = self.remoteSeqno
		self.remoteSeqno += msgsize
		if self.remoteSeqno > constants.MAX_SEQNO:
			self.remoteSeqno -= constants.MAX_SEQNO
		return new_seqno

	def allocateLocalSeqno(self, msgsize):
		new_seqno = self.localSeqno
		self.localSeqno += msgsize
		if self.localSeqno > constants.MAX_SEQNO:
			self.localSeqno -= constants.MAX_SEQNO
		return new_seqno


	# This method allocates a unique msgno for a message by
	# checking a list of allocated msgno's. Allocated msgno's
	# are removed from the list when they receive complete
	# replies.
	# This algorithm allocates the lowest available msgno
	def allocateMsgno(self):
		"""allocateMsgno() allocates a unique msgno for a message
		by checking a list of allocated msgnos and picking the
		lowest number not already allocated. Allocated msgnos
		should be removed from the list when the complete reply
		to the message is received. See deallocateMsgno().
		inputs: None
		outputs: msgno
		raises: ChannelOutOfMsgnos
		"""
		msgno = constants.MIN_MSGNO
		while msgno in self.allocatedMsgnos:
			msgno += 1
			# Since we start at MIN_MSGNO, if we make it
			# all the way to MAX_MSGNO, then we've run out
			# of message space on this channel. That's quite
			# bad, as it indicates a leak somewhere in that
			# messages are not being replied to correctly.
			# Not sure what should happen. Probably terminate
			# the channel immediately.
			if msgno > constants.MAX_MSGNO:
				raise ChannelOutOfMsgnos('No available msgnos on channel', self.channelnum)
		# If we got here, then we've found the lowest
		# available msgno, so allocate it
		self.allocatedMsgnos.append(msgno)
		return msgno

	# This method frees a msgno to be allocated again
	def deallocateMsgno(self, msgno):
		"""deallocateMsgno() deallocates a previously allocated
		msgno. This should be called when a complete reply to a
		message is received.
		inputs: msgno
		outputs: None
		raises: None
		"""
		if msgno in self.allocatedMsgnos:
			del self.allocatedMsgnos[msgno]

	# Send a frame of type MSG
	def sendMessage(self, data, more=constants.MoreTypes['.']):
		"""sendMessage() is used for sending a frame of type MSG
		It raises a ChannelQueueFull exception.
		inputs: data, the payload of the message
		        more, a constants.MoreType designating if this is the last message
		outputs: msgno, the msgno of the message that was sent
		"""

		size = len(data)
		seqno = self.allocateLocalSeqno(size)
		msgno = self.allocateMsgno()
		try:
			msg = frame.DataFrame(self.log, self.number, msgno, more, seqno, size, data, constants.DataFrameTypes['MSG'])
		except frame.DataFrameException, e:
			self.log.logmsg(logging.LOG_INFO, "Data Encapsulation Failed:", e)

		self.send(msg)
		return msgno

	# msgno here is the msgno to which this a reply
	def sendReply(self, msgno, data, more=constants.MoreTypes['.']):
		"""sendReply() is used for sending a frame of type RPY
		The msgno here is the msgno of the message to which this is a reply.
		It raises a ChannelQueueFull exception.
		"""
		size = len(data)
		seqno = self.allocateLocalSeqno(size)
		try:
			msg = frame.DataFrame(self.log, self.number, msgno, more, seqno, size, data, constants.DataFrameTypes['RPY'])

		except frame.DataFrameException, e:
			self.log.logmsg(logging.LOG_INFO, "Data Encapsulation Failed:", e)

		self.send(msg)

	def sendGreetingReply(self, data):
		self.sendReply(0, data)

	# seqno and more are not required for ERR frames
	# msgno is the MSG to which this error is a reply
	def sendError(self, msgno, data ):
		"""sendError() is used for sending a frame of type ERR
		The msgno here is the msgno of the message to which this is a reply.
		It raises a ChannelQueueFull exception.
		"""
		size = len(data)
		seqno = self.allocateLocalSeqno(size)
		try:
			msg = frame.DataFrame(self.log, self.number, msgno, constants.MoreTypes['.'], seqno, size, data, constants.DataFrameTypes['ERR'])
		except frame.DataFrameException, e:
			self.log.logmsg(logging.LOG_INFO, "Data Encapsulation Failed:", e)

		self.send(msg)

	def sendNul():
		raise NotImplementedError

	# msgno here is the msgno to which this an answer
	def sendAnswer(self, msgno, data, more=constants.MoreTypes['.']):
		"""sendAnswer() is used for sending a frame of type ANS
		The msgno here is the msgno of the message to which this is an answer.
		It raises a ChannelQueueFull exception.
		"""
		seqno = self.allocateLocalSeqno(size)
		size = len(data)
		try:
			msg = DataFrame(self.log, self.number, msgno, more, seqno, size, data, constants.DataFrameTypes['RPY'])
		except DataFrameException, e:
			self.log.logmsg(logging.LOG_INFO, "Data Encapsulation Failed:", e)

		self.send(msg)

	def processFrames(self):
		"""processFrames is called by a Session to get this
		Channel to process any pending frames. This gets
		handled by the Profile bound to this Channel.
		"""
		if self.profile:
			self.profile.processMessages()
		else:
			raise ChannelException('No profile bound to channel')

	def close(self):
		"""close() attempts to close the Channel.
		A Channel is not supposed to close unless all messages
		sent on the channel have been acknowledged.
		inputs: none
		outputs: none
		raises: ChannelMessagesOutstanding, if not all sent messages
		        have been acknowledged.
		"""
		if self.allocatedMsgnos[0]:
			raise ChannelMessagesOutstanding

	def transition(self, newstate):
		"""transition() attempts to move the Channel to the
		requested state, performing various state transition
		checks before it does.
		"""
		if newstate is constants.CHANNEL_STOPPED:
			if self.state != constants.CHANNEL_CLOSING or constants.CHANNEL_STARTING:
				raise ChannelCannotTransition("Cannot move to STOPPED unless CLOSING or STARTING")
			else:
				self.state = constants.CHANNEL_STOPPED
#		elif newstate is constants.CHANNEL_STARTING:
#			if self.state is not constants.CHANNEL_STOPPED:
#				raise ChannelCannotTransition("Cannot move to STARTING unless STOPPED")
#			else:
#				self.state = constants.CHANNEL_STARTING
		elif newstate is constants.CHANNEL_ACTIVE:
			if self.state is not constants.CHANNEL_STARTING and constants.CHANNEL_CLOSING:
				raise ChannelCannotTransition("Cannot move to ACTIVE unless STARTING or CLOSING")
			else:
				self.state = constants.CHANNEL_ACTIVE
		elif newstate is constants.CHANNEL_CLOSING:
			if self.state is not constants.CHANNEL_ACTIVE:
				raise ChannelCannotTransition("Cannot move to CLOSING unless ACTIVE")
			else:
				self.state = constants.CHANNEL_CLOSING
		else:
			raise ChannelCannotTransition("invalid state: %s" % newstate)

# Exception classes
class ChannelException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

class ChannelQueueFull(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelOutOfMsgnos(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelOutOfSequence(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelRPYMsgnoInvalid(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelNotStarted(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelMessagesOutstanding(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelCannotTransition(ChannelException):
	def __init__(self, args=None):
		self.args = args

class ChannelStateException(ChannelException):
	def __init__(self, args=None):
		self.args = args