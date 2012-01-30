# $Id: echoprofile.py,v 1.10 2004/09/28 01:19:20 jpwarren Exp $
# $Revision: 1.10 $
#
#    BEEPy - A Python BEEP Library
#    Copyright (c) 2002-2004 Justin Warren <daedalus@eigenmagic.com>
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
EchoProfile implements an example profile that simply
echoes back whatever the content of a frame is.
It sends a Reply to each Message it receives.
"""

#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import profile

class EchoProfile(profile.Profile):
    """
    A very basic example profile that just echos frames.
    """

    #uri = "http://www.eigenmagic.com/beep/ECHO"
    uri = "http://xml.resource.org/profiles/NULL/ECHO"

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
