# $Id: tlsprofile.py,v 1.8 2004/04/17 07:28:12 jpwarren Exp $
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
# This file implements the TLS transport security profile
#
__profileClass__ = "TLSProfile"
uri = "http://iana.org/beep/TLS"

import profile
from profile import TerminalProfileException
import re

import traceback
import logging
from beepy.core import debug
log = logging.getLogger('TLSProfile')

class TLSProfile(profile.Profile):
    """A TLSProfile is a profile that implements the TLS
       Transport Security Profile. It is used to set up a TLS
       encrypted TCP session.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        """This generic TLS profile has no way of determining your
           application specific key and certificate files. To do any sort
           of funky processing (such as picking specific keyfiles or
           certificates based on the address of the client, for example)
           you have to subclass from this class and implement extra
           bits and pieces to pass in the key and cert file locations.
        """

        profile.Profile.__init__(self, session, profileInit, init_callback)

    def processMessage(self, msg):
        """
        All processMessage should do is move the session from
        insecure to secured.
        """
        try:
            error = self.parseError(msg)
            if error:
                log.debug('Error in payload: %s' % error)

            ready = self.parseReady(msg)
            if ready:
                ## If I receive a <ready> message then I'm the peer
                ## acting in server mode and should start TLS
                log.debug('Ready to start TLS')
                data = '<proceed />'
                self.channel.sendReply(msg.msgno, data)
                self.session.tuningReset()

            proceed = self.parseProceed(msg)
            if proceed:
                ## If I receive a <proceed /> message then I'm the peer
                ## acting in the client mode.
                log.debug('Proceed to start TLS')
                self.session.tuningReset()
                
        except Exception, e:
            log.debug('%s' % e)
            traceback.print_exc()
            raise

    def parseReady(self, msg):
        """ Check data to see if it matches a 'ready' element
        """
        readyPattern = '<ready\s(.*)/>'
        readyRE = re.compile(readyPattern, re.IGNORECASE)

        match = re.search(readyRE, msg.payload)
        if match:

            ## Need to add a version indicator
                
            log.debug('Got ready. Matchgroup: %s' % match.group(1) )
            return match.group(1)
        else:
            return None

    def parseProceed(self, msg):
        proceedPattern = '<proceed\s*/>'
        proceedRE = re.compile(proceedPattern, re.IGNORECASE)

        match = re.search(proceedRE, msg.payload)
        if match:
            return True
        else:
            return None

    def parseError(self, msg):
        """parseError() extracts the error code from the <error> block
        """
        errorPattern = '<error\scode=[\'"](.*)[\'"]\s*>(.*)</error>'
        errorRE = re.compile(errorPattern, re.IGNORECASE)

        match = re.search(errorRE, msg.payload)
        if match:
            code = match.group(1)
            errormsg = match.group(2)
            return code,errormsg
        else:
            return None

    def sendReady(self):
        """ send a ready message to the remote end
        """
        data = '<ready version="1" />'
        self.channel.sendMessage(data)

