# $Id: message.py,v 1.3 2004/07/24 06:33:48 jpwarren Exp $
# $Revision: 1.3 $
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
This module defines a BEEP Management message, used on
Channel 0 of all sessions.

Management messages are XML formatted, so we use minidom
to represent them.

@version: $Revision: 1.3 $
@author: Justin Warren
"""
import logging
from beepy.core import debug
log = logging.getLogger('beepy')

import xml.dom.minidom
import string
import re

from beepy.core import errors


MessageTypes = ('greeting', 'start', 'close', 'ok', 'error', 'profile')
numberRegex = re.compile(r'[^0-9]')

class Message:
    """
    The Message class defines a BEEP Management message object.
    This is used by the BEEPManagementProfile to coordinate
    channel and session management operations.

    @see: beepmgmtprofile
    """

    def __init__(self, type, doc):
        """
        @param type: type, the message type
        @type type: a valid BEEP management message type

        @param doc: an XML document
        @type doc: an xml.dom.minidom.doc document
        """
        if type not in MessageTypes:
            raise MessageException('Invalid Message Type')
        self.type = type
        self.doc = doc
        if not self.validate():
            raise MessageInvalid('Invalid BEEP Message')

    def __del__(self):
        """
        In order to remove all references to a Message object
        we need to specifically unlink the XML document self.doc
        """
        if self.doc:
            self.doc.unlink()

    # These validation checkers are far from complete.
    # Really need a validating parser or something for completeness
    def isGreeting(self):
        """
        Is this Message a greeting message?
        
        @return: 1, if Message is a greeting
        """
        if self.type == 'greeting':
            return 1

    def isProfile(self):
        """
        Messages of type profile are replies to a channel
        start MSG that was successful.
        
        @return: 1, if Message is a profile
        """
        if self.type == 'profile':
            return 1

    def isStart(self):
        """
        Is this Message a greeting message?
        
        @return: 1, if Message is a greeting
        """
        if self.type == 'start':
            return 1

    def isError(self):
        """
        Is this Message an error message?
        
        @return: 1, if Message is a greeting
        """
        if self.type == 'error':
            return 1

    def isOK(self):
        """
        Is this Message an ok message?
        
        @return: 1, if Message is a greeting
        """
        if self.type == 'ok':
            return 1

    def isClose(self):
        """
        Is this Message a close message?
        
        @return: 1, if Message is a greeting
        """
        if self.type == 'close':
            return 1

    def getCloseChannelNum(self):
        """
        If this is a close message, find the channel number
        that the close message refers to.

        @returns: the channel number to close.
        """
        if self.isClose():
            channelnum = self.doc.childNodes[0].getAttribute('number')
            if numberRegex.search(channelnum):
                raise MessageInvalid('number attribute has non-numeric value')

            return string.atoi(channelnum)

    def getStartChannelNum(self):
        """
        If this is a start message, find the channel number
        that the start message refers to.

        @return: the channel number to start.
        """
        if self.isStart():
            channelnum = self.doc.childNodes[0].getAttribute('number')
            if numberRegex.search(channelnum):
                raise MessageInvalid('number attribute has non-numeric value')

            return string.atoi(channelnum)

    def getErrorCode(self):
        """
        If this is an error message, get the error code
        from the message.

        @return: the error code
        """
        if self.isError():
            errorCode = self.doc.childNodes[0].getAttribute('code')
            if numberRegex.search(errorCode):
                raise MessageInvalid('code attribute has non-numeric value')

            return string.atoi(errorCode)

    def getErrorDescription(self):
        """
        If this is an error message, get the error description
        from the message.

        @return: a string containing the error description
        """
        if self.isError():
            return self.doc.childNodes[0].childNodes[0].nodeValue

# FIXME: getProfileURI and getProfileURIList may be broken
# It depends on how getElementsByTagName processes the DOM structure I've
# hacked together to get around the lack of CDATA functionality in minidom.
# This appears to work so far.. but it isn't guaranteed to work all the
# time.
    def getProfileURI(self):
        """
        Returns the uri attribute of the first
        profile element found.

        @return: a string containing the URI for the profile

        @warning: getProfileURI may be broken. It depends on how
        getElementsByTagName processes the DOM structure I've
        hacked together to get around the lack of CDATA
        functionality in minidom. It appears to work so far,
        but there are no guarantees.
        """
        nodelist = self.doc.getElementsByTagName('profile')
        uri = nodelist[0].getAttribute('uri')
        return uri

    def getProfileURIList(self):
        """
        Finds all the uri attributes of any profile elements and places
        them in a sequence, which is returned.

        @return: a sequence of uri strings

        @warning: getProfileURIList may be broken. It depends on how
        getElementsByTagName processes the DOM structure I've
        hacked together to get around the lack of CDATA
        functionality in minidom. It appears to work so far,
        but there are no guarantees.
        """
        nodelist = self.doc.getElementsByTagName('profile')
#        nodelist = self.doc.childNodes[0].getElementsByTagName('profile')
#        print "DEBUG: nodelist: %s" % nodelist
        uriList = []
        for node in nodelist:
            uriList.append(node.getAttribute('uri'))
        return uriList

    def getStartProfileBlob(self):
        """
        getStartProfileBlob() gets the contents of the CDATA
        element within a <start> message profile, which should
        be a <blob></blob> section to be passed to the profile.

        @return: a string containing the CDATA
        """
        if not self.isStart():
            raise MessageException("Message isn't a start message")

        nodelist = self.doc.childNodes[0].getElementsByTagName('*')
        if nodelist[0].hasChildNodes():
            return nodelist[0].childNodes[0].nodeValue

    def validate(self):
        """
        This is a hack because I can't be bothered integrating
        a validating XML parser into the core just yet. Maybe later.
        All this does is validate the message against the
        BEEP management profile DTD.
        @return: 1 if valid.
        @raise MessageException: if message is invalid
        """
        # firstly, the document should only have one child
        # node
        if len(self.doc.childNodes) != 1:
            raise MessageInvalid('More than one root tag')

        # ok, firstly, the first node of the doc must be
        # a 'greeting', 'start', 'profile', 'close' or 'ok'
        # element.

        currentNode = self.doc.childNodes[0]

        # Greeting type validation
        if currentNode.nodeName == 'greeting':
            nodelist = currentNode.getElementsByTagName('*')
            if len(nodelist) == 0:
                return 1
            for node in nodelist:
                if node.childNodes:
                    raise MessageInvalid('Too many children')
                # profile is empty if in a greeting
                if node.nodeName == 'profile':
                    if len(node.childNodes) != 0:
                        raise MessageInvalid('profile not empty in greeting')
                    if not node.hasAttribute('uri'):
                        raise MessageInvalid
                    return 1

                if node.nodeName != 'features' or node.nodeName == 'localize':
                    return 1

        if currentNode.nodeName == 'start':
            if not currentNode.hasAttribute('number'):
                raise MessageInvalid('start tag has no number attribute')

#            channelnum = currentNode.getAttribute('number')
#            if numberRegex.search(channelnum):
#                raise MessageInvalid('number attribute has non-numeric value')

            foundProfile = 0
            for node in currentNode.childNodes:
                if node.nodeName == 'profile':
                    foundProfile = 1
                    if not node.hasAttribute('uri'):
                        raise MessageInvalid('start tag profile has no uri attribute')

                    # verify that if start profile contains an element
                    # it must be a CDATA section. Nothing else is
                    # permitted.
                    nodelist2 = node.getElementsByTagName('*')
                    for node2 in nodelist2:
                        if node2.nodeName != '#text' and node.nodeName != '#cdata-section':
                            raise MessageInvalid('Invalid start profile content')
                else:
                    raise MessageInvalid('start tag contains non profile element')

            if not foundProfile:
                raise MessageInvalid('start tag has no profile element')
            return 1

        if currentNode.nodeName == 'close':
            nodelist = currentNode.getElementsByTagName('*')
            if len(nodelist) != 0:
                raise MessageInvalid('close message should not have children')

            if not currentNode.hasAttribute('number'):
                raise MessageInvalid('close message must have number attribute')

#            channelnum = currentNode.getAttribute('number')
#            if numberRegex.search(channelnum):
#                raise MessageInvalid('number attribute has non-numeric value')

            if not currentNode.hasAttribute('code'):
                raise MessageInvalid('close message must have code attribute')

            code = currentNode.getAttribute('code')

#            if numberRegex.search(code):
#                raise MessageInvalid('code attribute has non-numeric value')

            return 1

        # Ok is easy to validate.
        if currentNode.nodeName == 'ok':

            # FIXME
            # This is here because minidom has no
            # convenience method for getting all
            # the attributes as a dictionary, which is poxy
            if len(currentNode._attrs.keys()) > 0:
                raise MessageInvalid("ok node shouldn't have attributes")

            if currentNode.childNodes:
                raise MessageInvalid("ok node shouldn't have children")
            else:
                return 1

        if currentNode.nodeName == 'error':
            nodelist = currentNode.getElementsByTagName('*')
            for node in nodelist:
                if node.nodeName != '#text' and node.nodeName != 'code' and node.nodeName != 'xml:lang':
                    raise MessageInvalid('Invalid error subsection')
            return 1

        # positive reply to greeting with profile with init CDATA
        # This message type has a single profile with a CDATA section
        if currentNode.nodeName == 'profile':

            for node in currentNode.childNodes:
                if node.nodeName != '#text' and node.nodeName != '#cdata-section':
                    raise MessageInvalid('Invalid profile content')

                # FIXME
                # minidom strips out CDATA sections and marks them as #text!
                # ARG! This is broken! doh! 

            return 1

        # If I make it this far, it's not valid
        raise MessageInvalid('Invalid BEEP Message')

    def __str__(self):
        """
        Print the XML DOM out for debugging purposes.
        """
        retstr = ''
        for node in self.doc.childNodes:
            retstr += "%s (parent: %s)\n" % (node.nodeName, node.parentNode)
            if node.childNodes:
                for child in node.childNodes:
                    retstr += "--%s (parent: %s)\n" % (child.nodeName, child.parentNode)
        return retstr

class MessageException ( errors.BEEPException ):
    """
    A base class for all Message exceptions.

    Somewhat redundant and should probably be removed.
    """
    def __init__(self, args=None):
        self.args = args

class MessageInvalid( MessageException ):
    """
    Raised whenever a message fails validation.
    """
    def __init__(self, args=None):
        self.args = args

