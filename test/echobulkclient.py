# $Id: echobulkclient.py,v 1.2 2004/08/02 09:46:08 jpwarren Exp $
# $Revision: 1.2 $
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
This file defines a client for testing multi-channel priorities and
SEQ frames. The idea is that I need some way to test out the efficiency
of the window sizing mechanisms within the TCP transport that comes with
BEEPy to make it useful in the majority of cases.

It's easy enough to override if you want to build one yourself, but I
want the default to be reasonable.

This client creates 3 channels with different priorities and sends a
big chunk of data across them. Each channel is started to support the
ECHO profile for testing it out. The idea is that the channel with the
highest priority should finish first, followed by the second highest
priority and finally by the last.

I'll probably tweak the parameters of this client so that I can test a
few different scenarios. I do a lot of performance testing in my day job,
so this shouldn't be that much different.
"""

import sys
sys.path.append('..')
import time

import logging
from beepy.core import debug
log = logging.getLogger('beepy')

import bulkechoprofile
#from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepClientProtocol, BeepClientFactory
from beepy.transports.tcp import reactor

class EchoClientProtocol(BeepClientProtocol):
    """ We subclass from the BeepClientProtocol so that
    we can define what should happen when varies events
    occur.
    """
    def greetingReceived(self):
        log.debug('echo protocol client has greeting')
        self.channel1 = self.newChannel(bulkechoprofile)
        self.channel2 = self.newChannel(bulkechoprofile)
        self.channel3 = self.newChannel(bulkechoprofile)

        self.factory.channelStats = {}

    def channelStarted(self, channelnum, uri):
        log.debug('started channel %d', channelnum)
        self.factory.channelStats[channelnum] = {}

        ## Set channel priorities
        channel = self.getChannel(channelnum)
        
        if channelnum == self.channel1:
            channel.setPriority(9)
        elif channelnum == self.channel2:
            channel.setPriority(10)
        elif channelnum == self.channel3:
            channel.setPriority(0)

        ## once the channel priority has been set, send
        ## some large message
        fd = open('bulkechoprofile.py', 'r')
        data = fd.read()
        fd.close()

        self.factory.channelStats[channelnum]['starttime'] = time.time()

        msgno = channel.sendMessage(data)
        log.debug('Sent message with id: %s' % msgno)

    def channelClosed(self, channelnum):
        log.debug('%d channels left.' % len(self.channels))
        if len(self.channels) == 1:
            self.shutdown()
        if len(self.channels) == 0:
            self.close()
        else:
            self.factory.channelStats[channelnum]['endtime'] = time.time()
            
class EchoClientFactory(BeepClientFactory):
    """ This is a short factory for echo clients
    """
    protocol = EchoClientProtocol

    def clientConnectionLost(self, connection, reason):
        BeepClientFactory.clientConnectionLost(self, connection, reason)
        factory.showStats()
        reactor.stop()

    def showStats(self):
        for chan in self.channelStats.keys():
            log.info('chan %s elapsed time: %s' % (chan, self.channelStats[chan]['endtime'] - self.channelStats[chan]['starttime']))

if __name__ == '__main__':
    factory = EchoClientFactory()
    factory.addProfile(bulkechoprofile)

    reactor.connectTCP('localhost', 1976, factory)
    reactor.run()
