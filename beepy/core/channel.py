# $Id: channel.py,v 1.15 2007/09/03 03:20:03 jpwarren Exp $
# $Revision: 1.15 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

"""
Channel related code

@version: $Revision: 1.15 $
@author: Justin Warren
"""
import logging
from debug import log
#log = logging.getLogger('beepy')

import constants
import errors
import logging
import frame
import traceback

from message import Message

#import Queue

class Channel:
    """
    A Channel object is an abstraction of a BEEP channel running over some
    form of transport.
    """
    channelnum = -1         # Channel number
    localSeqno = -1L        # My current Sequence number
    remoteSeqno = -1L       # Remote Sequence number
    profile = None          # channel Profile
#    state = 0

    # Create a new channel object
    def __init__(self, channelnum, profile, session):
        """
        @type channelnum: integer
        @param channelnum: The number to assign to this Channel object

        @type profile: Profile
        @param profile: The Profile object to bind to this channel

        @type session: Session
        @param session: The Session object this Channel belongs to

        @raise ChannelException: when the channel number is out of bounds.
        """

        try:
            assert( constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL)
            self.state = constants.CHANNEL_STARTING
            self.channelnum = channelnum
            self.priority = 0
            self.allocatedMsgnos = []
            self.receivedMsgnos = []
            self.nextMsgno = constants.MIN_MSGNO + 1
            self.localAnsno = {}
            self.remoteAnsno = {}
            self.started = 0
            self.localSeqno = 0
            self.remoteSeqno = 0
            self.ansno = 0
            self.profile = profile
            self.session = session
            self.moreFrameType = None
            self.moreFrameMsgno = 0

            self.msgbuf = {}             # Buffer for messages
            self.ansbuf = {}             # buffer for answer messages

            # records the last status for each message number used.
            self.msgStatus = {}

            # This binds the profile to this channel, readying it for operation.
            self.profile.setChannel(self)

        except AssertionError:
            raise ChannelException('Channel number %s out of bounds' % channelnum)

    def send(self, msg):
        """
        Used to send a frame over this channel. Predominantly used by
        the Profile bound to this channel to send messages.
        send() passes the Message to the Session and its associated
        transport layer.

        If messages are sent asynchronously (such as with fragmentation)
        then you should use the callback as a way to signify that the
        call finished.

        @type msg: a DataFrame object
        @param msg: the DataFrame to send

        """
#        log.debug('sending message...')
        self.session.sendMessage(msg, self.channelnum)

    def _recv(self):
        """
        recv() is used by Profiles to receive
        frames from the Channel inbound Queue for
        processing in their processMessages() method.
        It ignores a Queue.Empty condition.
        
        Deprecated.
        
        """
#        if self.state is constants.CHANNEL_ACTIVE:
#            try:
#                return self.inbound.get(0)
#            except Queue.Empty:
#                pass
#        else:
#            raise ChannelStateException('Channel not started')

    # interface to Session
    def validateFrame(self, theframe):
        """
        Performs sanity checking on an inbound Frame before it is
        passed to a profile for processing.

        @type theframe: DataFrame
        @param theframe: the DataFrame to validate

        @raise ChannelStateException: if Channel is not active
        @raise ChannelOutOfSequence: if frame seqno is not expected value
        @raise ChannelException: if frametype is incorrect
        @raise ChannelException: if frame msgno is not expected value
        @raise ChannelMsgnoInvalid: if frame msgno is invalid

        """
