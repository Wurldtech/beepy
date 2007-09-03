# $Id: mgmtcreator.py,v 1.8 2007/09/03 03:20:12 jpwarren Exp $
# $Revision: 1.8 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
"""
The BEEP Management Profile XML Creator

This class creates the various BEEP messages required
for channel management of BEEP.

This implementation uses DOM via xml.dom.minidom.

@version: $Revision: 1.8 $
@author: Justin Warren
"""
#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import types
import xml.dom.minidom

from beepy.core import errors
from beepy.core.constants import ReplyCodes

class Creator:
    """
    A Creator object is used to create management messages.
    This provides a convenience API for the creation of all
    the management messages used by the BEEP Management profile.
    """
    def __init__(self):
        """
        A newly created creator is basically empty.
        """
        self.doc = None

    def __del__(self):
        """
        We have to specifically unlink() the doc DOM else Python
        may not garbage collect it due to circular references.
        """
        if self.doc:
            self.doc.unlink()

    def createGreetingMessage(self, profileURIList=None, features=None, localize=None):
        """
        Create a <greeting/> message object with any parameters it
        might need.

        @param profileURIList: a list of profiles to include in the
        greeting.
        @type profileURIList: a list of strings

        @param features: any special features we want to advertise
        @type features: string

        @param localize: a localization definition, for language support
        @type localize: string
        """
        # This bit is for GC, since there's no guarantee python won't
        # leak memory because of circular references in DOM documents.
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        element = self.doc.createElement('greeting')

        # Set attributes, if they've been passed in
        if features:
            element.setAttribute('features', features)
        if localize:
            element.setAttribute('localize', localize)

        self.doc.appendChild(element)

        # Build a list of profiles as children to the greeting node
        if profileURIList:
            for profileURI in profileURIList:
                profile = self.doc.createElement('profile')
                profile.setAttribute('uri', profileURI)
                element.appendChild(profile)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception:
            raise CreatorException('Exception Converting to XML')


    def createStartMessage(self, number, profileList, serverName=None):
        """
        createStartMessage takes a profileList, different from
        createGreetingMessage. It is a list of profile descriptions.
        A profile description consists of a list thus::
        
        ['profileURI', 'encoding', chardata]
        
        profileURI is a string of the URI for this profile.
        eg: http://iana.org/beep/SASL/OTP
        
        encoding is an optional encoding type specifying if the
        chardata within the profile element is a base64-encoded string
        
        chardata is up to 4k octets of initialization message given to
        the channel.

        @param number: The number of the channel to start
        @type number: int or string

        @param profileList: a list of profiles, explained above

        @param serverName: a name used to refer to the server.
        Defined in RFC3080, but I'll have to look it up and update
        this bit of the doco.
        @type serverName: string
        
        """
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        # create start element
        element = self.doc.createElement('start')
        if type(number) != types.StringType:
            number = '%s' % number
#            raise CreatorException('number is supposed to be a string, dude.')
        element.setAttribute('number', number)
        # Set the servername, if need be
        if serverName:
            element.setAttribute('serverName', serverName)

        self.doc.appendChild(element)

        # Build a list of profiles as children to the start node
        # A start message must have at least one, so we don't check
        # for the list as in createGreetingMessage() above
        for profiledesc in profileList:
            try:
                profile = self.doc.createElement('profile')
                profile.setAttribute('uri', profiledesc[0])
                if profiledesc[1]:
                    profile.setAttribute('encoding', profiledesc[1])
                if profiledesc[2]:
                    data = self.doc.createCDATASection(profiledesc[2])
                    profile.appendChild(data)

            except IndexError, e:
                raise CreatorException('Malformed profileList')

            element.appendChild(profile)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception, e:
            raise
#            raise CreatorException('Exception Converting to XML')

    def createStartReplyMessage(self, profileURI):
        """
        Creates a positive reply message to a start message,
        which will be a <profile> message.

        @param profileURI: the URI used to create the channel
        @type profileURI: string
        """
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        # create profile element
        element = self.doc.createElement('profile')
#        if type(profileURI) != types.StringType:
#            raise CreatorException('profileURI is supposed to be a string, dude.')
        element.setAttribute('uri', profileURI)

        self.doc.appendChild(element)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception, e:
            raise
#            raise CreatorException('Exception Converting to XML')

    def createCloseMessage(self, number, code, text=None, xmlLang=None):
        """
        Creates a <close> message.

        @param number: the number of the channel to close
        @type number: int or string

        @param code: The reason the channel is being closed
        @type code: string

        @param text: A human language description of the close reason.
        @type text: string

        @param xmlLang: The language used by the optional text part
        of the message.
        @type xmlLang: string
        """
        # This bit is for GC, since there's no guarantee python won't
        # leak memory because of circular references in DOM documents.
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        element = self.doc.createElement('close')

        # Set attributes, if they've been passed in
        if type(number) != types.StringType:
            number = '%s' % number
        element.setAttribute('number', number)
        element.setAttribute('code', code)
        if xmlLang:
            element.setAttribute('xml:lang', xmlLang)
        if text:
            textNode = self.doc.createTextNode(text)
            element.appendChild(textNode)

        self.doc.appendChild(element)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception:
            raise CreatorException('Exception Converting to XML')

    def createOKMessage(self):
        """
        Creates an <ok> message, used for positive replies.
        """
        # This bit is for GC, since there's no guarantee python won't
        # leak memory because of circular references in DOM documents.
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        element = self.doc.createElement('ok')

        self.doc.appendChild(element)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception:
            raise CreatorException('Exception Converting to XML')

    def createErrorMessage(self, code, text=None, xmlLang=None):
        """
        Creates an <error> message populated with the supplied parameters.

        @param code: the error code
        @type code: string

        @param text: A human language description of the error
        @type text: string

        @param xmlLang: The language used by the optional text part
        of the message.
        @type xmlLang: string
        """
        # This bit is for GC, since there's no guarantee python won't
        # leak memory because of circular references in DOM documents.
        if self.doc:
            self.doc.unlink()
        self.doc = xml.dom.minidom.Document()
        self.doc.parentNode = self.doc
        self.doc.ownerDocument = self.doc

        element = self.doc.createElement('error')

        # Set attributes, if they've been passed in
        element.setAttribute('code', code)
        if xmlLang:
            element.setAttribute('xml:lang', xmlLang)

        ## Try to add default error text
        if text is None:
            if ReplyCodes.has_key(code):
                text = ReplyCodes[code]

        if text:
            textNode = self.doc.createTextNode(text)
            element.appendChild(textNode)

        self.doc.appendChild(element)

        # write pretty printed xml, using 2 spaces for indentation
        try:
            return self.messageToString(self.doc)

        except Exception:
            raise CreatorException('Exception Converting to XML')

    def messageToString(self, DOMdocument):
        """
        A convenience method to print messages without leading
        <?xml version="1.0" ?> type strings in them
        """
        string = DOMdocument.toprettyxml('  ', '\r\n')
        return string[23:]

class CreatorException(errors.BEEPException):
    """
    Exception raised if there's an error creating a message.
    """
    def __init__(self, args=None):
        self.args = args

