# $Id: test_saslotpprofile.py,v 1.16 2004/09/28 01:19:21 jpwarren Exp $
# $Revision: 1.16 $
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

import unittest
import sys
import time

sys.path.append('..')

from beepy.core.debug import log

from beepy.transports.tcp import SASLServerProtocol
from beepy.transports.tcp import SASLServerFactory
from beepy.transports.tcp import SASLClientProtocol
from beepy.transports.tcp import SASLClientFactory

from beepy.transports.tcp import reactor

from beepy.profiles import saslotpprofile
from beepy.profiles import echoprofile

class SASLOTPClientProtocol(SASLClientProtocol):
    """ We subclass from SASLClientProtocol to define
    what we want to do when various events occur
    """
    username = 'fred'
    passphrase = 'This is a test'
    
    def greetingReceived(self):

        ## Start a channel using the SASL/OTP profile
        self.authchannel = self.newChannel(saslotpprofile)
        log.debug('attempting to start channel %d...' % self.authchannel)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        if channelnum == self.authchannel:
            log.debug('Authentication channel started successfully.')
            

            channel = self.getChannel(channelnum)
            msgno = channel.profile.sendAuth(self.passphrase, self.username)

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

class SASLOTPClientFactory(SASLClientFactory):

    protocol = SASLOTPClientProtocol

class SASLOTPServerProtocol(SASLServerProtocol):

    def connectionLost(self, reason):
        reactor.stop()

class SASLOTPServerFactory(SASLServerFactory):
  
    protocol = SASLOTPServerProtocol

class SASLOTPProfileTest(unittest.TestCase):

    def setUp(self):
        factory = SASLOTPServerFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslotpprofile)
        reactor.listenTCP(1976, factory, interface='127.0.0.1')

        ## We create a new testing OTP database for
        ## testing the library. This assumes the server
        ## is running in the same directory as this tester
        generator = saslotpprofile.OTPGenerator()
        username = 'fred'
        seed = 'TeSt'
        passphrase = 'This is a test'
        algo = 'md5'
        sequence = 99

        passhash = generator.createOTP(username, algo, seed, passphrase, sequence)

    def test_createSASLOTPSession(self):
        """Test SASL OTP with no CDATA init"""

        factory = SASLOTPClientFactory()
        factory.addProfile(echoprofile)
        factory.addProfile(saslotpprofile)

#        log.debug("Reactor state: %s" % reactor.removeAll())

        reactor.connectTCP('localhost', 1976, factory)
        reactor.run()

        if factory.reason:
            log.error("Error occurred in factory: %s" % factory.reason)
            raise Exception(factory.reason.getErrorMessage())

if __name__ == '__main__':

    unittest.main()

