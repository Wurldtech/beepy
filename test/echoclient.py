#!/usr/bin/twistd -ny
# $Id: echoclient.py,v 1.8 2004/09/28 01:19:21 jpwarren Exp $
# $Revision: 1.8 $
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

import sys

sys.path.insert(0, '..')

from twisted.python import log

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

log.startLogging(sys.stdout)

## Ok, let's define our client application

class EchoClientProtocol(BeepClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.msg('echo protocol client has greeting')
        self.newChannel(echoprofile.EchoProfile)

    def channelStarted(self, channelnum, uri):
        log.msg('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.sendMessage('Hello World!')
        log.msg('Sent message with id: %s' % msgno)
        msgno = channel.sendMessage('Hello World 1!')
        msgno = channel.sendMessage('Hello World 2!')
        msgno = channel.sendMessage('Hello World 3!')
        msgno = channel.sendMessage('Hello World 4!')
        msgno = channel.sendMessage('Hello World 5!')
        self.shutdown()

class EchoClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = EchoClientProtocol

    def clientConnectionLost(self, connection, reason):
        BeepClientFactory.clientConnectionLost(self, connection, reason)
        reactor.stop()

if __name__ == '__main__':
    factory = EchoClientFactory()
    factory.addProfile(echoprofile.EchoProfile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

