# $Id: tlsserver.py,v 1.6 2004/09/28 01:19:22 jpwarren Exp $
# $Revision: 1.6 $
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
sys.path.append('..')

from beepy.profiles import tlsprofile
from beepy.profiles import echoprofile

from beepy.transports.tls import TLSServerFactory

from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug

log = logging.getLogger('tls-server')

factory = TLSServerFactory()
factory.addProfile(echoprofile)
factory.addProfile(tlsprofile)

factory.privateKeyFileName = 'serverKey.pem'
factory.certificateFileName = 'serverCert.pem'

application = service.Application('tls-server')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

