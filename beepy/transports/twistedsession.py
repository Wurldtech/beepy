
# First go at beepy as a twisted app

from twisted.internet import protocol, reactor
from twisted.internet.error import *
from twisted.protocols import basic

import re
import logging

from beepy.core.session import Session
from beepy.profiles import profile
from beepy.core import constants
from beepy.core import frame
from beepy.core import errors
from beepy.core import debug

from beepy.core import util

log = logging.getLogger('BeepProtocol')
log.setLevel(logging.DEBUG)

# The BEEPy protocol as a twisted thingy
class BeepProtocol(Session, basic.LineReceiver):

    def __init__(self):

        Session.__init__(self)

        self.framebuffer = ''
        self.newframe = None
        self.windowsize = {}

        self.frameHeaderPattern = re.compile('.*\r\n')
        self.dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
        SEQFrameRE = frame.SEQFrame.dataFrameType
        SEQFrameRE += '.*'
        SEQFrameRE += frame.SEQFrame.TRAILER
        self.SEQFramePattern = re.compile(SEQFrameRE)

        self.setRawMode()

    def connectionMade(self):
        ## Do this when a connection is first made

        self.profileDict = self.factory.getProfileDict()
        self.createChannelZero()

    def connectionLost(self, reason):
        log.info( reason.getErrorMessage() )

    def close(self):
        self.transport.loseConnection()

    ## What to do when a line is received
    def rawDataReceived(self, data):
        try:
            self.framebuffer += data
            if len(self.framebuffer) > (constants.MAX_FRAME_SIZE + constants.MAX_INBUF):
                log.error('Frame too large')
                self.framebuffer = ''
                pass

            while 1:
                self.startFrame()
                theframe = self.finishFrame()
                if theframe:
                    self.processFrame(theframe)
                    ## Manually zero out the now processed frame
                    self.newframe = None
                else:
                    break
            
        except Exception, e:
            log.error(e)
            log.info('Dropping connection...')
            self.transport.loseConnection()


    def startFrame(self):
        """ This method attempts to start a new frame, if
            one hasn't already been received.
        """
        ##
        ## Firstly, we look for the frame header, provided
        ## we're not in the middle of a frame
        ##
        if not self.newframe:
            match = re.search(self.frameHeaderPattern, self.framebuffer)
            if match:
                headerdata = self.framebuffer[:match.end()]
                self.framebuffer = self.framebuffer[match.end():]

                # If this is a SEQ frame, create it and process it
                if re.search(self.SEQFramePattern, headerdata):
                    seqframe = frame.SEQFrame(databuffer=headerdata)
                    self.processSEQFrame(seqframe)
                else:
                    # start a new dataframe
                    self.newframe = frame.DataFrame(databuffer=headerdata)
                    pass
                pass
            pass
        pass
                    
    def finishFrame(self):
        """ We attempt to finish a previously started frame
        """
        ## We're already somewhere in the middle of a frame
        ## after getting a valid header, so we add payload
        ## data to the frame until we hit the trailer

        if self.newframe:
            match = re.search(self.dataFrameTrailer, self.framebuffer)
            if match:
                framedata = self.framebuffer[:match.start()]
                self.framebuffer = self.framebuffer[match.end():]

                ## We check to make sure the payload isn't too long
                if len(self.newframe.payload) + len(framedata) > self.newframe.size:
                    log.debug("size: %s, expected: %s" % ( len(self.newframe.payload) + len(framedata), self.newframe.size ) )
                    log.debug("payload: %s, buffer: %s" % ( self.newframe.payload, framedata ) )
                    raise ProtocolError('Payload larger than expected size')
                else:
                    self.newframe.payload += framedata
                    return self.newframe

            else:
                ## The frame isn't complete yet, so we just add
                ## data to the payload. Hopefully the trailer will
                ## be in the next chunk off the transport layer
                if len(self.newframe.payload) + len(self.framebuffer) > self.newframe.size:
                    log.debug("size: %s, expected: %s" % ( len(self.newframe.payload) + len(self.framebuffer), self.newframe.size ) )
                    log.debug("payload: %s, buffer: %s" % ( self.newframe.payload, self.framebuffer ) ) 
                    raise ProtocolError("Payload larger than expected size")

                else:
                    self.newframe.payload += self.framebuffer
                    self.framebuffer = ''

    def processFrame(self, theframe):
        """ Allocate a given frame to the channel it belongs to
        and call the channel's processing method
        """
        if self.channels.has_key(theframe.channelnum):
            self.channels[theframe.channelnum].processFrame(theframe)
        else:
            log.info('Attempt to send to non-existant channel: %d' % theframe.channelnum)
            raise ProtocolError('Invalid Channel Number')

    def sendFrame(self, theframe):
        data = str(theframe)
        self.transport.write(data)

class ProtocolError(errors.BEEPException):
    def __init__(self, args=None):
        self.args = args

class BeepServerProtocol(BeepProtocol):
    """ This class is mostly identical, but servers only use
        even numbered channels
    """
    def __init__(self):
        BeepProtocol.__init__(self)
        self.nextChannelNum = 2

class BeepClientProtocol(BeepProtocol):
    """ This class is mostly identical to the base class, but
    clients only use odd numbered channels
    """
    def __init__(self):
        BeepProtocol.__init__(self)
        self.nextChannelNum = 1

    def greetingReceived(self):
        log.debug('Client has received a greeting from the server')
        raise NotImplementedError('Override greetingReceived in your client protocol')

class BeepServerFactory(protocol.ServerFactory):
    protocol = BeepServerProtocol

    def __init__(self):
        """ A comment
        """
        self.profileDict = profile.ProfileDict()
        pass
        
    def getProfileDict(self):
        return self.profileDict

    def addProfile(self, profileModule):
        self.profileDict.addProfile(profileModule)

class BeepClientFactory(protocol.ClientFactory):
    """ This class is the base class for all application
    clients. You would subclass from this class to
    build your application
    """
    protocol = BeepClientProtocol
    
    def __init__(self):
        """ startAction is a method defined by the application
        for what to do once a connection is made to the remote
        server.
        """
        self.profileDict = profile.ProfileDict()
        pass

    def getProfileDict(self):
        return self.profileDict

    def addProfile(self, profileModule):
        self.profileDict.addProfile(profileModule)

    def clientConnectionFailed(self, connector, reason):
        log.info('connection failed: %s' % reason.getErrorMessage() )
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        log.info('connection lost: %s' % reason.getErrorMessage() )
        reactor.stop()
