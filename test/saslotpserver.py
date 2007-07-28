# $Id: saslotpserver.py,v 1.4 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>
#

import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.profiles import saslotpprofile
from beepy.transports.tcp import SASLServerFactory

from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug

log = debug.log

factory = SASLServerFactory()
factory.addProfile(echoprofile)
factory.addProfile(saslotpprofile)

application = service.Application('saslanonybeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

