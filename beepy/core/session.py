# $Id: session.py,v 1.4 2003/01/08 05:38:11 jpwarren Exp $
# $Revision: 1.4 $
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

import util
import statemachine
import constants
import logging
import errors
import channel
import frame
import mgmtparser
import mgmtcreator

from beepy.profiles import profile
from beepy.profiles import beepmgmtprofile

class Session(statemachine.StateMachine):
	"""
	The Session class is an abstract class with only core functions
	implemented. All transport related functions remain unimplemented
	and should be implemented in a class that inherits from Session
	"""

#	log = None		# Logger
#	sentGreeting = 0	# have I sent a greeting yet?
#	receivedGreeting = 0	# have I received a greeting yet?
#	channels = {}		# dictionary of channels, indexed by channel number
#	nextChannelNum = -1	# The next channel number to be allocated
#	profileDict = {}	# dictionary of known profiles.
#	inbound = None		# session queue for inbound packets off the wire
#	outbound = None		# session queue for outbound packets destined for the wire

	# We do some transport independant stuff here, so ensure that when you 
	# subclass from Session, you also call session.Session.__init__(self) 
	# from your implementation unless you want to recode this yourself
	
	def __init__(self, log, profileDict):
		# zero the state machine
		statemachine.StateMachine.__init__(self)

		# define the states
		self.addState('INIT', self._stateINIT)
		self.addState('ACTIVE', self._stateACTIVE)
		self.addState('CLOSING', self._stateCLOSING)
		self.addState('TUNING', self._stateTUNING)
		self.addState('TERMINATE', self._stateTERMINATE)
		self.addState('EXITED', None, 1)
		self.setStart('INIT')

		# define the transitions
		self.addTransition('INIT', 'ok', 'ACTIVE')
		self.addTransition('INIT', 'close', 'TERMINATE')
		self.addTransition('INIT', 'error', 'EXITED')
		self.addTransition('ACTIVE', 'close', 'CLOSING')
		self.addTransition('ACTIVE', 'error', 'TERMINATE')
		self.addTransition('ACTIVE', 'reset', 'TUNING')
		self.addTransition('CLOSING', 'unable', 'ACTIVE')
		self.addTransition('CLOSING', 'ok', 'TERMINATE')
		self.addTransition('CLOSING', 'error', 'TERMINATE')
		self.addTransition('CLOSING', 'close', 'CLOSING')
		self.addTransition('TUNING', 'ok', 'EXITED')
		self.addTransition('TUNING', 'close', 'TUNING')
		self.addTransition('TUNING', 'error', 'TERMINATE')
		self.addTransition('TERMINATE', 'ok', 'EXITED')
		self.addTransition('TERMINATE', 'close', 'TERMINATE')
		self.addTransition('TERMINATE', 'error', 'TERMINATE')
		self.addTransition('EXITED', 'close', 'EXITED')

		self.log = log
		self.sentGreeting = 0
		self.receivedGreeting = 0
		self.channels = {}
		self.ID = 0

		self.profileDict = profileDict

		self.inbound = util.DataQueue(constants.MAX_INPUT_QUEUE_SIZE)
		self.outbound = util.DataQueue(constants.MAX_INPUT_QUEUE_SIZE)

	def _stateINIT(self):
		raise NotImplementedError

	def _stateACTIVE(self):
		""" overload _stateACTIVE in your subclass to implement the
		    main processing loop
		"""
		raise NotImplementedError

	def _stateCLOSING(self):
		""" _stateCLOSING attempts to shut down the session gracefully
		"""
		raise NotImplementedError

	def _stateTUNING(self):
		"""performs a tuning reset
		"""
		raise NotImplementedError

	def _stateTERMINATE(self):
		"""The session is terminating
		"""
		raise NotImplementedError

	def isActive(self):
		if self.currentState == 'ACTIVE':
			return 1
		return 0

	def isExited(self):
		if self.currentState == 'EXITED':
			return 1
		return 0

	def setID(self, sessId):
		self.ID = sessId

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
		self.unplexFrames()

		# Now, process all channels, round robin style
		self.processChannels()

	# method to un-encapsulate frames recv'd from transport
	def unplexFrames(self):
		theframe = self.recvFrame()
		if( theframe ):
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

					except channel.ChannelMsgnoInvalid, e:
						self.log.logmsg(logging.LOG_ERR, "Channel %i: %s" % (theframe.channelnum, e))
						raise TerminateException("Invalid msgno in channel")
				else:
					# Attempted to send a frame to a non-existant channel number
					# RFC says to terminate session
					self.log.logmsg(logging.LOG_ERR, "Attempt to send frame to non-existant channel: %i" % theframe.channelnum)
					raise TerminateException("Attempt to send to non-existant channel")

	def processChannels(self):

		chanlist = self.channels.keys()
		for channelnum in chanlist:
			# First up, get them to process inbound frames
			try:
				self.channels[channelnum].processFrames()

			except profile.TuningReset, e:
				raise TuningReset("Profile Tuning Reset: %s" % e)

			except profile.TerminalProfileException, e:
				raise TerminateException("%s" % e)

			except profile.ProfileException, e:
				if channelnum != 0:
					self.log.logmsg(logging.LOG_INFO, "ProfileException: %s. Closing Channel." % e )
					self.channels[0].profile.closeChannel(channelnum, '554')
				else:
