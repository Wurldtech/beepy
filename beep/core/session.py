# $Id: session.py,v 1.3 2002/08/13 06:29:21 jpwarren Exp $
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
#
# Session object

import socket
import Queue

import constants
import logging
import errors
import channel
import frame
import mgmtparser
import mgmtcreator
from beep.profiles import profile
from beep.profiles import beepmgmtprofile

class Session:
	"""
	The Session class is an abstract class with only core functions
	implemented. All transport related functions remain unimplemented
	and should be implemented in a class that inherits from Session
	"""
	state = constants.SESSION_UNINITIALIZED

	log = None		# Logger
	sentGreeting = 0	# have I sent a greeting yet?
	receivedGreeting = 0	# have I received a greeting yet?
	channels = {}		# dictionary of channels, indexed by channel number
	channelState = {}	# a dictionary of channel states, indexed by channel number
	nextChannelNum = -1	# The next channel number to be allocated
	profileDict = {}	# dictionary of known profiles.
	inbound = None		# session queue for inbound packets off the wire
	outbound = None		# session queue for outbound packets destined for the wire

	# We do some transport independant stuff here, so ensure that when you 
	# subclass from Session, you also call session.Session.__init__(self) 
	# from your implementation unless you want to recode this yourself
	
	def __init__(self, log, profileDict):
		self.state = constants.SESSION_UNINITIALIZED

		self.log = log
		self.sentGreeting = 0
		self.receivedGreeting = 0
		self.channels = {}

		self.profileDict = profileDict

		self.inbound = Queue.Queue(constants.MAX_INPUT_QUEUE_SIZE)
		self.outbound = Queue.Queue(constants.MAX_INPUT_QUEUE_SIZE)

		# Create channel 0 for this session
		self.createChannelZero()

	def processFrames(self):
		"""processFrames() is used by a Session to call each of the
		Channels in turn and get them to process any frames in their
		inbound Queue. It also gets any frames in their outbound
		Queue and readies them for sending out over the wire.
		This is a demo scheduler and may not be particularly efficient.

		"""
		# Firstly, get a frame from the inbound Queue and put it
		# on the appropriate channel
		# Possibly change this to read all pending input frames
		# up to a threshold for better scheduling.. 
		# maybe variable for tuning?
		theframe = self.recvFrame()
		if( theframe ):
#			self.log.logmsg(logging.LOG_DEBUG, "%s: unplexing frame" % self)
			self.unplex(theframe)

		# Now, process all channels, round robin style
		chanlist = self.channels.keys()
		for channelnum in chanlist:
			# First up, get them to process inbound frames
			try:
				self.channels[channelnum].processFrames()

			except profile.ProfileException, e:
				raise TerminateException(e)

			# This occurs if a channel is deleted by
			# another thread/process halfway through
			# a processing run. We just silently ignore it
			# since it has no affect.
			except KeyError:
				pass

