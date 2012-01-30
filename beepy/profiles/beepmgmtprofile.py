import traceback
import logging

import mgmtparser 
import mgmtcreator
import message
import profile
import beepy.core.session
#from beepy.core.debug import log
import logging
log = logging.getLogger('')

even = lambda x: (x % 2) != 1
odd = lambda x: (x % 2) == 1

class BEEPManagementProfile(profile.Profile):
    """
    The BEEPManagementProfile is used on Channel 0 for all Sessions
    to control the management of the Session and all channels on it.
    """
    
    content_type = "application/beep+xml"
    
    def __init__(self):
        profile.Profile.__init__(self)
        self.mgmtCreator = mgmtcreator.Creator()
        self.mgmtParser = mgmtparser.Parser()
        
        self.channelsStarting = {}
        self.channelsOpen = {0: self}
        self.channelsClosing = {}
        
    def channelStarted(self, channel, uri, cdata):
        profile.Profile.channelStarted(self, channel, uri, cdata)
        self.session = channel.session
        try:
            self.session.sessionRequested()
        except Exception, e:
            self.sendError("".join(e.args))
            self.session.close()
            return
        self.sendGreeting()
    
    def _parsePacket(self, msg):
        if msg.get_content_type() != self.content_type:
            raise profile.TerminalProfileException("Invalid content type for " \
                "message: %s != %s" % (msg.get_content_type(), self.content_type))
        parsed = self.mgmtParser.parse(msg.get_payload())
        return parsed
    
    def _sendError(self, msgno, code, descr):
        log.warning(descr)
        errmsg = self.mgmtCreator.createErrorMessage(str(code), descr)
        self.channel.sendError(msgno, errmsg, [('Content-Type', self.content_type)])
    
    def processMSG(self, msg):
        ''' Process incoming MSG packets. '''
        
        mgmtMsg = self._parsePacket(msg)
        if mgmtMsg.isStart():
            self.handleStart(msg, mgmtMsg)
        elif mgmtMsg.isClose():
            self.handleClose(msg, mgmtMsg)
        else:
            log.error("Unknown MSG type received" )
            raise profile.TerminalProfileException("Unknown MSG type received")
    
    def processRPY(self, msg):
        ''' Process incoming RPY packets. '''
        
        mgmtMsg = self._parsePacket(msg)
        if mgmtMsg.isGreeting():
            self.handleGreeting(msg, mgmtMsg)
        elif mgmtMsg.isProfile():
            self.handleProfile(msg, mgmtMsg)
        elif mgmtMsg.isOK():
            self.handleOK(msg, mgmtMsg)
        else:
            log.error("Unknown MSG type received" )
            raise profile.TerminalProfileException("Unknown MSG type received")
    
    def processERR(self, msg):
        ''' Process incoming ERR packets. '''
        
        mgmtMsg = self._parsePacket(msg)
        code = mgmtMsg.getErrorCode()
        desc = mgmtMsg.getErrorDescription()
        
        if msg.msgno in self.channelsStarting:
            # Error in response to a channel that is being opened
            chnum = self.channelsStarting[msg.msgno]
            del self.channelsStarting[msg.msgno]
            self.session.channelStartingError(chnum, code, desc)
        elif msg.msgno in self.channelsClosing:
            # Error in response to a channel that is being closed
            channel = self.channelsClosing[msg.msgno]
            del self.channelsClosing[msg.msgno]
            channel.channelClosingError(chnum, code, desc)
        else:
            # What is this error in response to?
            log.error('Received <error> message for a channel that was not ' \
                'being opened or closed')
            raise profile.TerminalProfileException('Received <error> message ' \
                'for a channel that was not being opened or closed')
    
    def handleStart(self, msg, mgmtMsg):
        ''' Called when a <start> message is received. '''
        chnum = mgmtMsg.getStartChannelNum()
        if chnum in self.channelsOpen:
            self._sendError(msg.msgno, 553, "Channel %d already exists" % chnum)
            return
        
        if self.session.listener and even(chnum):
            self._sendError(msg.msgno, 553, "Requested channel number (%d) is " \
                " even, but should be odd" % reqChannel)
            return
        elif not self.session.listener and odd(chnum):
            self._sendError(msg.msgno, 553, "Requested channel number (%d) is " \
                "odd, but should be even" % reqChannel)
            return
        else:
            log.debug("Creating new channel, number: %d" % chnum)
            
            profiles = mgmtMsg.getProfileList()
            try:
                uri, profile_obj, cdata, encoding = \
                    self.session.channelRequested(chnum, profiles)
                self.session.createChannel(chnum, profile_obj)
            except beepy.core.session.NoSuitableProfiles, e:
                self._sendError(msg.msgno, 550, "No suitable profiles")
                return
            except Exception, e:
                # FIXME: Maybe the error code should be set by thrower
                log.error(traceback.format_exc())
                self._sendError(msg.msgno, 554, "Internal server exception")
                return
            
            # Inform client of success, and which profile was used.
            data = self.mgmtCreator.createStartReplyMessage(uri, cdata, encoding)
            self.channelsOpen[chnum] = profile_obj
            self.channel.sendReply(msg.msgno, data, [('Content-Type', self.content_type)])
            
            # Notify the profile object that the channel is running
            profile_obj.channelStarted(self.session.channels[chnum], uri, \
                profiles[uri][0])
    
    def handleClose(self, msg, mgmtMsg):
        ''' Called when a <close> message is received. '''
        chnum = mgmtMsg.getCloseChannelNum()
        
        if chnum in self.channelsClosing:
            self._sendError(msg.msgno, 553, "Close already in progress for " \
                "channel %d" % chnum)
            return
        if chnum not in self.channelsOpen and chnum != 0:
            self._sendError(msg.msgno, 553, "Channel %d is not open" % chnum)
            return
        if chnum == 0 and len(self.channelsOpen) > 1:
            self._sendError(msg.msgno, 553, "Cannot close channel 0 while " \
                "other channels are open")
            return

        # FIXME - this is an API bug... the profile should be given the
        # opportunity to refuse to be closed.
        log.debug("Closing channel %d (by request of peer)" % chnum)
        data = self.mgmtCreator.createOKMessage()
        msgno = self.channel.sendReply(msg.msgno, data,
            [('Content-Type', self.content_type)])
        profile = self.channelsOpen[chnum]
        del self.channelsOpen[chnum]
        self.session.deleteChannel(chnum)
        self.session._channelClosedSuccess(chnum)
        profile.channelClosed()
    
    def handleGreeting(self, msg, mgmtMsg):
        ''' Called when a <greeting> message is received. '''
        try:
            self.session._handleGreeting()
        except beepy.core.session.TerminateException, e:
            raise profile.TerminalProfileException(e)
    
    def handleProfile(self, msg, mgmtMsg):
        ''' Called when a <profile> message is received. '''
        if msg.msgno not in self.channelsStarting:
            log.error('Received <profile> message for a channel that was not ' \
                'being opened')
            raise profile.TerminalProfileException('Received <profile> message ' \
                'for a channel that was not being opened')
        
        chnum, profile_obj, profiles = self.channelsStarting[msg.msgno]
        self.channelsOpen[chnum] = profile_obj
        del self.channelsStarting[chnum]
        
        # Notify the profile object that the channel is running
        uri = mgmtMsg.getProfileURI()
        cdata = mgmtMsg.getProfileCdata()
        channel = self.session.createChannel(chnum, profile_obj)
        profile_obj.channelStarted(channel, uri, cdata)
    
    def handleOK(self, msg, mgmtMsg):
        ''' Called when an <ok> message is received. '''
        if msg.msgno not in self.channelsClosing:
            log.error('Received <ok> message for a channel that was not ' \
                'being closed')
            raise profile.TerminalProfileException('Received <ok> message ' \
                'for a channel that was not being closed')
        profile = self.channelsClosing[msg.msgno]
        del self.channelsClosing[msg.msgno]
        self.session.deleteChannel(profile.channel.channelnum)
        self.session._channelClosedSuccess(profile.channel.channelnum)
        profile.channelClosed()
    
    def startChannel(self, chnum, profiles, handler_obj, serverName=None):
        ''' Initiates a channel by sending the <start> message to the remote
            peer.
        '''
        logging.debug('Requesting channel %d start' % chnum)
        data = self.mgmtCreator.createStartMessage(chnum, profiles, serverName)
        msgno = self.channel.sendMessage(data,
            [('Content-Type', self.content_type)])
        
        # Take note that I'm attempting to start this channel
        self.channelsStarting[msgno] = (chnum, handler_obj, profiles)
    
    def closeChannel(self, chnum, code=200):
        ''' Attempts to close a channel by sending the <close> message to the
            remote peer.
        '''
        logging.debug('Requesting channel %d close' % chnum)
        data = self.mgmtCreator.createCloseMessage(chnum, str(code))
        msgno = self.channel.sendMessage(data,
            [('Content-Type', self.content_type)])
        
        # Take note that I'm attempting to close this channel
        self.channelsClosing[msgno] = self.channelsOpen[chnum]
        del self.channelsOpen[chnum]
    
    def sendGreeting(self):
        ''' Completed the session start by sending the <start> message to the
            remote peer.
        '''
        uris = self.session.profiles.keys()
        data = self.mgmtCreator.createGreetingMessage(uris)
        self.channel.sendGreetingReply(data,
            [('Content-Type', self.content_type)])

    def sendError(self, message):
        data = self.mgmtCreator.createErrorMessage('421', message)
        self.channel.sendError(0, data,
            [('Content-Type', self.content_type)])

class BEEPManagementProfileException(profile.ProfileException):
    def __init__(self, args=None):
        self.args = args