#					self.log.logmsg(logging.LOG_ERR, "%s" % e )
					raise TerminateException("%s" % e)

			except Exception, e:
				self.log.logmsg(logging.LOG_INFO, "Exception in channel %i: %s" % (channelnum, e))

	# Open a new channel
	def createChannel(self, channelnum, profile):
		newchan = channel.Channel(self.log, channelnum, profile, self)
		self.channels[channelnum] = newchan

	def createChannelFromURIList(self, channelnum, uriList, profileInit=None):
		if not self.profileDict:
			self.log.logmsg(logging.LOG_CRIT, "Session's profileDict is undefined!")
			raise SessionException("Session's profileDict is undefined!")

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
			self.log.logmsg(logging.LOG_DEBUG, "%s: uri not found in profileDict: %s" % (self, self.profileDict))
#			for x in self.profileDict:
#				self.log.logmsg(logging.LOG_DEBUG, "%s" % x )

		raise SessionException("Profile not supported by Session")

	def closeAllChannels(self):
		"""attempts to close all the channels in a session
		before closing down the session itself.
		"""
		try:
			chanlist = self.channels.keys()
			self.log.logmsg(logging.LOG_DEBUG, "Channels to close: %s" % chanlist)
			for channelnum in chanlist:
				if channelnum != 0:
					self.log.logmsg(logging.LOG_DEBUG, "Attempting to close channel %i..." % channelnum)
					self.channels[0].profile.closeChannel(channelnum)
					self.log.logmsg(logging.LOG_DEBUG, "Finished queueing closure." % channelnum)

		except Exception, e:
			# If we can't close a channel, we must remain active
			# FIXME: more detailed error handling required here
			self.log.logmsg("Unable to close Session: %s" % e)

	def deleteChannel(self, channelnum):
		self.log.logmsg(logging.LOG_DEBUG, "sessID %d: Deleting channel %d..." % (self.ID, channelnum) )
		if self.channels.has_key(channelnum):
			try:
				self.channels[channelnum].close()
				del self.channels[channelnum]
				self.log.logmsg(logging.LOG_DEBUG, "sessID %d: Channel %d deleted." % (self.ID, channelnum) )
			except channel.ChannelMessagesOutstanding, e:
				self.log.logmsg(logging.LOG_DEBUG, "sessID %d: Exception deleting channel %d: %s..." % (self.ID, channelnum, e) )
				raise SessionException(e)

		else:
			raise SessionException('No such channel')

	def deleteAllChannels(self):
		chanlist = self.channels.keys()
		for channelnum in chanlist:
			del self.channels[channelnum]

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

	def isChannelActive(self, channelnum):
		"""This method provides a way of figuring out if a channel is
		   running.
		"""
		if self.channels.has_key(channelnum):
			return 1
		else:
			return 0

	def getActiveChannel(self, channelnum):
		"""This method provides a way of getting the channel object
		   by number.
		"""
		if self.isChannelActive(channelnum):
			return self.channels[channelnum]
		return None

	def flushChannelOutbound(self):
		"""This method gets all pending messages from all channels
		   one at a time and places them on the Session Outbound Queue.
		   This should probably only be used in Tuning Resets, but you
		   never know when it might come in handy.
		"""
		chanlist = self.channels.keys()
		for channelnum in chanlist:

			theframe = self.channels[channelnum].pull()
			if( theframe ):
				self.sendFrame(theframe)
				del theframe

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
		processing by the Session. 
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

	def getChannelZeroProfile(self):
		return self.channels[0].profile

	def reset(self):
		"""reset() does a tuning reset which closes all channels and
		   terminates the session.
		"""
		self.transition('reset')

	def startChannel(self, profileList):
		"""startChannel() attempts to start a new channel for communication.
		inputs: profileURIList, a list of URIs for profiles that are acceptable
		outputs: none
		raises: none
		"""
		if self.receivedGreeting:
			# Attempt to get the remote end to start the Channel
			channelnum = self.nextChannelNum
			self.channels[0].profile.startChannel( channelnum, profileList)
			# Increment nextChannelNum appropriately.
			self.nextChannelNum += 2
			# Return channelnum created
			return channelnum
		else:
			raise SessionException("Greeting not yet received")

	def closeChannel(self, channelnum):
		"""closeChannel() attempts to close a channel.
		inputs: channelnum, the number of the channel to close
		outputs: none
		raises: none
		"""
		self.log.logmsg(logging.LOG_DEBUG, "Attempting to close channel %s..." % channelnum)
		if self.channels.has_key(channelnum):
			self.channels[0].profile.closeChannel(channelnum)
		else:
			raise KeyError("Channel number invalid")

	def close(self):
		raise NotImplementedError

	def _showInternalState(self):
		self.log.logmsg(logging.LOG_DEBUG, "Current internal state of %s" % self)
		for var in self.__dict__.keys():
			self.log.logmsg(logging.LOG_DEBUG, "%s: %s" % (var, self.__dict__[var]))

