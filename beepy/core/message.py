# $Id: message.py,v 1.5 2004/04/17 07:30:42 jpwarren Exp $
# $Revision: 1.5 $
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
BEEPy Message class

This class is used for the internal representation of a potentially
multi-Frame message. It is very similar to a Frame object, with the
sequencing information removed. This means a Message only records
information pertinent to the application layer, not the BEEP Framing
and transport layer.

Profiles and applications deal with Messages, not directly with Frames.

@version: $Revision: 1.5 $
@author: Justin Warren

"""

import errors
import constants
import string

## Defines possible Message types
TYPE_MSG = 0
TYPE_RPY = 1
TYPE_ANS = 2
TYPE_ERR = 3
TYPE_NUL = 4

class Message:
    """
    A Message is the base unit of application data that is used
    by Channels and Profiles.
    """
    
    def __init__(self, dataframe=None, msgType=None, msgno=None, payload='', ansno=None, cb=None, args=None):
        """
        @type dataFrame: DataFrame
        @param dataFrame: a raw dataFrame
        """
        ## Create directly from a dataframe
        if dataframe:
            self.msgType = dataframe.dataFrameType
            self.msgno = dataframe.msgno
            self.payload = dataframe.payload
            if dataframe.isANS():
                self.ansno = dataframe.ansno
                pass

        else:
            self.msgType = msgType
            self.msgno = msgno
            self.payload = payload
            self.ansno = ansno

        ## Callback to use when message is completely sent
        self.cb = cb
        self.args = args

    def __str__(self):
        if self.isANS():
            return "%s %d %d:\n  %s" % (self.msgType, self.msgno, self.ansno, self.payload)
        else:
            return "%s %d:\n  %s" % (self.msgType, self.msgno, self.payload)

    def __repr__(self):
        return "<%s instance at %s>" % (self.__class__, hex(id(self)))

    def __len__(self):
        return len(self.payload)

    def __copy__(self):
        return Message(None, self.msgType, self.msgno, self.payload, self.ansno)

    def append(self, data):
        """
        Appends data to the Message payload
        """
        self.payload += data
    
    def isMSG(self):
        """
        Check to see if this is a MSG frame

        @return: 1 if true
        """
        if self.msgType == 'MSG':
            return 1

    def isRPY(self):
        """
        Check to see if this is a RPY frame

        @return: 1 if true
        """
        if self.msgType == 'RPY':
            return 1

    def isANS(self):
        """
        Check to see if this is an ANS frame

        @return: 1 if true
        """
        if self.msgType == 'ANS':
            return 1

    def isERR(self):
        """
        Check to see if this is an ERR frame

        @return: 1 if true
        """
        if self.msgType == 'ERR':
            return 1

    def isNUL(self):
        """
        Check to see if this is a NUL frame

        @return: 1 if true
        """
        if self.msgType == 'NUL':
            return 1


