# $Id: reverbprofile.py,v 1.2 2003/12/08 03:25:30 jpwarren Exp $
# $Revision: 1.2 $
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
# ReverbProfile is an extended example of the EchoServer that echos back
# multiple frames. It received a MSG frame with a payload of the form:
# <repeat_number> <delay> <content>
# Where <repeat_number> is the number of times to echo the <content>
# and <delay> is how long in seconds to delay between echos.
#
# Each echo is sent as an ANS frame.
# MSG frames that are not in the above format and replied to with an
# ERR frame.

__profileClass__ = "ReverbProfile"
uri = "http://www.eigenmagic.com/beep/REVERB"

import profile

import string
import time

import logging
log = logging.getLogger(__profileClass__)

class ReverbProfile(profile.Profile):

    def __init__(self, session, profileInit=None):
        profile.Profile.__init__(self, log, session, profileInit)

        self.reverbDict = {}

    def processFrame(self, theframe):

        # Do any historical echoing
        for msgno in self.reverbDict.keys():
            if self.reverbDict[msgno][0] + self.reverbDict[msgno][2] <= time.time():
                self.channel.sendAnswer(msgno, self.reverbDict[msgno][3])
                self.reverbDict[msgno][1] -= 1
                self.reverbDict[msgno][0] = time.time()

                log.debug("Reverb sent for msgno %d. %d reverbs left to do." % (msgno, self.reverbDict[msgno][1]) )

                if self.reverbDict[msgno][1] <= 0:
                    self.channel.sendNul(msgno)
                    del self.reverbDict[msgno]
                    pass
                pass
            pass
        
	try:
            if theframe.isMSG():
                # MSG frame, so parse out what to do
                self.parseMSG(theframe)
                pass

            if theframe.isRPY():
                self.channel.deallocateMsgno(theframe.msgno)
                pass

            if theframe.isERR():
                self.channel.deallocateMsgno(theframe.msgno)
                pass

            if theframe.isNUL():
                self.channel.deallocateMsgno(theframe.msgno)
                pass
            pass

        except Exception, e:
            raise profile.TerminalProfileException("Exception reverbing: %s" % e)

    def parseMSG(self, theframe):
        """parseMSG grabs the MSG payload and works out what to do
        """
        try:
            number, delay, content = string.split(theframe.payload, ' ', 3)
            number = string.atoi(number)
            delay = string.atoi(delay)
            self.log.logmsg(logging.LOG_DEBUG, "number: %d" % number)
            self.log.logmsg(logging.LOG_DEBUG, "delay: %d" % delay)
            self.log.logmsg(logging.LOG_DEBUG, "content: %s" % content)

            if number <= 0:
                self.channel.sendError(theframe.msgno, 'Cannot echo a frame %d times.\n' % number)

            else:
                log.debug("Adding reverb for msgno: %d, %d times with %d second delay" % (theframe.msgno, number, delay) )
                self.reverbDict[theframe.msgno] = [time.time(), number, delay, content]

        except ValueError:
            # A ValueError means the payload format is wrong.
            self.channel.sendError(theframe.msgno, 'Payload format incorrect\n')

