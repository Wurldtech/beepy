# $Id: message.py,v 1.3 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.3 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (C) 2002 Justin Warren <daedalus@eigenmagic.com>
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
#
# Messages are BEEP Management messages

import errors
import xml.dom.minidom
import string
import re

import logging
import debug
log = logging.getLogger('Message')

MessageTypes = ('greeting', 'start', 'close', 'ok', 'error', 'profile')
numberRegex = re.compile(r'[^0-9]')

class Message:

    def __init__(self, type, doc):
        if type not in MessageTypes:
            raise MessageException('Invalid Message Type')
        self.type = type
        self.doc = doc
        if not self.validate():
            raise MessageInvalid('Invalid BEEP Message')

    def __del__(self):
        if self.doc:
            self.doc.unlink()

    # These validation checkers are far from complete.
    # Really need a validating parser or something for completeness
    def isGreeting(self):
        if self.type == 'greeting':
            return 1

    # Message of type profile are replies to a channel start MSG
    # that was successful
    def isProfile(self):
        if self.type == 'profile':
            return 1

    def isStart(self):
        if self.type == 'start':
            return 1

    def isError(self):
        if self.type == 'error':
            return 1

    def isOK(self):
        if self.type == 'ok':
            return 1

    def isClose(self):
        if self.type == 'close':
            return 1

    def getCloseChannelNum(self):
        if self.isClose():
            channelnum = self.doc.childNodes[0].getAttribute('number')
            if numberRegex.search(channelnum):
                raise MessageInvalid('number attribute has non-numeric value')

            return string.atoi(channelnum)

    def getStartChannelNum(self):
        if self.isStart():
            channelnum = self.doc.childNodes[0].getAttribute('number')
            if numberRegex.search(channelnum):
                raise MessageInvalid('number attribute has non-numeric value')

            return string.atoi(channelnum)

    def getErrorCode(self):
        if self.isError():
            errorCode = self.doc.childNodes[0].getAttribute('code')
            if numberRegex.search(errorCode):
                raise MessageInvalid('code attribute has non-numeric value')

            return string.atoi(errorCode)

    def getErrorDescription(self):
        if self.isError():
            return self.doc.childNodes[0].childNodes[0].nodeValue

# FIXME: getProfileURI and getProfileURIList may be broken
# It depends on how getElementsByTagName processes the DOM structure I've
# hacked together to get around the lack of CDATA functionality in minidom.
# This appears to work so far.. but it isn't guaranteed to work all the
# time.
    def getProfileURI(self):
        """getProfileURI returns the uri attribute of the first
        profile element found.
        inputs: None
        outputs: uri, string
        raises: None
        """
        nodelist = self.doc.getElementsByTagName('profile')
        uri = nodelist[0].getAttribute('uri')
        return uri

    def getProfileURIList(self):
        """getProfileURIList() finds all the uri attributes of
        any profile elements and places them in a sequence, which
        is returned.
        inputs: None
        outputs: uriList, sequence of uri strings
        raises: None
        """
        nodelist = self.doc.getElementsByTagName('profile')
#        nodelist = self.doc.childNodes[0].getElementsByTagName('profile')
#        print "DEBUG: nodelist: %s" % nodelist
        uriList = []
        for node in nodelist:
            uriList.append(node.getAttribute('uri'))
        return uriList

    def getStartProfileBlob(self):
        """getStartProfileBlob() gets the contents of the CDATA
           element within a <start> message profile, which should
           be a <blob></blob> section to be passed to the profile.
        """
        if not self.isStart():
            raise MessageException("Message isn't a start message")

        nodelist = self.doc.childNodes[0].getElementsByTagName('*')
        if nodelist[0].hasChildNodes():
            return nodelist[0].childNodes[0].nodeValue

    # This is a hack because I can't be bothered integrating
    # a validating XML parser into the core just yet. Maybe later.
    # All this does is validate the message against the
    # BEEP management profile DTD.
    # returns 1 if valid. If invalid, raises MessageException
    def validate(self):

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
        retstr = ''
        for node in self.doc.childNodes:
            retstr += "%s (parent: %s)\n" % (node.nodeName, node.parentNode)
            if node.childNodes:
                for child in node.childNodes:
                    retstr += "--%s (parent: %s)\n" % (child.nodeName, child.parentNode)
        return retstr

class MessageException ( errors.BEEPException ):
    def __init__(self, args=None):
        self.args = args

class MessageInvalid( MessageException ):
    def __init__(self, args=None):
        self.args = args

