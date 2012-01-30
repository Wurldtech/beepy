# $Id: profile.py,v 1.16 2004/09/28 01:19:20 jpwarren Exp $
# $Revision: 1.16 $
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
This module defines the basic Profile class and related code.

Profiles are used by BEEP to define the protocol used over
a BEEP channel. You will need to implement or use profiles
in your applications, which will need to inherit from this class.
"""
#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

from beepy.core import constants
from beepy.core import errors

class ProfileFactory:
    
    def __init__(self, profileClass, *args, **kwargs):
        self.profileClass = profileClass
        self.args = args
        self.kwargs = kwargs
    
    def createProfile(self):
        self.profileClass.channelRequested()
        return (self.profileClass(*self.args, **self.kwargs), None, None)


class Profile:
    """
    The profile class is the base class for all BEEP profile classes.
    It defines the base profile API that all profile classes need to
    implement.
    """
    
    content_type = "application/octet-stream"
    
    def __init__(self):
        """
        Create a new Profile object.
        
        NOTE - the channel is NOT ready for use yet.
        """
        self.channel = None
    
    def close(self):
        """
        Close this profile's channel.
        """
        if self.channel:
            self.channel.session.closeChannel(self.channel.channelnum)
    
    @staticmethod
    def channelRequested():
        """
        Called after a channel of this type has been requested and chosen by the
        factory. Raise an error here to deny channel creation.
        """
        pass
    
    def channelStarted(self, channel, uri, cdata):
        """
        Override this method to be notified when the profile's channel has been started.
        """
        self.channel = channel
        #print "Channel %d open" % channel.channelnum
        
    def channelClosed(self):
        """
        Override this method to be notified when the profile's channel has been closed.
        """
        #if self.channel:
        #    print "Channel %d closed" % self.channel.channelnum
        pass
        
    def clientDisconnected(self):
        """
        Override this method to be notified when the client disconnects. This
        is different from channel closed because the client may have
        disconnected abruptly without bothering to close the channel properly.
        """
        pass
    
    def processMessage(self, msg):
        """
        processMessage() is called by the Channel to which this profile
        is bound. This forms the main processing method of a profile.
        
        This method could be overridden by subclasses.
        
        @param msg: the Message to process
        @type msg: a Message object
        """
        if msg.isMSG():
            self.processMSG(msg)
        elif msg.isRPY():
            self.processRPY(msg)
        elif msg.isANS():
            self.processANS(msg)
        elif msg.isNUL():
            self.processNUL(msg)
        elif msg.isERR():
            self.processERR(msg)
    
    # Default behavior is to just ignore any messages
    def processMSG(self, msg):
        pass
    
    def processRPY(self, msg):
        pass
    
    def processANS(self, msg):
        pass
    
    def processNUL(self, msg):
        pass
    
    def processERR(self, msg):
        pass
    
class ProfileException(errors.BEEPException):
    def __init__(self, args):
        self.args = args

class TerminalProfileException(ProfileException):
    def __init__(self, args):
        self.args = args

class TuningReset(ProfileException):
    def __init__(self, args):
        self.args = args


# vim:expandtab:
