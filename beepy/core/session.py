# $Id: session.py,v 1.19 2004/11/10 01:17:01 jpwarren Exp $
# $Revision: 1.19 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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

"""
This module defines the Session layer API for BEEPy.
Applications will spend a large amount of time interacting
with the API defined here, in concert with beepy.channel
and the transport layer.
"""

import socket
import threading
import Queue
import traceback

import logging
from debug import log
#log = logging.getLogger('')

import constants
import errors
import channel
import frame
from beepy.profiles import profile
from beepy.profiles import beepmgmtprofile

## Set some state definitions
PRE_GREETING = 0
ACTIVE = 1
CLOSING = 2
TERMINATING = 3
CLOSED = 4
TUNING = 5

class Session:
    """
    A Session is the main entity relating to a BEEP peer connection. A
    session represents a single connection to a remote peer and can contain
    numerous channels for processing.
    """
    
    def __init__(self, listener):
        """
        Create a new Session.
        """
        self.state = PRE_GREETING
        self.channels = {}
        self.localSeqno = {}
        self.remoteSeqno = {}
        self.ID = 0
        self.listener = listener

        self.setStartingChannelNum()
    
    def setStartingChannelNum(self):
        """
        Sets the channel number of the first channel that should be
        created. This is used to differentiate between Listener channels
        and Initiator channels.
        """
        if self.listener:
            self.nextChannelNum = 2
        else:
            self.nextChannelNum = 1
    
    def _setID(self, sessId):
        self.ID = sessId
    
    def validateFrame(self, theframe):
        if self.channels.has_key(theframe.channelnum):
            try:
                #import nice
                #logging.debug('Received frame: \n' + nice.hex_dump(str(theframe), 24, '    '))
                self.channels[theframe.channelnum].validateFrame(theframe)

            except TerminateException, e:
                self.close()
                
            except Exception, e:
                raise
        else:
            log.info('Attempt to send to non-existant channel: %d' % theframe.channelnum)
            raise SessionException('Invalid Channel Number')
    
    def processFrame(self, theframe):
        """
        Allocate a given frame to the channel it belongs to
        and call the channel's processing method.

        @param theframe: the frame to process
        @type theframe: a DataFrame object
        """
#        log.debug('processing frame: %s' % theframe)

        if self.channels.has_key(theframe.channelnum):
            try:
                #import nice
                #logging.debug('Received frame: \n' + nice.hex_dump(str(theframe), 24, '    '))
                self.channels[theframe.channelnum].processFrame(theframe)

            except TerminateException, e:
                self.close()
                
            except Exception, e:
                raise
        else:
            log.info('Attempt to send to non-existant channel: %d' % theframe.channelnum)
            raise SessionException('Invalid Channel Number')
    
    def createChannel(self, channelnum, profile):
        """
        Creates a new channel with the given channel number
        and binds the given profile to it for processing.

        @param channelnum: the channel number for the channel
        @type channelnum: integer

        @param profile: the profile to bind to the channel
        @type profile: a Profile object
        """
        self.createTransportChannel(channelnum)        
        newchan = channel.Channel(channelnum, profile, self)
        self.channels[channelnum] = newchan
        return newchan
    
    def createTransportChannel(self, channelnum):
        """
        This method should be overridden at the transport
        layer if there is any special work that needs to
        be done at channel create time.
        """
        log.debug('session creating transport channel')
        pass
    
    def channelRequested(self, channelnum, profiles):
        """
        Called when the other peer attempts to open a new channel.
        
        @param channelnum: the channel number of the channel to create
        @param profiles: a dictionary of {uri: (cdata, encoding)} items
        
        @return: a tuple: (chosen uri, profile object, response cdata)
        """
        # Find a supported URI in our list
        for uri in profiles:
            if uri in self.profiles:
                # Instantiate the profile
                profile, cdata, encoding = self.profiles[uri].createProfile()
                # (uri, profile object, response cdata, encoding)
                return (uri, profile, cdata, encoding)
        raise NoSuitableProfiles('No suitable profiles')
    
    def closeAllChannels(self):
        """
        Attempts to close all channels on this Session
        """
        try:
            for channelnum in self.channels.keys():
                if channelnum != 0:
                    self.closeChannel(channelnum)
                    log.debug("Finished queueing closure of %d" % channelnum)
            ## Close channel 0 last
            # FIXME: We DO NOT close channel 0 to avoid race condition because
            # the client should close it
            #self.closeChannel(0)
        
        except Exception, e:
            # If we can't close a channel, we must remain active
            # FIXME: more detailed error handling required here
            log.error("Unable to close Session: %s" % e)
            traceback.print_exc()
    
    def shutdown(self):
        """
        Attempts to close all the channels in a session
        before closing down the session itself.
        """
        log.debug('shutdown() started...')
        self.state = CLOSING
        self.closeAllChannels()
    
    def sessionClosed(self):
        """
        Called when the Session has completed its shutdown
        """
        pass
    
    def tuningBegin(self):
        """
        Called by a profile when a tuning reset process begins. This
        is to notify the session that we're just waiting for confirmation
        of the tuning reset from the remote end.
        """
