# $Id: echoprofile.py,v 1.3 2003/12/08 03:25:30 jpwarren Exp $
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
# EchoProfile implements an example profile that simply
# echoes back whatever the content of a frame is.
# It sends a Reply to each Message it receives.

__profileClass__ = "EchoProfile"
uri = "http://www.eigenmagic.com/beep/ECHO"

import profile
import logging
from beepy.core import debug

log = logging.getLogger(__profileClass__)

class EchoProfile(profile.Profile):

    def __init__(self, session, profileInit=None, init_callback=None):
        profile.Profile.__init__(self, session)
        self.numReplies = 0

    def processFrame(self, theframe):
        log.debug("EchoProfile: processing frame: %s" % theframe)
        try:
            if theframe.isMSG():
                log.debug("EchoProfile: sending RPY")
                self.channel.sendReply(theframe.msgno, theframe.payload)
                
            if theframe.isRPY():
                self.channel.deallocateMsgno(theframe.msgno)
                self.numReplies += 1
                log.debug('numReplies == %s' % self.numReplies)
                if self.numReplies > 5:
                    self.session.shutdown()

        except Exception, e:
            raise profile.TerminalProfileException("Exception echoing: %s" % e)
