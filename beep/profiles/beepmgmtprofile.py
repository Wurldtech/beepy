# $Id: beepmgmtprofile.py,v 1.1 2002/08/02 00:24:37 jpwarren Exp $
# $Revision: 1.1 $
#
# The BEEP Channel Management Profile implementation
# This Profile is used to manage BEEP Sessions

import profile
from beep.core import constants
from beep.core import logging
from beep.core import mgmtparser 
from beep.core import mgmtcreator
import beep.core.session		# Have to do it this way, as beep.core.session imports
					# this file.

class BEEPManagementProfile(profile.Profile):
	mgmtParser = None		# The parser for BEEP channel management messages
	mgmtCreator = None		# The creator for BEEP Channel management messages
	receivedGreeting = -1		# Have I received a greeting from the other end yet?
	session = None			# Session I'm associated with
	startingChannel = {}		# Dictionary of channels I'm trying to start
	closingChannel = {}		# Dictionary of channels I'm trying to close

	def __init__(self, log, session):
		profile.Profile.__init__(self, log, session)
		self.mgmtParser = mgmtparser.Parser(self.log)
		self.mgmtCreator = mgmtcreator.Creator(self.log)
		self.receivedGreeting = 0
		self.startingChannel = {}
		self.closingChannel = {}

	def doProcessing(self):
		theframe = self.channel.recv()
		if theframe:
			self.log.logmsg(logging.LOG_DEBUG, "MGMT: processing frame: %s" % theframe)
			try:
				msg = self.mgmtParser.parse(theframe.payload)

				if not msg:
					self.log.logmsg( logging.LOG_DEBUG, "Cannot parse message" )

				# Handle RPY Frames
				if theframe.isRPY():

				# If it's a greeting positive reply and we haven't heard one
				# already, cool.
					if msg.isGreeting():
						self._handleGreeting(theframe, msg)
					else:
						self.log.logmsg( logging.LOG_DEBUG, "Non-greeting RPY received" ) 

					# This means a channel start was successful
					if msg.isProfile():

						self._handleProfile(theframe, msg)


				# Message frame processing
				elif theframe.isMSG():

					self.log.logmsg( logging.LOG_DEBUG, "%s: channel 0 MSG: %s" % (self, theframe))
					if not self.receivedGreeting:
						raise BEEPManagementProfileException("Client sent MSG before greeting.")
	
					if msg.isStart():
						self.log.logmsg( logging.LOG_DEBUG, "isStart" )
						self._handleStart(theframe, msg)
		
					elif msg.isClose():
						# Attempt to close the channel
						self.log.logmsg( logging.LOG_DEBUG, "attempting to close channel" )
						self._handleClose()

					else:
						# you shouldn't ever get here, as this should have been
						# caught earlier during initial message parsing, but
						# just for completeness
						self.log.logmsg( logging.LOG_ERR, "Unknown MSG type in doProcessing()" )
						raise BEEPManagementProfileException("Unknown MSG type in doProcessing()")
	
				elif theframe.isERR():
					self.log.logmsg( logging.LOG_DEBUG, "channel 0 ERR" )

				elif theframe.isANS():
					self.log.logmsg( logging.LOG_DEBUG, "channel 0 ANS" )

				else:
					# Should never get here, but...
					self.log.logmsg( logging.LOG_ERR, "Unknown frame type" )
					errmsg = self.mgmtCreator.createErrorMessage('500', constants.ReplyCodes['500'])
					self.channel.sendError(theframe.msgno, errmsg)
	
			except mgmtparser.ParserException, e:
				# RFC says to terminate session without response
				# if a non-MSG frame is poorly formed.
				# Poorly-formed MSG frames receive a negative
				# reply with an error message.
				self.log.logmsg(logging.LOG_ERR, "Malformed Message: %s" % e)
				if theframe.isMSG():
					errmsg = self.mgmtCreator.createErrorMessage('500', constants.ReplyCodes['500'])
					self.channel.sendError(theframe.msgno, errmsg)
					return
				else:
					raise BEEPManagementProfileException("Malformed Message: %s" % e)

	def _handleGreeting(self, theframe, msg):
		"""_handleGreeting is an internal method used from within
		doProcessing() to split it up a bit and make it more manageable
		It deals with <greeting> RPY frames
		"""
		if not self.receivedGreeting:
			self.receivedGreeting = 1
			self.session.receivedGreeting = 1
			self.log.logmsg( logging.LOG_INFO, "%s -> Received Greeting" % self )
		else:
			self.log.logmsg( logging.LOG_INFO, "%s: Man, these guys are really friendly!" % self)
			raise BEEPManagementProfileException("Too many greetings.")

	def _handleProfile(self, theframe, msg):
		# look up which channel was being started by msgno
		channelnum = self.startingChannel[theframe.msgno]
		del self.startingChannel[theframe.msgno]

		# create it at this end
		try:
			self.session.createChannelFromURIList(msg.getProfileURIList())
		except beep.core.session.SessionException, e:
			# If we get here, something very wrong happened.
			# Being here means we requested a channel be started
			# for a profile that is supported by the remote end,
			# but not at this end, which is kinda dumb.
			# We now have to request the other end close down the Channel
			self.log.logmsg(logging.LOG_ERR, "Remote end started channel with profile unsupported at this end.")
			self.log.logmsg(logging.LOG_ERR, "You probably screwed something up somewhere.")

	def _handleStart(self, theframe, msg):
		"""_handleStart() is an internal method used from within
		doProcessing() to split it up a bit and make it more manageable.
		It deals with <start> MSG frames
		"""
		# ok, start which channel number?
		reqChannel = msg.getStartChannelNum()
		self.log.logmsg( logging.LOG_DEBUG, "request to start channel %d" % reqChannel)

		# If I'm a listener, channel number requested must be odd
		if (reqChannel % 2) != 1:
			self.log.logmsg(logging.LOG_NOTICE, "Requested channel number of %d is even, and should be odd" % reqChannel)
			errmsg = self.mgmtCreator.createErrorMessage('501', constants.ReplyCodes['501'])
			self.channel.sendError(theframe.msgno, errmsg)
		else:
			# create a new channel with this number
			self.log.logmsg(logging.LOG_NOTICE, "Creating new channel, number: %d" % reqChannel)

			try:
				uri = self.session.createChannelFromURIList(reqChannel, msg.getProfileURIList())

			except beep.core.session.SessionException, e:
				self.log.logmsg(logging.LOG_DEBUG, "Cannot start channel: %s" % e)
				errmsg = self.mgmtCreator.createErrorMessage('504', constants.ReplyCodes['504'])
				self.channel.sendError(theframe.msgno, errmsg)
			# Finally, inform client of success, and which profile was used.
			self.log.logmsg(logging.LOG_DEBUG, "uri: %s" % uri)
			print "uri:", uri
			msg = self.mgmtCreator.createStartReplyMessage(uri)
			self.channel.sendReply(theframe.msgno, msg)

	def _handleClose(self, theframe, msg):
		"""handleClose() is an internal method used from within
		doProcessing() to split it up a bit and make it more manageable
		It deals with <close> MSG frames
		"""
		pass

	def startChannel(self, channelnum, profileList, serverName=None):
		"""startChannel() attempts to start a new Channel by sending a
		message on the management channel to the remote end, requesting
		a channel start.
		"""
		msg = self.mgmtCreator.createStartMessage(channelnum, profileList, serverName)
		msgno = self.channel.sendMessage(msg)
		# Take note that I'm attempting to start this channel
		self.startingChannel[msgno] = channelnum

	def closeChannel(self, channelnum, code='200'):
		"""closeChannel() attempts to close a Channel at the remote end
		by sending a <close> message to the remote end.
		"""
		msg = self.mgmtCreator.createCloseMessage(channelnum, code)
		msgno = self.channel.sendMessage(msg)
		self.closingChannel[msgno] = channelnum

	def setChannel(self, channel):
		"""This profile overloads setChannel to perform some
		processing first thing after the Profile is bound to
		the channel
		"""
		profile.Profile.setChannel(self, channel)
		# This is a hack to permit the greeting RPY message
		# that gets sent without requiring a MSG to have
		# already been sent.
		msgno = self.channel.allocateMsgno()
		self.sendGreetingMessage()

	def sendGreetingMessage(self):
		"""sendGreetingMessage() places a special kind of RPY
		message onto the outbound Queue. This is designed to
		be used once at the beginning of a Session initialisation,
		so it doesn't use the standard rules for sequence numbers
		"""
		# If the session I'm managing is a Listener, then I send
		# a URI list as part of my greeting.
		if isinstance(self.session, beep.core.session.ListenerSession):
			profileDict = self.session.getProfileDict()
			uriList = profileDict.getURIList()
			msg = self.mgmtCreator.createGreetingMessage(uriList)
		else:
			msg = self.mgmtCreator.createGreetingMessage()

		self.channel.sendGreetingReply(msg)

class BEEPManagementProfileException(profile.ProfileException):
	def __init__(self, args=None):
		self.args = args
