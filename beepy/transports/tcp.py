# $Id: tcp.py,v 1.8 2004/11/22 04:20:09 jpwarren Exp $
# $Revision: 1.8 $
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

import logging
from beepy.core.debug import log

from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.error import ConnectionDone, ConnectionLost
from twisted.protocols.basic import LineReceiver

import re

import traceback

from beepy.core.session import Session, SessionException
from beepy.core.session import TUNING
from beepy.profiles import profile
from beepy.core import constants
from beepy.core import frame
from beepy.core import errors
from beepy.core import debug
from beepy.core.message import Message
from beepy.core.channel import ChannelException

class SEQBuffer:
    """
    A SEQ buffer is a data object that holds the current
    state of a channel buffer. It is used by SEQ frame
    processing to tune window sizes and queue pending
    data, if any.
    """
    STARTING_WINDOWSIZE = 4096
#    STARTING_WINDOWSIZE = 32
    MAX_WINDOWSIZE = 10 * STARTING_WINDOWSIZE
    MIN_WINDOWSIZE = 1
    
    ## This value determines the effect of a change in
    ## priority. Increasing the priority by one will add
    ## this amount to the windowsize, and a decrease will reduce it.
    PRIORITY_INCREMENT = STARTING_WINDOWSIZE / 2
    
    def __init__(self, channelnum):
        self.channelnum = channelnum
        
        ## The amount of space still available for this channel
        ## at the remote end.
        self.availspace = self.STARTING_WINDOWSIZE
        
        ## My window size for this channel
        self.windowsize = self.STARTING_WINDOWSIZE
        
        self.databuf = []
        self.cb = None
        
#        log.debug('created SEQBuffer for channel %d' % channelnum)
    
    def __str__(self):
        return 'SEQBuffer: %d %d %d (%s) %s' % (self.channelnum, self.windowsize, self.availspace, self.cb, self.databuf) 
        

# The BEEPy protocol as a twisted thingy
class BeepSession(LineReceiver, Session):
    
    def __init__(self, factory, listener, addr, profiles):
        
        Session.__init__(self, listener)
        
        self.addr = addr
        self.factory = factory
        self.profiles = factory.profiles
        self.framebuffer = ''
        self.newframe = None
        self.channelbuf = {}
        self.msgComplete = {}    # callback to call when a message
                                 # has been completely sent
        
        self.frameHeaderPattern = re.compile('.*\r\n')
        self.dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
        SEQFrameRE = '^' + frame.SEQFrame.dataFrameType
        SEQFrameRE += '.*'
        SEQFrameRE += frame.SEQFrame.TRAILER
        
        DataFrameRE = '.*'
        DataFrameRE += frame.DataFrame.TRAILER
        
        self.SEQFramePattern = re.compile(SEQFrameRE)
        self.DataFramePattern = re.compile(DataFrameRE)
        
        self.setRawMode()
    
    def sessionRequested(self):
        """ This is called before a session is established """
        pass
    
    def connectionMade(self):
        ## Do this when a connection is first made
        self.createChannelZero()
    
    def connectionLost(self, reason):
        #why = reason.trap(ConnectionDone)
        #if not why:
        #    log.error('connection lost: %s' % reason.getErrorMessage() )
        #    self.lostReason = reason
        self.factory.handleDisconnect(self)
        for c in self.channels.itervalues():
            if c.profile != None:
                c.profile.clientDisconnected()
    
    def close(self):
        #self.closeChannel(0)
        self.transport.loseConnection()
    
    ## What to do when a line is received
    def rawDataReceived(self, data):
        try:
            self.framebuffer += data
            
            while 1:
#                log.debug('fb: %s' % self.framebuffer)
                theframe = self.findFrame()
                if theframe:
                    ## We have received a frame, so process it
#                    log.debug('processFrame(): %s' % repr(theframe) )
                    
                    if isinstance(theframe, frame.SEQFrame):
#                        log.debug('processing SEQ frame')
                        self.processSEQFrame(theframe)
                    
                    elif isinstance(theframe, frame.DataFrame):
                        
# FIXME - sending a SEQ for every single received frame is NOT how things are
# supposed to be done.
                        
                        ## Process the inbound frame
                        self.validateFrame(theframe)
                        
                        ## Respond with a SEQ frame to the received frame
                        ## Don't send SEQ frames if we're doing a tuning
                        ## reset, as that can stuff the protocol setup.
                        if self.state != TUNING:
#                            log.debug('Not tuning. sending SEQ frame...')
                            self.sendSEQFrame(theframe.channelnum)
#                        else:
#                            log.debug('Currently tuning. No SEQ frames.')
                        
                        self.processFrame(theframe)

                    else:
                        log.error('Unknown frame type. Ignoring.')