#        log.debug('changing state to TUNING')
        self.state = TUNING
    
    def tuningReset(self):
        """
        A tuning reset causes all channels, including channel
        Zero to be closed and a new channel zero to be created,
        with a new greeting sent.
        
        This is used for turning on TLS.
        """
        self.deleteAllChannels()
        self.startTLS()
        self.setStartingChannelNum()
        self.createChannelZero()
        self.state = PRE_GREETING
    
    def deleteChannel(self, channelnum):
        """
        Delete a single channel from the Session
        
        @param channelnum: the channel number to delete
        @type channelnum: integer
        """
        self.deleteTransportChannel(channelnum)
        del self.channels[channelnum]
        log.debug("Channel %d deleted." % channelnum )
    
    def deleteAllChannels(self):
        """
        Attempt to delete all channels on the session
        """
        chanlist = self.channels.keys()
        for channelnum in chanlist:
            self.deleteChannel(channelnum)
    
    def createChannelZero(self):
        """
        Create the Channel 0 for the Session.
        A special case of createChannel that explicitly binds the channel
        to the BEEPManagementProfile.
        
        Should only get called once when a Session initialises
        """
        if self.channels.has_key(0):
            log.error("Attempted to create a Channel 0 when one already exists!")
            raise SessionException("Can't create more than one Channel 0")
        
        else:
            profile = beepmgmtprofile.BEEPManagementProfile()
            channel = self.createChannel(0, profile)
            profile.channelStarted(channel, '', '')
    
    def isChannelActive(self, channelnum):
        """
        This method provides a way of figuring out if a channel is
        running.
        
        @param channelnum: the channel number to check
        @type channelnum: int
        """
        if self.channels.has_key(channelnum):
            return 1
        else:
            return 0
    
    def _getActiveChannel(self, channelnum):
        """
        This method provides a way of getting the channel object
        by number.
        
        Deprecated
        """
        if self.isChannelActive(channelnum):
            return self.channels[channelnum]
        return None
    
    def _isChannelError(self, channelnum):
        """
        Checks to see if the channel has encountered an error condition.
        
        Deprecated.
        """
        return self.channels[0].profile.isChannelError(channelnum)
    
    def _flushChannelOutbound(self):
        """
        This method gets all pending messages from all channels
        one at a time and places them on the Session Outbound Queue.
        This should probably only be used in Tuning Resets, but you
        never know when it might come in handy.
        
        Deprecated.
        """
        chanlist = self.channels.keys()
        for channelnum in chanlist:

            theframe = self.channels[channelnum].pull()
            if( theframe ):
                self.sendFrame(theframe)
                del theframe
    
    def _handleGreeting(self):
        """
        A greeting may be received in two circumstances:
        - When first connecting to a peer
        - After a tuning reset
        """
        if not (self.state == PRE_GREETING):
            raise TerminateException('Greeting already received in state %s' % self.state)
        else:
#            log.debug('changing state to ACTIVE')
            self.state = ACTIVE
