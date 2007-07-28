# $Id: mgmtparser.py,v 1.7 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.7 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
"""
The BEEP Management Profile XML Parser.

I'm being sneaky here so that I can use just what's available
within the Python Standard Library.
I want to use DOM, so I'm using minidom, but minidom doesn't
support parsing of CDATA sections. Dumb, but that's the way it
is. minidom _does_ support the creation of them and subsequent
output, so we cheat, using pyExpat to parse things in, but create
a minidom DOM document anyway, sidestepping the limitations of
minidom.

If minidom ever gets fixed up to support CDATA, we can do away
with this smoke and mirrors technique.
"""
#import logging
from beepy.core.debug import log
#log = logging.getLogger('debug')

import types
import xml.dom.minidom
import xml.parsers.expat
import re

from beepy.core import errors
import message

class Parser:
    """
    A Parser object takes in string encodings of XML documents
    that represent a BEEP Management message
    """
    def __init__(self, data=None):
        """
        Sets up an XML document parser.
        """
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
        """
        Shutdown the parser and unlink any parsed documents
        """
        self.flushParser()
        if self.doc:
            self.doc.unlink()

    def flushParser(self):
        """
        Zero the parser so that it is empty and ready to parse
        a new message
        """
        if self.parser:
            self.parser.Parse('',1)
            del self.parser
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.startElementHandler
        self.parser.EndElementHandler = self.endElementHandler
        self.parser.CharacterDataHandler = self.dataHandler
        self.parser.StartCdataSectionHandler = self.startCdataSectionHandler
        self.parser.EndCdataSectionHandler = self.endCdataSectionHandler

    def feed(self, data):
        """
        Hand off some data to the XML parser.
        """
        try:
            self.parser.Parse(data, 0)
        except Exception, e:
            raise ParserException("Exception parsing document: %s" % e)

    def startElementHandler(self, name, attrs):
        """
        Called when the beginning of a tag is found.
        """
        # create the element and add its attributes
        element = self.doc.createElement(name)
        for attribname in attrs.keys():
            element.setAttribute(attribname, attrs[attribname])

        # plonk it on a stack in case this element has children
        self.elementStack.append(element)

    def endElementHandler(self, name):
        """
        Called when an element close tag is found.
        """
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

    def dataHandler(self, data):
        """
        Called when character data is found.
        Both normal text and CDATA text flag as character data
        so we use the extra flag self.withinCdataSection to
        know if we're within a CDATA section. Since a CDATA
        section isn't a container, we only need a boolean type flag.
        """
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
        """
        Called when the start of a CDATA section is found
        """
        self.withinCdataSection = 1

    def endCdataSectionHandler(self):
        """
        Called when the end of a CDATA section is found
        """
        self.withinCdataSection = 0


    def hasProfile(self, message=None):
        """
        Check to see if the message contains at least one profile tag.
        """
        if message:
        
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('profile')
        if len(nodelist) >= 1:
            return 1

    def getProfiles(self, message=None):
        """
        Get all the profiles in the message.

        @return: DOM nodes with tagname of profile
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        return self.doc.getElementsByTagName('profile')

    def getProfileURIs(self, message=None):
        """
        Get all the profile URIs in the message.

        @return: list of DOM nodes
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        uriList = []
        nodelist = self.doc.getElementsByTagName('profile')
        for node in nodelist:
            uriList.append(node.getAttribute('uri'))

        return uriList

    def isStartMessage(self, message=None):
        """
        Check to see if this is a <start> message.

        A start message has 1 <start> element that is a child of
        the document root. It must have a number attrib, may have
        a serverName attrib and must have at least one profile
        lement.

        @return: 1 if this is a <start> message.

        @raise ParserException: if XML document is invalid
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('start')
        if len(nodelist) == 1:
            return 1
        if len(nodelist) >= 1:
            raise ParserException("Too Many start Elements")

    def isCloseMessage(self, message=None):
        """
        Check to see if this is a <close> message.
        
        A close message has 1 <close> element. It must have a number
        attrib as well as a code attrib.

        @return: 1 is this is a <close> message.

        @raise ParserException: if XML document is invalid
        """
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
        """
        Check to see if this is an <ok> message.

        @return: 1 if this is an <ok> message.

        @raise ParserException: if XML document is invalid
        """
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
        """
        Check to see if this is an <error> message.

        @return: 1 if this is an <error> message.

        @raise ParserException: if XML document is invalid.
        """
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
        """
        Get the channel number from a <start> message.

        @return: string, the channel number
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('start')
        return nodelist[0].getAttribute('number')

    def getCloseChannelNum(self, message=None):
        """
        Get the channel number from a <close> message.

        @return: string, the channel number
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('close')
        return nodelist[0].getAttribute('number')

    def getErrorCode(self, message=None):
        """
        Get the code from an <error> message.

        @return: string, the error code
        """
        if message:
            self._parseData(message)

        if not self.doc:
            raise ParserException("No Document Provided")

        nodelist = self.doc.getElementsByTagName('error')
        return nodelist[0].getAttribute('code')

    def getErrorString(self, message=None):
        """
        Get the description from an <error> message.

        @return: string, the error description
        """
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
        """
        Parse a bytestring as an XML document encoding a
        BEEP Management message.

        @param data: the data to parse.
        @type data: bytestring
        """
        try:
            self._parseData(data)
            type = self._getMessageType()

            return message.Message(type, self.doc.cloneNode(1))
        except message.MessageException, e:
            raise ParserException("%s" % e)

    def _parseData(self, data):
        """
        The internal parsing mechanism, used to create an XML DOM.

        @raise ParserException: if XML is invalid.
        """
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

    def _getMessageType(self):
        """
        The message type should be the first child node of the doc
        This is probably really fragile.

        I don't think this is used anywhere. Should be removed.
        """
        children = self.doc.childNodes
        if len(children) != 1:
            raise ParserException('too many child nodes')
        return self.doc.childNodes[0].nodeName

class ParserException(errors.BEEPException):
    """
    Exception raised if there are any errors during parsing
    of XML data.
    """
    def __init__(self, args=None):
        self.args = args
