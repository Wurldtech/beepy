# $Id: echoserver.py,v 1.6 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.6 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>


import sys
sys.path.append('..')

from beepy.profiles import echoprofile
from beepy.transports.tcp import BeepServerFactory
from twisted.application import internet, service

# Put this here so we override twisted's logging
import logging
from beepy.core import debug

factory = BeepServerFactory()
factory.addProfile(echoprofile)

application = service.Application('echobeep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

