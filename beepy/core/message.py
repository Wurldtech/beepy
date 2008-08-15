# $Id: message.py,v 1.9 2004/09/28 01:19:20 jpwarren Exp $
# $Revision: 1.9 $
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
BEEPy Message class

This class is used for the internal representation of a potentially
multi-Frame message. It is very similar to a Frame object, with the
sequencing information removed. This means a Message only records
information pertinent to the application layer, not the BEEP Framing
and transport layer.

Profiles and applications deal with Messages, not directly with Frames.

@version: $Revision: 1.9 $
@author: Justin Warren

"""

import logging
import re

import email
from email import message
from email import utils
from email.generator import Generator

from cStringIO import StringIO

class Message(message.Message):
    
    def __init__(self, msgType, msgno, payload=None, ansno=None, cb=None, args=None):
        self.msgType = msgType
        self.msgno = msgno
        self.ansno = ansno
        self.cb = cb
        self.args = args
        self.start_index = 0
        self._splitre = re.compile("^\n|\n\n")
        self.__text = ""
        message.Message.__init__(self)
        
        if payload != None:
            self.set_payload(payload)
    
    @classmethod
    def from_frame(cls, dataframe):
        """ Create a Message object from a dataframe """
        
        def newmsg():
            return cls(dataframe.dataFrameType, dataframe.msgno)
        
        obj = email.message_from_string(dataframe.payload, newmsg)
        return obj
        
    def set_payload(self, payload, charset=None):
        self._payload = payload
    
    def isMSG(self):
        """
        Check to see if this is a MSG frame
        
        @return: 1 if true
        """
        if self.msgType == 'MSG':
            return True
    
    def isRPY(self):
        """
        Check to see if this is a RPY frame
        
        @return: 1 if true
        """
        if self.msgType == 'RPY':
            return True
    
    def isANS(self):
        """
        Check to see if this is an ANS frame
        
        @return: 1 if true
        """
        if self.msgType == 'ANS':
            return True
    
    def isERR(self):
        """
        Check to see if this is an ERR frame
        
        @return: 1 if true
        """
        if self.msgType == 'ERR':
            return True
    
    def isNUL(self):
        """
        Check to see if this is a NUL frame
        
        @return: 1 if true
        """
        if self.msgType == 'NUL':
            return True
    
    def as_string(self):
        """ Obtain the string representation of this BEEP message """
        return str(self)
    
    def content_as_string(self, amount=None):
        """ Obtain the string representation of the contained MIME message """
        
        # Caching
        if self.__text:
            text = self.__text
        else:
            fp = StringIO()
            g = Generator(fp, mangle_from_=False)
            g.flatten(self)
            text = fp.getvalue()
            header, payload = self._splitre.split(text, 1)
            if len(header) < 1:
                text = "\r\n" + payload
            else:
                text = utils.fix_eols(header) + "\r\n\r\n" + payload
            
            self.__text = text
        
        if amount:
            return text[self.start_index:self.start_index + amount]
        else:
            return text[self.start_index:]
    
    def __str__(self):
        if self.isANS():
            return "%s %d %d:\r\n%s" % (self.msgType, self.msgno, self.ansno,
                self.content_as_string())
        else:
            return "%s %d:\r\n%s" % (self.msgType, self.msgno,
                self.content_as_string())
    
    def __len__(self):
        return len(self.content_as_string())


# vim:expandtab:
