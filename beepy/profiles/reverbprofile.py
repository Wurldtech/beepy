# $Id: reverbprofile.py,v 1.5 2004/07/24 06:33:48 jpwarren Exp $
# $Revision: 1.5 $
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
ReverbProfile is an extended example of the EchoServer that echos back
multiple frames. It received a MSG frame with a payload of the form:
<repeat_number> <delay> <content>
Where <repeat_number> is the number of times to echo the <content>
and <delay> is how long in seconds to delay between echos.

Each echo is sent as an ANS frame.
MSG frames that are not in the above format and replied to with an
ERR frame.
"""
import logging
from beepy.core import debug
log = logging.getLogger('beepy')

__profileClass__ = "ReverbProfile"
uri = "http://www.eigenmagic.com/beep/REVERB"

import profile

import string
import time

class ReverbProfile(profile.Profile):

    def __init__(self, session, profileInit=None, init_callback=None):
        self.callLater = None

        self.msgno = 0
        
        profile.Profile.__init__(self, session, profileInit, init_callback)

        self.reverbDict = {}
        self.replyDict = {}

    def processMessage(self, msg):

	try:
            if msg.isMSG():
                # MSG frame, so parse out what to do
                self.parseMSG(msg)
                pass

            if msg.isANS():
                log.debug('Got reverb reply: %s' % msg.payload)

            if msg.isRPY():
                self.channel.deallocateMsgno(msg.msgno)
                pass

            if msg.isERR():
                self.channel.deallocateMsgno(msg.msgno)
                pass

            if msg.isNUL():

                log.debug('Got final message for %s' % msg.msgno)
                del self.replyDict[msg.msgno]
                self.channel.deallocateMsgno(msg.msgno)
                ## If I've got all my reverb replies, finish
                if len(self.replyDict) == 0:
                    log.debug('All reverbs received. Finishing...')
                    self.session.shutdown()
                pass
            pass

        except Exception, e:
            raise profile.TerminalProfileException("Exception reverbing: %s: %s" % ( e.__class__, e) )

    def parseMSG(self, msg):
        """parseMSG grabs the MSG payload and works out what to do
        """
        try:
            number, delay, content = string.split(msg.payload, ' ', 2)
            number = int(number)
            delay = int(delay)
            log.debug("number: %d" % number)
            log.debug("delay: %d" % delay)
            log.debug("content: %s" % content)

            if number <= 0:
                self.channel.sendError(msg.msgno, 'Cannot echo a frame %d times.\n' % number)

            else:
                log.debug("Adding reverb for msgno: %d, %d times with %d second delay" % (msg.msgno, number, delay) )
                self.reverbDict[msg.msgno] = [number, delay, content]
                self.callLater(delay, self.sendReverb, (msg.msgno) )

        except ValueError, e:
            # A ValueError means the payload format is wrong.
            log.error('Payload format incorrect: %s' % e)
            self.channel.sendError(msg.msgno, 'Payload format incorrect\n')

    def sendReverb(self, msgno):
        """
        Send the reverb for the given msgno.
        """
        number, delay, content = self.reverbDict[msgno]

        ## send the reverb

        ## Check to see if this is the last response
        number -= 1
        if number <= 0:
            self.channel.sendAnswer(msgno, content)
            self.channel.sendNul(msgno)
            del self.reverbDict[msgno]

        ## Otherwise, set up the next reverb call
        else:
            self.channel.sendAnswer(msgno, content)
            self.reverbDict[msgno][0] = number
            self.callLater(delay, self.sendReverb, (msgno) )
        
    def requestReverb(self, number, delay, content):
        """
        Ask the remote end to reverb back to me
        """
        msgno = self.channel.sendMessage('%s %s %s' % (number, delay, content) )

        ## Record what I've asked for
        self.replyDict[msgno] = [ number, delay, content ]
        log.debug('Started replyDict: %s' % self.replyDict)

        return msgno