#            log.debug('Greeting received')
            self.sessionStarted()
    
    def sessionStarted(self):
        """
        This is a callback from the management profile
        to trigger processing once the connection greeting
        is received from the remote end.
        Servers don't really do anything with this, but
        it's important for clients.
        """
        ## Do nothing by default
        pass
    
    def _getChannelZeroProfile(self):
        """ Deprecated.
        """
        return self.channels[0].profile
    
    def _reset(self):
        """
        reset() does a tuning reset which closes all channels and
        terminates the session.
        
        Deprecated.
        """
        self.transition('reset')
    
    def getChannelState(self, channelnum):
        """
        Get the state of a particular channel.
        
        """
        return self.channels[0].profile.getChannelState(channelnum)
    
    def newChannel(self, uri, handler_obj, cdata=None, encoding=None):
        """
        Attempt to start a new Channel with a given profile.
        This method is used by a peer to request a BEEP peer to start a
        new channel with the given profile.
        
        This is mostly a convenience function for the common case of
        starting a simple channel with a single profile. For more complex
        start scenarios, use startChannel().
        
        @param profile: the profile to bind to the channel
        @param chardata: initialisation data to send as part of the
        channel start request.
        """
        return self.startChannel({uri: (cdata, encoding)}, handler_obj)
    
    def startChannel(self, profiles, handler_obj):
        """
        startChannel() attempts to start a new channel for communication.
        It uses a more complex profileList to determine what to send to
        the remote peer as part of the start request.
        
        the profileList is a list of lists with the following structure:
        
        [ uri, encoding, chardata ]
        
        where uri is a string URI of the profile to request,
        encoding is an optional encoding to use and chardata is any
        initialisation data to send as part of the start message.
        
        To start a channel with the echoprofile and no special requirements,
        you would use a list like this:
        
        [ [echoprofile.uri, None, None] ]
        
        To try to start a channel first using SASL/OTP, then SASL/ANONYMOUS,
        you would use a list like this:
        
        [ [saslotpprofile.uri, None, None], [saslanonymousprofile.uri, None, None] ]
        
        More complex scenarios are possible.
        """
        
        ## We can only start channels if we're in the ACTIVE state
        if self.state == ACTIVE:
            # Attempt to get the remote end to start the Channel
            channelnum = self.nextChannelNum
            self.channels[0].profile.startChannel(channelnum, profiles, \
                handler_obj)
            # Increment nextChannelNum appropriately.
            self.nextChannelNum += 2
            # Return channelnum we asked to start
            return channelnum
            
        else:
            log.debug('startChannel received in state %s' % self.state)
            raise SessionException('Attempt to start channel when not ACTIVE')
    
    def channelStartingError(self, channelnum, code, desc):
        """
        Action to take when a negative RPY to a channel
        start message is received.

        @param channelnum: the channel number that failed to start
        """
        log.error('Failed to start channel: %d %s' % (code, desc) )
        self.shutdown()
    
    def closeChannel(self, channelnum):
        """
        requestCloseChannel() attempts to close a channel.
        @param channelnum: the number of the channel to close
        """
        log.debug("Attempting to close channel %s..." % channelnum)
        if self.channels.has_key(channelnum):
            self.channels[0].profile.closeChannel(channelnum)
        else:
            raise KeyError("Channel number invalid")
    
    def _channelClosedSuccess(self, channelnum):
        """
        Internal channel closure method.
        """
        log.debug('Channel %d closed.' % channelnum)
        if len(self.channels) == 0:
            self.close()
        self.channelClosed(channelnum)
        if channelnum == 0:
            self.sessionClosed()
    
    def channelClosed(self, channelnum):
        """
        Override this method to receive notification of channel closure
        """
        pass
    
    def _channelClosedError(self, channelnum, code, desc):
        """
        Internal channel closure error handling
        """
        ## does nothing but call api method at this stage
        self.channelClosedError(channelnum, code, desc)
    
    def channelClosedError(self, channelnum, code, desc):
        """ What to do if a channel close fails
        """
        log.info('close of channel %d failed: %s: %s' % (channelnum, code, desc) )
        pass
    
    def getChannel(self, channelnum):
        """ Get the channel object associated with a given channelnum
        """
        if self.channels.has_key(channelnum):
            return self.channels[channelnum]
    
    def _showInternalState(self):
        log.debug("Current internal state of %s" % self)
        for var in self.__dict__.keys():
            log.debug("%s: %s" % (var, self.__dict__[var]))
    
    ##
    ## Callback hooks for application programs
    ##
    def receivedMessage(self, frame):
        """
        Use this callback from your profiles to communicate
        with your apps when a MSG frame is received.
        """
        pass
    
    def receivedAnswer(self, frame):
        """
        Use this callback from your profiles to communicate
        with your apps when an ANS frame is received.
        """
        pass
    

# Exception classes
class SessionException(errors.BEEPException):
    """
    Base exception class for Sessions.
    """
    def __init__(self, args=None):
        self.args = args

class TerminateException(SessionException):
    """
    Raised when a session encounters an error that
    should result in the session being terminated/dropped.
    """
    def __init__(self, args=None):
        self.args = args

class TuningReset(SessionException):
    """
    Raised when a tuning reset should occur.
    @depreciated: This is no longer used and will be removed soon.
    """
    def __init__(self, args=None):
        self.args = args

class ChannelZeroOutOfSequence(SessionException):
    """
    Raised if channel 0 ever gets out of sequence.
    """
    def __init__(self, args=None):
        self.args = args

class NoSuitableProfiles(SessionException):
    pass

class SessionInboundQueueFull(SessionException):
    """
    Used when the session's inbound message queue is full.
    
    @depreciated: Was used in the old threading model. No
    longer used and will be removed.
    """
    def __init__(self, args=None):
        self.args = args

class SessionOutboundQueueFull(SessionException):
    """
    Used when the session's outbound message queue is full.
    
    @depreciated: Was used in the old threading model. No
    longer used and will be removed.
    """
    def __init__(self, args=None):
        self.args = args

