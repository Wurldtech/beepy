# $Id: test_saslanonymousprofile.py,v 1.8 2003/12/09 02:37:31 jpwarren Exp $
# $Revision: 1.8 $
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

import unittest
import sys
import time
import threading
import logging

sys.path.append('../')

from beepy.transports.twistedsession import SASLClientProtocol
from beepy.transports.twistedsession import SASLClientFactory

from twisted.internet import reactor

from beepy.profiles import saslanonymousprofile
from beepy.profiles import echoprofile

from beepy.core import debug
log = logging.getLogger('SASLAnonymousTest')

class SASLAnonClientProtocol(SASLClientProtocol):
    """ We subclass from the SASLClientProtocol so that
    we can define what should happen when various events
    occur.
    """
    def greetingReceived(self):

        ## Start a channel using the SASL/ANONYMOUS profile
        self.authchannel = self.newChannel(saslanonymousprofile)
        log.debug('attempting to start channel %d...' % self.authchannel)

    def channelStarted(self, channelnum):
        log.debug('started channel %d', channelnum)
        if channelnum == self.authchannel:
            log.debug('Authentication channel started successfully.')
            channel = self.getChannel(channelnum)
            msgno = channel.profile.sendAuth('hello!')

        elif channelnum == self.echochannel:
            log.debug('Echo channel started successfully.')
            channel = self.getChannel(channelnum)
            msgno = channel.sendMessage('Echo 1!')
            msgno = channel.sendMessage('Echo 2!')
            msgno = channel.sendMessage('Echo 3!')
            msgno = channel.sendMessage('Echo 4!')
            msgno = channel.sendMessage('Echo 5!')
            msgno = channel.sendMessage('Echo 6!')

        else:
            log.debug('Unknown channel created: %d' % channelnum)

    def authenticationSucceeded(self):
        log.debug('overloaded authComplete')
        self.echochannel = self.newChannel(echoprofile)

class SASLAnonClientFactory(SASLClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = SASLAnonClientProtocol

class SASLAnonymousProfileTest(unittest.TestCase):

    def test_SASLClient(self):
        """Test SASL Anonymous with Initiator"""

        factory = SASLAnonClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslanonymousprofile)

        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()


if __name__ == '__main__':

    unittest.main()

