# $Id: timeserver.py,v 1.5 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.5 $
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


import sys
sys.path.append('..')

from beepy.profiles import timeprofile
from beepy.transports.tcp import BeepServerFactory
from twisted.application import internet, service
from twisted.internet import reactor

# Put this here so we override twisted's logging
import logging
from beepy.core import debug
log = debug.log

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

factory = BeepServerFactory()
factory.addProfile(timeprofile, initTimeProfile)

application = service.Application('timeserver')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

