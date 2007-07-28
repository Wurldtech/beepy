# $Id: timeprofile.py,v 1.4 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#
"""
TimeProfile implements an example profile that sends
the current time to the remote peer every second.

After a TimeProfile channel is started, a peer asks to
receive the time every n seconds by sending a MSG
with the following payload::

time N

where N is the interval in seconds between when the time
should be sent. For example, to send the time every 5 seconds,
a peer would ask for::

time 5

To stop the timeserver from sending timing messages, the client
send a MSG containing the following payload::

stop

The server will then issue a final time ANS message and stop sending
the time.
"""
__profileClass__ = "TimeProfile"
uri = "http://www.eigenmagic.com/beep/TIME"

#import logging
from beepy.core.debug import log
#log = logging.getLogger('beepy')

import profile

import time
import traceback

class TimeProfile(profile.Profile):
    """
    A very basic example profile that just echos frames.
    """

    def __init__(self, session, profileInit=None, init_callback=None):

        ## This is a method used to execute something at
        ## a later stage. It gets passed in from the upper
        ## layer that manages scheduling, such as a twisted reactor
        self.callLater = None
        self.interval = 1
        self.sending = 0
        self.msgno = 0

        self.gotanswers = 0
        
        profile.Profile.__init__(self, session, profileInit, init_callback)

        log.debug('finished initialising: %s' % self.callLater)
        
    def processMessage(self, msg):
        """
        Get the time every 5 seconds.
        
        @raise profile.TerminalProfileException: if any exception occurs
        during processing.
        """
        log.debug("processing message: %s" % msg)
        try:
            if msg.isMSG():
                command = msg.payload.split()
                log.debug('command is: %s' % command)
                if command[0] == 'time':
                    log.debug('request for timing start')

                    if not command[1]:
                        log.debug('no time variable received')
                        self.channel.sendError(msg.msgno, 'No time interval specified\n')
                        return
                    
                    try:
                        interval = int(command[1])
                    except ValueError, e:
                        log.debug('FIXME! interval not an integer')
                        self.channel.sendError(msg.msgno, 'Interval not an integer\n')
                        return

                    log.debug('request to send time every %d seconds' % interval)
                    self.sending = 1
                    self.interval = interval
                    self.msgno = msg.msgno
                    log.debug('scheduling callLater: %s' % self.callLater)
                    self.callLater(self.interval, self.sendTime)
                    
                elif command[0] == 'stop':
                    self.sending = 0
                    self.channel.sendReply(msg.msgno, 'Ok')
                    self.channel.sendNul(self.msgno)
                
            if msg.isRPY():
                self.channel.deallocateMsgno(msg.msgno)
                log.debug('got RPY')

            if msg.isANS():
                log.debug('got ANS: %s' % msg)
                self.gotanswers += 1

                ## Stop getting the time after 5 of them
                if self.gotanswers > 5:
                    self.channel.sendMessage('stop')

            if msg.isNUL():
                self.channel.deallocateMsgno(msg.msgno)
                log.debug("got NUL. Guess I'm stopping.")
                self.session.shutdown()

        except Exception, e:
            traceback.print_exc()
            raise profile.TerminalProfileException("Exception echoing: %s" % e)

    def sendTime(self):
        """
        This method gets called every self.interval
        """
        if self.sending:
            ## We've been asked to stop sending, so we
            ## send one more ANS and then stop.
            log.debug('sending answer to msgno: %s' % self.msgno)
            self.channel.sendAnswer(self.msgno, 'The time is: %s\n' % time.asctime())
            self.callLater(self.interval, self.sendTime)

