# $Id: dummyclient.py,v 1.14 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.14 $
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
# Dummy client code to simulate a BEEP client connecting to a server
# for testing the server

import sys
import socket, select
import re

from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor, defer, error

from beepy.core import frame
from beepy.transports import tcp

import logging
log = logging.getLogger('dummyclient')

class DummyProtocol(Protocol):
    """
    A raw data transport protocol for talking to BEEP servers
    """

    servername = 'localhost'
    serverport = 1976

    frameHeaderPattern = re.compile('.*\r\n')
    dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
    SEQFrameRE = '^' + frame.SEQFrame.dataFrameType
    SEQFrameRE += '.*'
    SEQFrameRE += frame.SEQFrame.TRAILER

    DataFrameRE = '.*'
    DataFrameRE += frame.DataFrame.TRAILER

    SEQFramePattern = re.compile(SEQFrameRE)
    DataFramePattern = re.compile(DataFrameRE)

    def connectionMade(self):
        self.framebuffer = ''
        self.d = None
        self.later_call = None

    def connectionLost(self, reason):
        if self.d is not None:
            try:
                self.d.callback('')
            except defer.AlreadyCalledError:
                pass

        if self.later_call:
            self.later_call.cancel()
            self.later_call = None
    
    def dataReceived(self, data):
        #print "got some data:", data
        self.framebuffer += data

    def sendmsg(self, msg):
        """
        Grab the message, and send it to the remote host.
        """
        self.transport.write(msg)
	pass

    def getmsg(self, d=None, ignored=None, ignoreSEQ=True):
        """
        Get data from the protocol.
        """
        if d is None:
            self.d = defer.Deferred()
            
        frame = self.findFrame()
        if frame:
            #print "got frame"
            if frame.dataFrameType == 'SEQ' and ignoreSEQ:
                #print "ignoring seq frame"
                self.later_call = reactor.callLater(0.1, self.getmsg, self.d)
            else:
                #print "returning frame"
                self.later_call = None
                self.d.callback(str(frame))
                pass
            pass

        else:
            self.later_call = reactor.callLater(0.1, self.getmsg, self.d)

        return self.d

    def findFrame(self):
        """
        Search for a frame in the databuffer. Return a frame
        object for the first frame found.
        """
        ## Look for a SEQ frame
        match = self.SEQFramePattern.search(self.framebuffer)
        if match:
            ## Found a SEQ frame
            data = self.framebuffer[:match.end()]
            self.framebuffer = self.framebuffer[match.end():]
            return frame.SEQFrame(databuffer=data)

        ## Look for a Data frame
        match = self.DataFramePattern.search(self.framebuffer)
        if match:
            data = self.framebuffer[:match.end()]
            self.framebuffer = self.framebuffer[match.end():]
            return frame.DataFrame(databuffer=data)


class DummyClient:
    """
    A wrapper class to make testing easier to code.
    Basically used to connect to a server, and send and receive data
    """

    def __init__(self):
        """
        Initialising the client will connect it to the server.
        Returns a deferred that will fire when the connection has
        completed successfully.
        """
        self.factory = DummyFactory()