# FIXME - this is a protocol error, session should be terminated.
                
                else:
#                    log.debug('no more frames')
                    break
        
        
        except frame.DataFrameException, e:
            log.error('%s: %s', e.__class__.__name__, e )
            log.info('Dropping connection...')
            self.transport.loseConnection()
        
        except ChannelException, e:
            log.error('%s: %s', e.__class__.__name__, e )
            log.info('Dropping connection...')
            self.transport.loseConnection()
        
        except SessionException, e:
            log.error('%s: %s', e.__class__.__name__, e )
            log.info('Dropping connection...')
            self.transport.loseConnection()
        
        except profile.TerminalProfileException, e:
            log.error('%s: %s', e.__class__.__name__, e )
            log.info('Dropping connection...')
            self.transport.loseConnection()
        
        except Exception, e:
            log.error('Unexpected exception: %s: %s', e.__class__.__name__, e )
            traceback.print_exc()
            log.info('Dropping connection...')
            self.transport.loseConnection()
    
    def findFrame(self):
        """
        Search for a frame in the databuffer. Return a frame
        object for the first frame found.
        """
        ## This needs to be looked at again at some point.
        ## It's not as efficient as it could be, in that it
        ## waits for either a SEQ frame or DataFrame trailer
        ## to appear before doing any more parsing. It really
        ## should drop your connection if you send a single
        ## line (ending in \r\n) that doesn't match any known
        ## header format.
        ## Coding that up is a little trickier than what is
        ## currently happening, so I'll tackle that another day
        ## when we're in full cleanup and refactor mode.
        ## This is Good Enough(tm) for now.
        
        ## Look for a SEQ frame
        if self.framebuffer.startswith(frame.SEQFrame.dataFrameType):
            end = self.framebuffer.find(frame.SEQFrame.TRAILER)
            if end >= 0:
                end += len(frame.SEQFrame.TRAILER)
                data = self.framebuffer[:end]
                self.framebuffer = self.framebuffer[end:]
                return frame.SEQFrame(databuffer=data)
        
        ## Look for a Data frame
        end = self.framebuffer.find(frame.DataFrame.TRAILER)
        if end >= 0:
            end += len(frame.DataFrame.TRAILER)
            data = self.framebuffer[:end]
            self.framebuffer = self.framebuffer[end:]
            return frame.DataFrame(databuffer=data)
    
    def sendMessage(self, msg, channelnum):
        """
        sendMessage is used to send a Message as one or more
        Frames over the transport.
        """
        ## Decide what to do with the message.
        ## If there's stuff pending, send that first,
        ## adding the new message to the end of the queue
        ## Otherwise, attempt to just send the message
        
        log.debug('Channel %d: queue msgno=%d msglen=%d' % (channelnum, msg.msgno, len(msg)))
        self.channelbuf[channelnum].databuf.append(msg)
        self._processChannelBuffer(channelnum)
    
    def _processChannelBuffer(self, channelnum):
        while True:
            # In the case of channel zero, sending a RPY for it can cause the
            # session to be shut down, and buffers to dissappear.

            if channelnum not in self.channelbuf:
                log.debug('Channel %d: no longer around' % (channelnum))
                return

            chbuf = self.channelbuf[channelnum]
    
            log.debug('Channel %d: process outgoing availspace=%d queued messages=%d' %
                (channelnum, chbuf.availspace, len(chbuf.databuf)))
    
            if len(chbuf.databuf) == 0:
                # No messages available, nothing to do right now.
                return
            
            if chbuf.availspace < constants.MIN_CHANNEL_WINDOW:
                # No window space available, nothing to do right now.
                return
            
            msg = chbuf.databuf[0]
            log.debug('Channel %d: msgno=%d remaining size=%d' % (channelnum, msg.msgno, len(msg)))
            
            if chbuf.availspace < len(msg):
                # Split first frame out from the message, and requeue remainder for later.
                #log.debug('Channel %d: fragment msgno=%d frame msgno=%d sendsz=%d nextsz=%d' %
                #    (channelnum, msg.msgno, msg.msgno, len(frame), len(msg)))
                self.sendMsgFragment(channelnum, msg, chbuf.availspace)
            else:
                self.sendMsgComplete(channelnum, msg)
                chbuf.databuf.pop(0)
    
    def sendMsgFragment(self, channelnum, msg, amount):
        """
        Send a message fragment by setting the continuation indicator
        for the frame.
        """
        #log.debug('sending message fragment: %s' % msg)
        payload = msg.content_as_string(amount)
        size = len(payload)
        seqno = self.channels[channelnum].allocateLocalSeqno(size)
        theframe = frame.DataFrame(channelnum, msg.msgno, seqno, size, msg.msgType, constants.MoreTypes['*'])
        if msg.isANS():
            theframe.ansno = msg.ansno
        theframe.setPayload(payload)
        msg.start_index += size
        self.sendFrame(theframe)
        self.channelbuf[channelnum].availspace -= size
    
    def sendMsgComplete(self, channelnum, msg):
        """
        Send the final frame in a sequence of fragments.
        A sequence of fragments may only be one frame long,
        with that single frame containing the whole message.
        """
