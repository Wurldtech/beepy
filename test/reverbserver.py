# $Id: reverbserver.py,v 1.4 2007/07/28 01:45:23 jpwarren Exp $
# $Revision: 1.4 $
#
# BEEPy - A Python BEEP Library
# Copyright (c) 2002-2007 Justin Warren <daedalus@eigenmagic.com>


import sys
sys.path.append('..')

import logging
from beepy.core import debug

log = logging.getLogger('reverbserver')

from beepy.profiles import echoprofile, reverbprofile
#from beepy.transports.tcp import BeepProtocol
from beepy.transports.tcp import BeepServerFactory
from twisted.internet import reactor

from twisted.application import internet, service

def initReverbProfile(profileInst):
    
    """
    This initialisation method is required to give
    the profile access to a reactor method which
    calls a method later on.

    This allows us to add arbitrary functionality
    into a profile at runtime. Neat eh?
    """
    log.debug('reverb profile initializing')
    profileInst.callLater = reactor.callLater
    
factory = BeepServerFactory()
factory.addProfile(reverbprofile, initReverbProfile)

application = service.Application('reverb-beep')
serviceCollection = service.IServiceCollection(application)
internet.TCPServer(1976, factory).setServiceParent(serviceCollection)

