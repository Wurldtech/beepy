# $Id: frame.py,v 1.10 2004/08/22 04:15:57 jpwarren Exp $
# $Revision: 1.10 $
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
BEEPy Framing classes and related code.

RFC3080 only really defines one kind of frame, but states that
transport mappings may define other frames. I don't really grok
this yet, so I've just created a template object for Frames in
general and subclassed it to a DataFrame. This way, if other
frames are used for some reason, they can also subclass from
Frame. All the guts are in DataFrame, but that's what the RFC says.

@version: $Revision: 1.10 $
@author: Justin Warren

"""
import string
import traceback

#import logging
from debug import log
#log = logging.getLogger('beepy')

import errors
import constants

class Frame:
    """
    A Frame is a basic abstraction defined by RFC3080. All BEEP
    frames subclass from this class
    """
    def __init__(self, frameType):
        """
        @type frameType: string
        @param frameType: a supported frametype as defined in
            constants.FrameTypes
        """
        if( frameType not in constants.FrameTypes ):    # bad FrameType
            raise FrameException("Invalid Type")
        else:
            self.frameType = frameType

class FrameException(errors.BEEPException):
    """
    The base exception used for all framing exceptions
    """
    def __init__(self, args=None):
        self.args = args

class DataFrame( Frame ):
    """
    A DataFrame is the basic unit of data used by BEEP to transport
    information around.
    """

    # Class constants
    frameType = 'data'
    TRAILER = 'END\r\n'        # Trailer

    channelnum = -1
    msgno = -1
    seqno = -1L
    size = -1L
    ansno = -1

    def __init__(self, channelnum=None, msgno=None, seqno=None, size=None, dataFrameType='MSG', more=constants.MoreTypes['.'], ansno=None, databuffer=None):
        """
        When a frame is created, various checks on the data are performed
        to ensure that it is a correctly formed frame. This is most useful
        for validating data received from the transport layer.

        @type channelnum: integer
        @param channelnum: The channel number this frame is/was sent on

        @type msgno: integer
        @param msgno: The message number of the frame

        @type more: character, . or *
        @param more: The frame continuation indicator

        @type seqno: integer
        @param seqno: The frame sequence number

        @type size: long
        @param size: The length of the frame payload in bytes

        @type dataFrameType: string
        @param dataFrameType: a string type from constants.dataFrameTypes

        @type ansno: integer
        @param ansno: For a NUL frame, the ansno to which this is a reply

        @type databuffer: bytestring
        @param databuffer: A raw frame as a bytestring
        """
        Frame.__init__(self, self.frameType)

        # This lets us pass in a string type databuffer
        # to create a frame object
        if databuffer:
            self._bufferToFrame(databuffer)
        else:
            self._checkValues(channelnum, msgno, more, seqno, size, dataFrameType, ansno)
            self.dataFrameType = dataFrameType
            self.channelnum = channelnum
            self.msgno = msgno
            self.more = more
            self.seqno = seqno
            self.size = size
            self.payload = ''
            self.complete = 0
            self.ansno = ansno

    def __str__(self):
        """
        Returns a frame as a formatted bytestring ready for passing
        to the transport layer. Pretty printed so it's human readable.
        """

        framestring = "%s %i %i %s %i %i" % (constants.DataFrameTypes[self.dataFrameType], self.channelnum, self.msgno, self.more, self.seqno, self.size)

        if( self.ansno is not None ):
            framestring += " %i" % self.ansno
        framestring += '\r\n'
        framestring += "%s" % self.payload
        framestring += self.TRAILER
        return framestring

    def isMSG(self):
        """
        Check to see if this is a MSG frame

        @return: 1 if true
        """
        if self.dataFrameType == 'MSG':
            return 1

    def isRPY(self):
        """
        Check to see if this is a RPY frame

        @return: 1 if true
        """
        if self.dataFrameType == 'RPY':
            return 1

    def isANS(self):
        """
        Check to see if this is an ANS frame

        @return: 1 if true
        """
        if self.dataFrameType == 'ANS':
            return 1

    def isERR(self):
        """
        Check to see if this is an ERR frame

        @return: 1 if true
        """
        if self.dataFrameType == 'ERR':
            return 1

    def isNUL(self):
        """
        Check to see if this is a NUL frame

        @return: 1 if true
        """
        if self.dataFrameType == 'NUL':
            return 1

    def _bufferToFrame(self, data):
        """
        Convert a bytestring databuffer to a DataFrame object.
        Mostly used to decode incoming datastreams from the transport
        layer into DataFrame objects.

        @type data: string
        @param data: a bytestring containing a single frame as a bytestring
        """
        # Split buffer into header and payload
        header, rest = data.split('\r\n', 1)
        payload, trailer = rest.split(self.TRAILER, 1)

        # Split the header into bits
        headerbits = header.split()

        # Check for valid header format
        if len(headerbits) != 6 and len(headerbits) != 7:
            raise DataFrameException("Header Format Invalid")
        self.dataFrameType = headerbits[0]

        try:
            self.channelnum = string.atol(headerbits[1])
            self.msgno = string.atol(headerbits[2])
            self.more = headerbits[3]
            self.seqno = string.atol(headerbits[4])
            self.size = string.atol(headerbits[5])
            if len(headerbits) == 7:
                self.ansno = string.atol(headerbits[6])
            else:
                self.ansno = None
            self.setPayload(payload)

        except DataFrameException:
            raise

        except ValueError, e:
            raise DataFrameException("Non-numeric value in frame header")

        except Exception, e:
            traceback.print_exc()
            raise DataFrameException("Unhandled exception in _bufferToFrame: %s: %s" % (e.__class__, e) )
        

        self._checkValues(self.channelnum, self.msgno, self.more, self.seqno, self.size, self.dataFrameType, self.ansno)

    def _checkValues(self, channelnum, msgno, more, seqno, size, dataFrameType, ansno=None):
        """
        Performs sanity checking on values of DataFrames at create time.

        """

        if dataFrameType not in constants.DataFrameTypes.keys():
            raise DataFrameException("Invalid DataFrame Type")

        if not constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL:
            raise DataFrameException("Channel number (%s) out of bounds" % channelnum)

        if not constants.MIN_MSGNO <= msgno <= constants.MAX_MSGNO:
            raise DataFrameException("MSGNO (%s) out of bounds" % msgno )

        if not more in constants.MoreTypes.keys():
            raise DataFrameException("Invalid More Type")

        if not constants.MIN_SEQNO <= seqno <= constants.MAX_SEQNO:
            raise DataFrameException("SEQNO (%s) out of bounds" % seqno)

        if dataFrameType == constants.DataFrameTypes['ANS'] and ansno is None:
            raise DataFrameException("No ansno for ANS frame")

        if ansno is not None:
            if not dataFrameType == constants.DataFrameTypes['ANS']:
                raise DataFrameException("ANSNO in non ANS frame")

            elif not constants.MIN_ANSNO <= ansno <= constants.MAX_ANSNO:
                raise DataFrameException("ANSNO (%s) out of bounds" % ansno)

        if dataFrameType == constants.DataFrameTypes['NUL']:
            if more == constants.MoreTypes['*']:
                raise DataFrameException('NUL frame cannot be intermediate')
            elif size != 0:
                raise DataFrameException('NUL frame of non-zero size')

        if not constants.MIN_SIZE <= size <= constants.MAX_SIZE:
                raise DataFrameException("Frame size (%s) out of bounds" % size)

    def setPayload(self, payload):
        """
        Assigns a payload to a DataFrame. This is usually called after
        creating an empty frame with the header information set to
        populate the frame.

        @type payload: string
        @param payload: a bytestring that is a frame payload
        """
        mysize = len(payload)
        if mysize != self.size:
            raise DataFrameException('Size mismatch %i != %i' % (mysize, self.size))
        self.payload = payload

    def __repr__(self):
        return "<%s instance at %s>" % (self.__class__, hex(id(self)))

class DataFrameException(FrameException):
    """
    An Exception class used for DataFrame specific exceptions. A
    DataFrameException is usually raised if bounds checking fails.
    """
    def __init__(self, args=None):
        self.args = args

class SEQFrame(Frame):
    """
    SEQFrames are objects that represent the SEQ frames used in RFC3081
    for the TCP mapping of BEEP. SEQ frames are used to tune the window
    size for sending and receiving over a particular channel within an
    individual TCP connection. This is one of the most useful and cool
    parts of BEEP.
    """
    # class constants
    frameType = 'seq'
    TRAILER = str('\r\n')        # Trailer
    dataFrameType = 'SEQ'

    channelnum = -1
    ackno = -1L
    window = -1

    def __init__(self, channelnum=None, ackno=None, window=None, databuffer=None):
        Frame.__init__(self, self.frameType)

        # This lets us pass in a string type databuffer
        # to create a frame object
        if databuffer:
            self._bufferToFrame(databuffer)
        else:
            self._checkValues(channelnum, ackno, window)
            self.channelnum = channelnum
            self.ackno = ackno
            self.window = window

    def _bufferToFrame(self, data):
        """
        Converts a bytestring data buffer to a frame object.
        
        @param data: a bytestring containing a raw frame
        @type data: string

        @return: SEQFrame

        @raise SEQFrameException: if format of frame is invalid
        """
        # Now split the frame into bits
        headerbits = string.split(data)

        # Check for valid format
        if len(headerbits) != 4:
            raise SEQFrameException('Format Invalid')

        try:
            self.channelnum = string.atoi(headerbits[1])
            self.ackno = string.atoi(headerbits[2])
            self.window = string.atol(headerbits[3])

        except Exception, e:
            raise SEQFrameException('unknown error in _bufferToFrame')

        self._checkValues(self.channelnum, self.ackno, self.window)

    # Sanity checking
    def _checkValues(self, channelnum, ackno, window):

        if not constants.MIN_CHANNEL <= channelnum <= constants.MAX_CHANNEL:
            raise SEQFrameException('Channel number (%s) out of bounds' % channelnum)

        if not constants.MIN_ACKNO <= ackno <= constants.MAX_ACKNO:
            raise SEQFrameException('ACKNO (%s) out of bounds' % ackno)

        if not constants.MIN_WINDOWSIZE <= window <= constants.MAX_WINDOWSIZE:
            raise SEQFrameException('windowsize (%s) out of bounds' % window )

    def __str__(self):

        # We use this handy function to return a string representation

        framestring = "SEQ "
        framestring += "%i %i %i" % (self.channelnum, self.ackno, self.window)
        framestring += self.TRAILER
        return framestring

class SEQFrameException(FrameException):
    """
    A FrameException relating specifically to SEQ Frames.
    """
    def __init__(self, args=None):
        self.args = args

