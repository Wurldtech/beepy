# $Id: dummyclient.py,v 1.8 2004/06/27 07:38:32 jpwarren Exp $
# $Revision: 1.8 $
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
# Dummy client code to simulate a BEEP client connecting to a server
# for testing the server

import sys
import socket, select
import re

sys.path.append('..')

from beepy.core import frame
from beepy.transports import tcp

import logging
log = logging.getLogger('dummyclient')

class DummyClient:
    """
    A dummy client that uses almost raw frames to test a remote server.
    """

    sock = None
    wfile = None
    server = ("localhost", 1976)
    bufsize = 8096
    framebuffer = ''

    frameHeaderPattern = re.compile('.*\r\n')
    dataFrameTrailer = re.compile(frame.DataFrame.TRAILER)
    SEQFrameRE = '^' + frame.SEQFrame.dataFrameType
    SEQFrameRE += '.*'
    SEQFrameRE += frame.SEQFrame.TRAILER

    DataFrameRE = '.*'
    DataFrameRE += frame.DataFrame.TRAILER

    SEQFramePattern = re.compile(SEQFrameRE)
    DataFramePattern = re.compile(DataFrameRE)

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.numDataFrames = 0
        try:
            self.sock.connect(self.server)
            self.sock.setblocking(0)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except:
            raise

    def sendmsg(self, msg):
        self.sock.send(msg)
	pass

    def getmsg(self, blocking=1, ignoreSEQ=True):
        """
        This method needs to be smarter now that we're using SEQ frames.
        It needs to differentiate between the two frame types and only
        return data for non-SEQ frames.

        Simple pattern matching should do the trick.
        """
        try:
            if blocking:
                while 1:                
                    self.sock.setblocking(1)
                    data = self.sock.recv(self.bufsize)
                    
                    self.framebuffer += data
                    theframe = self.findFrame()
                    if isinstance(theframe, frame.SEQFrame):
                        ## Only return SEQ frames if told to
                        if ignoreSEQ:
                            pass
                        else:
                            return theframe

                    else:
                        if theframe is None:
                            return ''
                        else:
                            self.numDataFrames += 1
#                            log.debug('Data frame %d found: %s' % (self.numDataFrames, theframe))
                            return '%s' % theframe
                    
            else:
                self.sock.setblocking(0)
                data = self._getdata()

        except Exception, e:
            print "Exception occurred in dummyclient: %s: %s" % (e.__class__, e)
            raise

    def _getdata(self):
        inbit, outbit, oobit = select.select([self.sock], [], [], 0.25)
        if inbit:
            data = self.sock.recv(self.bufsize)
            return data

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

    def terminate(self):
#        self.sock.shutdown(2)
        self.sock.close()

