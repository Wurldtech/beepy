# $Id: profile.py,v 1.14 2004/08/02 09:46:07 jpwarren Exp $
# $Revision: 1.14 $
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
This module defines the basic Profile class and related code.

Profiles are used by BEEP to define the protocol used over
a BEEP channel. You will need to implement or use profiles
in your applications, which will need to inherit from this class.
"""
import logging
from beepy.core import debug
log = logging.getLogger('beepy')

from beepy.core import constants
from beepy.core import errors

# All payloads are expected to be MIME structured, so we include the
# library here.
import StringIO
import mimetools, mimetypes, MimeWriter

# Traceback information is useful for unexpected exceptions when
# developing profiles, so I've put this in here.
import traceback

# This is a special variable. It is used to dynamically instanciate
# the Profile by the Session (actually, the BEEPManagementProfile does it).
# Set this in your subclasses.
__profileClass__ = "Profile"

class Profile:
    """
    The profile class is the base class for all BEEP profile classes.
    It defines the base profile API that all profile classes need to
    implement.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        """
        Create a new Profile object.

        @param session: the session to which this profile's channel
        belongs.
        @type session: a Session object
        
        @param profileInit: initialisation data passed to the profile
        @type profileInit: bytestring

        @param init_callback: a method that will do further, more complex,
        profile initialisation at create time.
        @type init_callback: a bound method
        """
        self.session = session
        self.channel = None
        self.type = None
        self.encoding = None
        if init_callback:
            init_callback(self)

    def setChannel(self, channel):
        """
        setChannel() binds this Profile to the Channel
        it belongs to. If this method is not called to set
        the Channel for the Profile, they channel will be
        unable to process any messages.
        """
        self.channel = channel

    def processMessage(self, msg):
        """
        processMessage() is called by the Channel to which this profile
        is bound. This forms the main processing method of a profile.

        This method should be overridden by subclasses.

        @param msg: the Message to process
        @type msg: a Message object
        """
        raise NotImplementedError

    def mimeDecode(self, payload):
        """
        mimeDecode() is a convenience function used to help
        make life easier for profile programmers, like me.
        It takes the payload and extracts the data from
        the headers.

        @param payload: the data to decode
        """
        self.type = constants.DEFAULT_MIME_CONTENT_TYPE
        instring = StringIO.StringIO(payload)
        headers = mimetools.Message(instring)
        msgtype = headers.gettype()
        if headers.getmaintype() == "multipart":
            raise ProfileException("cannot handle multipart MIME yet")
        else:
            self.type = msgtype

        msgencoding = headers.getencoding()
        # only support base64 or binary encodings, default is binary
        outstring = StringIO.StringIO()
        if msgencoding:
            self.encoding = msgencoding

        if self.encoding == "base64":
            mimetools.decode(instring, outstring, self.encoding)
        else:
            outstring = instring

        msg = ''
        msg = outstring.read()

        return msg

    def mimeEncode(self, payload, contentType=constants.DEFAULT_MIME_CONTENT_TYPE, encoding=None):
        """
        mimeEncode() is a convenience function used to help
        make life easier for profile programmers, like me.

        It takes a given payload and adds MIME headers to it.
        Note: The separation between the MIME headers is a
        single newline '\n', not '\r\n'. Not sure why, but MimeWriter
        is doing it for some reason.

        @param payload: the data to encode
        @param contentType: the MIME content type
        @param encoding: an alternate encoding.
        """
        outstring = StringIO.StringIO()
        writer = MimeWriter.MimeWriter(outstring)
        writer.startbody(contentType)
        if encoding:
            writer.addheader("Content-transfer-encoding", encoding)
        writer.flushheaders()
        outstring.write(payload)
        # convert StringIO to string
        # potential buffer overflow here
        outstring.seek(0)
        msg = outstring.read()

        if len(msg) > constants.MAX_PAYLOAD_SIZE:
            log.warn("payload is large and should be fragmented")

        return msg

class ProfileException(errors.BEEPException):
    def __init__(self, args):
        self.args = args

class TerminalProfileException(ProfileException):
    def __init__(self, args):
        self.args = args

class TuningReset(ProfileException):
    def __init__(self, args):
        self.args = args

# This class is used to manage profiles that are known by
# an application. It gets passed in to a Session so each Session
# knows what profiles it knows and how to bind them to Channels
# This is really just a wrapper around a dictionary that contains
# a uri to python module mapping.
#
# It ends up containing a whole swag of stuff that can be played
# with dynamically. (Yay!)
#
# The structure of what is held is as follows:
# Key: URI of the profile
# profile: the actual module for the profile
# init_callback: an optional initialisation callback that gets
# called when the profile is instanciated.

class ProfileDict:
    """
    a ProfileDict is a specialised dictionary for managing profiles
    known by a Session.
    """
    def __init__(self):
        self._profiles = {}
        self._callbacks = {}

    # Convenience function to get profiles out
    # 
    def __getitem__(self, uri):
        return self._profiles[uri]

    # Add a profile map to the dictionary
    # uri is the uri used to refer to this profile
    # module is the path to the module for dynamic loading
    def __setitem__(self, uri, module):
        """
        Adds a profile to the dictionary

        @param uri: the uri used to refer to the profile
        @type uri: string
        
        @param module: a reference to a loaded module
        @type module: an imported module reference
        """
        self._profiles[uri] = module
        self._callbacks[uri] = None

    def __delitem__(self, uri):
        """
        Remove a profile from the dictionary

        @param uri: the uri of the profile to remove
        """
        del self._profiles[uri]

    def getURIList(self):
        """
        Gets a list of the URIs of profiles in the dictionary

        @return: a list of URI strings
        """
        if self._profiles:
            return self._profiles.keys()

    def addProfile(self, profileModule, init_callback=None):
        """
        Adds a module to the dictionary without needing to know the
        uri of the module.

        @param profileModule: the module to add
        @type profileModule: an imported module reference

        @param init_callback: a profile initialisation method to use
        at create time
        @type init_callback: a bound method
        """
        self._profiles[profileModule.uri] = profileModule
        self._callbacks[profileModule.uri] = init_callback

    def removeProfile(self, uri):
        """
        Remove a profile from the dictionary
        
        @param uri: the URI of the profile to remove
        @type uri: string
        """
        del self._profiles[uri]
        del self._callbacks[uri]

    def getCallback(self, uri):
        """
        Return a reference to a module's initalisation callback

        @param uri: the URI of the profile
        @type uri: string

        @return: a reference to a bound method
        """
        return self._callbacks[uri]

class ProfileDictException(errors.BEEPException):
    def __init__(self, args):
        self.args = args
