# $Id: timeclient.py,v 1.2 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.2 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import sys
sys.path.append('..')

from beepy.profiles import timeprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

import logging
from beepy.core import debug

log = logging.getLogger('timeclient')

## Ok, let's define our client application

class TimeClientProtocol(BeepClientProtocol):
    """
    We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        self.newChannel(timeprofile)

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.sendMessage('time 1')

class TimeClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = TimeClientProtocol

def initTimeProfile(profileInst):
    """
    This initialisation method is required to give
    the profile access to a reactor method which
    calls a method later on.

    This allows us to add arbitrary functionality
    into a profile at runtime. Neat eh?
    """
    log.debug('time profile initializing')
    profileInst.callLater = reactor.callLater

if __name__ == '__main__':
    factory = TimeClientFactory()
    factory.addProfile(timeprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

