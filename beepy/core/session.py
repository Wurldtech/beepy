# $Id: session.py,v 1.8 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.8 $
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
import threading
import Queue
import traceback
import logging

import debug
import util
import statemachine
import constants
import errors
import channel
import frame
import mgmtparser
import mgmtcreator

from beepy.profiles import profile
from beepy.profiles import beepmgmtprofile

log = logging.getLogger('Session')
log.setLevel(logging.DEBUG)

class Session(statemachine.StateMachine):
    """
    The Session class is an abstract class with only core functions
    implemented. All transport related functions remain unimplemented
    and should be implemented in a class that inherits from Session
    """

    def __init__(self):
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

        self.sentGreeting = 0
        self.receivedGreeting = 0
        self.channels = {}
        self.ID = 0

        self.profileDict = profile.ProfileDict()

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


    def addProfile(self, profileModule):
        """ This method adds a given profile to the Session so that
        it is known to be a supported profile. It will then get
        advertised in greeting messages and be able to be bound
        to a channel, and suchlike
        """
        self.profileDict.addProfile(profileModule)

    # method to un-encapsulate frames recv'd from transport
    def _unplexFrames(self):
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
                        log.error("Channel %i out of sequence: %s" % (theframe.channelnum, e) )
                        raise TerminateException("Channel out of sequence")

                    except channel.ChannelMsgnoInvalid, e:
                        log.error("Channel %i: %s" % (theframe.channelnum, e))
                        raise TerminateException("Invalid msgno in channel")
                else:
                    # Attempted to send a frame to a non-existant channel number
                    # RFC says to terminate session
                    log.error("Attempt to send frame to non-existant channel: %i" % theframe.channelnum)
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
                    log.info("ProfileException: %s. Closing Channel." % e )
                    self.channels[0].profile.closeChannel(channelnum, '554')
                else:
                    raise TerminateException("%s" % e)

            except Exception, e:
                log.info("Exception in channel %i: %s" % (channelnum, e))

    # Open a new channel
    def createChannel(self, channelnum, profile):
        newchan = channel.Channel(channelnum, profile, self)
        self.channels[channelnum] = newchan

    def createChannelFromURIList(self, channelnum, uriList, profileInit=None):
        if not self.profileDict:
            log.critical("Session's profileDict is undefined!")
            raise SessionException("Session's profileDict is undefined!")

        # First, check requested profile(s) are available
        myURIList = self.profileDict.getURIList()
        if not myURIList:
            log.critical("Session's profileDict is empty!")
            raise SessionException("Session's profileDict is empty!")
        # Now, find a supported URI in our list
        for uri in uriList:
            if uri in myURIList:
                log.debug("uri found in profileDict: %s" % uri)

                # Attempt to instanciate the profile
                profileClassName = self.profileDict[uri].__profileClass__
                if profileClassName in self.profileDict[uri].__dict__.keys():
                    callback = self.profileDict.getCallback(uri)
                    profile = self.profileDict[uri].__dict__[profileClassName](self, profileInit, callback)
                else:
                    log.error("__profileClass__ doesn't contain the name of the Class to instanciate for uri: %s" % uri)
                    raise SessionException("__profileClass__ doesn't contain correct Class name")

                # And create a channel, at long last.
                self.createChannel(channelnum, profile)

                # Inform caller of uri used
                return uri

            # If we get here, then no supported profile URI was found
            log.debug("%s: uri not found in profileDict: %s" % (self, self.profileDict))

        raise SessionException("Profile not supported by Session")

    def shutdown(self):
        """attempts to close all the channels in a session
        before closing down the session itself.
        """
        try:
            chanlist = self.channels.keys()
            log.debug("Channels to close: %s" % chanlist)
            for channelnum in chanlist:
                if channelnum != 0:
                    doneEvent = threading.Event()
                    self.closeChannel(channelnum)
                    log.debug("Finished queueing closure of %d" % channelnum)
            ## Close channel 0 last
            self.closeChannel(0)

        except Exception, e:
            # If we can't close a channel, we must remain active
            # FIXME: more detailed error handling required here
            log.debug("Unable to close Session: %s" % e)
            traceback.print_exc()

    def deleteChannel(self, channelnum):
        log.debug("sessID %d: Deleting channel %d..." % (self.ID, channelnum) )
        if self.channels.has_key(channelnum):
            try:
                self.channels[channelnum].close()
                del self.channels[channelnum]
                log.debug("sessID %d: Channel %d deleted." % (self.ID, channelnum) )
            except channel.ChannelMessagesOutstanding, e:
                log.debug("sessID %d: Exception deleting channel %d: %s..." % (self.ID, channelnum, e) )
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
            log.error("Attempted to create a Channel 0 when one already exists!")
            raise SessionException("Can't create more than one Channel 0")

        else:
            profile = beepmgmtprofile.BEEPManagementProfile(self)
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

    def isChannelError(self, channelnum):
        return self.channels[0].profile.isChannelError(channelnum)

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
        raise NotImplementedError
        
    def recvFrame(self):
        """recvFrame() is used to get Frames from the inbound Queue for
        processing by the Session. 
        It ignores an empty Queue condition since we want processing to
        continue in that case.
        """
        raise NotImplementedError
        try:
            theframe = self.inbound.get(0)
            if theframe:
                return theframe

        except Queue.Empty:
            pass

    def greetingReceived(self):
        """ This is a callback from the management profile
        to trigger processing once the connection greeting
        is received from the remote end.
        Servers don't really do anything with this, but
        it's important for clients.
        """
        ## Do nothing by default
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

    def getChannelState(self, channelnum):
        return self.channels[0].profile.getChannelState(channelnum)

    def newChannel(self, profile):
        log.debug('trying to start channel with %s' % profile.uri)
        self.startChannel([[profile.uri, None, None]])

    def startChannel(self, profileList):
        """startChannel() attempts to start a new channel for communication.
           doneEvent is an optional Event() used to signal completion,
           either successfully or unsuccessfully. You can use this instead of
           polling.
        """
        log.debug('profileList: %s' % profileList)
        if self.receivedGreeting:
            # Attempt to get the remote end to start the Channel
            channelnum = self.nextChannelNum
            self.channels[0].profile.startChannel( channelnum, profileList, self.channelStarted, self.channelStartedError )
            # Increment nextChannelNum appropriately.
            self.nextChannelNum += 2
            # Return channelnum created
            return channelnum
        else:
            raise SessionException("Greeting not yet received")

    def channelStarted(self, channelnum):
        """ Action to take when a positive RPY to a channel
        start message is received.
        Default is to do nothing, so override this in your subclass
        if you want anything to happen at this event.
        """
        pass

    def channelStartedError(self, channelnum):
        """ Action to take when a negative RPY to a channel
        start message is received.
        """
        state, code, desc = self.getChannelState(channelnum)
        log.error('Failed to start channel: %d %s' % (code, desc) )
        self.shutdown()
        pass

    def closeChannel(self, channelnum):
        """closeChannel() attempts to close a channel.
        inputs: channelnum, the number of the channel to close
        outputs: none
        raises: none
        """
        log.debug("Attempting to close channel %s..." % channelnum)
        if self.channels.has_key(channelnum):
            self.channels[0].profile.closeChannel(channelnum, self.channelClosed, self.channelClosedError)
        else:
            raise KeyError("Channel number invalid")

    def channelClosed(self, channelnum):
        """ This method gets called when a channel is closed successfully.
        """
        log.debug('Channel %d closed.' % channelnum)
        if len(self.channels) == 0:
            self.close()

    def channelClosedError(self, channelnum):
        """ What to do if a channel close fails
        """
        log.info('close of channel %d failed' % channelnum)
        pass

    def getChannel(self, channelnum):
        """ Get the channel object associated with a given channelnum
        """
        if self.channels.has_key(channelnum):
            return self.channels[channelnum]

    def close(self):
        raise NotImplementedError

    def _showInternalState(self):
        log.debug("Current internal state of %s" % self)
        for var in self.__dict__.keys():
            log.debug("%s: %s" % (var, self.__dict__[var]))