#        if self.state is not constants.CHANNEL_ACTIVE:
#            raise ChannelStateException('Channel not active')
        # check sequence number
        if theframe.seqno != self.remoteSeqno:
            raise ChannelException("Expected seqno: %i but got %i" % (self.remoteSeqno, theframe.seqno))
        else:
            # update my seqno
            self.allocateRemoteSeqno(theframe.size)

        # check the frametype is the right one if we're expecting More frames
        if self.moreFrameType:
            if theframe.dataFrameType is not self.moreFrameType:
                raise ChannelException("Frametype incorrect. Expecting more %s frames" % self.moreFrameType)
            # Then check the msgno is the right one
            if theframe.msgno is not self.moreFrameMsgno:
                raise ChannelException("Msgno incorrect. Expecting more frames for msgno: %i" % self.moreFrameMsgno)
        # if Frame has the more flag set, set our expected MoreType and Msgno
        if theframe.more is constants.MoreTypes['*']:
            self.moreFrameType = theframe.dataFrameType
            self.moreFrameMsgno = theframe.msgno
        else:
            self.moreFrameType = None
            self.moreFrameMsgno = 0

        # If the frametype is MSG, check that the msgno hasn't
        # been completely received, but not replied to yet.
        if theframe.dataFrameType == constants.DataFrameTypes['MSG']:
            if theframe.msgno in self.receivedMsgnos:
                raise ChannelMsgnoInvalid('msgno %i not valid for MSG' % theframe.msgno)

        # Otherwise, check the msgno is valid
        else:
            
            # Allow first frame received for the greeting on management channel
            if not ( theframe.dataFrameType == constants.DataFrameTypes['RPY'] and theframe.msgno == 0 and self.channelnum == 0 ):
                if theframe.msgno not in self.allocatedMsgnos:
                    if self.channelnum == 0:
                        raise ChannelMsgnoInvalid('msgno %i not valid for %s' % (theframe.msgno, theframe) )
                    else:
                        self.sendError(theframe.msgno, 'Invalid msgno')

    def processFrame(self, theframe):
        """
        Called by a Session when it receives a frame on this Channel
        to process the frame.

        @type theframe: DataFrame
        @param theframe: the DataFrame to process
	"""
	self.validateFrame(theframe)

        ## Special rules apply to ANS Frames
        if theframe.isANS():

            ## If we're partway through an ANS message, append to it
            if self.ansbuf.has_key(theframe.ansno):
                self.ansbuf[theframe.ansno].append(theframe.payload)

            else:
                self.ansbuf[theframe.ansno] = Message(dataframe=theframe)
                
            ## Check to see if this is the last Frame for the message.
            ## If it is, pass it to the profile for processing.
            if theframe.more == constants.MoreTypes['.']:
                self.profile.processMessage(self.ansbuf[theframe.ansno])
                self.deallocateMsgno(theframe.ansno)
                del self.ansbuf[theframe.ansno]

        ## If we've already got part of a message, append the payload
        ## to the existing message.
        else:
            if self.msgbuf.has_key(theframe.msgno):
                self.msgbuf[theframe.msgno].append(theframe.payload)

            else:
                self.msgbuf[theframe.msgno] = Message(dataframe=theframe)
                
            ## Check to see if this is the last Frame for the message.
            ## If it is, pass it to the profile for processing.
            if theframe.more == constants.MoreTypes['.']:
#                log.debug('Message complete. Processing...')
                if theframe.dataFrameType == constants.DataFrameTypes['MSG']:
#                    log.debug('Message received. Appending to receivedMsgnos')
                    self.receivedMsgnos.append(theframe.msgno)

                self.profile.processMessage(self.msgbuf[theframe.msgno])
                if theframe.dataFrameType == constants.DataFrameTypes['RPY']:
