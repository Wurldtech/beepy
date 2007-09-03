# $Id: echoprofile.py,v 1.12 2007/09/03 03:20:12 jpwarren Exp $
# $Revision: 1.12 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
"""
EchoProfile implements an example profile that simply
echoes back whatever the content of a frame is.
It sends a Reply to each Message it receives.
"""
__profileClass__ = "EchoProfile"
uri = "http://www.eigenmagic.com/beep/ECHO"

#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import profile

class EchoProfile(profile.Profile):
    """
    A very basic example profile that just echos frames.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        profile.Profile.__init__(self, session)
        self.numReplies = 0

    def processMessage(self, msg):
        """
        An EchoProfile simply sends a RPY to each MSG
        it receives containing the same payload as what was received.

        For demonstration purposes, this EchoProfile also asks the
        controlling session to shutdown() if more than 5 MSGs are
        received.

        @raise profile.TerminalProfileException: if any exception occurs
        during processing.
        """
#        log.debug("EchoProfile: processing message: %s" % msg)
        try:
            if msg.isMSG():
                log.debug("EchoProfile: sending RPY")
                self.channel.sendReply(msg.msgno, msg.payload)
                
            if msg.isRPY():
                self.channel.deallocateMsgno(msg.msgno)
                self.numReplies += 1
                log.debug('numReplies == %s' % self.numReplies)
                if self.numReplies > 5:
                    self.session.shutdown()

        except Exception, e:
            raise profile.TerminalProfileException("Exception echoing: %s" % e)