class SessionManager(statemachine.StateMachine):
    """A SessionManager is used to create and destroy sessions that
       handle BEEP connections
    """

    def __init__(self):
        self.log = log
        self.profileDict = profileDict
        self.sessionList = {}
        self.sessionIds = []

        self.sessionError = {}

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
#        self.log.logmsg(logging.LOG_DEBUG, "Allocated sessId: %d to %s" % (sessId, sessionInst))
        return sessId

    def deleteSession(self, sessId):
        self.log.logmsg(logging.LOG_DEBUG, "Removing session: %d..." % sessId)
        if sessId in self.sessionIds:
            del self.sessionList[sessId]
            self.sessionIds.remove(sessId)

    def replaceSession(self, sessId, sessionInst):
        self.sessionList[sessId] = sessionInst
        self.log.logmsg(logging.LOG_DEBUG, "Reallocated sessId: %d to %s" % (sessId, sessionInst))

    def deleteAllSessions(self):
        for sessId in self.sessionIds:
            self.deleteSession(sessId)

    def getSessionById(self, sessId):
        self.log.logmsg(logging.LOG_DEBUG, "Seeking session %d: in: %s" % (sessId, self.sessionList) ) 
        sess = self.sessionList[sessId]
        self.log.logmsg(logging.LOG_DEBUG, "Found session %d: %s" % (sessId, sess) ) 
        return sess

    def closeSession(self, sessionId):
        """ shutdown a given Session that is managed by this
            SessionManager.
        """
        sessionInst = self.getSessionById(sessionId)
        sessionInst.close()
        self.deleteSession(sessionInst.ID)

    def closeAllSessions(self):
        """ shutdown all Sessions managed by this SessionManager.
        """
        for sessionId in self.sessionIds:
            self.closeSession(sessionId)

    def setSessionError(self, sessionId, errorstr):
        """ Sets a session error in case a Session exits
            for some unexpected reason. This will get called
            from the Session itself.
        """
        self.sessionError[sessionId] = errorstr

    def getSessionError(self, sessionId):
        return self.sessionError[sessionId]

    def close(self):
        raise NotImplementedError

    def _showInternalState(self):
        self.log.logmsg(logging.LOG_DEBUG, "Current internal state of %s" % self)
        for var in self.__dict__.keys():
            self.log.logmsg(logging.LOG_DEBUG, "%s: %s" % (var, self.__dict__[var]))

# A ListenerManager is a special type of SessionManager that listens for
# incoming connections and creates Sessions to handle them.
# It is an abstract class.
class ListenerManager(SessionManager):

    def __init__(self, log, profileDict):
        SessionManager.__init__(self, log, profileDict)

class Listener(Session):
    """A Listener is a Session that is the result of
    a connection to a ListenerManager. It is the server side
    of a client/server connection. An Initiator would
    form the client side.
    """

    def __init__(self):
        Session.__init__(self) 

        # Listeners use only even numbered channels for allocation
        self.nextChannelNum = 2

class InitiatorManager(SessionManager):
    def __init__(self, log, profileDict):
        SessionManager.__init__(self, log, profileDict)

class Initiator(Session):
    """An Initiator is a Session that initiates a connection
    to a ListenerManager and then communicates with the resulting
    Listener. It forms the client side of a client/server
    connection.
    """
    def __init__(self):
        Session.__init__(self)

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
