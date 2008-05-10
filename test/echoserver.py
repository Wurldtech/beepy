#!/usr/bin/twistd -ny
# $Id: echoserver.py,v 1.7 2008/05/10 03:04:12 jpwarren Exp $
# $Revision: 1.7 $
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

sys.path.insert(0, '..')

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepServerFactory
from twisted.application import internet, service


factory = BeepServerFactory()
factory.addProfile(echoprofile.EchoProfile)

application = service.Application('echobeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