#                    log.debug('deallocating msgno after frame: %s' % theframe)
                    self.deallocateMsgno(theframe.msgno)

                del self.msgbuf[theframe.msgno]
        pass

    def allocateLocalSeqno(self, msgsize):
        """
        Identical to allocateRemoteSeqno() only used for the local
        side of a Channel connection.

        Wraps to zero at MAX_SEQNO.

        @type msgsize: integer
        @param msgsize: the size of the message this seqno is for

        @return: an integer sequence number for the message
        """
        new_seqno = self.localSeqno
        self.localSeqno += msgsize
        if self.localSeqno > constants.MAX_SEQNO:
            self.localSeqno -= constants.MAX_SEQNO
        return new_seqno

    def allocateRemoteSeqno(self, msgsize):
        """
        Allocate the next sequence number for the remote side of
        a channel connection.

        Wraps to zero at MAX_SEQNO.

        @type msgsize: integer
        @param msgsize: the size of the message this seqno is for

        @return: an integer sequence number for the message
        """
        
        new_seqno = self.remoteSeqno
        self.remoteSeqno += msgsize
        if self.remoteSeqno > constants.MAX_SEQNO:
            self.remoteSeqno -= constants.MAX_SEQNO
        return new_seqno

    # This method allocates a unique msgno for a message by
    # checking a list of allocated msgno's. Allocated msgno's
    # are removed from the list when they receive complete
    # replies.
    # This algorithm allocates the lowest available msgno
    def allocateMsgno(self):
        """
        allocateMsgno() allocates a unique msgno for a message
        by checking a list of allocated msgnos and picking the
        lowest number not already allocated. Allocated msgnos
        should be removed from the list when the complete reply
        to the message is received. See deallocateMsgno().
        
        @raise ChannelException: if no more msgnos can be allocated for
        this channel. This shouldn't ever happen, but if it does, messages
        are not being acknowledged by the remote peer. Alternately, the
        transport layer may be experiencing delays.

        """
        msgno = self.nextMsgno
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
                raise ChannelException('No available msgnos on channel', self.channelnum)
        # If we got here, then we've found the lowest
        # available msgno, so allocate it
        self.allocatedMsgnos.append(msgno)
        log.debug("Channel %d: Allocated msgno: %s" % (self.channelnum, msgno) )
        self.nextMsgno += 1
        if self.nextMsgno > constants.MAX_MSGNO:
            self.nextMsgno = constants.MINX_MSGNO
        return msgno


    # This method frees a msgno to be allocated again
    def deallocateMsgno(self, msgno):
        """
        deallocateMsgno() deallocates a previously allocated
        msgno. This should be called when a complete reply to a
        message is received and processed. This is most likely
        to be used from within a profile to signify that the
        message has been completely dealt with.

        @type msgno: integer
        @param msgno: the msgno of a received message reply.
        """

        if msgno in self.allocatedMsgnos:
            self.allocatedMsgnos.remove(msgno)
            log.debug("Channel %d: Deallocated msgno: %s" % (self.channelnum, msgno) )

    def allocateLocalAnsno(self, msgno):
        """
        Similar to allocateMsgno(), allocates a local ansno for a
        given msgno.

        Wraps to MIN_ANSNO at MAX_ANSNO.

        @param msgno: the msgno to associate with the ansno
        @type msgno: integer

        @return: integer, The allocated ansno
        """
        if msgno not in self.localAnsno.keys():
            self.localAnsno[msgno] = constants.MIN_ANSNO

        new_ansno = self.localAnsno[msgno]
        self.localAnsno[msgno] += 1
        if self.localAnsno[msgno] > constants.MAX_ANSNO:
            self.localAnsno[msgno] = constants.MIN_ANSNO
        return new_ansno

    def isMessageOutstanding(self, msgno=None):
        """
        isMessageOutstanding() checks to see if a particular
        message that was previously sent has been acknowledged.
        If no msgno is supplies, checks to see if there are any
        outstanding messages on this channel.

        @param msgno: msgno to check
        @type msgno: integer
        """
        if not msgno:
            if len(self.allocatedMsgnos) > 0:
                return 1
        elif msgno in self.allocatedMsgnos:
            return 1
        return 0

    # Send a Message of type MSG
    def sendMessage(self, data, cb=None, errback=None):
        """
        sendMessage() is used for sending a Message of type MSG

        @param data: the payload of the message

        @return: integer, the msgno of the message that was sent
        """
        msgno = self.allocateMsgno()
        msg = Message(None, constants.MessageType['MSG'], msgno, data)

        self.send(msg)
        return msgno

    # msgno here is the msgno to which this a reply
    def sendReply(self, msgno, data, cb=None, errback=None, *args ):
        """
        sendReply() is used for sending a frame of type RPY
        
        The msgno here is the msgno of the message to which this is a reply.

        @param msgno: The msgno for which this is the reply.
        @type msgno: integer
        
        @param data: The RPY payload
        
        """
        # First check we are responding to a MSG frame we received
        if msgno not in self.receivedMsgnos:
            raise ChannelMsgnoInvalid('Attempt to reply to msgno not received')

        msg = Message(None, constants.MessageType['RPY'], msgno, data, cb=cb, args=args)
        self.send(msg)

    def sendGreetingReply(self, data):
        """
        sendGreetingReply() is used to send the initial greeting message
        when a peer connects. It is identical to sendReply except that
        it doesn't check for a received Msgno as there isn't one.
        The msgno for this message is set to 0 as this must be
        the first frame sent.

        @param data: the greeting frame payload
        
        """
        msg = Message(None, constants.MessageType['RPY'], 0, data)
        self.send(msg)

    # seqno and more are not required for ERR frames
    # msgno is the MSG to which this error is a reply
    def sendError(self, msgno, data):
        """
        sendError() is used for sending a frame of type ERR

        @param msgno: the msgno this error is raised in reply to
        @param data: the payload of the ERR frame
        
        """
        msg = Message(None, constants.MessageType['ERR'], msgno, data)
        self.send(msg)

    # msgno here is the msgno to which this an answer
    def sendAnswer(self, msgno, data):
        """
        sendAnswer() is used for sending a frame of type ANS

        @param msgno: the msgno this ANS is in reply to
        @param data: the payload of the ANS frame
        """
        ansno = self.allocateLocalAnsno(msgno)
        msg = Message(None, constants.MessageType['ANS'], msgno, data, ansno)
        self.send(msg)

    def sendNul(self, msgno):
        """
        sendNul() is used for sending a frame of type NUL

        NUL frames are used to finish a series of ANS frames
        in response to a MSG. The msgno here is the msgno of the
        message to which the previous ANS frames were an answer to.

        @param msgno: the msgno all previous ANS frames have been in
        response to, and to which this is the final response frame.
        """
        msg = Message(None, constants.MessageType['NUL'], msgno)
        self.send(msg)
        # Once we've sent a NUL, we don't need to maintain a list of
        # ansno's for this msgno any more.
        del self.localAnsno[msgno]

    def close(self):
        """
        close() attempts to close the Channel.
        
        A Channel is not supposed to close unless all messages
        sent on the channel have been acknowledged and any
        messages inbound have been completely received.

        @raise ChannelMessagesOutstanding: if not all sent messages
                have been acknowledged.
        """
        if len(self.allocatedMsgnos) > 0:
            raise ChannelMessagesOutstanding("Channel %d: %s allocatedMsgno(s) unanswered: %s" % (self.channelnum, len(self.allocatedMsgnos), self.allocatedMsgnos) )

#        del self.inbound
        del self.profile

    def setPriority(self, priority):
        """
        Set the priority level of this channel to priority.
        priority must be between -10 and 10.
        """
        if not -10 <= priority <= 10:
            raise ChannelException("Priority value %d out of bounds" % priority)
        self.priority = priority

# Exception classes
class ChannelException(errors.BEEPException):
    def __init__(self, args=None):
        self.args = args

class ChannelMsgnoInvalid(ChannelException):
    def __init__(self, args=None):
        self.args = args

class ChannelNotStarted(ChannelException):
    def __init__(self, args=None):
        self.args = args

class ChannelMessagesOutstanding(ChannelException):
    def __init__(self, args=None):
        self.args = args
