# $Id: saslanonymousprofile.py,v 1.5 2003/12/09 02:37:30 jpwarren Exp $
# $Revision: 1.5 $
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

__profileClass__ = "SASLAnonymousProfile"
uri = "http://iana.org/beep/SASL/ANONYMOUS"

import traceback

import saslprofile
from profile import TerminalProfileException
from beepy.core import constants

import logging
from beepy.core import debug
log = logging.getLogger('SASLAnonymous')

class SASLAnonymousProfile(saslprofile.SASLProfile):
    """A SASLAnonymousProfile is a SASL Profile that implements
       the ANONYMOUS mechanism for anonymous authentication.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        saslprofile.SASLProfile.__init__(self, session)
        log.debug("initstring: %s" % profileInit)

    def processFrame(self, theframe):
        """All processFrame should do is move the session from
           non-authenticated to authenticated.
        """
        self.channel.deallocateMsgno(theframe.msgno)
	try:
            error = self.parseError(theframe.payload)
            if error:
                log.error("Error while authenticating: %s: %s" % (error[1], error[2]))
                return

            status = self.parseStatus(theframe.payload)
            if status:
                # do status code processing
                log.debug("status: %s" % status)
                if status == 'complete':

                    self.session.authenticationSucceeded()

                elif status == 'abort':
                    # other end has aborted negotiation, so we reset
                    # to our initial state
                    self.authentid = None
                    self.authid = None

                elif status == 'continue':
                    log.debug("continue during authentication")

            else:
                authentid = self.decodeBlob(theframe.payload)
                if authentid:
                    log.debug("authentid: %s" % authentid)
                    self.authentid = authentid
                    # I've now dealt with the message sufficiently for it to
                    # be marked as such, so we deallocate the msgno
                    self.channel.deallocateMsgno(theframe.msgno)

                    data = '<blob status="complete"/>'
                    self.channel.sendReply(theframe.msgno, data)
                    log.debug("Queued success message")

#                    self.session.authenticationComplete()

        except Exception, e:
            traceback.print_exc()
            raise TerminalProfileException("Exception: %s" % e)
            
    def sendAuth(self, authentid, authid=None):
        self.authentid = authentid
        data = self.encodeBlob(authentid)
        return self.channel.sendMessage(data)
