# $Id: timeserver.py,v 1.4 2007/07/28 01:45:24 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>


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

