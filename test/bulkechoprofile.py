# $Id: bulkechoprofile.py,v 1.1 2004/07/24 06:33:49 jpwarren Exp $
# $Revision: 1.1 $
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
EchoProfile implements an example profile that simply
echoes back whatever the content of a frame is.
It sends a Reply to each Message it receives.
"""
__profileClass__ = "BulkEchoProfile"
uri = "http://www.eigenmagic.com/beep/ECHO"

import sys
sys.path.append('..')

import logging
from beepy.core import debug
log = logging.getLogger('beepy')

from beepy.profiles import profile
import time

class BulkEchoProfile(profile.Profile):
    """
    A testing profile for checking bulk transfer capabilities.
    """

    def __init__(self, session, profileInit=None, init_callback=None):
        profile.Profile.__init__(self, session)
        self.numReplies = 0

    def processMessage(self, msg):
        """
        When a complete message is received, update some statistics
        in my channel.

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
                self.channel.endtime = time.time()
#                self.numReplies += 1
#                log.debug('numReplies == %s' % self.numReplies)
#                if self.numReplies > 5:
#                log.error('shutting down bulkprofile')
                self.session.closeChannel(self.channel.channelnum)

        except Exception, e:
            raise profile.TerminalProfileException("Exception echoing: %s" % e)