#        log.debug('Sending without fragmenting...')
        ## Plenty of space, send the whole message
        payload = msg.content_as_string()
        size = len(payload)
        seqno = self.channels[channelnum].allocateLocalSeqno(size)
        theframe = frame.DataFrame(channelnum, msg.msgno, seqno, size, msg.msgType, ansno = msg.ansno)
        if msg.isANS():
            theframe.ansno = msg.ansno
        theframe.setPayload(payload)
        self.sendFrame(theframe)
        self.channelbuf[channelnum].availspace -= size
        ## call the callback for complete message send
        if msg.cb is not None:
#            log.debug("Message args: %s" % msg.args)
            msg.cb(msg.args[0])
    
    def sendFrame(self, theframe):
        """
        sendFrame is used to push frames over the transport.
        
        With the addition of SEQ frames, this becomes a little
        more complex. We need to check that the amount of data
        we're about to send isn't larger than the allocated
        window size. If it is, then we fragment the data and
        only send bytes up to the window size. We then have to
        wait for a SEQ frame from the remote peer saying that
        it has room for more data before sending the rest.
        
        The sending of pending data happens asynchronously
        via the processQueuedData() method.
        """
        try:
            data = str(theframe)
            #import nice
            #logging.debug('Sending frame: \n' + nice.hex_dump(data, 24, '    '))
            result = self.transport.write(data)
        
        except Exception, e:
            log.debug('Exception sending frame: %s: %s' % (e.__class__, e))
            traceback.print_exc()
    
    def doSEQFrame(self):
        """
        """
        # If this is a SEQ frame, create it and process it
        match = re.search(self.SEQFramePattern, self.framebuffer)
        if match:
            seqframe = frame.SEQFrame(databuffer=self.framebuffer[:match.end()])
            self.framebuffer = self.framebuffer[match.end():]
            self.processSEQFrame(seqframe)
    
    def processSEQFrame(self, theframe):
        """
        Perform window size management for inbound SEQ frames.
        """
        chnum = theframe.channelnum
#        log.debug('Received SEQ frame: %s' % theframe)
        
        ## Validate the sequence number
        
        ## Reset the window size
        if self.channelbuf.has_key(chnum):
            seqno = self.channels[chnum].localSeqno
            availspace = theframe.ackno + theframe.window - seqno
            log.debug('Channel %d SEQ ackno %d window %d seqno %d availspace now %d' %
                    (chnum, theframe.ackno, theframe.window, seqno, availspace)
                )
            self.channelbuf[chnum].availspace = availspace
        ## send pending data
        try:
            if self.channelbuf.has_key(chnum):
                self._processChannelBuffer(chnum)
        
        except IndexError:
#            log.debug('No pending data.')
            pass
        
        except Exception, e:
            log.debug('exception %s' % e)
            traceback.print_exc()
   
    def sendSEQFrame(self, channelnum):
        """
        This is the simplest tuning. We simply reset the
        window to max, allowing the remote peer to send
        more data on this channel.
        """
        ## This gets called every time we receive an inbound
        ## frame. This is the defined behaviour within RFC 2030
        ## somewhere.. I have to go look it up.
        ##
        ## We want to modify this to be a bit more intelligent
        ## soon so that we can alter the way in which channels
        ## behave. We want to be able to set relative channel
        ## priorities and have this method check the current channel
        ## priority before changing the window size.
        ##
        ## We need to develop a tuning algorithm so that we can have
        ## channels share the available bandwidth according to their
        ## priority. I'll have to look up the algorithm used for unix
        ## process scheduling so that I can hopefully use the same
        ## concept. No sense reinventing the wheel, and that one seems
        ## to work well.
        ##
        ## The idea is that there is a total amount of bandwidth,
        ## represented by the total of all the channel's max window
        ## size. If all channels are of equal priority, they should share
        ## this bandwidth equally. If a channel is of lesser priority,
        ## it should get a proportionally lower amount of bandwidth.
        
        try:
            ## Make sure the channel is still open
            if self.channels.has_key(channelnum):
                
                ## FIXME? The sequence number of the channel isn't
                ## changed because allocateLocalSeqno() will only
                ## increase the seqno if the payload length is
                ## non-zero. SEQ frames have no length, so the seqno
                ## stays the same. This is a bit weird, but that seems
                ## to be the way it should be.
                ackno = self.channels[channelnum].remoteSeqno
                
                seqf = frame.SEQFrame(channelnum, ackno, self.channelbuf[channelnum].windowsize)
