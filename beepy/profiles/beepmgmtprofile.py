# $Id: beepmgmtprofile.py,v 1.13 2004/08/02 09:46:07 jpwarren Exp $
# $Revision: 1.13 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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
This module implements the BEEP Management profile.

This profile is used to manage BEEP sessions and channels.

@version: $Revision: 1.13 $
@author: Justin Warren
"""
import logging
from beepy.core import debug
log = logging.getLogger('beepy')

import profile
from beepy.core import constants
import mgmtparser 
import mgmtcreator
import message

# Have to do it this way, as beepy.core.session imports
# this file.
import beepy.core.session

import traceback

class BEEPManagementProfile(profile.Profile):
    """
    The BEEPManagementProfile is used on Channel 0 for all Sessions
    to control the management of the Session and all channels on it.
    """

    CONTENT_TYPE = "application/beep+xml"

    CHANNEL_STARTING = 1
    CHANNEL_OPEN = 2
    CHANNEL_CLOSING = 3
    CHANNEL_CLOSED = 4
    CHANNEL_ERROR = 5

    def __init__(self, session):
        """
        Create a new profile instance for the given session.
        @param session: the session this profile's channel is on.
        """
        profile.Profile.__init__(self, session)
        self.mgmtParser = mgmtparser.Parser()
        self.mgmtCreator = mgmtcreator.Creator()

        # channels that are starting, keyed by msgno
        self.startingChannel = {}
        # channels that are closing, keyed by msgno
        self.closingChannel = {}
        # holder for synchronisation events for channel start/close/error
        self.channelEvent = {}
        # persistent channel state, keyed by channelnum
        self.channelState = {}

    def processMessage(self, msg):
        """
        process any incoming Messages

        @param msg: an incoming DataFrame object
        """
#        log.debug('processing message: %s' % msg.payload)
        try:
            data = self.mimeDecode(msg.payload)
            if self.type != self.CONTENT_TYPE:
                raise profile.TerminalProfileException("Invalid content type for message: %s != %s" % (self.type, self.CONTENT_TYPE) )

            mgmtMsg = self.mgmtParser.parse(data)

            # Handle RPY Frames
            if msg.isRPY():

                # handle <greeting> RPY frames
                if mgmtMsg.isGreeting():
                    try:
                        self.session._handleGreeting()
                    except beepy.core.session.TerminateException, e:
                        raise profile.TerminalProfileException(e)
#                else:
#                    log.debug("Non-greeting RPY received" ) 

                # This means a channel start was successful
                if mgmtMsg.isProfile():

                    self._handleProfile(msg, mgmtMsg)

                # Confirmation messages, such as for a close
                if mgmtMsg.isOK():
                    self._handleOK(msg, mgmtMsg)

            # Message frame processing
            elif msg.isMSG():

#                log.debug("%s: channel 0 MSG: %s" % (self, msg))
#                if not self.receivedGreeting:
#                    raise profile.TerminalProfileException("Client sent MSG before greeting.")

                if mgmtMsg.isStart():
#                    log.debug("msg isStart" )
                    self._handleStart(msg, mgmtMsg)

                elif mgmtMsg.isClose():
                    # Attempt to close the channel
#                    log.debug("msg isClose " )
                    try:
                        self._handleClose(msg, mgmtMsg)
                    except Exception, e:
                        log.error("Exception handling channel closure: %s" % e)
                        traceback.print_exc()
                        raise

                else:
                    # you shouldn't ever get here, as this should have been
                    # caught earlier during initial message parsing, but
                    # just for completeness
                    log.error("Unknown MSG type in doProcessing()" )
                    raise profile.TerminalProfileException("Unknown MSG type in doProcessing()")

            elif msg.isERR():
                log.debug("channel 0 ERR" )
                try:
                    self._handleError(msg, mgmtMsg)

                except Exception, e:
                    log.error("Exception handling error frame: %s" % e)
                    traceback.print_exc()

            elif msg.isANS():
                log.debug("channel 0 ANS")

            elif msg.isNUL():
                log.debug("channel 0 NUL")

            else:
                # Should never get here, but...
                log.error("Unknown frame type" )
                errmsg = self.mgmtCreator.createErrorMessage('500')
                errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
                self.channel.sendError(msg.msgno, errmsg)

        except mgmtparser.ParserException, e:
            # RFC says to terminate session without response
            # if a non-MSG frame is poorly formed.
            # Poorly-formed MSG frames receive a negative
            # reply with an error message.
            log.error("Malformed Message: %s" % e)
            if msg.isMSG():
                errmsg = self.mgmtCreator.createErrorMessage('500')
                errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
                self.channel.sendError(msg.msgno, errmsg)
                return
            else:
                raise profile.TerminalProfileException("Malformed Message: %s" % e)

        except profile.TerminalProfileException:
            raise

        except Exception, e:
            log.debug("Unhandled exception in BEEP management profile: %s: %s" % (e.__class__, e) )
            traceback.print_exc()
            raise
            
    def _handleProfile(self, msg, mgmtMsg):
        # look up which channel was being started by msgno
        try:
            channelnum = self.startingChannel[msg.msgno]

            del self.startingChannel[msg.msgno]

            # create it at this end
            uri = self.session.createChannelFromURIList(channelnum, mgmtMsg.getProfileURIList())

            log.debug("Channel %s created successfully." % channelnum )
            # Channel was started successfully, so set the event
            self.channelState[channelnum] = [ self.CHANNEL_OPEN ]
            log.debug('remote channel started')
            self.channelEvent[channelnum][0](channelnum, uri)            

        except KeyError:
            # a profile was received for a channel that we weren't
            # starting, which is bad, so kill session.
            log.error("Attempt to confirm start of channel we didn't ask for.")
            raise profile.TerminalProfileException("Invalid Profile RPY Message")

        except beepy.core.session.SessionException, e:
            # If we get here, something very wrong happened.
            # Being here means we requested a channel be started
            # for a profile that is supported by the remote end,
            # but not at this end, which is kinda dumb.
            # We now have to request the other end close down the Channel
            log.error("%s" % e)
            log.error("Remote end started channel with profile unsupported at this end.")
            raise
        
        except Exception, e:
            log.error("Unhandled exception: %s" % e)
            traceback.print_exc()
            raise profile.TerminalProfileException("%s" % e)

    def _handleStart(self, msg, mgmtMsg):
        """_handleStart() is an internal method used from within
        doProcessing() to split it up a bit and make it more manageable.
        It deals with <start> MSG frames
        """
        # ok, start which channel number?
        try:
            reqChannel = mgmtMsg.getStartChannelNum()

            # If I'm a listener, channel number requested must be odd
            if (reqChannel % 2) != 1:
                log.warning("Requested channel number of %d is even, and should be odd" % reqChannel)
                errmsg = self.mgmtCreator.createErrorMessage('501')
                errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
                self.channel.sendError(msg.msgno, errmsg)
            else:
                # Check to see if start message has a CDATA section
                cdata = mgmtMsg.getStartProfileBlob()
                # create a new channel with this number
                log.debug("Creating new channel, number: %d" % reqChannel)

                uri = self.session.createChannelFromURIList(reqChannel, mgmtMsg.getProfileURIList(), cdata)
                # Inform client of success, and which profile was used.
                data = self.mgmtCreator.createStartReplyMessage(uri)
                data = self.mimeEncode(data, self.CONTENT_TYPE)
                self.channel.sendReply(msg.msgno, data)

                # Notify local stuff of the channel being started
                log.debug('local channel started')
                self.session.channelStarted(reqChannel, uri)

        except beepy.core.session.SessionException, e:
            log.warning("Cannot start channel: %s" % e)
            errmsg = self.mgmtCreator.createErrorMessage('504')
            errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
            self.channel.sendError(msg.msgno, errmsg)

        except message.MessageInvalid, e:
            log.warning("Requested channel number is invalid.")
            errmsg = self.mgmtCreator.createErrorMessage('501', 'Requested channel number is invalid.')
            errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
            self.channel.sendError(msg.msgno, errmsg)

        except Exception, e:
            log.error("Unhandled exception in _handleStart: %s, %s" % (e.__class__, e) )
            traceback.print_exc()
            errmsg = self.mgmtCreator.createErrorMessage('550', 'Unexpected exception: %s' % e)
            errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
            self.channel.sendError(msg.msgno, errmsg)

    def _handleClose(self, msg, mgmtMsg):
        """_handleClose() is an internal method used from within
        doProcessing() to split it up a bit and make it more manageable
        It deals with <close> MSG frames
        """
        try:
            channelnum = mgmtMsg.getCloseChannelNum()
            ## check we're not already closing the channel
            if channelnum in self.closingChannel.values():
                log.warning('Close already in progress for channel %d' % channelnum)
                errmsg = self.mgmtCreator.createErrorMessage('553')
                errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
                self.channel.sendError(msg.msgno, errmsg)
                
            else:
                ## If the channel number is 0, we can't close it
                ## unless all the other channels are closed first.
                if channelnum == 0 and len(self.session.channels) != 1:
                    ## Tell the remote end we can't do it yet.
                    errmsg = self.mgmtCreator.createErrorMessage('550')
                    errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
                    self.channel.sendError(msg.msgno, errmsg)
                else:
                    
                    log.debug('handling closure of channel %d' % channelnum)
                    self.session.channels[channelnum].close()
                    data = self.mgmtCreator.createOKMessage()
                    data = self.mimeEncode(data, self.CONTENT_TYPE)
                    msgno = self.channel.sendReply(msg.msgno, data, self.session.deleteChannel, None, channelnum )

        except beepy.core.channel.ChannelMessagesOutstanding:
            ## Can't close the channel yet because the peer
            ## hasn't replied to all MSGs. Send an error.
            errmsg = self.mgmtCreator.createErrorMessage('550')
            errmsg = self.mimeEncode(errmsg, self.CONTENT_TYPE)
            self.channel.sendError(msg.msgno, errmsg)
            
        except Exception, e:
            log.error('Exception in management profile: %s' % e)
            raise

    def _completeClosure(self, msgno):
        """
        Used as a callback for the successful sending of a
        close confirmation message.
        """
        log.debug('close completed successfully: %d' % msgno)
        log.debug('%s' % self.closingChannel)

    def _handleOK(self, msg, mgmtMsg):
        """_handleOK is an internal method used from within
        doProcessing() to split it up a bit and make it more manageable
        It deals with <ok> MSG frames, such as those used to confirm
        a channel close.
        """
        
        # First, we check if this is a close confirmation
        if self.closingChannel.has_key(msg.msgno):
            # yep, we're closing, and it's ok to delete this end
            channelnum = self.closingChannel[msg.msgno]
            self.session.deleteChannel(channelnum)
            del self.closingChannel[msg.msgno]
            self.channelState[channelnum] = [ self.CHANNEL_CLOSED ]
            self.channelEvent[channelnum][0](channelnum)

    def _handleError(self, msg, mgmtMsg):
        """
        called from doProcessing() to handle ERR frames
        """
        code = mgmtMsg.getErrorCode()
        desc = mgmtMsg.getErrorDescription()

        log.warning('Remote error: %s: %s' % ( code, desc ))

        ## Error during channel start
        if self.startingChannel.has_key(msg.msgno):
            channelnum = self.startingChannel[msg.msgno]

            del self.startingChannel[msg.msgno]
            self.channelState[channelnum] = [ self.CHANNEL_ERROR, code, desc ]
            if self.channelEvent[channelnum]:
                self.channelEvent[channelnum][1](channelnum, code, desc)

        ## Error during channel close
        elif self.closingChannel.has_key(msg.msgno):
            channelnum = self.closingChannel[msg.msgno]

            del self.closingChannel[msg.msgno]
            self.channelState[channelnum] = [ self.CHANNEL_ERROR, code, desc ]
            if self.channelEvent[channelnum]:
                self.channelEvent[channelnum][1](channelnum, code, desc)

    def getChannelState(self, channelnum):
        if self.channelState.has_key(channelnum):
            return self.channelState[channelnum]

    def startChannel(self, channelnum, profileList, startedOk, startedError, serverName=None):
        """
        startChannel() attempts to start a new Channel by sending a
        message on the management channel to the remote end, requesting
        a channel start.
        """
        data = self.mgmtCreator.createStartMessage(channelnum, profileList, serverName)
        data = self.mimeEncode(data, self.CONTENT_TYPE)
        msgno = self.channel.sendMessage(data)
        # Take note that I'm attempting to start this channel
        self.startingChannel[msgno] = channelnum
        self.channelState[channelnum] = [ self.CHANNEL_STARTING ]
        self.channelEvent[channelnum] = [ startedOk, startedError ]

    def closeChannel(self, channelnum, closedOk, closedError, code='200'):
        """closeChannel() attempts to close a Channel at the remote end
        by sending a <close> message to the remote end.
        """
        data = self.mgmtCreator.createCloseMessage(channelnum, code)
        data = self.mimeEncode(data, self.CONTENT_TYPE)
        msgno = self.channel.sendMessage(data)
        self.closingChannel[msgno] = channelnum
        self.channelState[channelnum] = [ self.CHANNEL_STARTING ]
        self.channelEvent[channelnum] = [ closedOk, closedError ]

    def sendGreeting(self):
        """sendGreetingMessage() places a special kind of RPY
        message onto the outbound Queue. This is designed to
        be used once at the beginning of a Session initialisation,
        so it doesn't use the standard rules for sequence numbers
        """
        profileDict = self.session.getProfileDict()
        uriList = profileDict.getURIList()
        data = self.mgmtCreator.createGreetingMessage(uriList)
        data = self.mimeEncode(data, self.CONTENT_TYPE)
        self.channel.sendGreetingReply(data)
        
    def isChannelError(self, channelnum):
        log.debug("channelState: %s" % self.channelState[channelnum] )
        if self.channelState[channelnum][0] == self.CHANNEL_ERROR:
            return 1

class BEEPManagementProfileException(profile.ProfileException):
    def __init__(self, args=None):
        self.args = args
