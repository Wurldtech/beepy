# $Id: saslanonymousprofile.py,v 1.15 2007/09/03 03:20:13 jpwarren Exp $
# $Revision: 1.15 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

"""
This module implements the SASL ANONYMOUS mechanism as a
BEEPy profile.

@version: $Revision: 1.15 $
@author: Justin Warren
"""

__profileClass__ = "SASLAnonymousProfile"
uri = "http://iana.org/beep/SASL/ANONYMOUS"

#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import saslprofile
from profile import TerminalProfileException

import traceback

class SASLAnonymousProfile(saslprofile.SASLProfile):
    """
    A SASLAnonymousProfile is a SASL Profile that implements
    the ANONYMOUS mechanism for anonymous authentication.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        saslprofile.SASLProfile.__init__(self, session)
        log.debug("initstring: %s" % profileInit)

    def processMessage(self, msg):
        """
        All processFrame should do is move the session from
        non-authenticated to authenticated.
        """
	try:
            error = self.parseError(msg.payload)
            if error:
                log.error("Error while authenticating: %s: %s" % (error[1], error[2]))
                return

            status = self.parseStatus(msg.payload)
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
                authentid = self.decodeBlob(msg.payload)
                if authentid:
                    log.debug("authentid: %s" % authentid)
                    self.authentid = authentid
                    # I've now dealt with the message sufficiently for it to
                    # be marked as such, so we deallocate the msgno
                    self.channel.deallocateMsgno(msg.msgno)

                    data = '<blob status="complete"/>'
                    self.channel.sendReply(msg.msgno, data)
                    log.debug("Queued success message")

#                    self.session.authenticationComplete()

        except Exception, e:
            traceback.print_exc()
            raise TerminalProfileException("Exception: %s" % e)
            
    def sendAuth(self, authentid, authid=None):
        """
        Send my authentication identification to the remove peer.
        """
        self.authentid = authentid
        data = self.encodeBlob(authentid)
        return self.channel.sendMessage(data)