#			except Exception, e:
#				self.log.logmsg(logging.LOG_INFO, "Exception in channel %i processMessages(): %s" % (channelnum, e))
			# Now that that's over, get a pending frame and
			# prepare it for sending over the wire
			try:
				theframe = self.channels[channelnum].pull()
				if( theframe ):
					self.log.logmsg(logging.LOG_DEBUG, "sending data on channel %i: %s" % (channelnum, theframe) )
					self.sendFrame(theframe)
					del theframe
			# Same as above, ignore KeyErrors
			except KeyError:
				pass

	# method to un-encapsulate frames recv'd from transport
	def unplex(self, theframe):
		if( theframe.frameType != 'data' ):
			raise SessionException('Unknown Frame Type')
		else:
			if theframe.channelnum in self.channels.keys():
				try:
					self.channels[theframe.channelnum].push(theframe)
				except channel.ChannelOutOfSequence, e:
					# Out of sequence error terminates session without response, logs an error
					self.log.logmsg(logging.LOG_ERR, "Channel %i out of sequence: %s" % (theframe.channelnum, e) )
					raise TerminateException("Channel out of sequence")

				except channel.ChannelRPYMsgnoInvalid, e:
					self.log.logmsg(logging.LOG_NOTICE, "Channel %i received RPY with invalid msgno: %s" % (theframe.channelnum, e))
			else:
				# Attempted to send a frame to a non-existant channel number
				# RFC says to terminate session
				self.log.logmsg(logging.LOG_ERR, "Attempt to send frame to non-existant channel: %i" % theframe.channelnum)
				raise TerminateException("Attempt to send to non-existant channel")

	# Open a new channel
	def createChannel(self, channelnum, profile):
		newchan = channel.Channel(self.log, channelnum, profile)
		self.channels[channelnum] = newchan

	def createChannelFromURIList(self, channelnum, uriList, profileInit=None):
		# First, check requested profile(s) are available
		myURIList = self.profileDict.getURIList()
		if not myURIList:
			self.log.logmsg(logging.LOG_CRIT, "Session's profileDict is empty!")
			raise SessionException("Session's profileDict is empty!")

		# Now, find a supported URI in our list
		for uri in uriList:
			if uri in myURIList:
				self.log.logmsg(logging.LOG_DEBUG, "uri found in profileDict: %s" % uri)

				# Attempt to instanciate the profile
				profileClassName = self.profileDict[uri].__profileClass__
				if profileClassName in self.profileDict[uri].__dict__.keys():
					profile = self.profileDict[uri].__dict__[profileClassName](self.log, self, profileInit)
				else:
					self.log.logmsg(logging.LOG_ERR, "__profileClass__ doesn't contain the name of the Class to instanciate for uri: %s" % uri)
					raise SessionException("__profileClass__ doesn't contain correct Class name")

				# And create a channel, at long last.
				self.createChannel(channelnum, profile)

				# Inform caller of uri used
				return uri

		# If we get here, then no supported profile URI was found
		self.log.logmsg(logging.LOG_DEBUG, "uri not found in profileDict")
		raise SessionException("Profile not supported by Session")

	def deleteChannel(self, channelnum):
		if channelnum in self.channels.keys():
			del self.channels[channelnum]
		else:
			raise SessionException('No such channel')

	def createChannelZero(self):
		"""Create the Channel 0 for the Session.
		Should only get called once when a Session initialises
		"""
		if self.channels.has_key(0):
			self.log.logmsg(logging.LOG_ERR, "Attempted to create a Channel 0 when one already exists!")
			raise SessionException("Can't create more than one Channel 0")

		else:
			profile = beepmgmtprofile.BEEPManagementProfile(self.log, self)
			self.createChannel(0, profile)

	def sendFrame(self, theframe):
		"""sendFrame() is used to place outbound Frames onto the
		output Queue for later collection by the transport layer
		and sending over the wire. It converts a Frame into the
		data representation of the Frame before it is placed on the Queue.
		If the Queue is full, it raises a SessionOutboundQueueFull exception.
		"""
		data = str(theframe)
		try:
#			self.log.logmsg(logging.LOG_DEBUG, "sendFrame(): %s" % data)
			self.outbound.put(data, 0)
		except Queue.Full:
			raise SessionOutboundQueueFull('Outbound queue full')

	def recvFrame(self):
		"""recvFrame() is used to get Frames from the inbound Queue for
		processing by the Session. This is used by unplex() to place
		Frames on the appropriate Channel
		It ignores an empty Queue condition since we want processing to
		continue in that case.
		"""
		try:
			theframe = self.inbound.get(0)
			if theframe:
				return theframe

		except Queue.Empty:
			pass

	def pushFrame(self, theframe):
		"""pushFrame() is used by the transport layer to place Frames
		into the inbound Queue after the data is read off the wire
		and converted to a Frame object.
		"""	
		try:
#			self.log.logmsg(logging.LOG_DEBUG, "pushing frame: %s" % theframe)
			self.inbound.put(theframe, 0)

		# Drop frames if queue is full
		# log a warning
		except Queue.Full:
			raise SessionInboundQueueFull('Inbound Queue Full')

	def pullFrame(self):
		"""
		pullFrame() is used by the transport layer to get Frames
		from the outbound Queue so it can send them out over the wire.
		Ignore Queue.Empty condition.
		"""
		try:
			theframe = self.outbound.get(0)
			if theframe:
#				self.log.logmsg(logging.LOG_DEBUG, "pulling frame: %s" % theframe)
				return theframe
		except Queue.Empty:
			pass

	def getProfileDict(self):
		return self.profileDict

	def close(self):
		"""close() attempts to close all the channels in a session
		before closing down the session itself.
		"""
		if self.state < constants.SESSION_CLOSING:
			self.state = constants.SESSION_CLOSING
			try:
				chanlist = self.channels.keys()
				for chan in chanlist:
					chan.close()
					self.deleteChannel(chan)

			except Exception, e:
				raise SessionException('Unable to close Session: %s' % e)

	def reset(self):
		"""reset() does a tuning reset which closes all channels and
		   terminates the session.
		"""
		pass

	def startChannel(self, profileList):
		"""startChannel() attempts to start a new channel for communication.
		inputs: profileURIList, a list of URIs for profiles that are acceptable
		outputs: none
		raises: none
		"""
		if self.receivedGreeting:
			# Attempt to get the remote end to start the Channel
			self.channels[0].profile.startChannel(str(self.nextChannelNum), profileList)
			# Increment nextChannelNum appropriately.
			self.nextChannelNum += 2
		else:
			raise SessionException("Greeting not yet received")

class SessionManager:
	"""A SessionManager is used to create and destroy sessions that
	   handle BEEP connections
	"""
	log = None
	profileDict = {}
	sessionList = []

	def __init__(self, log, profileDict):
		self.log = log
		self.profileDict = profileDict

	# Add a Session instance to the sessionList
	def addSession(self, sessionInst):
		self.sessionList.append(sessionInst)

	def removeSession(self, sessionInst):
		if sessionInst in self.sessionList:
			self.sessionList.remove(sessionInst)

	def deleteAllSessions(self):
		for sess in self.sessionList:
			self.removeSession(sess)

	def close(self):
		self.deleteAllSessions()

# A SessionListener is a special type of SessionManager that listens for
# incoming connections and creates Sessions to handle them.
# It is an abstract class.
class SessionListener(SessionManager):

	def __init__(self, log, profileDict):
		SessionManager.__init__(self, log, profileDict)

# A ListenerSession is a special kind of Session for handling
# Sessions initiated by a client, rather than as an Initiator
# on this side.
class ListenerSession(Session):
	"""A ListenerSession is a Session that is the result of
	a connection to a SessionListener. It is the server side
	of a client/server connection. An InitiatorSession would
	form the client side.
	"""

	def __init__(self, log, profileDict):
		Session.__init__(self, log, profileDict)

		# Listeners use only even numbered channels for allocation
		self.nextChannelNum = 2

class InitiatorSession(Session):
	"""An InitiatorSession is a Session that initiates a connection
	to a SessionListener and then communicates with the resulting
	ListenerSession. It forms the client side of a client/server
	connection.
	"""
	def __init__(self, log, profileDict):
		Session.__init__(self, log, profileDict)

		# Initiators use only odd numbered channels for allocation
		self.nextChannelNum = 1

# Exception classes
class SessionException(errors.BEEPException):
	def __init__(self, args=None):
		self.args = args

class TerminateException(SessionException):
	def __init__(self, args=None):
		self.args = args

class ChannelZeroOutOfSequence(SessionException):
	def __init__(self, args=None):
		self.args = args

class SessionInboundQueueFull(SessionException):
	def __init__(self, args=None):
		self.args = args

class SessionOutboundQueueFull(SessionException):
	def __init__(self, args=None):
		self.args = args