#                log.debug('Sending SEQ frame: %s' % seqf)
                self.sendFrame(seqf)
        
        except KeyError:
            ## A KeyError will occur if the channel was deleted
            ## as part of the received message processing,
            ## so we don't need to send a SEQ frame for the channel
            ## any more. Only really occurs for channel 0
            pass
    
    def setWindowSize(self, channelnum, windowsize):
        """
        Set the window size for a specific channel.

        Silently ignored if new window size is smaller than old.

        Currently only allows the windowsize to be increased - if it was decreased
        we'd have to be careful to not retract windowsize we've already advertised
        as being available in a SEQ message. Not time or need for that now.
        """
        if channelnum not in self.channelbuf:
            return

        if windowsize <= self.channelbuf[channelnum].windowsize:
            return

        self.channelbuf[channelnum].windowsize = windowsize

        # Tell the peer that our window size has increased.
        self.sendSEQFrame(channelnum)


    def processQueuedData(self):
        """
        This method examines the local data queues to see
        if there is pending data that didn't fit within a
        window for a given channel. If data is available
        and there is available space at the remote peer
        then more data is sent, up to the amount of available
        space. If no space is available yet (because we haven't
        received another SEQ frame yet) then we don't send the
        data for that channel.
        """
        pass
    
    def createTransportChannel(self, channelnum):
        """
        Performs transport specific channel creation
        """
        self.channelbuf[channelnum] = SEQBuffer(channelnum)
#        log.debug('created transport for channel %d' % channelnum)
    
    def deleteTransportChannel(self, channelnum):
        """
        Performs transport specific channel deletion
        """
#        log.debug('Trying to delete channel buffer for %s: %s' % (channelnum, self.channelbuf))
        ## Ensure we've sent all pending data
        self.flushDatabuf(channelnum)
        
        del self.channelbuf[channelnum]
#        log.debug('deleted SEQ Buffer for channel %s' % channelnum)
    
    def flushDatabuf(self, channelnum):
        """
        Flush any data left in the channel buffer before closing.
        FIXME: This is really dodgy, and must be fixed in the refactor.
        """
        try:
            while(1):
                msg = self.channelbuf[channelnum].databuf.pop(0)
                # FIXME channelnum was missing in original source, is this method dead code?
                self.sendMessage(msg, channelnum)
        
        except IndexError:
            pass

class ProtocolError(errors.BEEPException):
    def __init__(self, args=None):
        self.args = args


class BeepFactory:
    protocol = BeepSession
    
    def __init__(self):
        self.profiles = {}
    
    def addProfile(self, uri, profileFactory):
        self.profiles[uri] = profileFactory
    
    def buildProtocol(self, addr):
        return self.protocol(self, self.listener, addr, self.profiles)
        
    def handleDisconnect(self, protocol):
        pass


class BeepListenerFactory(BeepFactory, ServerFactory):
    listener = True


class BeepInitiatorFactory(BeepFactory, ClientFactory):
    """ This class is the base class for all application
    clients. You would subclass from this class to
    build your application
    """
    listener = False
    
    reason = None
    lostReason = None
    
    def clientConnectionFailed(self, connector, reason):
        """
        Override this to change client functionality
        """
        self.reason = reason
        log.error('connection failed: %s' % reason.getErrorMessage() )
    
    def clientConnectionLost(self, connector, reason):
        """
        Override this to change client functionality
        """
        why = reason.trap(ConnectionDone)
        if not why:
            log.error('connection lost: %s' % reason.getErrorMessage() )
            self.lostReason = reason
            self.reason = None
        
        log.debug('Client finished. Stopping reactor.')


class ReconnectingBeepClientFactory(BeepFactory, ReconnectingClientFactory):
    """
    An alternative BeepClientFactory that will attempt to reconnect
    to a server automatically.
    """

##
## SASL related code
##

#from beepy.core.saslsession import SASLListener, SASLInitiator
#
#class SASLServerProtocol(BeepProtocol, SASLListener):
#    """ SASL Server Protocol
#    """
#
#class SASLClientProtocol(BeepProtocol, SASLInitiator):
#    """ SASL Client Protocol
#    """
#
#class SASLServerFactory(BeepServerFactory):
#    protocol = SASLServerProtocol
#
#class SASLClientFactory(BeepClientFactory):
#    protocol = SASLClientProtocol

# vim:expandtab:
