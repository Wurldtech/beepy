# $Id: echoclient.py,v 1.3 2004/01/15 05:41:13 jpwarren Exp $
# $Revision: 1.3 $
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


import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

import logging
from beepy.core import debug

log = logging.getLogger('echoclient')

## Ok, let's define our client application

class EchoClientProtocol(BeepClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        self.newChannel(echoprofile)

    def channelStarted(self, channelnum):
        log.debug('started channel %d', channelnum)
        
        channel = self.getChannel(channelnum)
        msgno = channel.sendMessage('Hello World!')
        log.debug('Sent message with id: %s' % msgno)
        msgno = channel.sendMessage('Hello World 1!')
        msgno = channel.sendMessage('Hello World 2!')
        msgno = channel.sendMessage('Hello World 3!')
        msgno = channel.sendMessage('Hello World 4!')
        msgno = channel.sendMessage('Hello World 5!')

class EchoClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = EchoClientProtocol


if __name__ == '__main__':
    factory = EchoClientFactory()
    factory.addProfile(echoprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()