class SessionManager(statemachine.StateMachine):
	"""A SessionManager is used to create and destroy sessions that
	   handle BEEP connections
	"""

	def __init__(self, log, profileDict):
		self.log = log
		self.profileDict = profileDict
		self.sessionList = {}
		self.sessionIds = []

		statemachine.StateMachine.__init__(self)

		self.addState('INIT', self._stateINIT)
		self.addState('ACTIVE', self._stateACTIVE)
		self.addState('CLOSING', self._stateCLOSING)
		self.addState('TERMINATE', self._stateTERMINATE)
		self.addState('EXITED', None, 1)
		self.setStart('INIT')

		self.addTransition('INIT', 'ok', 'ACTIVE')
		self.addTransition('INIT', 'error', 'EXITED')
		self.addTransition('INIT', 'close', 'EXITED')
		self.addTransition('ACTIVE', 'close', 'CLOSING')
		self.addTransition('ACTIVE', 'error', 'TERMINATE')
		self.addTransition('CLOSING', 'ok', 'TERMINATE')
		self.addTransition('CLOSING', 'close', 'TERMINATE')
		self.addTransition('TERMINATE', 'ok', 'EXITED')
		self.addTransition('TERMINATE', 'close', 'TERMINATE')
		self.addTransition('EXITED', 'close', 'EXITED')

	def _stateINIT(self):
		raise NotImplementedError

	def _stateACTIVE(self):
		raise NotImplementedError

	def _stateCLOSING(self):
		raise NotImplementedError

	def _stateTERMINATE(self):
		raise NotImplementedError

	def isActive(self):
		if self.currentState != 'ACTIVE':
			return 0
		return 1

	def isExited(self):
		if self.currentState == 'EXITED':
			return 1
		return 0

	# Add a Session instance to the sessionList
	def addSession(self, sessionInst):
		sessId = 0
		while sessId in self.sessionIds:
			sessId += 1

		sessionInst.setID(sessId)
		self.sessionList[sessId] = sessionInst
		self.sessionIds.append(sessId)
#		self.log.logmsg(logging.LOG_DEBUG, "Allocated sessId: %d to %s" % (sessId, sessionInst))
		return sessId

	def removeSession(self, sessId):
		if sessId in self.sessionIds:
			del self.sessionList[sessId]
			self.sessionIds.remove(sessId)

	def replaceSession(self, sessId, sessionInst):
		self.sessionList[sessId] = sessionInst
		self.log.logmsg(logging.LOG_DEBUG, "Reallocated sessId: %d to %s" % (sessId, sessionInst))

	def deleteAllSessions(self):
		for sessId in self.sessionIds:
			self.removeSession(sessId)

	def getSessionById(self, sessId):
		self.log.logmsg(logging.LOG_DEBUG, "Seeking session %d: in: %s" % (sessId, self.sessionList) ) 
		sess = self.sessionList[sessId]
		self.log.logmsg(logging.LOG_DEBUG, "Found session %d: %s" % (sessId, sess) ) 
		return sess

	def close(self):
		raise NotImplementedError

	def _showInternalState(self):
		self.log.logmsg(logging.LOG_DEBUG, "Current internal state of %s" % self)
		for var in self.__dict__.keys():
			self.log.logmsg(logging.LOG_DEBUG, "%s: %s" % (var, self.__dict__[var]))

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

class InitiatorManager(SessionManager):
	def __init__(self, log, profileDict):
		SessionManager.__init__(self, log, profileDict)

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

class TuningReset(SessionException):
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
