# $Id: tlsserver.py,v 1.7 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.7 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
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

