# $Id: reverbclient.py,v 1.4 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import sys
sys.path.append('..')

from beepy.profiles import reverbprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

import logging
from beepy.core import debug

log = logging.getLogger('reverbclient')

## Ok, let's define our client application

class ReverbClientProtocol(BeepClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('reverb protocol client has greeting')
        self.newChannel(reverbprofile)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.profile.requestReverb(5, 1, 'Reverb 1')
        msgno = channel.profile.requestReverb(5, 2, 'Reverb 2')        
        log.debug('Sent message with id: %s' % msgno)
#        msgno = channel.sendMessage('Hello World 2!')
#        msgno = channel.sendMessage('Hello World 3!')
#        msgno = channel.sendMessage('Hello World 4!')
#        msgno = channel.sendMessage('Hello World 5!')
#        self.shutdown()

class ReverbClientFactory(BeepClientFactory):
    """ This is a short factory for reverb clients
    """
    protocol = ReverbClientProtocol


if __name__ == '__main__':
    factory = ReverbClientFactory()
    factory.addProfile(reverbprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

