# $Id: mgmtparser.py,v 1.2 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.2 $
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
# The BEEP Management Profile XML Parser
# I'm being sneaky here so that I can use just what's available
# within the Python Standard Library.
# I want to use DOM, so I'm using minidom, but minidom doesn't
# support parsing of CDATA sections. Dumb, but that's the way it
# is. minidom _does_ support the creation of them and subsequent
# output, so we cheat, using pyExpat to parse things in, but create
# a minidom DOM document anyway, sidestepping the limitations of
# minidom.
# If minidom ever gets fixed up to support CDATA, we can do away
# with this smoke and mirrors technique.

import errors
import message
import logging

import types
import xml.dom.minidom
import xml.parsers.expat
import re

log = logging.getLogger('MGMTParser')

class Parser:

    def __init__(self, data=None):
        self.doc = None
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.startElementHandler
        self.parser.EndElementHandler = self.endElementHandler
        self.parser.CharacterDataHandler = self.dataHandler
        self.parser.StartCdataSectionHandler = self.startCdataSectionHandler
        self.parser.EndCdataSectionHandler = self.endCdataSectionHandler
#        self.parser.ErrorHandler = self.errorHandler
#        self.parser.IgnorableWhitespaceHandler = self.ignoreWhitespaceHandler
        self.elementStack = []
        self.withinCdataSection = 0
        if data:
            self._parseData(data)

    def __del__(self):
        self.close()

    def close(self):
        self.flushParser()
        if self.doc:
            self.doc.unlink()

    def flushParser(self):
        if self.parser:
            self.parser.Parse('',1)
            del self.parser
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.startElementHandler
        self.parser.EndElementHandler = self.endElementHandler
        self.parser.CharacterDataHandler = self.dataHandler
        self.parser.StartCdataSectionHandler = self.startCdataSectionHandler
        self.parser.EndCdataSectionHandler = self.endCdataSectionHandler

    # Hand off some data to the parser
    def feed(self, data):
        try:
            self.parser.Parse(data, 0)
        except Exception, e:
            raise ParserException("Exception parsing document: %s" % e)

    # Called when the beginning of a tag is found
    def startElementHandler(self, name, attrs):

        # create the element and add its attributes
        element = self.doc.createElement(name)
        for attribname in attrs.keys():
            element.setAttribute(attribname, attrs[attribname])

        # plonk it on a stack in case this element has children
        self.elementStack.append(element)

    # Called when an element close tag is found
    def endElementHandler(self, name):
        # we've just ended this element, so it should be 
        # on the top of the stack
        try:
            element = self.elementStack.pop()

            # if there's another element on the stack, then
            # that is our parent, so we need to link as a child
            if len(self.elementStack) >= 1:
                parent = self.elementStack.pop()
                parent.appendChild(element)
                # That done, the parent might have other
                # children that we haven't finished parsing yet
                # so put it back on the stack
                self.elementStack.append(parent)
            else:
                # No parent element, so we must be the
                # first topmost element of the document
                self.doc.appendChild(element)

        except Exception, e:
            # Weird. Getting here means you've started an
            # element but it didn't get pushed onto the stack.
            # That's, like, bad and stuff, so log an error
            raise ParserException("Possible bug: xml element started but not on stack: %s" % e)

    # Called when character data is found
    # Both normal text and CDATA text flag as character data
    # so we use the extra flag self.withinCdataSection to
    # know if we're within a CDATA section. Since a CDATA
    # section isn't a container, we only need a boolean type flag.
    def dataHandler(self, data):
        # ignore nothing but whitespace
        whitespace = re.compile(r'^\s*$')

        match = re.search(whitespace, data)
        if match:
            return
        # check to see if we're in a CDATA section
        if self.withinCdataSection:
            element = self.doc.createCDATASection(data)
        else:
            element = self.doc.createTextNode(data)

        # append this element as a child of whichever element
        # is topmost on the stack
        if len(self.elementStack) < 1:
            # This probably means someone put data text outside
            # the main tags, so this is malformed BEEP XML
            raise ParserException("CDATA found outside outermost tags")
        else:
            parent = self.elementStack.pop()

            parent.appendChild(element)
            self.elementStack.append(parent)

    def startCdataSectionHandler(self):
        self.withinCdataSection = 1

    def endCdataSectionHandler(self):
        self.withinCdataSection = 0

    # Check to see if the message contains at least one profile tag
    def hasProfile(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('profile')
        if len(nodelist) >= 1:
            return 1

    def getProfiles(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        return self.doc.getElementsByTagName('profile')

    def getProfileURIs(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        uriList = []
        nodelist = self.doc.getElementsByTagName('profile')
        for node in nodelist:
            uriList.append(node.getAttribute('uri'))

        return uriList

    # A start message has 1 <start> element that is a child of
    # the document root. It must have a number attrib, may have
    # a serverName attrib and must have at least one profile
    # element.
    def isStartMessage(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('start')
        if len(nodelist) == 1:
            return 1
        if len(nodelist) >= 1:
            raise ParserException("Too Many start Elements")

    # A close message has 1 <close> element. It must have a number
    # attrib as well as a code attrib.
    def isCloseMessage(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('close')
        if len(nodelist) == 1:
            return 1
        if len(nodelist) >= 1:
            raise ParserException("Too Many close Elements")

    def isOKMessage(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('ok')
        if len(nodelist) == 1:
            return 1
        if len(nodelist) >= 1:
            raise ParserError("Too Many ok Elements")

    def isErrorMessage(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('error')
        if len(nodelist) != 1:
            raise ParserError("Too Many error Elements")
        else:
            return 1

    def getStartChannelNum(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('start')
        return nodelist[0].getAttribute('number')

    def getCloseChannelNum(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('close')
        return nodelist[0].getAttribute('number')

    def getErrorCode(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('error')
        return nodelist[0].getAttribute('code')

    def getErrorString(self, message=None):
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('error')
        # FIXME
        # This is a semi-broken way of doing this, but no
        # convenience methods yet exist for this in minidom
        # It may go away at some point, so beware
        newnode = nodelist[0]._get_firstChild()
        return newnode.nodeValue

    def parse(self, data):
        try:
            self._parseData(data)
            type = self._getMessageType()

            return message.Message(type, self.doc.cloneNode(1))
        except message.MessageException, e:
            raise ParserException("%s" % e)

    def _parseData(self, data):
        if type(data) == types.NoneType:
            # Passed in an empty data object, return None
            return None

        # Initialise a new minidom document for filling
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        if type(data) == types.StringType:
            try:
                self.feed(data)
                self.flushParser()
            except Exception, e:
                raise ParserException('Bad XML: %s' % e)
        else:
            try:
                while 1:
                    mydata = data.read(1024)
                    if not mydata:
                        break
                    self.feed(mydata)
                self.flushParser()
            except Exception, e:
                raise ParserException('Bad XML: %s' % e)

    # The message type should be the first child node of the doc
    # This is probably really fragile
    def _getMessageType(self):
        children = self.doc.childNodes
        if len(children) != 1:
            raise ParserException('too many child nodes')
        return self.doc.childNodes[0].nodeName

class ParserException(errors.BEEPException):
    def __init__(self, args=None):
        self.args = args
